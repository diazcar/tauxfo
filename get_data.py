import sys
import os
sys.path.insert(0, "./src")

import pandas as pd
import datetime as dt
import argparse
from tqdm import tqdm
import sys

from src.dictionaries import GROUP_LIST, YEAR_NOW

from src.fonctions import (
    build_csv_data,
    data_time_window,
    get_month_datetimes,
    list_of_strings,
    request_xr,
)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""
This script request data
from Xair rest api
        """,
        formatter_class=argparse.RawTextHelpFormatter,)
    parser.add_argument("-o",
                        "--outdir",
                        type=str,
                        default=".",
                        help="Output path directory",
                        metavar="\b")
    parser.add_argument("-y",
                        "--year",
                        type=int,
                        help="""
                        Year to retreve data
                        """,
                        default=YEAR_NOW,
                        metavar="\b")
    parser.add_argument("-sd",
                        "--startdate",
                        type=str,
                        help="""
                        Start date to retreve data 
                        like YYYY-MM-DDT00:00:00Z
                        """,
                        default=data_time_window()[0],
                        metavar="\b")
    parser.add_argument("-ed",
                        "--enddate",
                        type=str,
                        help="""
                        End date to retreve data 
                        like YYYY-MM-DDT00:00:00Z
                        """,
                        default=data_time_window()[1],
                        metavar="\b")
    parser.add_argument("-g", "--group",
                        type=list_of_strings,
                        help="Stations group",
                        default=GROUP_LIST,
                        metavar="\b")
    parser.add_argument("-s",
                        "--station",
                        type=list_of_strings,
                        help="Single station",
                        metavar="\b")
    parser.add_argument("-sl",
                        "--station_list_path",
                        type=str,
                        help="stations_GROUP.csv path",
                        default="./data",
                        metavar="\b")

    args = parser.parse_args()

    if args.station:
        sites = args.station
        for s in tqdm(sites, desc="SITES"):
            output_path = f"{args.outdir}/data/{args.year}"
            if os.path.exists(output_path) is False:
                os.makedirs(output_path)
            if args.year:
                end_month = 12
                start_date = f"{args.year}-01-01T00:00:00Z"
            else:
                start_date = args.startdate
                end_dto = dt.datetime.strptime(args.enddate,
                                               "%Y-%m-%dT%H:%M:%SZ")
                end_month = int(end_dto.strftime('%m'))

            if os.path.exists(f"{output_path}/{s}.csv"):
                os.remove(f"{output_path}/{s}.csv")
            for month in tqdm(range(1, end_month+1),
                              desc=f"Retreving Data for {s}",
                              leave=False):
                sd, ed = get_month_datetimes(start_date, month)
                request = request_xr(folder="data",
                                     fromtime=sd,
                                     totime=ed,
                                     sites=s,
                                     )
                build_csv_data(request, f"{output_path}/{s}.csv")
        sys.exit("Done.")

    for group in args.group:
        print(f"Retreving {group} group ...")
        if args.year:
            year_folder = str(args.year)
        else:
            year_folder = args.startdate.split("-", 1)[0]
        if os.path.exists(f"{args.outdir}/data/{year_folder}/{group}") is False:
            os.makedirs(f"{args.outdir}/data/{year_folder}/{group}")

        sites_file_path = os.path.join(
            args.station_list_path,
            f"stations_{group}.csv"
            )
        sites = pd.read_csv(
            sites_file_path,
            usecols=["id"]
            )["id"].tolist()

        for s in tqdm(sites, desc="SITES"):
            output_file_path = f"{args.outdir}/data/{year_folder}/{group}/{s}.csv"
            if args.year:
                end_month = 12
                start_date = f"{args.year}-01-01T00:00:00Z"
            else:
                start_date = args.startdate
                end_dto = dt.datetime.strptime(args.enddate,
                                               "%Y-%m-%dT%H:%M:%SZ")
                end_month = int(end_dto.strftime('%m'))
            if os.path.exists(output_file_path):
                os.remove(output_file_path)
            for month in tqdm(range(1, end_month+1),
                              desc=f"Retreving Data for {s}",
                              leave=False):
                sd, ed = get_month_datetimes(start_date, month)
                request = request_xr(folder="data",
                                     fromtime=sd,
                                     totime=ed,
                                     sites=s,
                                     )
                build_csv_data(request, output_file_path)
    print("Done.")
