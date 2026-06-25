import polars as pl
from datetime import date
from pathlib import Path
#from config import FOLDER_PATH, COLUMNS_TO_READ


def extract_sermsuk_data(
                         columns_to_read: list[int]
                         ,sub_folder: Path 
                         ,day:int | None = None
                         ,rows_to_read: int  = 80
                         ,rows_to_skip: int  = 5
                         ,files: int = 50
                         ,has_header: bool = False
                         ) -> pl.DataFrame:
    ''' 
    This function gets the current day the system, finds the fsrm stock folder and loops through each file, extracting the branch details from the name of the file. It then reads the sheet corresponding to the day, takes the relevant columns such as SKU and ending stock, and cleans all the junk cells below the sheet. Finally, it joins all the data into 1 table and returns that as a dataframe.
    '''

    df = []
    if day == None:
        extracted_date = date.today()
        day = date.today().day
    else:
        extracted_date = date.today().replace(day = day)




    if sub_folder.exists() and sub_folder.is_dir():
        for index, file in enumerate(sub_folder.iterdir(), start=1):
                if (not file.is_file() 
                        or not file.name.endswith(".xlsx") 
                        or not file.name.startswith("3")
                        ):
                        continue
                
                
                name_only = file.stem
                parts = name_only.split("_", 3)

                if len(parts) == 4:
                    code, region, _, name = parts
                    name = name[5:]

                else:
                    raise SyntaxError(f"Wrong file name format, rename {name_only}.")

    

                file_df = pl.read_excel(file,
                                        sheet_name = str(day)
                                        ,engine = 'calamine'
                                        ,columns = columns_to_read
                                        ,read_options={"n_rows": rows_to_read
                                                    , "skip_rows": rows_to_skip}
                                        ,drop_empty_cols = False
                                        ,drop_empty_rows = False
                                        ,has_header = has_header
                                        ,schema_overrides={"column_4": pl.String
                                                        ,"column_5": pl.String
                                                        ,"column_6": pl.String
                                                        ,"column_7": pl.String
                                                        ,"column_8": pl.String
                                                        }
                                        )
                
                file_df = file_df.filter(
                    #filter all rows after the first empty row 
                    pl.all_horizontal(pl.all().is_null()).cum_max() == False
                        ).filter(~pl.all_horizontal((pl.all().cast(pl.String).str.strip_chars() == ""))
                                    ).with_columns(
                                pl.lit(code).alias("branch_code")
                                ,pl.lit(region).alias("region")
                                ,pl.lit(name).alias("sermsuk_branch_name")
                                ,pl.lit(extracted_date).alias("stock_date")
                                                )

                df.append(file_df)
                print(f"Concated file: {file.name}, files in dir: {index}")
    else:
        raise NameError(f"Wrong folder name or folder not exists.")  
             
    if df and len(df) == files:
        df = pl.concat(df, how="vertical")
        print(f"{df.height} rows extracted")
    else:
        raise SystemError(f"Too many files. Check folder again.")
    
    return df


def extract_sermsuk_TBL_mapping(file_name: Path | str) -> pl.DataFrame:

    '''This function finds and extract data from the master_dim file'''


    df = pl.read_excel(file_name, engine='calamine', has_header = True, sheet_name= "warehouse")
    
    return df


def extract_SFC_data(file_path: str | Path, columns_to_read: list[int], rename_map: dict[str, str] )-> pl.DataFrame:
    
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
     
    
    
     



def validate_extracted_data(df: pl.DataFrame, stock_columns: list[str]) -> pl.DataFrame:

    '''This function does some checks to make sure that there are no empty cells in some of the columns that are supposed to have values. Able to add more checks in the future'''

    if df.height == 0:
        raise ValueError("Extracted DataFrame is empty")

    null_violations = {
        col: df.filter(pl.col(col).is_null()).height
        for col in ["branch_code", "region", "sermsuk_branch_name", "SKU", "base_unit_bottle"]
    }
    null_violations = {col: rows for col, rows in null_violations.items() if rows > 0}
    if null_violations:
        raise ValueError(f"Null values found in required fields: {null_violations}")

    # for col in stock_columns:
    #     if df[col].dtype != pl.Float64:
    #         raise ValueError(f"Expected {col} to be Float64 after normalization, got {df[col].dtype}")
    
    return df



