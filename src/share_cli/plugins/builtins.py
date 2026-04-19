"""Built-in plugin providers."""

from __future__ import annotations

from share_cli.core.plugin_contract import CliPluginBase
from share_cli.commands.file_batch_rename import FileCommandsPlugin
from share_cli.commands.plugin_admin import PluginAdminPlugin


def get_builtin_plugins() -> list[CliPluginBase]:
    """Return built-in plugin instances."""
    return [
        PluginAdminPlugin(),
        FileCommandsPlugin(),
    ]
