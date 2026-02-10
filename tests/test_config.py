"""Tests for config loading and saving."""

import tomllib

from oai_whisper import config
from oai_whisper.constants import DEFAULT_MODEL


def test_load_defaults_when_no_file(tmp_path, monkeypatch):
    """load() returns defaults when config file doesn't exist."""
    monkeypatch.setattr(config, "_config_path", lambda: tmp_path / "nonexistent.toml")
    cfg = config.load()
    assert cfg["model"] == DEFAULT_MODEL
    assert cfg["hotkey"] == "option"
    assert cfg["language"] == ""


def test_load_merges_with_defaults(tmp_path, monkeypatch):
    """load() merges file values with defaults (file wins)."""
    path = tmp_path / "config.toml"
    path.write_text('model = "gpt-4o-transcribe"\n')
    monkeypatch.setattr(config, "_config_path", lambda: path)

    cfg = config.load()
    assert cfg["model"] == "gpt-4o-transcribe"
    # Defaults still present for keys not in file
    assert cfg["hotkey"] == "option"
    assert cfg["language"] == ""


def test_save_creates_file(tmp_path, monkeypatch):
    """save() creates the config file and parent dirs."""
    path = tmp_path / "subdir" / "config.toml"
    monkeypatch.setattr(config, "_config_path", lambda: path)

    config.save({"model": "gpt-4o-transcribe", "hotkey": "left_option", "language": "en"})
    assert path.exists()

    with open(path, "rb") as f:
        data = tomllib.load(f)
    assert data["model"] == "gpt-4o-transcribe"
    assert data["hotkey"] == "left_option"
    assert data["language"] == "en"


def test_save_then_load_roundtrip(tmp_path, monkeypatch):
    """save() followed by load() returns the same data."""
    path = tmp_path / "config.toml"
    monkeypatch.setattr(config, "_config_path", lambda: path)

    original = {"model": "gpt-4o-transcribe", "hotkey": "right_option", "language": "ja"}
    config.save(original)
    loaded = config.load()
    assert loaded == original
