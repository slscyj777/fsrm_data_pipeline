import polars as pl
import xlwings as xw
import pandas as pd
from pathlib import Path


def check_duplicate_dates(existing_df: pl.DataFrame, new_df: pl.DataFrame) -> bool:
    '''
    helper: check if data from that day is already in backup
    '''
    existing_dates = existing_df["stock_date"].cast(pl.String)
    
    has_overlap = new_df.select(
        pl.col("stock_date").cast(pl.String).is_in(existing_dates).any()
    ).item()
    
    return has_overlap


def check_and_load_to_backup(df: pl.DataFrame, csv_file_path: Path) -> None:
    '''
    check if csv backup for that month exists, if no, create file and save data, if yes, append data to the end of existing file. if data with the same date already exists, skip saving data to prevent duplicate data
    '''

    if not csv_file_path.exists():
        df.write_csv(csv_file_path, separator=",", float_precision=1)
    else:
        existing_dates_df = pl.scan_csv(csv_file_path).select("stock_date").collect()
        if check_duplicate_dates(existing_dates_df, df):
            print(f"Data for that date already exists, skipping.")
            return None
        else:
            with open(csv_file_path, mode="a", encoding= "UTF-8") as f:
                df.write_csv(f, include_header=False, separator=",", float_precision=1)


    return None


def load_to_excel(output_file: Path, table_name: str, csv_file_path: Path):
    '''
    This function uses a package xlwings to interact directly with the excel workbook, mimicking user action of opening the file, finding the right sheet and table, and copy pasting into the raw data sheet. 
    '''
    df = pl.read_csv(csv_file_path).to_pandas()
    
    # Connect to the workbook
    wb = xw.Book(output_file)
    app = wb.app
    
    # Disable screen rendering and formula calculations
    app.screen_updating = False
    app.calculation = 'manual'
    
    try:
        sheet = wb.sheets[0]
        
        if table_name in [table.name for table in sheet.tables]:
            target_table = sheet.tables[table_name]
        else:
            target_table = sheet.tables.add(source=sheet['A1'], name=table_name)

        target_table.show_autofilter = False
        target_table.table_style = "TableStyleLight9"

        target_table.update(df, index=False)
        
        
        if target_table.header_row_range is not None:
            target_table.header_row_range.columns.autofit()
        
    finally:
        # Ensure Excel is restored to its normal state even if an error occurs
        app.calculation = 'automatic'
        app.screen_updating = True

    return None

if __name__ == "__main__":
    nrows, ncols = 3, 12
    df = pd.DataFrame(data=nrows * [ncols * ['test']],
                columns=['col ' + str(i) for i in range(ncols)])
    dfl = pl.DataFrame(data=nrows * [ncols * ['hi']],
                schema=['col ' + str(i) for i in range(ncols)]
                , orient= "row")

    #load_to_excel(df, table_name = 'Frame0')
    print('check')