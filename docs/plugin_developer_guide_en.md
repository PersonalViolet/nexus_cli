# nexuscli Plugin Development and Release Guide

This guide targets two roles:

- Plugin developers: extend new commands and publish plugin packages independently
- Core maintainers: release the nexuscli core package

For a hands-on workflow first, read:

- [docs/plugin_dev_publish_quickstart.md](docs/plugin_dev_publish_quickstart.md)

## 1. Design Goals

The plugin architecture of nexuscli focuses on:

- Loose coupling: plugins are independent Python packages
- Governance: standard integration via Python Entry Points
- Isolation: one broken plugin must not crash the entire CLI
- Hot-plug behavior: plugin changes take effect on the next CLI invocation

## 2. Plugin Contract

A plugin must implement `CliPluginBase` and provide `CommandMetadata` and `typer_app`.

Contract source:

- `src/nexuscli/core/plugin_contract.py`

### 2.1 Required Metadata Fields

| Field | Type | Description |
| --- | --- | --- |
| `plugin_id` | `str` | Globally unique plugin identifier |
| `command_name` | `str` | Command name mounted into CLI |
| `command_group` | `str \| None` | Optional group; root-level when omitted |
| `help_text` | `str` | Help message |
| `version` | `str` | Plugin version |
| `min_cli_version` | `str` | Compatible CLI version specifier (PEP 440) |
| `dependencies` | `tuple[str, ...]` | Runtime dependency specifiers (PEP 508) |

### 2.2 Lifecycle Hooks

- `on_load(context)`: called after successful registration
- `on_error(error)`: called when plugin activation fails

Hooks should be idempotent and should not raise unhandled exceptions.

### 2.3 Naming Recommendations

- `plugin_id` format: `<team>.<domain>-<name>`
- Example: `acme.file-rename-plus`
- `command_name`: kebab-case, for example `batch-report`
- `command_group`: business domain, for example `file`, `calc`, `ops`

## 3. Loading, Validation, and Conflict Policy

Main orchestration:

- `src/nexuscli/plugins/manager.py`

### 3.1 Load Order

1. Built-in plugins
2. Entry Points plugins (default)
3. Local folder plugins (only when `enable_folder_loader=true`)

### 3.2 Compatibility Validation

Before activation, nexuscli validates:

- `plugin_id` is not empty and not duplicated
- `command_name` is not empty
- `min_cli_version` is parseable by `packaging.specifiers.SpecifierSet`
- current CLI version satisfies `min_cli_version`
- every dependency in `dependencies` is installed and version-compatible

### 3.3 Command Conflict Policy

Conflict detection:

- `src/nexuscli/plugins/registry.py`

Policy is controlled by `conflict_policy`:

- `error` (default): conflict raises an error and plugin is marked as failed
- `skip`: conflicting plugin is skipped and CLI continues

### 3.4 Hot-Plug Semantics

nexuscli is a short-lived process. Hot-plug means:

- install/upgrade/remove plugin, then run `nexuscli` again to take effect
- no in-process safe hot-reload support

## 4. Configuration Contract

Configuration is resolved from user-level JSON plus environment variables:

- `src/nexuscli/config.py`

Key fields:

- `entrypoint_group`: default `nexuscli.command`
- `conflict_policy`: `error` or `skip`
- `enable_folder_loader`: enable local folder discovery
- `plugin_dirs`: folder loader search paths
- `disabled_plugins`: disabled plugin IDs

Environment variables:

- `NEXUSCLI_ENTRYPOINT_GROUP`
- `NEXUSCLI_CONFLICT_POLICY`
- `NEXUSCLI_ENABLE_FOLDER_LOADER`
- `NEXUSCLI_PLUGIN_DIRS`
- `NEXUSCLI_DISABLED_PLUGINS`

## 5. Minimal Plugin Example

### 5.1 Layout

```text
acme-nexuscli-hello/
  pyproject.toml
  src/
    acme_nexuscli_hello/
      __init__.py
      plugin.py
```

### 5.2 Plugin Code

```python
from __future__ import annotations

import typer
from nexuscli.core.plugin_contract import CliPluginBase, CommandMetadata

hello_app = typer.Typer(help="Hello commands")


@hello_app.command("say")
def say(name: str) -> None:
    typer.echo(f"hello, {name}")


class HelloPlugin(CliPluginBase):
    @property
    def metadata(self) -> CommandMetadata:
        return CommandMetadata(
            plugin_id="acme.hello",
            command_name="hello",
            command_group=None,
            help_text="Hello demo plugin",
            version="0.1.0",
            min_cli_version=">=0.1.0",
            dependencies=("typer>=0.12,<1",),
        )

    @property
    def typer_app(self) -> typer.Typer:
        return hello_app
```

### 5.3 Entry Points Declaration

```toml
[project]
name = "acme-nexuscli-hello"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["nexuscli>=0.1.0", "typer>=0.12,<1"]

[project.entry-points."nexuscli.command"]
acme-hello = "acme_nexuscli_hello.plugin:HelloPlugin"
```

The loader currently accepts entry point targets as:

- `CliPluginBase` subclass (recommended)
- `CliPluginBase` instance
- callable object returning a `CliPluginBase` instance

## 6. Local Development Workflow

Windows PowerShell example:

```powershell
# 1) install core dev dependencies in nexuscli root
D:/Develop/Python/3.10.6/python.exe -m pip install -e .[dev]

# 2) install your plugin project
D:/Develop/Python/3.10.6/python.exe -m pip install -e .

# 3) run CLI
$env:PYTHONPATH = "src"
D:/Develop/Python/3.10.6/python.exe -m nexuscli.main --help
D:/Develop/Python/3.10.6/python.exe -m nexuscli.main plugin list
```

## 7. Plugin Release Workflow (3rd Party)

### 7.1 Pre-release Checklist

1. Bump plugin version (semantic versioning)
2. Verify `min_cli_version` and `dependencies`
3. Run tests and static checks
4. Validate visibility with `nexuscli plugin list`

### 7.2 Build and Validate

```powershell
D:/Develop/Python/3.10.6/python.exe -m pip install build twine
D:/Develop/Python/3.10.6/python.exe -m build
D:/Develop/Python/3.10.6/python.exe -m twine check dist/*
```

### 7.3 Publish

```powershell
# Public PyPI
D:/Develop/Python/3.10.6/python.exe -m twine upload dist/*

# Private index example
# D:/Develop/Python/3.10.6/python.exe -m twine upload --repository-url <internal-url> dist/*
```

### 7.4 Post-release Validation

1. Install `nexuscli` + plugin in a clean environment
2. Run `nexuscli --help` and verify command visibility
3. Run plugin command smoke tests
4. Record compatibility matrix (plugin version -> supported CLI versions)

## 8. Core CLI Release Workflow (Maintainers)

1. Update versions in `src/nexuscli/__init__.py` and `pyproject.toml`
2. Run tests:

```powershell
$env:PYTHONPATH = "src"
D:/Develop/Python/3.10.6/python.exe -m pytest -q
```

3. Build and check artifacts:

```powershell
D:/Develop/Python/3.10.6/python.exe -m build
D:/Develop/Python/3.10.6/python.exe -m twine check dist/*
```

4. Run release regression:

- built-in commands: `plugin`, `file`
- conflict policy behavior: `error` and `skip`
- disable/enable workflow: `plugin disable`, `plugin enable`

## 9. Troubleshooting

### 9.1 Plugin Not Visible

1. Check entry point group is `nexuscli.command`
2. Confirm plugin is installed in the active Python environment
3. Inspect `nexuscli plugin list --failed --skipped`
4. Check disabled state via `plugin inspect <plugin_id>`

### 9.2 Dependency Errors

- Look for `Missing dependency` or `Dependency mismatch`
- Fix plugin `dependencies` and reinstall

### 9.3 Command Conflicts

- Change `command_name` or `command_group`
- Or temporarily switch `conflict_policy` to `skip`

## 10. Team Collaboration Recommendations

- Keep each plugin in an independent repository
- Require in PR:
  - metadata completeness check
  - at least one executable command test
  - compatibility/version change notes
- Maintain changelog with breaking-change flags
