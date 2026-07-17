from datetime import date
from pathlib import Path
from pipeline.config import get_settings


def sp_root() -> Path:
    return Path.home() / get_settings().SP_SYNC_PATH


def validate_sp_root(root: Path) -> Path:
    if not root.exists():
        raise FileNotFoundError(f"SharePoint sync directory not found at: {root}\nEnsure folder is synced.")
    return root


def csv_backup_filepath(stock_date: date, root: Path | None = None) -> Path:
    settings = get_settings()
    root = root or sp_root()
    filename = f"FSRM_consolidated_{stock_date.strftime('%B')}_{stock_date.year}.csv"
    return root / settings.FSRM_FOLDER / "backup_csv" / filename