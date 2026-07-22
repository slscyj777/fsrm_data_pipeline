""" paste uv run python -m utils.clear_csv_data into terminal """

import polars as pl
from datetime import date
from pipeline.paths import sp_root, validate_sp_root, csv_backup_filepath

unique_days: list[int] = [22]
target_month: int = 7 
target_year: int = 2026
#if target_month is not None else today.month
target_file_date = date(target_year, target_month, 1)

SP_ROOT = validate_sp_root(sp_root())
csv_file_path = csv_backup_filepath(stock_date=target_file_date, root=SP_ROOT)

df = pl.read_csv(
    csv_file_path, 
    schema_overrides={"stock_date": pl.Date,}
) 

for day in unique_days:
    target_date = date(target_year, target_month, day)
    print(f"Removing data for {target_date} from CSV...")


    df = df.filter(pl.col("stock_date") != target_date)


df.write_csv(csv_file_path)