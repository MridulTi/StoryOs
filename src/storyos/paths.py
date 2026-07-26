from __future__ import annotations

import os
from pathlib import Path

from platformdirs import user_config_dir, user_data_dir

APP_NAME = "storyos"
APP_AUTHOR = False


def default_config_path() -> Path:
    return Path(user_config_dir(APP_NAME, appauthor=APP_AUTHOR)) / f"{APP_NAME}.toml"


def default_data_path() -> Path:
    return Path(user_data_dir(APP_NAME, appauthor=APP_AUTHOR))


def expand_path(value: str) -> Path:
    return Path(os.path.expanduser(value)).resolve()


def resolve_config_path(config: Path | None) -> Path:
    if config is not None:
        return config.expanduser().resolve()
    env_path = os.environ.get("STORYOS_CONFIG")
    if env_path:
        return Path(env_path).expanduser().resolve()
    return default_config_path()
