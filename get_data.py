import pandas as pd
import datetime as dt
import os
import argparse
from tqdm import tqdm
import sys

from src.dictionaries import (
    GROUP_LIST,
    STATION_LIST_CSV,
    )

from src.fonctions import (
    build_csv_data,
    data_time_window,
    get_month_datetimes,
    list_of_strings,
    request_xr,
)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""
                                     This script request data
                                     from Xair rest api
                                     """,)
    parser.add_argument("-o",
                        "--outdir",
                        type=str,
                        default="./data",
                        help="Output path directory",
                        metavar="\b")
    parser.add_argument("-y",
                        "--year",
                        type=int,
                        help="""
                        Year to retreve data
                        """,
                        metavar="\b")
    parser.add_argument("-sd",
                        "--startdate",
                        type=str,
                        help="""
                        Start date to retreve data like YYYY-MM-DDT00:00:00Z
                        """,
                        default=data_time_window()[0],
                        metavar="\b")
    parser.add_argument("-ed",
                        "--enddate",
                        type=str,
                        help="""
                        End date to retreve data like YYYY-MM-DDT00:00:00Z
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
                        help="path/to/folder/stations_group.csv",
                        default="./data",
                        metavar="\b")
    parser.add_argument("-clean",
                        type=str,
                        help="clean retrived data by year from Xair rest api",
                        default="./data",
                        metavar="\b")

    args = parser.parse_args()

    if args.clean:
        if args.year:
            print("ca marche")
            sys.exit(f"Directory {args.clean}/{args.year} was cleaned")
        else:
            sys.exit("Or provide year by setting [-y] option ")

    if args.station:
        sites = args.station
        for s in tqdm(sites, desc="SITES"):
            output_file_path = f"{args.outdir}/{s}.csv"
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
        sys.exit("Done.")

    for group in args.group_list:
        print(f"Retreving {group} group ...")
        if args.year:
            year_folder = str(args.year)
        else:
            year_folder = args.startdate.split("-", 1)[0]
        if os.path.exists(f"{args.outdir}/{year_folder}/{group}") is False:
            os.makedirs(f"{args.outdir}/{year_folder}/{group}")

        sites_file_path = os.path.join(
            args.station_list_path,
            STATION_LIST_CSV[group]
            )
        sites = pd.read_csv(
            sites_file_path,
            usecols=["id"]
            )["id"].tolist()

        for s in tqdm(sites, desc="SITES"):
            output_file_path = f"{args.outdir}/{year_folder}/{group}/{s}.csv"
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
