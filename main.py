from calendar import month_abbr
from datetime import date
import argparse
import polars as pl
from pathlib import Path
import time


# Pipeline Config
from pipeline.settings import load_settings

from pipeline.config import (
    ASSIGN_COLUMN_MAPPING,
    ASSIGN_COLUMN_ORDER,
    COLUMNS_TO_READ,
    SHIP_COL,
    STOCK_COL,
    SFC_RENAME_MAPPING,
    BEER_COLUMNS_TO_READ,
    SPIRITS_COLUMNS_TO_READ,
    SKU_COLUMNS_TO_READ,
    SKU_RENAME_MAPPING,
)
# stages
from pipeline.extract import (
    extract_sfc_data,
    extract_sermsuk_TBL_mapping,
    extract_sermsuk_data,
    extract_sku_data,
    validate_extracted_data,
)
from pipeline.transform import (
    branch_code_to_int,
    map_forecast_to_daily,
    map_base_unit_to_sku,
    map_sermsuk_to_TBL_WH_select_columns,
    rearrange_columns,
    rename_normalize_stock_columns,
    total_shippment_as_crates,
    total_stock_as_crates,
    transform_consolidate_forecasts,
)
from pipeline.load import check_and_load_to_backup, load_to_excel


REQUIRED_VARS = [
    "MASTER_DIM_FILE", "FORECAST_FILE",
    "SP_SYNC_PATH", "SUB_FOLDER_NAME", "FSRM_FOLDER", "OUTPUT_FILE","SKU_DIM_FILE",
    "COLUMNS_TO_READ", "ASSIGN_COLUMN_MAPPING", "STOCK_COL", "SHIP_COL",
    "ASSIGN_COLUMN_ORDER", "BEER_COLUMNS_TO_READ", "SPIRITS_COLUMNS_TO_READ",
    "SFC_RENAME_MAPPING","SKU_COLUMNS_TO_READ","SKU_RENAME_MAPPING",
]

CYAN = '\033[96m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

def step_start(message):
    print(f"{YELLOW}[...]{RESET} {message}", end="\r", flush=True)

def step_done(message):
    print(f"\033[K{GREEN}[OK]{RESET} {message}")

def month_folder_name(month: int, year: int) -> str:
    '''Resolves the SharePoint subfolder name for a given month/year, e.g. "7_Jul_2026".'''
    return f"{month}_{month_abbr[month]}_{year}"

def run_pipeline(steps: list[str] = ["all"], day: int | None = None, month: int | None = None, year: int | None = None) -> bool:
    """
    Initialize all file paths, then run compute steps, followed by saving to a parquet cache, before saving cache to backup csv, reading that updated csv and loading updated data into excel. Each segment broken into arg blocks that can be called by parsing the arg name specified when running the code using --step"
    """
    start_time = time.perf_counter()
    requested_steps = set(steps)
    print(f"\n{BOLD}{CYAN}Starting pipeline (Step: {steps})...{RESET}\n")

  
    PROJECT_ROOT = Path(__file__).resolve().parent
    settings = load_settings()

    # -------- json variables -------------
    target_day = day if day is not None else date.today().day
    target_month = month if month is not None else date.today().month
    target_year = year if year is not None else date.today().year
    SUB_FOLDER_NAME = settings["SUB_FOLDER_NAME"]
    FSRM_FOLDER = settings["FSRM_FOLDER"]
    MASTER_DIM_FILE = settings["MASTER_DIM_FILE"]
    SKU_DIM_FILE = settings["SKU_DIM_FILE"]
    SP_SYNC_PATH = settings["SP_SYNC_PATH"]
    FORECAST_FILE = settings["FORECAST_FILE"]
    OUTPUT_FILE = settings["OUTPUT_FILE"]

    missing = [key for key, value in settings.items() if not value]
    if missing:
        raise ValueError(
            f"Missing/empty setting(s): {', '.join(missing)}. Check settings.json."
        )

    input_path = PROJECT_ROOT / "excel" / "input" / MASTER_DIM_FILE
    forecast_path = PROJECT_ROOT / "excel" / "input" / FORECAST_FILE
    sku_path = PROJECT_ROOT / "excel" / "input" / SKU_DIM_FILE
    SP_ROOT = Path.home() / SP_SYNC_PATH

    if not SP_ROOT.exists():
        raise FileNotFoundError(f"SharePoint sync directory not found at: {SP_ROOT}\nEnsure folder is synced.")
    
    try:
        stock_date = date(day=target_day, month=target_month, year=target_year)
    except ValueError as e:
        raise ValueError(f"Invalid date combination: day={target_day}, month={target_month}, year={target_year}") from e

    sub_folder = SP_ROOT / SUB_FOLDER_NAME /  month_folder_name(target_month, target_year)
    output_path = SP_ROOT / FSRM_FOLDER / OUTPUT_FILE


    filename = f"FSRM_consolidated_{stock_date.strftime('%B')}_{stock_date.year}.csv"
    csv_file_path = PROJECT_ROOT / "data" / filename
    #SP_ROOT / FSRM_FOLDER / "backup_csv" / filename
    

    cache_file_path = PROJECT_ROOT / "data" / f"temp_transformed.parquet"

    df = None
    skipped_backup = False

    if "all" in requested_steps or "transform" in requested_steps:
        print(f"Extracting and transforming data from {sub_folder.name}, day: {target_day}")

        df_mapping = extract_sermsuk_TBL_mapping(input_path, sheet_name="warehouse")

        df_beer = extract_sfc_data(
            forecast_path, 
            sheet_name="BEER",
            columns_to_read=BEER_COLUMNS_TO_READ,
            rename_map=SFC_RENAME_MAPPING 
        )

        df_spirits = extract_sfc_data(
            forecast_path,
            sheet_name="Spirits", 
            columns_to_read=SPIRITS_COLUMNS_TO_READ,
            rename_map=SFC_RENAME_MAPPING
        )

        df_sku = extract_sku_data(
            sku_path,
            columns_to_read=SKU_COLUMNS_TO_READ,
            rename_map=SKU_RENAME_MAPPING,
            sheet_name="DIM_SKU (DZ_CS)"
        )

        df_SFC = transform_consolidate_forecasts(df_beer, df_spirits)

        df = (extract_sermsuk_data(
                    columns_to_read = COLUMNS_TO_READ
                    ,sub_folder= sub_folder
                    ,day = target_day
                    ,stock_date=stock_date
                    ,rows_to_read= 180
                    )
            .pipe(rename_normalize_stock_columns,column_mapping = ASSIGN_COLUMN_MAPPING
                                                ,stock_columns = STOCK_COL
                                                ,ship_columns = SHIP_COL
                                                )
            .pipe(map_base_unit_to_sku, sku_df = df_sku)
            .pipe(validate_extracted_data)
            .pipe(total_stock_as_crates, stock_columns = STOCK_COL)
            .pipe(total_shippment_as_crates, ship_columns = SHIP_COL)
            .pipe(map_sermsuk_to_TBL_WH_select_columns
                , mapping_df = df_mapping
                , column_to_map = "branch_code")
            .pipe(rearrange_columns, column_order = ASSIGN_COLUMN_ORDER)
            .pipe(branch_code_to_int)
            .pipe(map_forecast_to_daily, df_SFC)
        ) 

        # localized caching layer
        cache_file_path.parent.mkdir(exist_ok=True)
        df.write_parquet(cache_file_path)
        step_done("Data extracted and transformed successfully.")



    if "all" in requested_steps or "backup" in requested_steps:
        step_start("Updating CSV backup...")
        
        # load from intermediate cache if performing a partial execution
        if df is None:
            if not cache_file_path.exists():
                raise FileNotFoundError("Cache missing. Run the 'transform' step first to build cache.")
            df = pl.read_parquet(cache_file_path)

        skipped_backup = check_and_load_to_backup(df, csv_file_path=csv_file_path)
        if skipped_backup:
            step_done("Backup skipped successfully.")
        else:
            step_done("Backup updated successfully.")


    if "all" in requested_steps or "excel" in requested_steps:
        step_start(f"Loading data into Excel ({output_path.name})")

        if not csv_file_path.exists():
            raise FileNotFoundError("CSV backup missing. Run 'backup' step first.")
        df_to_load = pl.read_csv(csv_file_path)
        
        if not df_to_load.is_unique().all():
            raise ValueError(f"Pipeline halted: Duplicates found in {csv_file_path.name}")
        load_to_excel(df_pl=df_to_load, output_file=output_path, table_name='raw')
        step_done("Excel file ready.")

    end_time = time.perf_counter()
    print(f"\n{BOLD}{CYAN}success {RESET}")
    print("----------------------------")
    print(f"Execution time: {end_time - start_time:.2f} seconds")

    return skipped_backup


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FSRM Data Pipeline Orchestrator")
    parser.add_argument(
        "--steps",  
        nargs="+",  
        default=["all"],
        choices=["all", "transform", "backup", "excel"],
        help="Specify one or more pipeline slices to execute (e.g., --steps backup excel)"
    )
    parser.add_argument("--day", type=int, default=None, help="Day override (default: today)")
    parser.add_argument("--month", type=int, default=None, help="Month override (default: today)")
    parser.add_argument("--year", type=int, default=None, help="Year override (default: today)")

    args = parser.parse_args()
    
    run_pipeline(steps=args.steps, day=args.day, month=args.month, year=args.year)