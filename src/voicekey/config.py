"""TOML config at ~/.config/voicekey/config.toml."""

import tomllib
from pathlib import Path

import tomli_w

from .constants import CONFIG_DIR, CONFIG_FILE, DEFAULT_MODEL, DEFAULT_PROVIDER

DEFAULTS = {
    "provider": DEFAULT_PROVIDER,
    "model": DEFAULT_MODEL,
    "hotkey": "option",  # "option", "left_option", "right_option"
    "language": "",      # empty = auto-detect
}


def _config_path() -> Path:
    return Path(CONFIG_DIR).expanduser() / CONFIG_FILE


def load() -> dict:
    path = _config_path()
    if not path.exists():
        return dict(DEFAULTS)
    with open(path, "rb") as f:
        data = tomllib.load(f)
    merged = dict(DEFAULTS)
    merged.update(data)
    return merged


def save(cfg: dict) -> None:
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        tomli_w.dump(cfg, f)
