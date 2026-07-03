import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# -------- env variables -------------
# fallbacks in case they aren't set in the .env file
day_env = os.getenv("DAY")
DAY: int | None = int(day_env) if day_env else None
month_env = os.getenv("MONTH")
MONTH: int | None = int(month_env) if month_env else None
year_env = os.getenv("YEAR")
YEAR: int | None = int(year_env) if year_env else None
SUB_FOLDER_NAME: str = os.getenv("SUB_FOLDER_NAME", "1.Stock FSRM SSC")
FSRM_FOLDER: str = os.getenv("FSRM_FOLDER", "FSRM_files")

MASTER_DIM_FILE: str = os.getenv("MASTER_DIM_FILE", "master_dim.xlsx")
SKU_DIM_FILE: str = os.getenv("SKU_DIM_FILE", "DIM_SKU.xlsx")
SP_SYNC_PATH: str = os.getenv("SP_SYNC_PATH", "Thai Beverage Public Company Limited/Nitita Chaiarsa - Stock FSRM SSC")

BEER_FORECAST_FILE: str = os.getenv("BEER_FORECAST_FILE", "FSRM_Beer Sales Forecasting_July 2026.xlsx")

SPIRITS_FORECAST_FILE: str = os.getenv("SPIRITS_FORECAST_FILE", "FSRM_Spirits Sales Forecasting_July 2026.xlsx")

OUTPUT_FILE: str = os.getenv("OUTPUT_FILE", "FSRM_consolidated.xlsx")

TEST_FILE: str = "output.xlsx"



# -------- column structures & logic  -------------
COLUMNS_TO_READ: list[int] = [1, 2, 17, 18, 13, 14]

BEER_COLUMNS_TO_READ: list[int] = [6, 7, 11, 13]

SPIRITS_COLUMNS_TO_READ: list[int] = [5, 8, 12, 14]

SKU_COLUMNS_TO_READ: list[int] = [3, 21]

ASSIGN_COLUMN_MAPPING: dict[str, str] = {
    "column_1": "SKU",
    "column_2": "description",
    "column_3": "stock_case",
    "column_4": "stock_bottle",
    "column_5": "shippment_case",
    "column_6": "shippment_bottle",
}

SFC_RENAME_MAPPING: dict[str, str] = {
    "column_1": "branch_code",
    "column_2": "category",
    "column_3": "SKU",
    "column_4": "forecast"
}

SKU_RENAME_MAPPING: dict[str, str] = {
    "column_1": "SKU",
    "column_2": "base_unit_bottle"
}

ASSIGN_COLUMN_ORDER: list[str] = [
    'branch_code', 'region', 'region_TBL', 'warehouse_name_TBL',
    'sermsuk_branch_name', 'SKU', 'description', 
    'base_unit_bottle', 'stock_case', 'stock_bottle', 'stock_date', 
    'ending_stock_case', "act_shippment_case"
]

STOCK_COL: list[str] = ["stock_case", "stock_bottle"]
SHIP_COL: list[str] = ["shippment_case", "shippment_bottle"]