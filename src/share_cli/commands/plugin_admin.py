"""Built-in plugin admin commands."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from share_cli.config import (
    Settings,
    get_config_path,
    load_settings,
    save_settings,
    set_plugin_disabled,
)
from share_cli.core.plugin_contract import CliPluginBase, CommandMetadata
from share_cli.runtime import get_runtime_state


console = Console()
app = typer.Typer(help="Manage plugin lifecycle and runtime status.")
VALID_CONFLICT_POLICIES = {"error", "skip"}


def _normalize_plugin_dirs(values: list[str]) -> list[str]:
    """Normalize and deduplicate plugin directory values while preserving order."""
    result: list[str] = []
    for value in values:
        cleaned = value.strip()
        if not cleaned:
            continue
        normalized = str(Path(cleaned).expanduser())
        if normalized not in result:
            result.append(normalized)
    return result


def _format_setting_value(value: object) -> str:
    """Render setting values for human-friendly table output."""
    if isinstance(value, list):
        return "\n".join(value) if value else "(empty)"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _settings_changes(before: Settings, after: Settings) -> list[tuple[str, str, str]]:
    """Build a list of changed fields for preview output."""
    changes: list[tuple[str, str, str]] = []
    fields = (
        "entrypoint_group",
        "conflict_policy",
        "enable_folder_loader",
        "plugin_dirs",
        "disabled_plugins",
    )
    for field_name in fields:
        before_value = getattr(before, field_name)
        after_value = getattr(after, field_name)
        if before_value != after_value:
            changes.append(
                (
                    field_name,
                    _format_setting_value(before_value),
                    _format_setting_value(after_value),
                )
            )
    return changes


def _print_changes(changes: list[tuple[str, str, str]]) -> None:
    """Render configuration changes as a table."""
    table = Table(title="Config Changes")
    table.add_column("Field")
    table.add_column("Current")
    table.add_column("New")

    for field_name, current_value, new_value in changes:
        table.add_row(field_name, current_value, new_value)

    console.print(table)


def _print_current_settings(settings: Settings) -> None:
    """Render full settings snapshot."""
    table = Table(title="Current Plugin Settings")
    table.add_column("Field")
    table.add_column("Value")

    table.add_row("entrypoint_group", settings.entrypoint_group)
    table.add_row("conflict_policy", settings.conflict_policy)
    table.add_row("enable_folder_loader", _format_setting_value(settings.enable_folder_loader))
    table.add_row("plugin_dirs", _format_setting_value(settings.plugin_dirs))
    table.add_row("disabled_plugins", _format_setting_value(settings.disabled_plugins))

    console.print(table)


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


@app.command("config")
def update_config(
    entrypoint_group: str | None = typer.Option(
        None,
        "--entrypoint-group",
        help="Set plugin discovery entry point group.",
    ),
    conflict_policy: str | None = typer.Option(
        None,
        "--conflict-policy",
        help="Set command conflict policy: error or skip.",
    ),
    enable_folder_loader: bool | None = typer.Option(
        None,
        "--folder-loader/--no-folder-loader",
        help="Enable or disable folder-based plugin discovery.",
    ),
    set_plugin_dir: list[str] = typer.Option(
        [],
        "--set-plugin-dir",
        help="Replace plugin directory list. Repeat option for multiple values.",
    ),
    add_plugin_dir: list[str] = typer.Option(
        [],
        "--add-plugin-dir",
        help="Add one plugin directory. Repeat option for multiple values.",
    ),
    remove_plugin_dir: list[str] = typer.Option(
        [],
        "--remove-plugin-dir",
        help="Remove one plugin directory. Repeat option for multiple values.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview changes without writing the config file.",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Apply changes without confirmation prompt.",
    ),
) -> None:
    """Update plugin-related configuration with preview and validation."""
    current = load_settings()
    proposed = Settings(
        entrypoint_group=current.entrypoint_group,
        conflict_policy=current.conflict_policy,
        enable_folder_loader=current.enable_folder_loader,
        plugin_dirs=list(current.plugin_dirs),
        disabled_plugins=list(current.disabled_plugins),
    )

    has_direct_options = any(
        [
            entrypoint_group is not None,
            conflict_policy is not None,
            enable_folder_loader is not None,
            bool(set_plugin_dir),
            bool(add_plugin_dir),
            bool(remove_plugin_dir),
        ]
    )

    if not has_direct_options:
        _print_current_settings(current)
        typer.echo("No option provided. Starting interactive setup.")

        entrypoint_group = typer.prompt(
            "Entry point group",
            default=current.entrypoint_group,
        )
        conflict_policy = typer.prompt(
            "Conflict policy (error/skip)",
            default=current.conflict_policy,
        )
        enable_folder_loader = typer.confirm(
            "Enable folder loader",
            default=current.enable_folder_loader,
        )
        plugin_dirs_text = typer.prompt(
            "Plugin directories (comma-separated)",
            default=", ".join(current.plugin_dirs),
        )
        set_plugin_dir = [item.strip() for item in plugin_dirs_text.split(",") if item.strip()]

    if entrypoint_group is not None:
        cleaned_group = entrypoint_group.strip()
        if not cleaned_group:
            raise typer.BadParameter("entrypoint_group cannot be empty")
        proposed.entrypoint_group = cleaned_group

    if conflict_policy is not None:
        cleaned_policy = conflict_policy.strip().lower()
        if cleaned_policy not in VALID_CONFLICT_POLICIES:
            allowed = ", ".join(sorted(VALID_CONFLICT_POLICIES))
            raise typer.BadParameter(f"conflict_policy must be one of: {allowed}")
        proposed.conflict_policy = cleaned_policy

    if enable_folder_loader is not None:
        proposed.enable_folder_loader = enable_folder_loader

    if set_plugin_dir:
        proposed.plugin_dirs = _normalize_plugin_dirs(set_plugin_dir)

    if add_plugin_dir:
        for directory in _normalize_plugin_dirs(add_plugin_dir):
            if directory not in proposed.plugin_dirs:
                proposed.plugin_dirs.append(directory)

    if remove_plugin_dir:
        removed = set(_normalize_plugin_dirs(remove_plugin_dir))
        proposed.plugin_dirs = [directory for directory in proposed.plugin_dirs if directory not in removed]

    if not proposed.plugin_dirs:
        raise typer.BadParameter("plugin_dirs cannot be empty")

    changes = _settings_changes(current, proposed)
    if not changes:
        typer.echo("No config changes detected.")
        return

    _print_changes(changes)

    if dry_run:
        typer.echo(f"Dry-run mode. No file written. Config path: {get_config_path()}")
        return

    if not yes and not typer.confirm("Apply these changes?", default=True):
        typer.echo("Update canceled.")
        return

    save_settings(proposed)
    typer.echo(f"Config updated: {get_config_path()}")
    _print_current_settings(proposed)


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
