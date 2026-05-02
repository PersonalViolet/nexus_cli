from __future__ import annotations

import json
from pathlib import Path

from share_cli import config
from share_cli.config import Settings


def test_load_settings_language_defaults(monkeypatch, tmp_path: Path) -> None:
    """Missing language fields should fall back to backward-compatible defaults."""
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(config, "get_config_path", lambda: cfg_path)

    settings = config.load_settings()

    assert settings.language == "en"
    assert settings.plugin_languages == {}


def test_load_settings_language_env_overrides(monkeypatch, tmp_path: Path) -> None:
    """Environment variables should override file-level language settings."""
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(
        json.dumps(
            {
                "language": "zh",
                "plugin_languages": {
                    "example.release-hello": "ja",
                    "bad.plugin": "zh-cn",
                },
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(config, "get_config_path", lambda: cfg_path)
    monkeypatch.setenv("SHARE_CLI_LANGUAGE", "fr")
    monkeypatch.setenv(
        "SHARE_CLI_PLUGIN_LANGUAGES",
        "example.release-hello:de,builtin.file:ja,malformed,no_lang:",
    )

    settings = config.load_settings()

    assert settings.language == "fr"
    assert settings.plugin_languages == {
        "example.release-hello": "de",
        "builtin.file": "ja",
    }


def test_save_settings_persists_language_fields(monkeypatch, tmp_path: Path) -> None:
    """save_settings should persist global and per-plugin language fields."""
    cfg_path = tmp_path / "config.json"

    monkeypatch.setattr(config, "get_config_path", lambda: cfg_path)

    settings = Settings(
        entrypoint_group="share_cli.command",
        conflict_policy="error",
        enable_folder_loader=False,
        plugin_dirs=["C:/plugins/default"],
        disabled_plugins=[],
        language="zh",
        plugin_languages={"example.release-hello": "ja"},
    )
    config.save_settings(settings)

    data = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert data["language"] == "zh"
    assert data["plugin_languages"] == {"example.release-hello": "ja"}
