import polars as pl
from datetime import date
from pipeline.config import MONTH

today = date.today()
unique_days = [30]
target_month = MONTH if MONTH is not None else today.month

for day in unique_days:
    target_date = date(today.year, target_month, day)
    print(f"Removing data for {target_date} from CSV...")
    df = pl.read_csv(
        "data/FSRM_consolidated_June_2026.csv", 
        schema_overrides={"stock_date": pl.Date}
    )

    df = df.filter(pl.col("stock_date") != target_date)

    df.write_csv("data/FSRM_consolidated_June_2026.csv")