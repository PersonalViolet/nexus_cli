"""Runtime configuration loading and persistence."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir


APP_NAME = "share-cli"
DEFAULT_ENTRYPOINT_GROUP = "share_cli.command"
DEFAULT_CONFIG_FILE = "config.json"


@dataclass(slots=True)
class Settings:
    """Application settings resolved from file and environment."""

    entrypoint_group: str = DEFAULT_ENTRYPOINT_GROUP
    conflict_policy: str = "error"
    enable_folder_loader: bool = False
    plugin_dirs: list[str] = field(
        default_factory=lambda: [str(Path.home() / ".share-cli" / "plugins")]
    )
    disabled_plugins: list[str] = field(default_factory=list)


def get_config_path() -> Path:
    """Return the user-level config file path."""
    cfg_dir = Path(user_config_dir(APP_NAME, APP_NAME))
    return cfg_dir / DEFAULT_CONFIG_FILE


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return raw if isinstance(raw, dict) else {}


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_settings() -> Settings:
    """Load settings from config file first, then apply env overrides."""
    data = _read_json(get_config_path())

    settings = Settings(
        entrypoint_group=str(data.get("entrypoint_group", DEFAULT_ENTRYPOINT_GROUP)),
        conflict_policy=str(data.get("conflict_policy", "error")),
        enable_folder_loader=bool(data.get("enable_folder_loader", False)),
        plugin_dirs=list(data.get("plugin_dirs", [str(Path.home() / ".share-cli" / "plugins")])),
        disabled_plugins=list(data.get("disabled_plugins", [])),
    )

    env_group = os.getenv("SHARE_CLI_ENTRYPOINT_GROUP")
    env_policy = os.getenv("SHARE_CLI_CONFLICT_POLICY")
    env_folder_loader = os.getenv("SHARE_CLI_ENABLE_FOLDER_LOADER")
    env_plugin_dirs = os.getenv("SHARE_CLI_PLUGIN_DIRS")
    env_disabled = os.getenv("SHARE_CLI_DISABLED_PLUGINS")

    if env_group:
        settings.entrypoint_group = env_group
    if env_policy:
        settings.conflict_policy = env_policy
    settings.enable_folder_loader = _as_bool(env_folder_loader, settings.enable_folder_loader)
    if env_plugin_dirs:
        settings.plugin_dirs = [p for p in env_plugin_dirs.split(os.pathsep) if p]
    if env_disabled:
        settings.disabled_plugins = [p.strip() for p in env_disabled.split(",") if p.strip()]

    return settings


def save_settings(settings: Settings) -> None:
    """Persist settings to user config path."""
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "entrypoint_group": settings.entrypoint_group,
        "conflict_policy": settings.conflict_policy,
        "enable_folder_loader": settings.enable_folder_loader,
        "plugin_dirs": settings.plugin_dirs,
        "disabled_plugins": settings.disabled_plugins,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def set_plugin_disabled(plugin_id: str, disabled: bool) -> bool:
    """Enable or disable a plugin id in persisted settings.

    Returns True when the state changed.
    """
    settings = load_settings()
    current = set(settings.disabled_plugins)

    if disabled:
        before = len(current)
        current.add(plugin_id)
        changed = len(current) != before
    else:
        changed = plugin_id in current
        current.discard(plugin_id)

    settings.disabled_plugins = sorted(current)
    if changed:
        save_settings(settings)

    return changed
