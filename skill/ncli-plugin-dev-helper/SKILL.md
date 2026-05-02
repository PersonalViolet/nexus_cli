---
name: ncli-plugin-dev-helper
description: 'Guide for third-party nexuscli plugins: entrypoint nexus-open-cli.command, lifecycle on_configure/build_app/on_load/on_error, Babel-based localization, and release-ready packaging. Use when creating or updating a plugin package.'
argument-hint: 'Provide plugin id, command name, and supported languages.'
---

# Nexus-Open-CLI Plugin Dev Helper

## When to Use
- Create a third-party plugin package for nexuscli.
- Implement the plugin lifecycle (on_configure, build_app, on_load/on_error).
- Add language selection with Babel translations.
- Package and publish with the nexuscli.command entrypoint.

## Inputs To Collect
- plugin_id (globally unique, reverse-domain style)
- command_name (root command name)
- command_group (optional group prefix)
- min_cli_version (version specifier)
- languages to support (for Babel locales)

## Procedure
1. Scaffold the package with a src layout and a plugin module.
2. Implement a plugin class that extends CliPluginBase.
3. In on_configure, load Babel translations based on the provided context language.
4. In build_app, build a Typer app and register commands.
5. Return the Typer app from build_app and expose it via the typer_app property.
6. Implement on_load for any post-registration behavior and on_error to capture failures.
7. Register the entrypoint group nexuscli.command in pyproject.toml.
8. Add locales under a locales/ directory and compile catalogs.

## Reference Structure
```
my_plugin/
  pyproject.toml
  src/
    my_plugin/
      __init__.py
      plugin.py
      locales/
        messages.pot
        zh/
          LC_MESSAGES/
            messages.po
            messages.mo
```

## Reference Code (Plugin)
```python
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import typer
from babel.core import Locale
from babel.support import Translations

from nexuscli.core.plugin_contract import CliPluginBase, CommandMetadata


class HelloPlugin(CliPluginBase):
    def __init__(self) -> None:
        self._: Callable[[str], str] = lambda message: message
        self._app: typer.Typer | None = None
        self.loaded_context: dict[str, Any] | None = None
        self.last_error: str | None = None

    @property
    def metadata(self) -> CommandMetadata:
        return CommandMetadata(
            plugin_id="example.vendor-hello",
            command_name="hello",
            command_group=None,
            help_text=self._("Hello commands from a plugin"),
            version="0.1.0",
            min_cli_version=">=0.1.0",
            dependencies=("typer>=0.12,<1.0",),
        )

    @property
    def typer_app(self) -> typer.Typer:
        return self._app

    def on_configure(self, context: dict[str, Any]) -> None:
        language = context.get("language", "en")
        locale = Locale.parse(language.replace("-", "_"))
        locales_dir = Path(__file__).resolve().parent / "locales"
        try:
            translations = Translations.load(
                str(locales_dir), locales=[str(locale)], domain="messages"
            )
        except OSError:
            return
        self._ = translations.gettext

    def build_app(self) -> typer.Typer:
        _ = self._
        self._app = typer.Typer(help=_("Example plugin commands."))

        @self._app.command("greet", help=_("Print a greeting message."))
        def greet(name: str = typer.Argument(..., help=_("Target name."))) -> None:
            typer.echo(_("Hello, {name}!").format(name=name))

        return self._app

    def on_load(self, context: dict[str, Any]) -> None:
        self.loaded_context = context

    def on_error(self, error: Exception) -> None:
        self.last_error = str(error)
```

## Reference Code (pyproject.toml)
```toml
[project]
name = "my-plugin"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["nexuscli", "typer>=0.12,<1.0", "babel"]

[project.entry-points."nexuscli.command"]
hello = "my_plugin.plugin:HelloPlugin"
```

## Notes
- The CLI passes language in the on_configure/on_load context. Prefer Babel and translations.gettext for localization.
- Keep the command metadata help_text localized by using self._().
- Avoid side effects in __init__. Use on_configure for environment-dependent setup.
