import pandas as pd  # type: ignore
import requests  # type: ignore
import datetime as dt
import os

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

GROUP_LIST = ["DIDON"]
STATIONS_OUTFILE_DIC = {
    "DIDON": "./data/stations_DIDON.csv"
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
    data = requests.get(url, verify=False).json()
    return data[DATA_KEYS[folder]]


def build_csv_data(data, outfile):
    if os.path.exists(outfile):
        os.remove(outfile)
    for i in range(len(data[:])):
        if data[i]["sta"]["data"][0]["state"] != "N":
            id = data[i]["id"]
            df = pd.DataFrame(data[i]["sta"]["data"])
            df["id"] = id
            df.to_csv(outfile,
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


if __name__ == "__main__":

    sites = pd.read_csv("./data/sites.csv", usecols=["id"])["id"].tolist()
    output_file_path = f"./data/{sites[0]}.csv"
    startdate, enddate = data_time_window()
    request = request_xr(folder="data",
                         fromtime=startdate,
                         totime=enddate,
                         sites=sites[0],
                         )
    build_csv_data(request, output_file_path)
