"""Typer command registration for plugins."""

from __future__ import annotations

from dataclasses import dataclass

import typer

from share_cli.core.errors import PluginConflictError
from share_cli.core.plugin_contract import CliPluginBase


@dataclass(slots=True)
class RegisteredPlugin:
    """Registration details for one plugin."""

    plugin: CliPluginBase
    source: str
    command_path: str


class PluginRegistry:
    """Mount plugins onto Typer app with conflict detection."""

    def __init__(self, app: typer.Typer, conflict_policy: str = "error") -> None:
        self._app = app
        self._conflict_policy = conflict_policy
        self._groups: dict[str, typer.Typer] = {}
        self._registered: dict[str, RegisteredPlugin] = {}
        self._command_to_plugin: dict[str, str] = {}

    def register(self, plugin: CliPluginBase, source: str) -> tuple[bool, str]:
        """Register one plugin and return (success, command_path)."""
        meta = plugin.metadata
        command_path = (
            f"{meta.command_group}.{meta.command_name}"
            if meta.command_group
            else meta.command_name
        )

        existing = self._command_to_plugin.get(command_path)
        if existing is not None:
            message = (
                f"Command path '{command_path}' already registered by plugin '{existing}'"
            )
            if self._conflict_policy == "skip":
                return False, message
            raise PluginConflictError(message)

        mount_target = self._resolve_mount_target(meta.command_group)
        mount_target.add_typer(
            plugin.typer_app,
            name=meta.command_name,
            help=meta.help_text or None,
            no_args_is_help=True,
        )

        self._command_to_plugin[command_path] = meta.plugin_id
        self._registered[meta.plugin_id] = RegisteredPlugin(
            plugin=plugin,
            source=source,
            command_path=command_path,
        )
        return True, command_path

    def _resolve_mount_target(self, group_name: str | None) -> typer.Typer:
        if not group_name:
            return self._app

        group = self._groups.get(group_name)
        if group is None:
            group = typer.Typer(help=f"Commands under group '{group_name}'.")
            self._app.add_typer(group, name=group_name, no_args_is_help=True)
            self._groups[group_name] = group
        return group
