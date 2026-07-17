from agent.workflow import agent_workflow
from datetime import date
from pipeline.paths import csv_backup_filepath
import polars as pl


def run_agent_summary(stock_date: date, threshold_pct: float):
    csv_file_path = csv_backup_filepath(stock_date)
    df = pl.read_csv(csv_file_path,
                     schema_overrides={"stock_date": pl.Date}).filter(pl.col("stock_date") == stock_date)
    summary = agent_workflow(df, threshold_pct, stock_date)

    return summary

