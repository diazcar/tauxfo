from datetime import datetime

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

YEAR_NOW = int(datetime.now().strftime("%Y"))
