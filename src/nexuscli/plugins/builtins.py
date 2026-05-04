"""Built-in plugin providers."""

from __future__ import annotations

from nexuscli.core.plugin_contract import CliPluginBase
from nexuscli.commands.file_batch_rename import FileCommandsPlugin
from nexuscli.commands.plugin_admin import PluginAdminPlugin
from nexuscli.commands.repo import RepoCommandsPlugin


def get_builtin_plugins() -> list[CliPluginBase]:
    """Return built-in plugin instances."""
    return [
        PluginAdminPlugin(),
        RepoCommandsPlugin(),
    ]
