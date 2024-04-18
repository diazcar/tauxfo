from request.get_data import request_xr, GROUP_LIST, STATIONS_OUTFILE_DIC
import pandas as pd

for group in GROUP_LIST:
    sites_json = request_xr(folder="sites",
                            groups=group
                            )
    pd.DataFrame(sites_json).to_csv(STATIONS_OUTFILE_DIC[group])

physicals_json = request_xr(folder="physicals")
pd.DataFrame(physicals_json).to_csv("./data/physicals.csv")
