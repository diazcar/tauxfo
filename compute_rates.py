import sys
import os
import shutil
sys.path.insert(0, "./src")

import pandas as pd
import calendar
import datetime as dt
import argparse
from tqdm import tqdm

from src.dictionaries import (
    RATE_FILE_NAMES_DIC,
    RATE_VAR_DIC,
    RATE_VARS,
    YEAR_NOW,
    GROUP_LIST,
    )

from src.fonctions import (
    compute_rates,
    list_of_strings,
    current_days
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""
This script compute :
-   Monthly operational rates
-   Monthly disponibility rate
-   Accumulated lost rate
-   Accumulated lost rate by
    indisponibility
This, for a group of measuring stations.
            """,
        formatter_class=argparse.RawTextHelpFormatter,


    )
    parser.add_argument(
        "-i",
        "--indir",
        type=str,
        default=".",
        help="input data path directory",
        metavar="\b",
    )
    parser.add_argument(
        "-o",
        "--outdir",
        type=str,
        default=".",
        help="Output path directory",
        metavar="\b",
    )
    parser.add_argument(
        "-y",
        "--year",
        type=int,
        help="Year to compute",
        default=YEAR_NOW,
        metavar="\b",
    )
    parser.add_argument(
        "-g", "--group",
        help="Station group to process",
        type=list_of_strings,
        default=GROUP_LIST,
        metavar="\b",
    )
    parser.add_argument(
        "-sl",
        "--station_list_path",
        type=str,
        help="""path/to/folder/stations_group.csv
        from get_physicals_and_site_info.py""",
        default="./data",
        metavar="\b"
    )
    parser.add_argument("-clean",
                        type=str,
                        help="clean retrived data by year from Xair rest api",
                        metavar="\b")

    args = parser.parse_args()

    if args.clean:
        if args.year:
            dir_to_delete = f"{args.clean}/data/{args.year}"
            input_text = ("Are you sure that you want to delete data from :",
                          f"{dir_to_delete} (YES/NO) : ")
            if input("".join(input_text)) == "YES":
                if os.path.isdir(dir_to_delete):
                    shutil.rmtree(dir_to_delete)
                sys.exit(f"Directory {dir_to_delete} was cleaned")
            sys.exit("Cleaning interrupted.")
        else:
            sys.exit("Provide year to clean by setting [-y] option ")

    for group in args.group:
        print(f"Processing sites of {group} ...")
        name_list = f"{args.station_list_path}/stations_{group}.csv"
        site_list = pd.read_csv(name_list, usecols=["id"])["id"].tolist()

        poll_index = pd.read_csv(
            f"{args.station_list_path}/measures_{group}.csv",
            usecols=['id', 'phy_name']
            )

        if args.year != YEAR_NOW:
            year = args.year
            month = 12
        else:
            year = YEAR_NOW
            month = dt.datetime.now().month

        out_dir = f"{args.outdir}/rates/{year}/{group}"

        if os.path.exists(out_dir):
            for file in os.listdir(out_dir):
                os.remove(os.path.join(out_dir, file))
        else:
            os.makedirs(out_dir)

        for site in tqdm(site_list,
                         leave=False):

            csv_file = f"{args.indir}/data/{year}/{group}/{site}.csv"

            if os.path.exists(csv_file) is False:
                csv_file_exit_text = (
                    f"CSV file for {site} not found.",
                    f" Run : python -m get_data -y {year} -g {group}"
                    )
                sys.exit("".join(csv_file_exit_text))

            data = pd.read_csv(
                csv_file,
                low_memory=False,
                parse_dates=["date"]
                )
            ids = data["id"].unique()
            for id in tqdm(ids,
                           desc=site,
                           leave=False):
                model_df = pd.DataFrame(
                        [
                            {
                                "id": id,
                                "site": site,
                                "polluant": (
                                    poll_index[poll_index['id'] == id]
                                    ['phy_name']
                                    .values[0]
                                )
                            }
                        ]
                    )
                rate_dfs = [
                    model_df.copy(deep=True),
                    model_df.copy(deep=True),
                    model_df.copy(deep=True),
                    model_df.copy(deep=True),
                    model_df.copy(deep=True),
                ]
                acc_count = 2
                acc_lost = 0
                acc_indisponibility_lost = 0
                all_valid_count = 0
                all_disp_count = 0
                id_data = data[data["id"] == id]

                for m in range(1, month + 1):
                    month_name = calendar.month_name[m]
                    month_data = id_data[id_data["date"].dt.month == m]

                    (month_rates,
                     total_count,
                     total_count_lost,
                     total_indisponibility_lost,
                     disponibility_count,
                     valid_count
                     ) = compute_rates(
                            site,
                            month_data,
                            acc_count,
                            acc_lost,
                            acc_indisponibility_lost
                        )
                    acc_count = total_count
                    acc_lost = total_count_lost
                    acc_indisponibility_lost = total_indisponibility_lost
                    all_valid_count = all_valid_count + valid_count
                    all_disp_count = all_disp_count + disponibility_count

                    for n in range(5):

                        rate_dfs[n] = pd.concat(
                            [
                                rate_dfs[n],
                                pd.DataFrame(
                                    {
                                        month_name: month_rates[
                                            RATE_VAR_DIC[RATE_VARS[n]]
                                        ]
                                    }
                                ),
                            ],
                            axis=1,
                        )
                for n in range(5):
                    if RATE_VARS[n] == "dispo":
                        rate_dfs[n][year] = (
                            (
                                all_disp_count/(current_days(year, month)*96)
                             )
                        )
                    if RATE_VARS[n] == "tauxfo":
                        rate_dfs[n][year] = (
                            (
                                all_valid_count/(current_days(year, month)*96)
                             )
                        )
                    if RATE_VARS[n] == "pert":
                        if rate_dfs[n][calendar.month_name[month]].values > 1:
                            rate_dfs[n].to_csv(
                                f"{out_dir}/pert_repport.csv",
                                mode="a",
                                header=(not os.path.exists(
                                    f"{out_dir}/pert_repport.csv"
                                        )
                                    ),
                            )
                    file_name = RATE_FILE_NAMES_DIC[RATE_VARS[n]]
                    out_file_to_append = f"{out_dir}/{file_name}"
                    rate_dfs[n].to_csv(
                        out_file_to_append,
                        mode="a",
                        header=(not os.path.exists(out_file_to_append))
                    )
    print("DONE")
