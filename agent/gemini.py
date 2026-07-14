import logging
import os
import time
from datetime import date
from functools import cache
from pathlib import Path

import polars as pl
import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-3.5-flash"  # free tier
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


@cache
def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent

@cache
def _load_env() -> None:
    load_dotenv(_project_root() / ".env", override=True)

def summarize_anomalies(
    anomalies_df: pl.DataFrame,
    stock_date: date,
    max_records: int = 500,
    max_retries: int = 2,
) -> str:
    """Sends top flagged shortage rows to Gemini for a plain-language executive briefing."""
    _load_env()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "No summary generated: GEMINI_API_KEY not set in .env"

    payload_data = anomalies_df.head(max_records).to_dicts()

    prompt = (
        f"You're an AI logistics analyst briefing a non-technical replenishment team on shortages for {stock_date}. "
        f"Below is a list of the top {len(payload_data)} SKUs currently below forecast. "
        "Write a short, plain-language summary in bullet points in thai, calling out the branches/SKUs most in need of stock and which branches/ region the planner should follow up on those areas:\n\n"
        f"{payload_data}\n\n"
        "Do not hallucinate numbers or data outside this provided dictionary.\n\n"
        "Schema info = {sermsuk_branch_name: name of branch ,region_TBL: region of TBL mapped to the branch , SKU: product code, description: product description, brand: brand of product, category: category of product (beer, spirits, soda),ending_stock_case: ending stock level for the day, forecast: forecasted stocked needed, shortage_pct: percentage below forecast}"
        "Sample analysis format to follow:"
        f"Replenishment summary for {stock_date}:"
        "Product ____ in branch หน่วยปทุมธานี in tbl region R1 is 80 % below forecast, please check dashboard etc etc."
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
            logger.error("Gemini request failed: %s", e)
            return f"Summary generation failed ({e}). Anomalies were still detected."
        except requests.exceptions.RequestException as e:
            logger.error("Gemini request failed: %s", e)
            return f"Summary generation failed ({e}). Anomalies were still detected."
        except (KeyError, IndexError) as e:
            logger.exception("Unexpected Gemini response shape")
            return f"Summary generation failed ({e}). Anomalies were still detected."
    return "Summary generation failed: retries exhausted."