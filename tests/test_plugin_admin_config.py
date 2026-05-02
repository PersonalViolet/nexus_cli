from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from nexuscli.commands import plugin_admin
from nexuscli.config import Settings


def test_config_command_updates_and_saves(monkeypatch) -> None:
    """config command should apply validated options and persist settings."""
    base = Settings(
        entrypoint_group="nexuscli.command",
        conflict_policy="error",
        enable_folder_loader=False,
        plugin_dirs=["C:/plugins/default"],
        disabled_plugins=[],
        language="en",
        plugin_languages={"legacy.plugin": "zh"},
    )
    saved: dict[str, Settings] = {}

    def fake_load_settings() -> Settings:
        return Settings(
            entrypoint_group=base.entrypoint_group,
            conflict_policy=base.conflict_policy,
            enable_folder_loader=base.enable_folder_loader,
            plugin_dirs=list(base.plugin_dirs),
            disabled_plugins=list(base.disabled_plugins),
            language=base.language,
            plugin_languages=dict(base.plugin_languages),
        )

    def fake_save_settings(settings: Settings) -> None:
        saved["value"] = settings

    monkeypatch.setattr(plugin_admin, "load_settings", fake_load_settings)
    monkeypatch.setattr(plugin_admin, "save_settings", fake_save_settings)
    monkeypatch.setattr(plugin_admin, "get_config_path", lambda: Path("C:/tmp/config.json"))

    runner = CliRunner()
    result = runner.invoke(
        plugin_admin.app,
        [
            "config",
            "--entrypoint-group",
            "custom.group",
            "--conflict-policy",
            "skip",
            "--folder-loader",
            "--set-plugin-dir",
            "D:/plugins/a",
            "--add-plugin-dir",
            "D:/plugins/b",
            "--remove-plugin-dir",
            "C:/plugins/default",
            "--language",
            "zh",
            "--set-plugin-language",
            "example.release-hello:ja",
            "--set-plugin-language",
            "builtin.file:en",
            "--remove-plugin-language",
            "builtin.file",
            "--yes",
        ],
    )

    assert result.exit_code == 0
    assert "Config updated" in result.stdout
    assert "value" in saved

    updated = saved["value"]
    assert updated.entrypoint_group == "custom.group"
    assert updated.conflict_policy == "skip"
    assert updated.enable_folder_loader is True
    assert updated.plugin_dirs == [
        str(Path("D:/plugins/a").expanduser()),
        str(Path("D:/plugins/b").expanduser()),
    ]
    assert updated.language == "zh"
    assert updated.plugin_languages == {
        "legacy.plugin": "zh",
        "example.release-hello": "ja",
    }


def test_config_command_rejects_invalid_conflict_policy(monkeypatch) -> None:
    """config command should show a friendly validation error for bad policy."""

    monkeypatch.setattr(plugin_admin, "load_settings", lambda: Settings())
    monkeypatch.setattr(plugin_admin, "get_config_path", lambda: Path("C:/tmp/config.json"))

    runner = CliRunner()
    result = runner.invoke(
        plugin_admin.app,
        [
            "config",
            "--conflict-policy",
            "replace",
            "--yes",
        ],
    )

    assert result.exit_code != 0
    assert "conflict_policy must be one of" in result.output


def test_config_command_rejects_invalid_language(monkeypatch) -> None:
    """config command should reject non ISO-639-1 language values."""

    monkeypatch.setattr(plugin_admin, "load_settings", lambda: Settings())
    monkeypatch.setattr(plugin_admin, "get_config_path", lambda: Path("C:/tmp/config.json"))

    runner = CliRunner()
    result = runner.invoke(
        plugin_admin.app,
        [
            "config",
            "--language",
            "zh-cn",
            "--yes",
        ],
    )

    assert result.exit_code != 0
    assert "language must be ISO-639-1 format" in result.output
