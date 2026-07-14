import json
from pathlib import Path
from functools import cache

@cache
def _settings_path() -> Path:
    return Path(__file__).resolve().parent.parent / "settings.json"


def load_settings() -> dict[str, str]:
    path = _settings_path()
    if path.exists():
        settings = (json.loads(path.read_text(encoding="utf-8")))
    else:
        settings = {}

    return settings


def save_settings(current: dict[str, str], values: dict[str, str]) -> None:
    current.update(values)
    path = _settings_path()
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(current, indent=4), encoding="utf-8")
    tmp_path.replace(path)