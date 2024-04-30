import pandas as pd
import calendar
import os
import argparse
from tqdm import tqdm

from src.dictionaries import (
    RATE_FILE_NAMES_DIC,
    RATE_VAR_DIC,
    RATE_VARS,
    YEAR_NOW,
    GROUP_LIST,
    STATION_LIST_CSV,
    )

from src.fonctions import (
    compute_rates,
    get_outliers,
    list_of_strings,
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""
                                     This script compute :\n
                                        -   Monthly operational rates\n
                                        -   Monthly disponibility rate\n
                                        -   Accumulated lost rate\n
                                        -   Accumulated lost rate by\n
                                            indisponibility\n
                                     This, for a group of measuring stations.
                                     """,
    )
    parser.add_argument(
        "-i",
        "--indir",
        type=str,
        default="./data",
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
        "-s", "--station",
        type=list_of_strings,
        help="Single station",
        metavar="\b",
    )
    parser.add_argument(
        "-sl",
        "--station_list_path",
        type=str,
        help="""path/to/folder/stations_group.csv
        from get_physicals_and_site_info.py""",
        default="./data",
    )
    args = parser.parse_args()

    for group in args.group:
        print(f"Processing sites of {group} ...")
        name_list = f"{args.station_list_path}/{STATION_LIST_CSV[group]}"
        site_list = pd.read_csv(name_list, usecols=["id"])["id"].tolist()

        out_dir = f"{args.outdir}/rates/{args.year}/{group}"
        if os.path.exists(out_dir):
            for file in os.listdir(out_dir):
                os.remove(os.path.join(out_dir, file))
        else:
            os.makedirs(out_dir)

        for site in tqdm(site_list,
                         leave=False):

            csv_file = f"{args.indir}/{args.year}/{group}/{site}.csv"
            data = pd.read_csv(
                csv_file,
                low_memory=False,
                parse_dates=["date"]
                )
            get_outliers(
                    data,
                    threshold=5
                    ).to_csv(f"{out_dir}/outliers.csv",
                             mode="a",
                             header=(not os.path.exists(
                                 f"{out_dir}/outliers.csv")
                                 )
                             )
            ids = data["id"].unique()
            for id in tqdm(ids,
                           desc=site,
                           leave=False):
                model_df = pd.DataFrame(
                        [{"id": id,
                          "site": site,
                          "polluant": id.split(site[:3], 2)[0]}]
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

                id_data = data[data["id"] == id]

                for m in range(1, 13):
                    month_name = calendar.month_name[m]
                    month_data = id_data[id_data["date"].dt.month == m]

                    (month_rates,
                     total_count,
                     total_count_lost,
                     total_indisponibility_lost,
                     ) = compute_rates(
                            month_data,
                            acc_count,
                            acc_lost,
                            acc_indisponibility_lost,
                        )
                    acc_count = total_count
                    acc_lost = total_count_lost
                    acc_indisponibility_lost = total_indisponibility_lost

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
                    if RATE_VARS[n] == "dispo" or RATE_VARS[n] == "tauxfo":
                        rate_dfs[n][args.year] = (
                            rate_dfs[n][calendar.month_name[1:]].sum(axis=1)/12
                            )
                    if RATE_VARS[n] == "pert":
                        if rate_dfs[n][calendar.month_name[12]].values > 0.25:
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
