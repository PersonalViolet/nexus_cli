"""CLI process entry point."""

from __future__ import annotations

from nexuscli.app import create_app
from nexuscli.config import load_settings
from nexuscli.plugins.manager import PluginManager


def cli() -> None:
    """Start CLI and dynamically load plugins on each invocation."""
    app = create_app()
    settings = load_settings()

    manager = PluginManager(app=app, settings=settings)
    manager.load_plugins()

    app()


if __name__ == "__main__":
    cli()
