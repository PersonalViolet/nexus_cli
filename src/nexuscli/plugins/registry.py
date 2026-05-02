"""Typer command registration for plugins."""

from __future__ import annotations

from dataclasses import dataclass

import typer

from nexuscli.core.errors import PluginConflictError
from nexuscli.core.plugin_contract import CliPluginBase


@dataclass(slots=True)
class RegisteredPlugin:
    """Registration details for one plugin."""

    plugin: CliPluginBase
    source: str
    command_path: str


class PluginRegistry:
    """Mount plugins onto Typer app with conflict detection."""

    def __init__(self, app: typer.Typer, conflict_policy: str = "error") -> None:
        self._app = app # The root Typer application instance where commands are mounted.
        self._conflict_policy = conflict_policy # Strategy for handling command conflicts: 'error' (raise exception) or 'skip' (ignore duplicate).
        
        # Maps group names to their corresponding Typer sub-application instances.
        # Used to ensure all plugins in the same group share a single parent command.
        self._groups: dict[str, typer.Typer] = {}

        # Maps plugin IDs to their RegisteredPlugin details.
        # Serves as a registry to look up plugin metadata and instances by ID.
        self._registered: dict[str, RegisteredPlugin] = {}

        # Maps unique command paths (e.g., "group.command" or "justCommandname") to the plugin ID that owns them.
        # Used for fast conflict detection to prevent multiple plugins from registering the same command.      
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
        """Resolve the Typer application instance where the plugin commands should be mounted.

        This method handles the hierarchical structure of commands:
        - If no group is specified, it returns the main CLI application instance.
        - If a group name is provided, it retrieves or creates a dedicated Typer sub-application
          for that group. This ensures that all plugins belonging to the same group are nested
          under a single parent command.

        Args:
            group_name: The name of the command group (e.g., 'release'). 
                        If None or empty, the root app is used.

        Returns:
            The typer.Typer instance that serves as the parent for the plugin's commands.
        """
        if not group_name:
            return self._app

        group = self._groups.get(group_name)
        if group is None:
            group = typer.Typer(help=f"Commands under group '{group_name}'.")
            self._app.add_typer(group, name=group_name, no_args_is_help=True)
            self._groups[group_name] = group
        return group
