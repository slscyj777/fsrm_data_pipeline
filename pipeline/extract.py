import polars as pl
from datetime import date
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


def _parse_filename_metadata(filename: str) -> tuple[str, str, str]:
    """Helper: Extracts code, region, and branch name from the specific file format."""
    parts = filename.split("_", 3)
    if len(parts) != 4:
        raise ValueError(f"Wrong file name format, rename {filename}.")
    
    code, region, _, name = parts
    return code, region, name[5:]

def clean_sermsuk_dataframe(
    df: pl.DataFrame, 
    code: str, 
    region: str, 
    branch_name: str, 
    extracted_date: date
) -> pl.DataFrame:
    """
    Pure data manipulation. Takes a raw loaded dataframe and applies 
    cleansing, filtering, and metadata enrichment.
    """
    return (
        df.filter(pl.all_horizontal(pl.all().is_null()).cum_max() == False)
          .filter(~pl.all_horizontal(pl.all().cast(pl.String).str.strip_chars() == ""))
          .with_columns(
              pl.lit(code).alias("branch_code"),
              pl.lit(region).alias("region"),
              pl.lit(branch_name).alias("sermsuk_branch_name"),
              pl.lit(extracted_date).alias("stock_date")
          )
    )

def _read_and_clean_branch_file(
    file: Path,
    *,
    day: int,
    columns_to_read: list[int],
    rows_to_read: int,
    rows_to_skip: int,
    has_header: bool,
    schema_overrides: dict,
    stock_date: date,
) -> pl.DataFrame:
    """Worker: reads + cleans one branch file. Isolated thread."""
    code, region, branch_name = _parse_filename_metadata(file.stem)

    raw_df = pl.read_excel(
        file,
        sheet_name=str(day),
        engine='calamine',
        columns=columns_to_read,
        read_options={"n_rows": rows_to_read, "skip_rows": rows_to_skip},
        drop_empty_cols=False,
        drop_empty_rows=False,
        has_header=has_header,
        schema_overrides=schema_overrides
    )

    return clean_sermsuk_dataframe(raw_df, code, region, branch_name, stock_date)


def extract_sermsuk_data(
    columns_to_read: list[int],
    *,
    sub_folder: Path,
    stock_date: date,
    day: int ,
    rows_to_read: int = 80,
    rows_to_skip: int = 5,
    files: int = 50,
    has_header: bool = False,
    max_workers: int = 8,
) -> pl.DataFrame:
    """folder scanning and execution"""
    if not (sub_folder.exists() and sub_folder.is_dir()):
        raise ValueError(f"Folder not found or not a directory: {sub_folder}")

    schema_overrides = {f"column_{i+1}": pl.String for i in range(len(columns_to_read))}

    valid_files = [
        f for f in sub_folder.iterdir()
        if f.is_file() and f.name.endswith(".xlsx") and f.name.startswith("3")
    ]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        df_list = list(executor.map(
            lambda f: _read_and_clean_branch_file(
                f, day=day, columns_to_read=columns_to_read,
                rows_to_read=rows_to_read, rows_to_skip=rows_to_skip,
                has_header=has_header, schema_overrides=schema_overrides,
                stock_date=stock_date,
            ),
            valid_files,
        ))

    for index, file in enumerate(valid_files, start=1):
        logger.info("Concatenated file: %s, files in dir: %d", file.name, index)

    if len(df_list) != files:
        raise ValueError(f"Expected {files} files, found {len(df_list)}. Check folder again.")

    final_df = pl.concat(df_list, how="vertical")
    logger.info("%d rows extracted", final_df.height)
    return final_df

def extract_sermsuk_TBL_mapping(file_name: Path | str,sheet_name: str) -> pl.DataFrame:

    '''This function finds and extract data from the master_dim file'''


    df = pl.read_excel(file_name, engine='calamine', has_header = True, sheet_name= sheet_name)
    
    return df


def extract_sfc_data(file_path: str | Path, sheet_name: str, columns_to_read: list[int], rename_map: dict[str, str])-> pl.DataFrame:
    
    return (
        pl.read_excel(
            file_path,
            sheet_name=sheet_name,
            engine="calamine",
            columns=columns_to_read,
            has_header=False,
            read_options={"skip_rows": 1}
        )
        .rename(rename_map)
    )

def extract_sku_data(file_path: str | Path, columns_to_read: list[int], rename_map: dict[str, str], sheet_name: str  )-> pl.DataFrame:
    
    return (
        pl.read_excel(
            file_path,
            sheet_name=sheet_name,
            engine="calamine",
            columns=columns_to_read,
            has_header=False,
            read_options={"skip_rows": 1},
            schema_overrides={"column_3": pl.Float64}
        )
        .rename(rename_map)
    )

     



def validate_extracted_data(df: pl.DataFrame) -> pl.DataFrame:
    '''Checks required columns for nulls; reports affected branch_codes for debugging.'''

    if df.height == 0:
        raise ValueError("Extracted DataFrame is empty")

    required_cols = [
        "branch_code", "region", "sermsuk_branch_name", "SKU", "base_unit_bottle",
        "stock_case", "stock_bottle", "shippment_case", "shippment_bottle"
    ]

    null_violations = {
        col: {"count": bad.height, "branch_codes": bad.get_column("branch_code").unique().to_list()}
        for col in required_cols
        if (bad := df.filter(pl.col(col).is_null())).height > 0
    }

    if null_violations:
        raise ValueError(f"Null values found in required fields: {null_violations}")

    return df



