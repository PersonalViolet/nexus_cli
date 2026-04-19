"""Custom errors for plugin lifecycle."""

from __future__ import annotations


class PluginError(Exception):
    """Base plugin error."""


class PluginLoadError(PluginError):
    """Plugin failed to load from source."""


class PluginCompatibilityError(PluginError):
    """Plugin metadata/version is incompatible."""


class PluginDependencyError(PluginError):
    """Plugin dependency is missing or incompatible."""


class PluginConflictError(PluginError):
    """Plugin command conflicts with an existing command."""
