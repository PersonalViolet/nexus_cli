"""Plugin contract definitions."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Any

import typer

from pathlib import Path

from babel.core import Locale
from babel.support import Translations


@dataclass(frozen=True, slots=True)
class CommandMetadata:
    """Required metadata for each plugin."""

    plugin_id: str  # Globally unique plugin identifier.
    command_name: str  # Command name exposed by this plugin.
    command_group: str | None = None  # Optional group; None mounts at root level.
    help_text: str = ""  # Short help message shown in CLI help output.
    version: str = "0.1.0"  # Plugin version string.
    min_cli_version: str = ">=0.1.0"  # Required nexuscli version specifier.
    dependencies: tuple[str, ...] = ()  # Runtime dependency specifiers to validate.


class CliPluginBase(ABC):
    """Base plugin class for command providers."""

    @property
    def metadata(self) -> CommandMetadata:
        raise NotImplementedError

    @property
    def typer_app(self) -> typer.Typer:
        """Return the Typer app instance for this plugin."""
        raise NotImplementedError


    def on_configure(self, context: dict[str, Any]) -> None:
        """Lifecycle hook called before the plugin's Typer app is built.
        
        Common context keys include:
        - language: effective language for this plugin.
        - global_language: global CLI language.
        - plugin_language: plugin-specific language override or None.
        """
        pass

    def build_app(self) -> typer.Typer:
        """Build and return the Typer app instance for this plugin."""
        # raise NotImplementedError



    def on_load(self, context: dict[str, Any]) -> None:
        """Lifecycle hook called after successful registration.

        Common context keys include:
        - source: plugin discovery source identifier.
        - command_path: resolved command mount path.
        - language: effective language for this plugin.
        - global_language: global CLI language.
        - plugin_language: plugin-specific language override or None.
        """

    def on_error(self, error: Exception) -> None:
        """Lifecycle hook called when plugin activation fails."""

