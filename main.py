from datetime import date, datetime
import argparse
import polars as pl
import os
from pathlib import Path
import time
import uuid

# Pipeline Config
from pipeline.config import (
    ASSIGN_COLUMN_MAPPING,
    ASSIGN_COLUMN_ORDER,
    COLUMNS_TO_READ,
    DAY,
    FSRM_FOLDER,
    MASTER_DIM_FILE,
    MONTH,
    OUTPUT_FILE,
    SHIP_COL,
    STOCK_COL,
    SUB_FOLDER_NAME,
    SFC_RENAME_MAPPING,
    SP_SYNC_PATH,
    BEER_FORECAST_FILE,
    SPIRITS_FORECAST_FILE,
    BEER_COLUMNS_TO_READ,
    SPIRITS_COLUMNS_TO_READ,
)
# stages
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


def run_pipeline(steps: list[str] = ["all"]) -> None:
    """
    Initialize all file paths, then run compute steps, followed by saving to a parquet cache, before saving cache to backup csv, reading that updated csv and loading updated data into excel. Each segment broken into arg blocks that can be called by parsing the arg name specified when running the code using --step"
    """
    start_time = time.perf_counter()
    requested_steps = set(steps)
    print(f"\n{UI.BOLD}{UI.CYAN}Starting pipeline (Step: {steps})...{UI.RESET}\n")

  
    PROJECT_ROOT = Path(__file__).resolve().parent
    input_path = PROJECT_ROOT / "excel" / "input" / MASTER_DIM_FILE
    beer_path = PROJECT_ROOT / "excel" / "input" / BEER_FORECAST_FILE
    spirits_path = PROJECT_ROOT / "excel" / "input" / SPIRITS_FORECAST_FILE
    SP_ROOT = Path.home() / SP_SYNC_PATH

    if not SP_ROOT.exists():
        raise FileNotFoundError(f"SharePoint sync directory not found at: {SP_ROOT}\nEnsure folder is synced.")

    sub_folder = SP_ROOT / SUB_FOLDER_NAME 
    output_path = SP_ROOT / FSRM_FOLDER / OUTPUT_FILE

    if MONTH is None:
        today = date.today()
    else:
        today = date.today().replace(month=MONTH)

    filename = f"FSRM_consolidated_{today.strftime('%B')}_{today.year}.csv"
    csv_file_path = PROJECT_ROOT / "data" / filename

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    cache_file_path = PROJECT_ROOT / "data" / f"temp_transformed_{timestamp}_{unique_id}.parquet"

    df = None

    if "all" in requested_steps or "transform" in requested_steps:
        UI.step_start("Extracting and transforming data...")

        df_mapping = extract_sermsuk_TBL_mapping(input_path)

        df_beer = extract_SFC_data(
            beer_path, 
            columns_to_read=BEER_COLUMNS_TO_READ,
            rename_map=SFC_RENAME_MAPPING 
        )

        df_spirits = extract_SFC_data(
            spirits_path, 
            columns_to_read=SPIRITS_COLUMNS_TO_READ,
            rename_map=SFC_RENAME_MAPPING
        )

        df_SFC = transform_consolidate_forecasts(df_beer, df_spirits)

        df = (extract_sermsuk_data(
                    columns_to_read = COLUMNS_TO_READ
                    ,sub_folder= sub_folder
                    ,day = DAY
                    ,month = MONTH
                    ,rows_to_read= 150
                    )
            .pipe(rename_normalize_stock_columns,column_mapping = ASSIGN_COLUMN_MAPPING
                                                ,stock_columns = STOCK_COL
                                                ,ship_columns = SHIP_COL
                                                )
            .pipe(validate_extracted_data, stock_columns = STOCK_COL)
            .pipe(total_stock_as_crates, stock_columns = STOCK_COL)
            .pipe(total_shippment_as_crates, ship_columns = SHIP_COL)
            .pipe(map_sermsuk_to_TBL_WH_select_columns
                , mapping_df = df_mapping
                , column_to_map = "branch_code"
                , column_order = ASSIGN_COLUMN_ORDER)
            .pipe(branch_code_to_int)
            .pipe(map_forecast_to_daily, df_SFC)
        ) 

        # localized caching layer
        cache_file_path.parent.mkdir(exist_ok=True)
        df.write_parquet(cache_file_path)
        UI.step_done("Data extracted and transformed successfully.")



    if "all" in requested_steps or "backup" in requested_steps:
        UI.step_start("Updating CSV backup...")
        
        # load from intermediate cache if performing a partial execution
        if df is None:
            if not cache_file_path.exists():
                raise FileNotFoundError("Cache missing. Run the 'transform' step first to build cache.")
            df = pl.read_parquet(cache_file_path)

        check_and_load_to_backup(df, csv_file_path=csv_file_path)
        UI.step_done("Backup updated/skipped successfully.")


    if "all" in requested_steps or "excel" in requested_steps:
        UI.step_start(f"Loading data into Excel ({output_path.name})")

        df_to_load = pl.read_csv(csv_file_path)
        
        if not df_to_load.is_unique().all():
            raise ValueError(f"Pipeline halted: Duplicates found in {csv_file_path.name}")
        load_to_excel(df_pl=df_to_load, output_file=output_path, table_name='raw')
        UI.step_done("Excel file ready                                      ")

    end_time = time.perf_counter()
    print(f"\n{UI.BOLD}{UI.CYAN}success {UI.RESET}")
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