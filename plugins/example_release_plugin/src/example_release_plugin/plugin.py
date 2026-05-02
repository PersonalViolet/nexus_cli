"""Example external plugin implementation for nexuscli."""

from __future__ import annotations

from typing import Any

import typer

from nexuscli.core.plugin_contract import CliPluginBase, CommandMetadata


DEFAULT_LANGUAGE = "en"
GREETING_TEMPLATES: dict[str, dict[str, str]] = {
    "en": {
        "friendly": "Hi, {name}! Glad to see you.",
        "formal": "Hello, {name}. Welcome.",
        "excited": "HEY {upper_name}! GREAT TO HAVE YOU HERE!",
    },
    "zh": {
        "friendly": "你好, {name}! 很高兴见到你",
        "formal": "你好, {name}. 欢迎.",
        "excited": "欢迎你, {upper_name}!",
    },
}

STYLE_ERROR_MESSAGES: dict[str, str] = {
    "en": "style must be one of: friendly, formal, excited",
    "zh": "style 支持: friendly, formal, excited",
}

def _resolve_language(value: Any) -> str:
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in GREETING_TEMPLATES:
            return normalized
    return DEFAULT_LANGUAGE


class HelloReleasePlugin(CliPluginBase):
    """Example plugin for development and release workflow."""

    def __init__(self) -> None:
        self.loaded_context: dict[str, Any] | None = None
        self.last_error: str | None = None
        self.language = DEFAULT_LANGUAGE

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
        return self._app

    def on_configure(self, context: dict[str, Any]) -> None:
        self.language = _resolve_language(context.get("language"))


    def build_app(self) -> typer.Typer:
        self._app = typer.Typer(help="Greeting commands from example external plugin.")
        @self._app.command("greet", help="打印问候消息，支持多种风格")
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
            templates = GREETING_TEMPLATES[self.language]
            template = templates.get(normalized)

            if template is None:
                raise typer.BadParameter(STYLE_ERROR_MESSAGES[self.language])

            typer.echo(template.format(name=name, upper_name=name.upper()))
        return self._app

    def on_load(self, context: dict[str, Any]) -> None:
        self.loaded_context = context
        self.language = _resolve_language(context.get("language"))

    def on_error(self, error: Exception) -> None:
        self.last_error = str(error)
