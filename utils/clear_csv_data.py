import polars as pl
from datetime import date

unique_days = [4,5,6]
target_month = 7 
target_year = 2026
#if target_month is not None else today.month

for day in unique_days:
    target_date = date(target_year, target_month, day)
    print(f"Removing data for {target_date} from CSV...")
    df = pl.read_csv(
        f"data/FSRM_consolidated_{target_date.strftime('%B')}_{target_year}.csv", 
        schema_overrides={"stock_date": pl.Date}
    )

    df = df.filter(pl.col("stock_date") != target_date)

    df.write_csv(f"data/FSRM_consolidated_{target_date.strftime('%B')}_{target_year}.csv")