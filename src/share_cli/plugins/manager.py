"""Plugin manager orchestrating discovery, validation and registration."""

from __future__ import annotations

from importlib import metadata
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
import typer

from share_cli import __version__
from share_cli.config import Settings
from share_cli.core.errors import (
    PluginCompatibilityError,
    PluginDependencyError,
    PluginLoadError,
)
from share_cli.core.plugin_contract import CliPluginBase
from share_cli.loaders.entrypoints_loader import EntrypointLoader
from share_cli.loaders.folder_loader import FolderLoader
from share_cli.plugins.builtins import get_builtin_plugins
from share_cli.plugins.registry import PluginRegistry
from share_cli.runtime import LoadedPluginRecord, reset_runtime_state


class PluginManager:
    """Manage plugin lifecycle for each CLI process run."""

    def __init__(self, app: typer.Typer, settings: Settings) -> None:
        self._app = app
        self._settings = settings
        self._registry = PluginRegistry(app=app, conflict_policy=settings.conflict_policy)
        self._seen_plugin_ids: set[str] = set()

    def load_plugins(self) -> None:
        """Load built-in and external plugins with isolation."""
        state = reset_runtime_state()
        state.disabled_plugins = set(self._settings.disabled_plugins)
        state.settings_snapshot = {
            "entrypoint_group": self._settings.entrypoint_group,
            "conflict_policy": self._settings.conflict_policy,
            "enable_folder_loader": self._settings.enable_folder_loader,
            "plugin_dirs": list(self._settings.plugin_dirs),
            "language": self._settings.language,
            "plugin_languages": dict(self._settings.plugin_languages),
        }

        self._load_builtin(state)
        self._load_entrypoints(state)

        if self._settings.enable_folder_loader and 1 == 0:  # Disabled for now - folder plugins are not yet stable
            self._load_folder_plugins(state)

    def _load_builtin(self, state) -> None:
        for plugin in get_builtin_plugins():
            plugin_language = self._settings.plugin_languages.get(plugin.metadata.plugin_id)
            effective_language = plugin_language or self._settings.language
            plugin.on_configure(
                {
                    "language": effective_language,
                    "global_language": self._settings.language,
                    "plugin_language": plugin_language,
                }
            )
            plugin.build_app()
            self._activate(plugin=plugin, source="builtin", state=state)

    def _load_entrypoints(self, state) -> None:
        loader = EntrypointLoader(group_name=self._settings.entrypoint_group)
        plugins, errors = loader.load()

        for source, message in errors.items():
            state.failed_plugins[source] = message

        for plugin, source in plugins:
            plugin_language = self._settings.plugin_languages.get(plugin.metadata.plugin_id)
            effective_language = plugin_language or self._settings.language
            plugin.on_configure(
                {
                    "language": effective_language,
                    "global_language": self._settings.language,
                    "plugin_language": plugin_language,
                }
            )
            plugin.build_app()
            self._activate(plugin=plugin, source=source, state=state)

    def _load_folder_plugins(self, state) -> None:
        loader = FolderLoader(plugin_dirs=self._settings.plugin_dirs)
        plugins, errors = loader.load()

        for source, message in errors.items():
            state.failed_plugins[source] = message
        for plugin, source in plugins:
            self._activate(plugin=plugin, source=source, state=state)

    def _activate(self, 
                  plugin: CliPluginBase, # The plugin instance to be activated and registered.
                  source: str, # A string identifying the origin of the plugin (e.g., "builtin", "entrypoint:name", or folder path).
                  state # The current runtime state object used to track loaded, failed, or skipped plugins.
                  ) -> None:
        """
        Activate a single plugin by validating, registering, and recording its status.

        This method orchestrates the lifecycle of a plugin during startup:
        1. Checks if the plugin is explicitly disabled.
        2. Validates compatibility and dependencies.
        3. Registers the plugin's commands with the CLI registry.
        4. Notifies the plugin via on_load callback.
        5. Records the outcome (loaded, skipped, or failed) in the runtime state.

        Args:
            plugin: The plugin instance implementing CliPluginBase.
            source: Identifier for where the plugin was discovered (e.g., 'builtin', 'entrypoint:my-plugin').
            state: The mutable RuntimeState object to update with plugin status.
        """
        meta = plugin.metadata

        if meta.plugin_id in state.disabled_plugins:
            state.skipped_plugins[meta.plugin_id] = "disabled"
            return

        try:
            self._validate_plugin(plugin)

            ok, detail = self._registry.register(plugin=plugin, source=source)
            if not ok:
                state.skipped_plugins[meta.plugin_id] = detail
                return

            plugin_language = self._settings.plugin_languages.get(meta.plugin_id)
            effective_language = plugin_language or self._settings.language
            plugin.on_load(
                {
                    "source": source,
                    "command_path": detail,
                    "language": effective_language,
                    "global_language": self._settings.language,
                    "plugin_language": plugin_language,
                }
            )
            state.loaded_plugins[meta.plugin_id] = LoadedPluginRecord(
                plugin_id=meta.plugin_id,
                source=source,
                command_path=detail,
                version=meta.version,
                help_text=meta.help_text,
            )
        except Exception as exc:  # pragma: no cover - defensive isolation
            state.failed_plugins[meta.plugin_id] = str(exc)
            try:
                plugin.on_error(exc)
            except Exception:
                pass

    def _validate_plugin(self, plugin: CliPluginBase) -> None:
        meta = plugin.metadata

        if not meta.plugin_id:
            raise PluginCompatibilityError("plugin_id is required")
        if meta.plugin_id in self._seen_plugin_ids:
            raise PluginLoadError(f"Duplicate plugin_id: {meta.plugin_id}")
        if not meta.command_name:
            raise PluginCompatibilityError("command_name is required")

        try:
            spec = SpecifierSet(meta.min_cli_version)
        except Exception as exc:
            raise PluginCompatibilityError(
                f"Invalid min_cli_version: {meta.min_cli_version}"
            ) from exc

        if not spec.contains(__version__, prereleases=True):
            raise PluginCompatibilityError(
                f"Requires CLI {meta.min_cli_version}, current is {__version__}"
            )

        for dep_spec in meta.dependencies:
            req = Requirement(dep_spec)
            try:
                installed = metadata.version(req.name)
            except metadata.PackageNotFoundError as exc:
                raise PluginDependencyError(f"Missing dependency: {dep_spec}") from exc

            if req.specifier and not req.specifier.contains(installed, prereleases=True):
                raise PluginDependencyError(
                    f"Dependency mismatch for {req.name}: need {req.specifier}, got {installed}"
                )

        self._seen_plugin_ids.add(meta.plugin_id)
