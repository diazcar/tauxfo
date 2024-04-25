from calendar import monthrange
import warnings
import pandas as pd  # type: ignore
import requests  # type: ignore
import datetime as dt
import os
import argparse
from tqdm import tqdm

URL_DICT = {
    "data": "https://172.16.13.224:8443/dms-api/public/v2/data?",
    "sites": "https://172.16.13.224:8443/dms-api/public/v1/sites?",
    "physicals": "https://172.16.13.224:8443/dms-api/public/v1/physicals?",
}

DATA_KEYS = {
    "data": "data",
    "sites": "sites",
    "physicals": "physicals",
}

GROUP_LIST = ["DIDON", "V_NICE", "V_MARS", "V_MART"]

STATION_LIST_CSV = {
    "DIDON": "stations_DIDON.csv",
    "V_NICE": "stations_V_NICE.csv",
    "V_MARS": "stations_V_MARS.csv",
    "V_MART": "stations_V_MART.csv",

}


def request_xr(
    fromtime: str = "",
    totime: str = "",
    folder: str = "",
    datatypes: str = "base",
    groups: str = "",
    sites: str = "",
):
    """
    Get json objects from XR rest api

    input :
    -------
        fromtime : str
            Start time  in YYYY-MM-DDThh:mm:ssZ format
        totime : str
            End time  in YYYY-MM-DDThh:mm:ssZ format
        folder : str
            Url string to request XR rest api
            Default = "data"
        dataTypes : str,
            Time mean in base(15min), hour, day, month
            Default = "base"
        groups : str
            Site groupes
            Default = "DIDON"
        sites : str
            site or list of sites to retrive
            Default = "" (all sistes)
    return :
    --------
        csv : csv file
            File in ../data directory
    """
    url = (
        f"{URL_DICT[folder]}&"
        f"from={fromtime}&"
        f"to={totime}&"
        f"sites={sites}&"
        f"dataTypes={datatypes}&"
        f"groups={groups}"
    )

    # SECURITY RISK IF IN PRODUCTION - ADD CERTIFICATE SSL VERIFICATION
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        data = requests.get(url, verify=False).json()
    return data[DATA_KEYS[folder]]


def build_csv_data(data, outfile):
    if os.path.exists(outfile):
        os.remove(outfile)
    for i in range(len(data[:])):
        header_df = pd.DataFrame(columns=['date',
                                          'id',
                                          'value',
                                          'unit',
                                          'state',
                                          'validated']
                                 )
        df = pd.DataFrame(data[i]["sta"]["data"])
        df["id"] = data[i]["id"]
        df["unit"] = data[i]["sta"]['unit']['id']
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning)
            out_df = pd.concat([header_df, df],
                               ignore_index=True,
                               sort=False)
        out_df.to_csv(outfile,
                      mode='a',
                      header=(not os.path.exists(outfile))
                      )


def data_time_window():
    """
    Select time window from month[0] to month[n-1]

    return :
    ------
    startdate : str
    endate : str
    """
    data_now = dt.datetime.now()
    y = data_now.strftime("%Y")
    m = data_now.strftime("%m")

    startdate = f"{y}-01-01T00:00:00Z"
    enddate = f"{y}-{m}-01T00:00:00Z"
    return (startdate, enddate)


def get_month_datetimes(start_date):
    start_dt = dt.datetime.strptime(start_date,
                                    "%Y-%m-%dT%H:%M:%SZ")
    year = int(start_dt.strftime('%Y'))
    month = int(start_dt.strftime('%m'))
    days = monthrange(year, month)[1]
    start_month_date = f'{year}-{str(month).zfill(2)}-01T00:00:00Z'
    end_month_date = f'{year}-{str(month).zfill(2)}-{days}T23:45:00Z'
    if month == 12:
        end_month_date = f'{year+1}-01-31T:00:00:00Z'
    return (start_month_date, end_month_date)


def list_of_strings(arg):
    return arg.split(',')


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
                        """)
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
    parser.add_argument("-g", "--group_list",
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
                        default="./data")

    args = parser.parse_args()

    for group in args.group_list:
        print(f"Retreving {group} group ...")
        if args.year:
            year_folder = str(args.year)
        else:
            year_folder = args.startdate.split("-", 1)[0]
        if os.path.exists(f"{args.outdir}/{year_folder}/{group}") is False:
            os.makedirs(f"{args.outdir}/{year_folder}/{group}")

        if args.station:
            sites = [args.station]
        else:
            sites_file_path = os.path.join(
                args.station_list_path,
                STATION_LIST_CSV[group]
                )
            sites = pd.read_csv(
                sites_file_path,
                usecols=["id"]
                )["id"].tolist()
        for s in sites:
            i = i + 1
            output_file_path = f"{args.outdir}/{year_folder}/{group}/{s}.csv"
            if args.year:
                end_month = 12
                start_date = f"{args.year}-01-01T00:00:00Z"
            else:
                start_date = args.startdate
                end_dto = dt.datetime.strptime(args.enddate,
                                               "%Y-%m-%dT%H:%M:%SZ")
                end_month = int(end_dto.strftime('%m'))

            for month in tqdm(range(1, end_month+1),
                              desc=f"Retreving Data for {s}",
                              leave=False):
                sd, ed = get_month_datetimes(start_date)
                request = request_xr(folder="data",
                                     fromtime=sd,
                                     totime=ed,
                                     sites=s,
                                     )
                build_csv_data(request, output_file_path)
