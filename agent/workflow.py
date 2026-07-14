from datetime import date

import polars as pl

from agent.anomalies import flag_anomalies
from agent.gemini import summarize_anomalies


def agent_workflow(df: pl.DataFrame, threshold_pct: float, stock_date: date) -> str:
    anomalies_df = flag_anomalies(df, threshold_pct=threshold_pct)
    if anomalies_df.height > 0:
        return summarize_anomalies(anomalies_df, stock_date)
    return f"No shortages found below {threshold_pct:.0%} of forecast for {stock_date}."