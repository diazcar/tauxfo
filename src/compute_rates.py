import pandas as pd
import calendar
import os
import argparse
from datetime import datetime
from tqdm import tqdm
from scipy import stats
import numpy as np

from src.get_data import GROUP_LIST, STATION_LIST_CSV, list_of_strings

RATE_VARS = ["tauxfo", "dispo", "pert", "pert_indi", "max"]

RATE_FILE_NAMES_DIC = {
    "tauxfo": "tauxfo.csv",
    "pert": "pert.csv",
    "dispo": "dispo.csv",
    "pert_indi": "pert_indi.csv",
    "max": "monthly_max.csv",
}

RATE_VAR_DIC = {
    "tauxfo": "month_operational_rate",
    "dispo": "month_disponibility_rate",
    "pert": "overall_lost_rate",
    "pert_indi": "overall_indisponibility_lost",
    "max": "max",
}

state_code = [
    "A",
    "O",
    "R",
    "P",
    "W",
    "N",
    "Z",
    "C",
    "D",
    "M",
    "i",
]

YEAR_NOW = int(datetime.now().strftime("%Y"))


def compute_rates(
    data: pd.DataFrame,
    acc_count: int = 2,
    acc_lost: int = 0,
    acc_indisponibility_lost: int = 0,
):
    """
    This fonction compute :
        - Operational rate (Tauxfo)
        - Disponibility rate (Dispo)
        - Lost rate (Perte)
        - Los rate du to the indisponibility (Perte_indi)

    INPUTS
    ------
        data : dataframe
            Dataframe of a monthly data with state code of measuring stations
        acc_count : int
            last month count of validated data
        acc_lost : int
            las month count of lost data
        acc_indisponibility_lost : int
            Las month count of lost data du to indisponibility

    RETURN
    ------
        month_rates : dict
            Dictionary of monthly operational and disponibility rates and
            accumulated lost rates over the past months. As:
                {'month_disponibility_rate': int,
                'month_operational_rate': int,
                'overall_lost_rate': int,
                'overall_indisponibility_lost': int}
        total_count-1 : int
            validated accumulated count over the months
        total_count_lost : int
            accumulated lost count over the months
        total_indisponibility_lost : int
            accumulated lost du to indi. count over the months
    """
    A = data[data["state"] == "A"]["state"].count()
    O = data[data["state"] == "O"]["state"].count()
    R = data[data["state"] == "R"]["state"].count()
    P = data[data["state"] == "P"]["state"].count()
    N = data[data["state"] == "N"]["state"].count()
    Z = data[data["state"] == "Z"]["state"].count()
    C = data[data["state"] == "C"]["state"].count()
    D = data[data["state"] == "D"]["state"].count()
    M = data[data["state"] == "M"]["state"].count()
    I = data[data["state"] == "I"]["state"].count()

    month_count = data["id"].count()
    total_count = month_count + acc_count

    month_disponibility_rate = (A + O + R + P + C + Z + M) / month_count
    valid_data = A + O + R + P
    month_operational_rate = valid_data / month_count

    total_count_lost = acc_lost + C + Z + M + D + N + I
    overall_lost_rate = total_count_lost / 8760

    total_indisponibility_lost = acc_indisponibility_lost + D + N + I
    overall_indisponibility_lost = total_indisponibility_lost / 3504

    month_rates = {
        "month_disponibility_rate": [month_disponibility_rate],
        "month_operational_rate": [month_operational_rate],
        "overall_lost_rate": [overall_lost_rate],
        "overall_indisponibility_lost": [overall_indisponibility_lost],
        "max": [data[data['state'].isin(['A', 'O', 'R'])]['value'].max()],
    }

    return (
        month_rates,
        total_count - 1,
        total_count_lost,
        total_indisponibility_lost)


def get_outliers(in_data, threshold=1.5):
    data = in_data[(in_data['state'].isin(['A', 'O', 'R']))]
    z = np.abs(stats.zscore(data['value']))
    outliers = data[z > threshold]
    return (outliers)


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
