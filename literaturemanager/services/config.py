"""Application configuration management."""

import json
import os
from typing import Any


def get_config_path() -> str:
    if os.name == "nt":
        app_data = os.environ.get("APPDATA", os.path.expanduser("~"))
        config_dir = os.path.join(app_data, "LiteratureManager")
    else:
        config_dir = os.path.join(os.path.expanduser("~"), ".literaturemanager")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "config.json")


DEFAULTS = {
    "theme": "dark",
    "api_port": 52525,
    "api_enabled": True,
    "window_width": 1200,
    "window_height": 800,
}


class Config:
    """Simple JSON-based application configuration."""

    def __init__(self):
        self.path = get_config_path()
        self._data: dict[str, Any] = {}
        self.load()

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._data = {}
        for key, val in DEFAULTS.items():
            self._data.setdefault(key, val)

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value):
        self._data[key] = value
        self.save()
