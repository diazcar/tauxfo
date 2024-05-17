import sys
import os
sys.path.insert(0, "./src")
from src.fonctions import request_xr, list_of_strings
from src.dictionaries import GROUP_LIST
import pandas as pd
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            description="""
This module retrive physicals information 
and a list of sites by GROUPS
            """,
            formatter_class=argparse.RawTextHelpFormatter,)
    parser.add_argument(
        "-o",
        "--outdir",
        type=str,
        default=".",
        help="Output path directory",
        metavar="\b")
    parser.add_argument(
        "-g", "--group",
        type=list_of_strings,
        help="Stations group",
        default=GROUP_LIST,
        metavar="\b")

    args = parser.parse_args()

    out_dir_data = f"{args.outdir}/data"
    if os.path.exists(out_dir_data) is False:
        os.makedirs(f"{out_dir_data}")

    for group in args.group:
        sites_json = request_xr(folder="sites",
                                groups=group
                                )
        pd.DataFrame(sites_json).to_csv(f"{out_dir_data}/stations_{group}.csv")

        measures_json = request_xr(folder="measures",
                                   groups=group,)
        pd.DataFrame(measures_json).to_csv(f"{out_dir_data}/measures_{group}.csv")

    physicals_json = request_xr(folder="physicals")
    pd.DataFrame(physicals_json).to_csv(f"{out_dir_data}/physicals.csv")
