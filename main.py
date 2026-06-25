from datetime import date
import os
from pathlib import Path
import time

# Pipeline Config
from pipeline.config import (
    ASSIGN_COLUMN_MAPPING,
    ASSIGN_COLUMN_ORDER,
    COLUMNS_TO_READ,
    DAY,
    FSRM_FOLDER,
    MASTER_DIM_FILE,
    OUTPUT_FILE,
    SHIP_COL,
    STOCK_COL,
    SUB_FOLDER_NAME,
    SFC_RENAME_MAPPING,
    SP_SYNC_PATH,
)
# ETL stages
from pipeline.extract import (
    extract_SFC_data,
    extract_sermsuk_TBL_mapping,
    extract_sermsuk_data,
    validate_extracted_data,
)
from pipeline.transform import (
    branch_code_to_int,
    map_forecast_to_daily,
    map_sermsuk_to_TBL_WH_select_columns,
    rename_normalize_stock_columns,
    total_shippment_as_crates,
    total_stock_as_crates,
    transform_consolidate_forecasts,
)
from pipeline.load import check_and_load_to_backup, load_to_excel

class UI:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

    @classmethod
    def step_start(cls, message):
        print(f"{cls.YELLOW}[ ... ]{cls.RESET} {message}", end="\r", flush=True)

    @classmethod
    def step_done(cls, message):
        # overwrites the previous line with a success indicator
        print(f"{cls.GREEN}[OK]{cls.RESET} {message}")


start_time = time.perf_counter()
print(f"\n{UI.BOLD}{UI.CYAN}Starting...{UI.RESET}\n")

PROJECT_ROOT = Path(__file__).resolve().parent
input_path = PROJECT_ROOT / "excel" / "input" / MASTER_DIM_FILE

SP_ROOT = Path.home() / SP_SYNC_PATH

if not SP_ROOT.exists():
    raise FileNotFoundError(f"SharePoint sync directory not found at: {SP_ROOT}\nEnsure folder is synced.")

sub_folder = SP_ROOT / SUB_FOLDER_NAME

#output_path = PROJECT_ROOT/ "excel" / "output" / TEST_FILE
output_path = SP_ROOT / FSRM_FOLDER / OUTPUT_FILE

today = date.today()
filename = f"FSRM_consolidated_{today.strftime('%B')}_{today.year}.csv"
csv_file_path = PROJECT_ROOT / "data" / filename


UI.step_start("Extracting and transforming data...")

#=================================================================================

df_mapping = extract_sermsuk_TBL_mapping(input_path)

df_beer = extract_SFC_data(
    "excel/input/FSRM_Beer Sales Forecasting_July 2026.xlsx", 
    columns_to_read=[6, 7, 11, 13],
    rename_map=SFC_RENAME_MAPPING 
)

df_spirits = extract_SFC_data(
    "excel/input/FSRM_Spirits Sales Forecasting_July 2026.xlsx", 
    columns_to_read=[5, 8, 12, 14],
    rename_map=SFC_RENAME_MAPPING
)

df_SFC = transform_consolidate_forecasts(df_beer, df_spirits)

df = (extract_sermsuk_data(
                        columns_to_read = COLUMNS_TO_READ
                        ,sub_folder= sub_folder
                        ,day = DAY
                        )
    .pipe(rename_normalize_stock_columns,column_mapping = ASSIGN_COLUMN_MAPPING
                                ,stock_columns = STOCK_COL
                                ,ship_columns = SHIP_COL
                                )
    .pipe(validate_extracted_data, stock_columns = STOCK_COL
        )
    .pipe(total_stock_as_crates, stock_columns = STOCK_COL 
        )
    .pipe(total_shippment_as_crates, ship_columns = SHIP_COL 
        )
    .pipe(map_sermsuk_to_TBL_WH_select_columns
        , mapping_df = df_mapping
        , column_to_map = "branch_code"
        , column_order = ASSIGN_COLUMN_ORDER)
    .pipe(branch_code_to_int)
    .pipe(map_forecast_to_daily, df_SFC)
    ) 

UI.step_done("Data extracted and transformed successfully.")
#print(df.head)

UI.step_start("Updating CSV backup...")

check_and_load_to_backup(df, csv_file_path= csv_file_path)

UI.step_done("                           ")

UI.step_start(f"Loading data into Excel ({output_path.name})")

load_to_excel(output_file= output_path, table_name= 'raw', csv_file_path = csv_file_path)

#=================================================================================

UI.step_done(f"Excel file ready                                                 ")


end_time = time.perf_counter()
print(f"\n{UI.BOLD}{UI.CYAN}success {UI.RESET}")
print("----------------------------")
print(f"Execution time: {end_time - start_time:.2f} seconds")