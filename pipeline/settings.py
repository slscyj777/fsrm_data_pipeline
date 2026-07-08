import json
from pathlib import Path
from pipeline.config import DEFAULTS

SETTINGS_PATH = Path(__file__).resolve().parent.parent / "settings.json"


def load_settings() -> dict[str, str]:
    settings = dict(DEFAULTS)
    if SETTINGS_PATH.exists():
        settings.update(json.loads(SETTINGS_PATH.read_text(encoding="utf-8")))

    return settings


def save_settings(values: dict[str, str]) -> None:
    tmp_path = SETTINGS_PATH.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(values, indent=4), encoding="utf-8")
    tmp_path.replace(SETTINGS_PATH) 