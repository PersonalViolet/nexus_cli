"""Built-in plugin admin commands."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from share_cli.config import get_config_path, set_plugin_disabled
from share_cli.core.plugin_contract import CliPluginBase, CommandMetadata
from share_cli.runtime import get_runtime_state


console = Console()
app = typer.Typer(help="Manage plugin lifecycle and runtime status.")


@app.command("list")
def list_plugins(
    show_failed: bool = typer.Option(True, "--failed/--no-failed", help="Show failed plugins."),
    show_skipped: bool = typer.Option(True, "--skipped/--no-skipped", help="Show skipped plugins."),
) -> None:
    """List loaded plugins and diagnostics for this invocation."""
    state = get_runtime_state()

    if state.loaded_plugins:
        table = Table(title="Loaded Plugins")
        table.add_column("Plugin ID")
        table.add_column("Source")
        table.add_column("Command Path")
        table.add_column("Version")

        for rec in sorted(state.loaded_plugins.values(), key=lambda x: x.plugin_id):
            table.add_row(rec.plugin_id, rec.source, rec.command_path, rec.version)

        console.print(table)
    else:
        typer.echo("No plugin loaded in current invocation.")

    if show_skipped and state.skipped_plugins:
        table = Table(title="Skipped Plugins")
        table.add_column("Plugin ID")
        table.add_column("Reason")
        for plugin_id, reason in sorted(state.skipped_plugins.items()):
            table.add_row(plugin_id, reason)
        console.print(table)

    if show_failed and state.failed_plugins:
        table = Table(title="Failed Plugins")
        table.add_column("Plugin")
        table.add_column("Error")
        for plugin_id, reason in sorted(state.failed_plugins.items()):
            table.add_row(plugin_id, reason)
        console.print(table)


@app.command("disable")
def disable_plugin(plugin_id: str = typer.Argument(..., help="Plugin ID to disable.")) -> None:
    """Disable a plugin for next CLI invocations."""
    changed = set_plugin_disabled(plugin_id=plugin_id, disabled=True)
    if changed:
        typer.echo(f"Disabled plugin '{plugin_id}'. Effective next invocation.")
    else:
        typer.echo(f"Plugin '{plugin_id}' was already disabled.")


@app.command("enable")
def enable_plugin(plugin_id: str = typer.Argument(..., help="Plugin ID to enable.")) -> None:
    """Enable a previously disabled plugin."""
    changed = set_plugin_disabled(plugin_id=plugin_id, disabled=False)
    if changed:
        typer.echo(f"Enabled plugin '{plugin_id}'. Effective next invocation.")
    else:
        typer.echo(f"Plugin '{plugin_id}' was already enabled.")


@app.command("inspect")
def inspect_plugin(plugin_id: str = typer.Argument(..., help="Plugin ID to inspect.")) -> None:
    """Inspect one plugin from current runtime state."""
    state = get_runtime_state()
    rec = state.loaded_plugins.get(plugin_id)

    if rec is not None:
        typer.echo(f"plugin_id: {rec.plugin_id}")
        typer.echo(f"source: {rec.source}")
        typer.echo(f"command_path: {rec.command_path}")
        typer.echo(f"version: {rec.version}")
        typer.echo(f"help: {rec.help_text}")
        return

    if plugin_id in state.disabled_plugins:
        typer.echo(f"Plugin '{plugin_id}' is currently disabled.")
        typer.echo(f"Config file: {get_config_path()}")
        return

    reason = state.skipped_plugins.get(plugin_id) or state.failed_plugins.get(plugin_id)
    if reason:
        typer.echo(f"Plugin '{plugin_id}' is not active. Reason: {reason}")
        return

    typer.echo(f"Plugin '{plugin_id}' not found in current invocation.")


@app.command("config-path")
def show_config_path() -> None:
    """Show where plugin config is stored."""
    typer.echo(str(get_config_path()))


class PluginAdminPlugin(CliPluginBase):
    """Expose plugin administration commands."""

    @property
    def metadata(self) -> CommandMetadata:
        return CommandMetadata(
            plugin_id="builtin.plugin-admin",
            command_name="plugin",
            help_text="Plugin management commands",
            version="0.1.0",
            min_cli_version=">=0.1.0",
        )

    @property
    def typer_app(self) -> typer.Typer:
        return app
