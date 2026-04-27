"""Example external plugin implementation for share-cli."""

from __future__ import annotations

from typing import Any

import typer

from share_cli.core.plugin_contract import CliPluginBase, CommandMetadata


hello_app = typer.Typer(help=
"Greeting commands from example external plugin.")


@hello_app.command("greet")
def greet(
    name: str = typer.Argument(..., help="Name of the target person."),
    style: str = typer.Option(
        "friendly",
        "--style",
        "-s",
        help="Greeting style: friendly, formal, excited.",
    ),
) -> None:
    """Print a greeting message with selectable style."""
    normalized = style.strip().lower()

    if normalized == "friendly":
        typer.echo(f"Hi, {name}! Glad to see you.")
        return
    if normalized == "formal":
        typer.echo(f"Hello, {name}. Welcome.")
        return
    if normalized == "excited":
        typer.echo(f"HEY {name.upper()}! GREAT TO HAVE YOU HERE!")
        return

    raise typer.BadParameter("style must be one of: friendly, formal, excited")


class HelloReleasePlugin(CliPluginBase):
    """Example plugin for development and release workflow."""

    def __init__(self) -> None:
        self.loaded_context: dict[str, Any] | None = None
        self.last_error: str | None = None

    @property
    def metadata(self) -> CommandMetadata:
        return CommandMetadata(
            plugin_id="example.release-hello",
            command_name="hello",
            help_text="Example hello command from external plugin",
            version="0.1.0",
            min_cli_version=">=0.1.0",
            dependencies=("typer>=0.12,<1.0",),
        )

    @property
    def typer_app(self) -> typer.Typer:
        return hello_app

    def on_load(self, context: dict[str, Any]) -> None:
        self.loaded_context = context

    def on_error(self, error: Exception) -> None:
        self.last_error = str(error)
