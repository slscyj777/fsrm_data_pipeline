import json
from pathlib import Path

SETTINGS_PATH = Path(__file__).resolve().parent.parent / "settings.json"


def load_settings() -> dict[str, str]:
    if SETTINGS_PATH.exists():
        settings = (json.loads(SETTINGS_PATH.read_text(encoding="utf-8")))
    else:
        settings = {}

    return settings


def save_settings(current: dict[str, str], values: dict[str, str]) -> None:
    current.update(values)
    
    tmp_path = SETTINGS_PATH.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(current, indent=4), encoding="utf-8")
    tmp_path.replace(SETTINGS_PATH)