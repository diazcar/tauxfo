from src.get_data import request_xr, GROUP_LIST, STATION_LIST_CSV
import pandas as pd

for group in GROUP_LIST:
    sites_json = request_xr(folder="sites",
                            groups=group
                            )
    pd.DataFrame(sites_json).to_csv(f"./data/{STATION_LIST_CSV[group]}")

physicals_json = request_xr(folder="physicals")
pd.DataFrame(physicals_json).to_csv("./data/physicals.csv")
