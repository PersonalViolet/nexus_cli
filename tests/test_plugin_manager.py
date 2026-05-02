from __future__ import annotations

import typer

from nexuscli.app import create_app
from nexuscli.core.plugin_contract import CliPluginBase, CommandMetadata
from nexuscli.config import Settings
from nexuscli.plugins.manager import PluginManager
from nexuscli.runtime import get_runtime_state, reset_runtime_state


class _DummyLanguagePlugin(CliPluginBase):
    def __init__(self, plugin_id: str) -> None:
        self._plugin_id = plugin_id
        self.context: dict[str, str | None] | None = None
        self._app = typer.Typer()

        @self._app.command("ping")
        def ping() -> None:
            return None

    @property
    def metadata(self) -> CommandMetadata:
        return CommandMetadata(
            plugin_id=self._plugin_id,
            command_name=f"cmd-{self._plugin_id.replace('.', '-')}",
            help_text="dummy",
        )

    @property
    def typer_app(self) -> typer.Typer:
        return self._app

    def on_load(self, context: dict[str, str | None]) -> None:
        self.context = context


def test_builtin_plugins_are_loaded() -> None:
    app = create_app()
    settings = Settings(entrypoint_group="nexuscli.nonexistent", enable_folder_loader=False)

    manager = PluginManager(app=app, settings=settings)
    manager.load_plugins()

    state = get_runtime_state()
    assert "builtin.plugin-admin" in state.loaded_plugins
    assert "builtin.file" in state.loaded_plugins


def test_plugin_language_context_prefers_plugin_override() -> None:
    app = create_app()
    settings = Settings(
        entrypoint_group="nexuscli.nonexistent",
        enable_folder_loader=False,
        language="zh",
        plugin_languages={"dummy.lang": "ja"},
    )

    manager = PluginManager(app=app, settings=settings)
    state = reset_runtime_state()
    state.disabled_plugins = set()
    plugin = _DummyLanguagePlugin(plugin_id="dummy.lang")

    manager._activate(plugin=plugin, source="test", state=state)  # type: ignore[attr-defined]

    assert plugin.context is not None
    assert plugin.context["language"] == "ja"
    assert plugin.context["global_language"] == "zh"
    assert plugin.context["plugin_language"] == "ja"


def test_plugin_language_context_falls_back_to_global() -> None:
    app = create_app()
    settings = Settings(
        entrypoint_group="nexuscli.nonexistent",
        enable_folder_loader=False,
        language="zh",
        plugin_languages={"another.plugin": "ja"},
    )

    manager = PluginManager(app=app, settings=settings)
    state = reset_runtime_state()
    state.disabled_plugins = set()
    plugin = _DummyLanguagePlugin(plugin_id="dummy.global")

    manager._activate(plugin=plugin, source="test", state=state)  # type: ignore[attr-defined]

    assert plugin.context is not None
    assert plugin.context["language"] == "zh"
    assert plugin.context["global_language"] == "zh"
    assert plugin.context["plugin_language"] is None
