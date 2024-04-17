from request.get_data import request_xr
import os
didon_sites_file_path = "./data/sites.csv"
physical_file_path = "./data/physicals.csv"

# Get DIDON especies+site names
if os.path.exists(didon_sites_file_path) is False:
    (request_xr(
                folder="sites",
                groups="DIDON"
                ).to_csv(didon_sites_file_path))

if os.path.exists(physical_file_path) is False:
    (request_xr(folder="physicals")
        .to_csv(physical_file_path))
