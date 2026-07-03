import polars as pl
from datetime import date
from pathlib import Path
from calendar import month_abbr
#from config import FOLDER_PATH, COLUMNS_TO_READ


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

def extract_sermsuk_data(
    columns_to_read: list[int],
    sub_folder: Path,
    stock_date: date, 
    day: int | None = None,
    rows_to_read: int = 80,
    rows_to_skip: int = 5,
    files: int = 50,
    has_header: bool = False
) -> pl.DataFrame:
    """folder scanning and execution"""
    if not (sub_folder.exists() and sub_folder.is_dir()):
        print(f"check {sub_folder}")
        print(f"Folder exists: {sub_folder.exists()}")
        print(f"Is directory: {sub_folder.is_dir()}")
        raise ValueError("Wrong folder name or folder not exists.")

    df_list = []
    
    
    schema_overrides = {f"column_{i+1}": pl.String for i in range(len(columns_to_read))}

    for index, file in enumerate(sub_folder.iterdir(), start=1):
        if not file.is_file() or not file.name.endswith(".xlsx") or not file.name.startswith("3"):
            continue
            
        
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
        
        
        cleaned_df = clean_sermsuk_dataframe(raw_df, code, region, branch_name, stock_date)
        
        df_list.append(cleaned_df)
        print(f"Concatenated file: {file.name}, files in dir: {index}")

    
    if len(df_list) != files:
        raise ValueError(f"Expected {files} files, found {len(df_list)}. Check folder again.")

    final_df = pl.concat(df_list, how="vertical")
    print(f"{final_df.height} rows extracted")
    return final_df


def extract_sermsuk_TBL_mapping(file_name: Path | str,sheet_name: str) -> pl.DataFrame:

    '''This function finds and extract data from the master_dim file'''


    df = pl.read_excel(file_name, engine='calamine', has_header = True, sheet_name= sheet_name)
    
    return df


def extract_sfc_data(file_path: str | Path, columns_to_read: list[int], rename_map: dict[str, str])-> pl.DataFrame:
    
    return (
        pl.read_excel(
            file_path,
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
            schema_overrides={"column_2": pl.Float64}
        )
        .rename(rename_map)
    )

     



def validate_extracted_data(df: pl.DataFrame) -> pl.DataFrame:

    '''This function does some checks to make sure that there are no empty cells in some of the columns that are supposed to have values. Able to add more checks in the future'''

    if df.height == 0:
        raise ValueError("Extracted DataFrame is empty")

    null_violations = {
        col: df.filter(pl.col(col).is_null()).height
        for col in ["branch_code", "region", "sermsuk_branch_name", "SKU", "base_unit_bottle", "stock_case", "stock_bottle", "shippment_case", "shippment_bottle"]
    }
    null_violations = {col: rows for col, rows in null_violations.items() if rows > 0}
    if null_violations:
        raise ValueError(f"Null values found in required fields: {null_violations}")
    
    return df



