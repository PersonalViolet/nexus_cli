# NexusOpenCLI

[English](README.md) | [中文](docs/README.zh-CN.md)

Extensible Typer CLI with hot-pluggable commands. NexusOpenCLI loads built-in and third-party plugins on every invocation so you can add new commands by installing packages.

## Features

- Plugin-based command system with runtime discovery
- Built-in commands for plugin management and batch file renaming
- Configurable plugin sources (entry points and optional folder loader)
- Per-plugin and global language settings

## Installation

For end users, install inside a virtual environment:

```bash
pip install nexus-open-cli
```

## Quick Start

```bash
ncli --help
ncli plugin list

# Batch rename preview (dry-run is default)
ncli file rename ./my-folder --pattern "\s+" --replacement "_"

# Apply the rename plan
ncli file rename ./my-folder --pattern "\s+" --replacement "_" --apply
```

## Installing Plugins

After installing NexusCLI, add plugins via pip:

```bash
# Install a local plugin folder
pip install /path/to/your-plugin

# Install a plugin published on PyPI
pip install your-plugin-package
```

Plugins should register into the `nexuscli.command` entry point group so NexusCLI can discover them on startup. After installing the plugin, type `ncli` again to verify that the plugin was installed successfully.

## Configuration

Inspect or update plugin settings:

```bash
ncli plugin config
ncli plugin config-path
```

Manage plugin directories via interactive prompt or the `--set-plugin-dir`, `--add-plugin-dir`, `--remove-plugin-dir` options.

Note:

`ncli plugin config --folder-loader` is ineffective for enabling directory loading; this command is deprecated soon. Ignore it.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Developing Plugins

You can use the `skill/ncli-plugi-dev-helper/SKILL.md` skill provided in this repository to quickly develop third-party plugins from scratch (even with zero prior knowledge).

## License

MIT
