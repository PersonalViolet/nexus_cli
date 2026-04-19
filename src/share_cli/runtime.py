"""Shared runtime state used by internal commands."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class LoadedPluginRecord:
    """Runtime details for one loaded plugin."""

    plugin_id: str
    source: str
    command_path: str
    version: str
    help_text: str


@dataclass(slots=True)
class RuntimeState:
    """Mutable process-scoped runtime state."""

    loaded_plugins: dict[str, LoadedPluginRecord] = field(default_factory=dict)
    failed_plugins: dict[str, str] = field(default_factory=dict)
    skipped_plugins: dict[str, str] = field(default_factory=dict)
    disabled_plugins: set[str] = field(default_factory=set)
    settings_snapshot: dict[str, Any] = field(default_factory=dict)


_STATE = RuntimeState()


def get_runtime_state() -> RuntimeState:
    """Get the singleton runtime state."""
    return _STATE


def reset_runtime_state() -> RuntimeState:
    """Reset runtime state at each CLI startup."""
    _STATE.loaded_plugins.clear()
    _STATE.failed_plugins.clear()
    _STATE.skipped_plugins.clear()
    _STATE.disabled_plugins.clear()
    _STATE.settings_snapshot.clear()
    return _STATE
