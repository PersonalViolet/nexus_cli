"""Discover plugins from Python entry points."""

from __future__ import annotations

from importlib import metadata
import inspect
from typing import Any

from nexuscli.core.plugin_contract import CliPluginBase


class EntrypointLoader:
    """Load plugins from an entry point group."""

    def __init__(self, group_name: str) -> None:
        self._group_name = group_name

    def load(self) -> tuple[list[tuple[CliPluginBase, str]], dict[str, str]]:
        """Return loaded plugins and errors from entry points."""

        # List to store successfully loaded plugin instances and their source identifiers.
        # Each element is a tuple: (plugin_instance, source_string).
        loaded: list[tuple[CliPluginBase, str]] = []

        # Dictionary to record loading failures.
        # Key: Source identifier (e.g., "entrypoint:my-plugin"), Value: Error message string.
        errors: dict[str, str] = {}

        # Set to track processed entry points and prevent duplicate loading.
        # Each element is a tuple: (entry_point_name, entry_point_value).
        seen_targets: set[tuple[str, str]] = set()

        all_eps = metadata.entry_points()
        if hasattr(all_eps, "select"):
            candidates = list(all_eps.select(group=self._group_name))
        else:
            candidates = list(all_eps.get(self._group_name, []))

        for ep in candidates:
            target_key = (ep.name, ep.value)
            if target_key in seen_targets:
                continue
            seen_targets.add(target_key)

            source = f"entrypoint:{ep.name}"
            try:
                obj: Any = ep.load()
                plugin = self._coerce_to_plugin(obj)
                loaded.append((plugin, source))
            except Exception as exc:  # pragma: no cover - defensive
                errors[source] = str(exc)
        # Returns a tuple containing:
        # 1. A list of successfully loaded plugins with their sources.
        # 2. A dictionary of errors encountered during the loading process.
        return loaded, errors

    @staticmethod
    def _coerce_to_plugin(obj: Any) -> CliPluginBase:
        if isinstance(obj, CliPluginBase):
            return obj

        if inspect.isclass(obj) and issubclass(obj, CliPluginBase):
            return obj()

        if callable(obj):
            candidate = obj()
            if isinstance(candidate, CliPluginBase):
                return candidate

        raise TypeError("Entry point object must resolve to CliPluginBase")
