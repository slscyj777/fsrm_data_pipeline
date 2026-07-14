import polars as pl
from datetime import date

unique_days = [10,11,12,13]
target_month = 7 
target_year = 2026
#if target_month is not None else today.month
month_name = date(target_year, target_month, 1).strftime('%B')
df = pl.read_csv(
    f"data/FSRM_consolidated_{month_name}_{target_year}.csv", 
    schema_overrides={"stock_date": pl.Date,}
)

for day in unique_days:
    target_date = date(target_year, target_month, day)
    print(f"Removing data for {target_date} from CSV...")


    df = df.filter(pl.col("stock_date") != target_date)

    df.write_csv(f"data/FSRM_consolidated_{target_date.strftime('%B')}_{target_year}.csv")