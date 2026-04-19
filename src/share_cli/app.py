"""Typer application factory."""

from __future__ import annotations

import typer


def create_app() -> typer.Typer:
    """Create the root Typer application."""
    return typer.Typer(
        name="share-cli",
        help="Extensible CLI with pluggable command modules.",
        no_args_is_help=True,
        add_completion=False,
    )
