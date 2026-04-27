from __future__ import annotations

from pathlib import Path
import sys

import typer

ROOT = Path(__file__).resolve().parents[3]
CORE_SRC = ROOT / "src"
PLUGIN_SRC = Path(__file__).resolve().parents[1] / "src"

for candidate in (str(CORE_SRC), str(PLUGIN_SRC)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from typer.testing import CliRunner

from example_release_plugin.plugin import HelloReleasePlugin


def test_metadata_contract() -> None:
    plugin = HelloReleasePlugin()
    meta = plugin.metadata

    assert meta.plugin_id == "example.release-hello"
    assert meta.command_name == "hello"
    assert meta.min_cli_version.startswith(">=")


def test_greet_command_outputs_formal_message() -> None:
    plugin = HelloReleasePlugin()
    runner = CliRunner()
    root = typer.Typer()
    root.add_typer(plugin.typer_app, name="hello")

    result = runner.invoke(root, ["hello", "greet", "Copilot", "--style", "formal"])

    assert result.exit_code == 0
    assert "Hello, Copilot. Welcome." in result.stdout
