import polars as pl
from pathlib import Path
from pipeline.summary import agent_workflow
from datetime import date

PROJECT_ROOT = Path(__file__).resolve().parent

def get_csv_backup_filepath(stock_date: date) -> Path:
    filename = f"FSRM_consolidated_{stock_date.strftime('%B')}_{stock_date.year}.csv"
    csv_file_path = PROJECT_ROOT / "data" / filename
    return csv_file_path


def run_agent_summary(stock_date: date, threshold_pct: float):
    csv_file_path = get_csv_backup_filepath(stock_date)
    df = pl.read_csv(csv_file_path,
                     schema_overrides={"stock_date": pl.Date}).filter(pl.col("stock_date") == stock_date)
    summary = agent_workflow(df, threshold_pct, stock_date)

    return summary


  