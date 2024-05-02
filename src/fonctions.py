from calendar import monthrange
import os
import sys
import warnings
import numpy as np
import pandas as pd
import requests
import datetime as dt
from scipy import stats


from dictionaries import (
    URL_DICT,
    DATA_KEYS,
    )


def compute_rates(
    site: str,
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
        site : str
            Processing site
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
    O_ = data[data["state"] == "O"]["state"].count()
    R = data[data["state"] == "R"]["state"].count()
    P = data[data["state"] == "P"]["state"].count()
    N = data[data["state"] == "N"]["state"].count()
    Z = data[data["state"] == "Z"]["state"].count()
    C = data[data["state"] == "C"]["state"].count()
    D = data[data["state"] == "D"]["state"].count()
    M = data[data["state"] == "M"]["state"].count()
    I_ = data[data["state"] == "I"]["state"].count()

    month_count = data["id"].count()
    if month_count == 0:
        sys.exit(f"Corrupted or incomplete CSV file for site : {site}")
    total_count = month_count + acc_count

    month_disponibility_rate = (A + O_ + R + P + C + Z + M) / month_count
    valid_data = A + O_ + R + P
    month_operational_rate = valid_data / month_count

    total_count_lost = acc_lost + C + Z + M + D + N + I_
    overall_lost_rate = total_count_lost / 8760

    total_indisponibility_lost = acc_indisponibility_lost + D + N + I_
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
    for i in range(len(data[:])):
        cols = ['date', 'id', 'value', 'unit', 'state', 'validated']
        header_df = pd.DataFrame(columns=cols
                                 )
        df = pd.DataFrame(data[i]["sta"]["data"])
        df["id"] = data[i]["id"]
        df["unit"] = data[i]["sta"]['unit']['id']
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning)
            out_df = pd.concat([header_df, df],
                               join="inner",
                               ignore_index=True,
                               sort=False)
            for col in cols:
                if col not in out_df.columns:
                    out_df.insert(2, col, None)

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


def get_month_datetimes(start_date, month):
    start_dt = dt.datetime.strptime(start_date,
                                    "%Y-%m-%dT%H:%M:%SZ")
    year = int(start_dt.strftime('%Y'))
    days = monthrange(year, month)[1]
    start_month_date = f'{year}-{str(month).zfill(2)}-01T00:00:00Z'
    end_month_date = f'{year}-{str(month).zfill(2)}-{days}T23:45:00Z'
    if month == 12:
        end_month_date = f'{year+1}-01-01T00:00:00Z'
    return (start_month_date, end_month_date)


def list_of_strings(arg):
    return arg.split(',')
