"""Plugin contract definitions."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Any

import typer


@dataclass(frozen=True, slots=True)
class CommandMetadata:
    """Required metadata for each plugin."""

    plugin_id: str
    command_name: str
    command_group: str | None = None
    help_text: str = ""
    version: str = "0.1.0"
    min_cli_version: str = ">=0.1.0"
    dependencies: tuple[str, ...] = ()


class CliPluginBase(ABC):
    """Base plugin class for command providers."""

    @property
    def metadata(self) -> CommandMetadata:
        raise NotImplementedError

    @property
    def typer_app(self) -> typer.Typer:
        raise NotImplementedError

    def on_load(self, context: dict[str, Any]) -> None:
        """Lifecycle hook called after successful registration."""

    def on_error(self, error: Exception) -> None:
        """Lifecycle hook called when plugin activation fails."""
