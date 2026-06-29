import polars as pl
from datetime import date

today = date.today()
day = 25
target_date = date(today.year, today.month, day)

df = pl.read_csv(
    "data/FSRM_consolidated_June_2026.csv", 
    schema_overrides={"stock_date": pl.Date}
)

df = df.filter(pl.col("stock_date") != target_date)

df.write_csv("data/FSRM_consolidated_June_2026.csv")