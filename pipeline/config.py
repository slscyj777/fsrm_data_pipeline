import os
from pathlib import Path
from dotenv import load_dotenv

# Load environmental/runtime variables from .env file
load_dotenv()

# -------- Runtime Variables (Pulled from Environment) -------------
# Using fallback defaults in case they aren't set in the .env file
day_env = os.getenv("DAY")
DAY: int | None = int(day_env) if day_env else None
SUB_FOLDER_NAME: str = os.getenv("SUB_FOLDER_NAME", "1.Stock FSRM SSC")
FSRM_FOLDER: str = os.getenv("FSRM_FOLDER", "FSRM_files")

MASTER_DIM_FILE: str = os.getenv("MASTER_DIM_FILE", "master_dim.xlsx")
SP_SYNC_PATH: str = os.getenv("SP_SYNC_PATH", "Thai Beverage Public Company Limited/Nitita Chaiarsa - Stock FSRM SSC")

TEST_FILE: str = "output.xlsx"
OUTPUT_FILE: str = "fsrm_consolidated.xlsx"


# -------- column structures & Logic Constants  -------------
COLUMNS_TO_READ: list[int] = [1, 2, 3, 4, 17, 18, 13, 14]

ASSIGN_COLUMN_MAPPING: dict[str, str] = {
    "column_1": "SKU",
    "column_2": "description",
    "column_3": "base_unit",
    "column_4": "base_unit_bottle",
    "column_5": "stock_case",
    "column_6": "stock_bottle",
    "column_7": "shippment_case",
    "column_8": "shippment_bottle",
}

SFC_RENAME_MAPPING: dict[str, str] = {
    "column_1": "branch_code",
    "column_2": "category",
    "column_3": "SKU",
    "column_4": "forecast"
}

ASSIGN_COLUMN_ORDER: list[str] = [
    'branch_code', 'region', 'region_TBL', 'warehouse_name_TBL',
    'sermsuk_branch_name', 'SKU', 'description', 'base_unit', 
    'base_unit_bottle', 'stock_case', 'stock_bottle', 'stock_date', 
    'ending_stock_case', "act_shippment_case"
]

STOCK_COL: list[str] = ["stock_case", "stock_bottle", "base_unit_bottle"]
SHIP_COL: list[str] = ["shippment_case", "shippment_bottle"]