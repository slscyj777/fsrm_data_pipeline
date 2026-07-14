import os
import time
from datetime import date
from dotenv import load_dotenv
from pathlib import Path
from functools import cache
import polars as pl
import requests

 
@cache
def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent

@cache
def _load_env() -> None:
    load_dotenv(_project_root() / ".env", override=True)

def flag_anomalies(df: pl.DataFrame, threshold_pct: float) -> pl.DataFrame:
    '''
    Flags SKU/branch rows where ending stock is below forecast by more than threshold_pct.
    Rows with no forecast (forecast == 0, filled by map_forecast_to_daily) are excluded
    since there's nothing to compare against.
    '''
    return (
        df.filter(pl.col("forecast") > 0)
          .with_columns(
              (1 - pl.col("ending_stock_case") / pl.col("forecast")).alias("shortage_pct")
          )
          .filter(pl.col("shortage_pct") > threshold_pct)
          .select(
              "sermsuk_branch_name","region_TBL", "SKU", "description", "brand", "category",
              "ending_stock_case", "forecast", "shortage_pct"
          )
          .sort("shortage_pct", descending=True)
    )


GEMINI_MODEL = "gemini-3.5-flash"  # free tier
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


def summarize_anomalies(anomalies_df: pl.DataFrame, stock_date: date, max_records: int = 500, max_retries: int = 2) -> str:
    """Sends top flagged shortage rows to Gemini for a plain-language executive briefing."""
    _load_env()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "No summary generated: GEMINI_API_KEY not set in .env"

    payload_data = anomalies_df.head(max_records).to_dicts()
    
    prompt = (
        f"You're an AI logistics analyst briefing a non-technical replenishment team on shortages for {stock_date}. "
        f"Below is a list of the top {len(payload_data)} SKUs currently below forecast. "
        "Write a short, plain-language summary in bullet points in thai, calling out the branches/SKUs most in need of stock and which branches/ region the planner should look deeper into in the monitoring dashboard:\n\n"
        f"{payload_data}\n\n"
        "Do not hallucinate numbers or data outside this provided dictionary.\n\n"
        "Schema info = {sermsuk_branch_name: name of branch ,region_TBL: region of TBL mapped to the branch , SKU: product code, description: product description, brand: brand of product, category: category of product (beer, spirits, soda),ending_stock_case: ending stock level for the day, forecast: forecasted stocked needed, shortage_pct: percentage below forecast}"
        "Sample analysis:"
        f"Replenishment summary for {stock_date}:"
        "product ____ in branch หน่วยปทุมธานี in tbl region R1 is 80 % below forecast, please check dashboard"
    )
    
    for attempt in range(max_retries + 1):
            try:
                response = requests.post(
                    GEMINI_URL,
                    headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                    timeout=30,
                )
                response.raise_for_status()
                return response.json()["candidates"][0]["content"]["parts"][0]["text"]
            except requests.exceptions.HTTPError as e:
                status = e.response.status_code if e.response is not None else None
                if status in (429, 503) and attempt < max_retries:
                    time.sleep(2**attempt) 
                    continue
                return f"Summary generation failed ({e}). Anomalies were still detected."
            except Exception as e:
                return f"Summary generation failed ({e}). Anomalies were still detected."
    return "Summary generation failed: retries exhausted."

def agent_workflow(df: pl.DataFrame, threshold_pct: float, stock_date: date) -> str:

    anomalies_df = flag_anomalies(df, threshold_pct=threshold_pct)
    if anomalies_df.height > 0:
        summary = summarize_anomalies(anomalies_df, stock_date)

    else:
        summary = f"No shortages found below {threshold_pct:.0%} of forecast for {stock_date}."

    return summary