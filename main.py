from calendar import month_abbr
from datetime import date
import argparse
from dotenv import load_dotenv
from os import getenv
import polars as pl
from pathlib import Path
import time


# Pipeline Config
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


REQUIRED_ENV_VARS = [
    "MASTER_DIM_FILE", "BEER_FORECAST_FILE", "SPIRITS_FORECAST_FILE",
    "SP_SYNC_PATH", "SUB_FOLDER_NAME", "FSRM_FOLDER", "OUTPUT_FILE","SKU_DIM_FILE",
    "COLUMNS_TO_READ", "ASSIGN_COLUMN_MAPPING", "STOCK_COL", "SHIP_COL",
    "ASSIGN_COLUMN_ORDER", "BEER_COLUMNS_TO_READ", "SPIRITS_COLUMNS_TO_READ",
    "SFC_RENAME_MAPPING","SKU_COLUMNS_TO_READ","SKU_RENAME_MAPPING",
]

def validate_env_vars() -> None:
    missing = [name for name in REQUIRED_ENV_VARS if globals().get(name) in (None, "")]
    if missing:
        raise EnvironmentError(
            f"Missing/empty .env variable(s): {', '.join(missing)}. Check your .env file."
        )

CYAN = '\033[96m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

def step_start(message):
    print(f"{YELLOW}[...]{RESET} {message}", end="\r", flush=True)

def step_done(message):
    print(f"\033[K{GREEN}[OK]{RESET} {message}")


def run_pipeline(steps: list[str] = ["all"]) -> None:
    """
    Initialize all file paths, then run compute steps, followed by saving to a parquet cache, before saving cache to backup csv, reading that updated csv and loading updated data into excel. Each segment broken into arg blocks that can be called by parsing the arg name specified when running the code using --step"
    """
    start_time = time.perf_counter()
    requested_steps = set(steps)
    print(f"\n{BOLD}{CYAN}Starting pipeline (Step: {steps})...{RESET}\n")

  
    PROJECT_ROOT = Path(__file__).resolve().parent
    env_path = PROJECT_ROOT / '.env'

    load_dotenv(dotenv_path=env_path)

    # -------- env variables -------------
    # fallbacks in case they aren't set in the .env file
    day_env = getenv("DAY")
    DAY: int | None = int(day_env) if day_env else None
    month_env = getenv("MONTH")
    MONTH: int | None = int(month_env) if month_env else None
    year_env = getenv("YEAR")
    YEAR: int | None = int(year_env) if year_env else None
    SUB_FOLDER_NAME: str = getenv("SUB_FOLDER_NAME", "1.Stock FSRM SSC")
    FSRM_FOLDER: str = getenv("FSRM_FOLDER", "FSRM_files")

    MASTER_DIM_FILE: str = getenv("MASTER_DIM_FILE", "master_dim.xlsx")
    SKU_DIM_FILE: str = getenv("SKU_DIM_FILE", "DIM_SKU.xlsx")
    SP_SYNC_PATH: str = getenv("SP_SYNC_PATH", "Thai Beverage Public Company Limited/Nitita Chaiarsa - Stock FSRM SSC")

    BEER_FORECAST_FILE: str = getenv("BEER_FORECAST_FILE", "FSRM_Beer Sales Forecasting_July 2026.xlsx")

    SPIRITS_FORECAST_FILE: str = getenv("SPIRITS_FORECAST_FILE", "FSRM_Spirits Sales Forecasting_July 2026.xlsx")

    OUTPUT_FILE: str = getenv("OUTPUT_FILE", "FSRM_consolidated.xlsx")

    input_path = PROJECT_ROOT / "excel" / "input" / MASTER_DIM_FILE
    beer_path = PROJECT_ROOT / "excel" / "input" / BEER_FORECAST_FILE
    spirits_path = PROJECT_ROOT / "excel" / "input" / SPIRITS_FORECAST_FILE
    sku_path = PROJECT_ROOT / "excel" / "input" / SKU_DIM_FILE
    SP_ROOT = Path.home() / SP_SYNC_PATH

    if not SP_ROOT.exists():
        raise FileNotFoundError(f"SharePoint sync directory not found at: {SP_ROOT}\nEnsure folder is synced.")
    
    
    target_day = DAY if DAY is not None else date.today().day
    target_month = MONTH if MONTH is not None else date.today().month
    target_year = YEAR if YEAR is not None else date.today().year
    try:
        stock_date = date(day=target_day, month=target_month, year=target_year)
    except ValueError as e:
        raise ValueError(f"Invalid date combination: day={target_day}, month={target_month}, year={target_year}") from e

    sub_folder = SP_ROOT / SUB_FOLDER_NAME /  f"{target_month}_{month_abbr[target_month]}_{target_year}"
    output_path = SP_ROOT / FSRM_FOLDER / OUTPUT_FILE


    filename = f"FSRM_consolidated_{stock_date.strftime('%B')}_{stock_date.year}.csv"
    csv_file_path = PROJECT_ROOT / "data" / filename

    cache_file_path = PROJECT_ROOT / "data" / f"temp_transformed.parquet"

    df = None

    if "all" in requested_steps or "transform" in requested_steps:
        print(f"Extracting and transforming data from {sub_folder.name}, day: {target_day}")

        df_mapping = extract_sermsuk_TBL_mapping(input_path, sheet_name="warehouse")

        df_beer = extract_sfc_data(
            beer_path, 
            columns_to_read=BEER_COLUMNS_TO_READ,
            rename_map=SFC_RENAME_MAPPING 
        )

        df_spirits = extract_sfc_data(
            spirits_path, 
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

        check_and_load_to_backup(df, csv_file_path=csv_file_path)
        step_done("Backup updated/skipped successfully.")


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

  


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FSRM Data Pipeline Orchestrator")
    parser.add_argument(
        "--steps",  
        nargs="+",  
        default=["all"],
        choices=["all", "transform", "backup", "excel"],
        help="Specify one or more pipeline slices to execute (e.g., --steps backup excel)"
    )
    args = parser.parse_args()
    
    run_pipeline(steps=args.steps)