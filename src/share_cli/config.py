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
DEFAULT_LANGUAGE = "en"


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
    language: str = DEFAULT_LANGUAGE
    plugin_languages: dict[str, str] = field(default_factory=dict)


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


def _normalize_language_code(value: str | None) -> str | None:
    """Normalize language code to lowercase ISO-639-1 form."""
    if value is None:
        return None

    cleaned = value.strip().lower()
    if len(cleaned) == 2 and cleaned.isalpha():
        return cleaned
    return None


def _normalize_plugin_languages(raw: Any) -> dict[str, str]:
    """Normalize plugin language mapping from config file payload."""
    if not isinstance(raw, dict):
        return {}

    normalized: dict[str, str] = {}
    for plugin_id, language in raw.items():
        if not isinstance(plugin_id, str):
            continue
        plugin_key = plugin_id.strip()
        if not plugin_key:
            continue

        language_code = (
            _normalize_language_code(language)
            if isinstance(language, str)
            else None
        )
        if language_code is None:
            continue

        normalized[plugin_key] = language_code

    return normalized


def _parse_plugin_languages_env(value: str | None) -> dict[str, str] | None:
    """Parse plugin language overrides from env text.

    Format: plugin_id:lang,another.plugin:zh
    """
    if value is None:
        return None

    mapping: dict[str, str] = {}
    for item in value.split(","):
        pair = item.strip()
        if not pair or ":" not in pair:
            continue

        plugin_raw, language_raw = pair.split(":", 1)
        plugin_id = plugin_raw.strip()
        if not plugin_id:
            continue

        language_code = _normalize_language_code(language_raw)
        if language_code is None:
            continue

        mapping[plugin_id] = language_code

    return mapping


def load_settings() -> Settings:
    """Load settings from config file first, then apply env overrides."""
    data = _read_json(get_config_path())
    file_language = _normalize_language_code(str(data.get("language", DEFAULT_LANGUAGE)))
    if file_language is None:
        file_language = DEFAULT_LANGUAGE

    settings = Settings(
        entrypoint_group=str(data.get("entrypoint_group", DEFAULT_ENTRYPOINT_GROUP)),
        conflict_policy=str(data.get("conflict_policy", "error")),
        enable_folder_loader=bool(data.get("enable_folder_loader", False)),
        plugin_dirs=list(data.get("plugin_dirs", [str(Path.home() / ".share-cli" / "plugins")])),
        disabled_plugins=list(data.get("disabled_plugins", [])),
        language=file_language,
        plugin_languages=_normalize_plugin_languages(data.get("plugin_languages", {})),
    )

    env_group = os.getenv("SHARE_CLI_ENTRYPOINT_GROUP")
    env_policy = os.getenv("SHARE_CLI_CONFLICT_POLICY")
    env_folder_loader = os.getenv("SHARE_CLI_ENABLE_FOLDER_LOADER")
    env_plugin_dirs = os.getenv("SHARE_CLI_PLUGIN_DIRS")
    env_disabled = os.getenv("SHARE_CLI_DISABLED_PLUGINS")
    env_language = os.getenv("SHARE_CLI_LANGUAGE")
    env_plugin_languages = os.getenv("SHARE_CLI_PLUGIN_LANGUAGES")

    if env_group:
        settings.entrypoint_group = env_group
    if env_policy:
        settings.conflict_policy = env_policy
    settings.enable_folder_loader = _as_bool(env_folder_loader, settings.enable_folder_loader)
    if env_plugin_dirs:
        settings.plugin_dirs = [p for p in env_plugin_dirs.split(os.pathsep) if p]
    if env_disabled:
        settings.disabled_plugins = [p.strip() for p in env_disabled.split(",") if p.strip()]

    if env_language:
        env_language_code = _normalize_language_code(env_language)
        if env_language_code is not None:
            settings.language = env_language_code

    env_plugin_language_map = _parse_plugin_languages_env(env_plugin_languages)
    if env_plugin_language_map is not None:
        settings.plugin_languages = env_plugin_language_map

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
        "language": settings.language,
        "plugin_languages": settings.plugin_languages,
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
