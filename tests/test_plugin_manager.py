from __future__ import annotations

from share_cli.app import create_app
from share_cli.config import Settings
from share_cli.plugins.manager import PluginManager
from share_cli.runtime import get_runtime_state


def test_builtin_plugins_are_loaded() -> None:
    app = create_app()
    settings = Settings(entrypoint_group="share_cli.nonexistent", enable_folder_loader=False)

    manager = PluginManager(app=app, settings=settings)
    manager.load_plugins()

    state = get_runtime_state()
    assert "builtin.plugin-admin" in state.loaded_plugins
    assert "builtin.file" in state.loaded_plugins
