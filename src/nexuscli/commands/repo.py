"""Plugin repository commands."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
import json
import subprocess
import sys
import urllib.error
import urllib.request

import typer
from babel.core import Locale
from babel.support import Translations
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from nexuscli.core.plugin_contract import CliPluginBase, CommandMetadata


console = Console()
REGISTRY_REPO = "PersonalViolet/NexusOpenCLI-plugins-registry"
REGISTRY_BRANCH = "main"
REGISTRY_PATH = "plugins.json"
REGISTRY_TIMEOUT_SECONDS = 10


def _registry_cache_path() -> Path:
    return Path.home() / ".nexuscli" / "plugins.json"


def _registry_url() -> str:
    return (
        "https://raw.githubusercontent.com/"
        f"{REGISTRY_REPO}/{REGISTRY_BRANCH}/{REGISTRY_PATH}"
    )


def _normalize_registry(payload: Any) -> dict[str, dict[str, str]]:
    if not isinstance(payload, dict):
        raise ValueError("Registry payload must be a JSON object.")

    normalized: dict[str, dict[str, str]] = {}
    for name, raw in payload.items():
        if not isinstance(name, str):
            continue
        plugin_name = name.strip()
        if not plugin_name or not isinstance(raw, dict):
            continue

        entry = {
            "package": str(raw.get("package") or "").strip(),
            "description": str(raw.get("description") or "").strip(),
            "version": str(raw.get("version") or "").strip(),
            "author": str(raw.get("author") or "").strip(),
        }
        normalized[plugin_name] = entry

    return normalized


def _load_registry_cache() -> tuple[dict[str, dict[str, str]] | None, str | None, Path]:
    path = _registry_cache_path()
    if not path.exists():
        return None, "missing", path

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, "invalid", path

    try:
        normalized = _normalize_registry(payload)
    except ValueError:
        return None, "invalid", path

    return normalized, None, path


def _save_registry_cache(data: dict[str, dict[str, str]]) -> Path:
    path = _registry_cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    return path


def _fetch_registry() -> dict[str, dict[str, str]]:
    url = _registry_url()
    try:
        with urllib.request.urlopen(url, timeout=REGISTRY_TIMEOUT_SECONDS) as response:
            raw = response.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive fallback
        raise RuntimeError(str(exc)) from exc

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Registry response is not valid JSON.") from exc

    try:
        return _normalize_registry(payload)
    except ValueError as exc:
        raise RuntimeError(str(exc)) from exc


class RepoCommandsPlugin(CliPluginBase):
    """Expose plugin registry commands as `ncli repo`."""

    def __init__(self) -> None:
        self._app: typer.Typer | None = None
        self._: Callable[[str], str] = lambda message: message

    @property
    def metadata(self) -> CommandMetadata:
        return CommandMetadata(
            plugin_id="builtin.repo",
            command_name="repo",
            help_text=self._("Plugin repository commands"),
            version="0.1.0",
            min_cli_version=">=0.1.0",
        )

    @property
    def typer_app(self) -> typer.Typer:
        return self._app

    def on_configure(self, context: dict[str, Any]) -> None:
        language = context.get("language", "en")
        language_tag = language.replace("-", "_")

        try:
            locale = Locale.parse(language_tag)
        except Exception:
            return

        locales_dir = Path(__file__).resolve().parents[1] / "locales"
        try:
            translations = Translations.load(
                str(locales_dir),
                locales=[str(locale)],
                domain="messages",
            )
        except OSError:
            return

        self._ = translations.gettext

    def build_app(self) -> typer.Typer:
        _ = self._
        self._app = typer.Typer(
            help=_("Manage plugin registry entries."),
            no_args_is_help=True,
        )

        @self._app.command(
            "list",
            help=_("List available plugins from the registry cache."),
        )
        def list_repo() -> None:
            entries, error, path = _load_registry_cache()
            if error == "missing":
                console.print(
                    Panel(
                        _("Registry cache not found. Run 'ncli repo update' first."),
                        style="yellow",
                    )
                )
                console.print(
                    _("Registry cache path: {path}").format(path=path)
                )
                raise typer.Exit(code=1)

            if error == "invalid":
                console.print(
                    Panel(
                        _("Registry cache is invalid. Run 'ncli repo update' to refresh."),
                        style="yellow",
                    )
                )
                console.print(
                    _("Registry cache path: {path}").format(path=path)
                )
                raise typer.Exit(code=1)

            if not entries:
                console.print(
                    Panel(
                        _("No plugins found in registry cache."),
                        style="yellow",
                    )
                )
                return

            console.print(_("Registry cache path: {path}").format(path=path))

            table = Table(title=_("Plugin Registry"))
            table.add_column(_("Name"))
            table.add_column(_("Description"))
            table.add_column(_("Version"))
            table.add_column(_("Author"))

            for name in sorted(entries):
                entry = entries[name]
                table.add_row(
                    name,
                    entry.get("description") or "-",
                    entry.get("version") or "-",
                    entry.get("author") or "-",
                )

            console.print(table)

        @self._app.command(
            "update",
            help=_("Update the local registry cache from GitHub."),
        )
        def update_registry() -> None:
            try:
                with console.status(_("Downloading registry...")):
                    entries = _fetch_registry()
            except RuntimeError as exc:
                console.print(
                    Panel(
                        _("Failed to download registry: {error}").format(error=exc),
                        style="red",
                    )
                )
                raise typer.Exit(code=1)

            path = _save_registry_cache(entries)
            console.print(
                Panel(
                    _("Registry updated at {path} ({count} plugins).").format(
                        path=path,
                        count=len(entries),
                    ),
                    style="green",
                )
            )

        @self._app.command(
            "install",
            help=_("Install a plugin by name from the registry cache."),
        )
        def install_repo_plugin(
            name: str = typer.Argument(
                ..., help=_("Plugin name from the registry."),
            )
        ) -> None:
            entries, error, path = _load_registry_cache()
            if error == "missing":
                console.print(
                    Panel(
                        _("Registry cache not found. Run 'ncli repo update' first."),
                        style="yellow",
                    )
                )
                console.print(
                    _("Registry cache path: {path}").format(path=path)
                )
                raise typer.Exit(code=1)

            if error == "invalid":
                console.print(
                    Panel(
                        _("Registry cache is invalid. Run 'ncli repo update' to refresh."),
                        style="yellow",
                    )
                )
                console.print(
                    _("Registry cache path: {path}").format(path=path)
                )
                raise typer.Exit(code=1)

            plugin_name = name.strip()
            entry = entries.get(plugin_name) if entries else None
            if entry is None:
                console.print(
                    Panel(
                        _("Plugin '{name}' not found in registry cache.").format(
                            name=plugin_name
                        ),
                        style="red",
                    )
                )
                raise typer.Exit(code=1)

            package = entry.get("package") or ""
            version = entry.get("version") or ""
            if not package or not version:
                console.print(
                    Panel(
                        _("Registry entry for '{name}' is missing package or version.")
                        .format(name=plugin_name),
                        style="red",
                    )
                )
                raise typer.Exit(code=1)

            package_spec = f"{package}=={version}"
            with console.status(
                _("Installing {package}...").format(package=package_spec)
            ):
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", package_spec],
                    capture_output=True,
                    text=True,
                )

            if result.returncode == 0:
                console.print(
                    Panel(
                        _("Installed {package}.").format(package=package_spec),
                        style="green",
                    )
                )
                return

            console.print(
                Panel(
                    _("Install failed with exit code {code}.").format(
                        code=result.returncode
                    ),
                    style="red",
                )
            )
            if result.stdout:
                console.print(result.stdout.rstrip())
            if result.stderr:
                console.print(result.stderr.rstrip(), style="red")
            raise typer.Exit(code=result.returncode)

        return self._app
