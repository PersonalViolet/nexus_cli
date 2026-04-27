"""Discover plugins from local filesystem paths."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import inspect
from pathlib import Path
from types import ModuleType
from typing import Any

from share_cli.core.plugin_contract import CliPluginBase


class FolderLoader:
    """Load plugins from python modules under configured directories."""

    def __init__(self, plugin_dirs: list[str]) -> None:
        self._plugin_dirs :list[Path] = [Path(p).expanduser() for p in plugin_dirs]

    def load(self) -> tuple[list[tuple[CliPluginBase, str]], dict[str, str]]:
        """Return loaded plugins and loader errors."""
        loaded: list[tuple[CliPluginBase, str]] = []
        errors: dict[str, str] = {}

        for directory in self._plugin_dirs:
            if not directory.exists() or not directory.is_dir():
                continue

            for file_path in sorted(directory.rglob("*.py")):
                if file_path.name.startswith("_"):
                    continue

                source_prefix = f"folder:{file_path}"
                try:
                    module = self._load_module(file_path)
                except Exception as exc:
                    errors[source_prefix] = str(exc)
                    continue

                module_plugins, module_errors = self._extract_plugins(module, source_prefix)
                loaded.extend(module_plugins)
                errors.update(module_errors)

        return loaded, errors

    @staticmethod
    def _load_module(file_path: Path) -> ModuleType:
        module_name = f"share_cli_local_plugin_{file_path.stem}_{abs(hash(file_path))}"
        spec = spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot create import spec for {file_path}")

        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    @staticmethod
    def _extract_plugins(
        module: ModuleType,
        source_prefix: str,
    ) -> tuple[list[tuple[CliPluginBase, str]], dict[str, str]]:
        loaded: list[tuple[CliPluginBase, str]] = []
        errors: dict[str, str] = {}

        for attr_name, attr in vars(module).items():
            if attr_name.startswith("_"):
                continue

            source = f"{source_prefix}:{attr_name}"
            try:
                plugin = FolderLoader._coerce_to_plugin(attr)
            except TypeError:
                continue
            except Exception as exc:
                errors[source] = str(exc)
                continue

            loaded.append((plugin, source))

        return loaded, errors

    @staticmethod
    def _coerce_to_plugin(attr: Any) -> CliPluginBase:
        if isinstance(attr, CliPluginBase):
            return attr

        if inspect.isclass(attr) and issubclass(attr, CliPluginBase):
            return attr()

        raise TypeError("Not a plugin")
