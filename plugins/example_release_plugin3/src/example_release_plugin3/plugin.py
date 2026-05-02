"""Example external plugin implementation for nexuscli."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import typer

from babel.core import Locale
from babel.support import Translations

from nexuscli.core.plugin_contract import CliPluginBase, CommandMetadata

class HelloReleasePlugin(CliPluginBase):
    """Example plugin for development and release workflow."""

    def __init__(self) -> None:
        self.loaded_context: dict[str, Any] | None = None
        self.last_error: str | None = None
        self.hello_app: typer.Typer | None = None
        self._: Callable[[str], str] = lambda message: message

    @property
    def metadata(self) -> CommandMetadata:
        return CommandMetadata(
            plugin_id="example.release-hello3",
            command_name="hello3",
            help_text=self._("Example hello3 command from external plugin"),
            version="0.1.0",
            min_cli_version=">=0.1.0",
            dependencies=("typer>=0.12,<1.0",),
        )

    @property
    def typer_app(self) -> typer.Typer:
        return self.hello_app

    def on_configure(self, context: dict[str, Any]) -> None:
        """Lifecycle hook called before the plugin's Typer app is built.
        
        Common context keys include:
        - language: effective language for this plugin.
        - global_language: global CLI language.
        - plugin_language: plugin-specific language override or None.
        """
        language = context.get("language", "en")
        language_tag = language.replace("-", "_")
        locale = Locale.parse(language_tag)
        locales_dir = Path(__file__).resolve().parent / "locales"

        try:
            translations = Translations.load(
                str(locales_dir),
                locales=[str(locale)],
                domain="messages"
            )
        except OSError:
            return

        self._ = translations.gettext

    def build_app(self) -> typer.Typer:
        _ = self._
        self.hello_app = typer.Typer(
            help=_("Greeting commands from example external plugin."),
        )

        @self.hello_app.command(
            "greet",
            help=_("Print a greeting message with selectable style."),
        )
        def greet(
            name: str = typer.Argument(
                ..., help=_("Name of the target person."),
            ),
            style: str = typer.Option(
                "friendly",
                "--style",
                "-s",
                help=_("Greeting style: friendly, formal, excited."),
            ),
        ) -> None:
            """Print a greeting message with selectable style."""
            normalized = style.strip().lower()

            if normalized == "friendly":
                typer.echo(_("Hi, {name}! Glad to see you.").format(name=name))
                return
            if normalized == "formal":
                typer.echo(_("Hello, {name}. Welcome.").format(name=name))
                return
            if normalized == "excited":
                typer.echo(
                    _("HEY {name}! GREAT TO HAVE YOU HERE!").format(
                        name=name.upper(),
                    )
                )
                return

            raise typer.BadParameter(
                _("style must be one of: friendly, formal, excited")
            )

        return self.hello_app

    def on_load(self, context: dict[str, Any]) -> None:
        """Lifecycle hook called after successful registration.

        Common context keys include:
        - source: plugin discovery source identifier.
        - command_path: resolved command mount path.
        - language: effective language for this plugin.
        - global_language: global CLI language.
        - plugin_language: plugin-specific language override or None.
        """
        self.loaded_context = context
        
        # Log plugin loading information
        source = context.get("source", "unknown")
        command_path = context.get("command_path", "unknown")
        language = context.get("language", "en")
        global_language = context.get("global_language", "en")
        plugin_language = context.get("plugin_language")

    def on_error(self, error: Exception) -> None:
        self.last_error = str(error)
