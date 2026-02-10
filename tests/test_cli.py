"""Tests for CLI commands."""

from click.testing import CliRunner

from oai_whisper.cli import main


def test_help():
    """--help shows usage and commands."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "voice dictation" in result.output
    assert "setup" in result.output
    assert "config" in result.output


def test_config_show_all(monkeypatch):
    """'config' with no args shows all config values."""
    from oai_whisper import config
    monkeypatch.setattr(config, "load", lambda: {
        "model": "gpt-4o-mini-transcribe",
        "hotkey": "option",
        "language": "",
    })

    runner = CliRunner()
    result = runner.invoke(main, ["config"])
    assert result.exit_code == 0
    assert "model" in result.output
    assert "gpt-4o-mini-transcribe" in result.output
    assert "hotkey" in result.output


def test_config_show_single(monkeypatch):
    """'config <key>' shows a single value."""
    from oai_whisper import config
    monkeypatch.setattr(config, "load", lambda: {"model": "gpt-4o-mini-transcribe"})

    runner = CliRunner()
    result = runner.invoke(main, ["config", "model"])
    assert result.exit_code == 0
    assert "gpt-4o-mini-transcribe" in result.output


def test_config_show_unknown_key(monkeypatch):
    """'config <unknown>' prints error."""
    from oai_whisper import config
    monkeypatch.setattr(config, "load", lambda: {"model": "gpt-4o-mini-transcribe"})

    runner = CliRunner()
    result = runner.invoke(main, ["config", "nonexistent"])
    assert "Unknown config key" in result.output


def test_config_set_value(monkeypatch, tmp_path):
    """'config <key> <value>' saves the new value."""
    from oai_whisper import config
    saved = {}

    def mock_save(cfg):
        saved.update(cfg)

    monkeypatch.setattr(config, "load", lambda: {"model": "gpt-4o-mini-transcribe"})
    monkeypatch.setattr(config, "save", mock_save)

    runner = CliRunner()
    result = runner.invoke(main, ["config", "model", "gpt-4o-transcribe"])
    assert result.exit_code == 0
    assert "Set model" in result.output
    assert saved["model"] == "gpt-4o-transcribe"


def test_setup_new_key(monkeypatch):
    """'setup' prompts for API key when none exists."""
    from oai_whisper import auth

    monkeypatch.setattr(auth, "get_api_key", lambda: None)
    stored_keys = []
    monkeypatch.setattr(auth, "set_api_key", lambda k: stored_keys.append(k))

    # Mock permissions module to avoid macOS-specific calls
    import types
    mock_perms = types.ModuleType("permissions")
    mock_perms.check_and_guide = lambda: None
    monkeypatch.setattr("oai_whisper.cli.permissions", mock_perms, raising=False)
    import oai_whisper.permissions
    monkeypatch.setattr(oai_whisper.permissions, "check_and_guide", lambda: None)

    runner = CliRunner()
    result = runner.invoke(main, ["setup"], input="sk-testkey123\n")
    assert result.exit_code == 0
    assert "API key saved" in result.output
    assert stored_keys == ["sk-testkey123"]
