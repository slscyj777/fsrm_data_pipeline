import json
from pathlib import Path

SETTINGS_PATH = Path(__file__).resolve().parent.parent / "settings.json"

DEFAULTS: dict[str, str] = {
    "SUB_FOLDER_NAME": "1.Stock FSRM SSC",
    "FSRM_FOLDER": "FSRM_files",
    "SP_SYNC_PATH": "Thai Beverage Public Company Limited/Nitita Chaiarsa - Stock FSRM SSC",
    "MASTER_DIM_FILE": "master_dim.xlsx",
    "SKU_DIM_FILE": "DIM_SKU.xlsx",
    "FORECAST_FILE": "FSRM_Beer&Spirits Sales Forecasting_July 2026 (SOP Template).xlsx",
    "OUTPUT_FILE": "FSRM_consolidated.xlsx",
}


def load_settings() -> dict[str, str]:
    if not SETTINGS_PATH.exists():
        return dict(DEFAULTS)
    saved = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    
    return {**DEFAULTS, **saved}


def save_settings(values: dict[str, str]) -> None:
    tmp_path = SETTINGS_PATH.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(values, indent=4), encoding="utf-8")
    tmp_path.replace(SETTINGS_PATH) 