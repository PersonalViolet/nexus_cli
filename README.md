# NexusOpenCLI

![logo](docs/image/logo.png)

[English](README.md) | [中文](docs/README.zh-CN.md)

Extensible Typer CLI with hot-pluggable commands. NexusOpenCLI loads built-in and third-party plugins on every invocation so you can add new commands by installing packages.

## Development Motivation

In the process of daily development and using productivity tools, I have identified a long-standing issue:

> There are many CLI tools, but they are fragmented and difficult to manage in a unified way.

For example:

- Different tools need to be installed separately, and their commands must be memorized individually
- Functionalities are scattered, lacking a unified entry point
- When wanting to extend functionality, you often need to develop your own CLI from scratch

Therefore, I aim to build a CLI project that is:

> **Like an App Store for CLI tools**

The core goals are:

- Enable CLI tools to **be installed like plugins**
- Allow commands to **be auto-discovered at runtime**

Ultimately forming:

> An **extensible** CLI ecosystem infrastructure

## Features

- Plugin-based command system with runtime discovery
- Built-in commands for plugin management and batch file renaming
- Configurable plugin sources (entry points and optional folder loader)
- Per-plugin and global language settings

## Quick Start

It is recommended to install using `pip install nexus-open-cli` in a virtual environment in the specified directory, and then enter `ncli plugin list` to view the current command groups.

[quick start](https://github.com/user-attachments/assets/20eb3058-9bee-45c1-8ae7-7a70ea16bd15)

```bash
ncli --help
ncli plugin list
```

## Installing Plugins

It is recommended to download plugins via `ncli repo`.

All plugins are reviewed by the maintainers of `NexusOpenCLI`, allowing you to discover and install plugins just like using an App Store.

Take `ncli repo` as an example:

[ncli repo](https://github.com/user-attachments/assets/f49316a2-8fb5-4f7a-9c59-9bc99bf614a3)

You can also install plugins via `pip install nexus-open-cli-doctor` for a quick experience.

[show2](https://github.com/user-attachments/assets/be3a310e-2dc2-4a73-892f-a6c30dbef677)

For subsequent plugin installation, you can either use `ncli repo` (**recommended**), or install from a local directory or PyPI via pip:

```bash
# Install plugin via ncli repo
ncli repo install pluginName

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

## Run `ncli` Anywhere on Your PC Under Virtual Environment

### Windows

### Steps

1. Right-click **This PC** → **Properties** → **Advanced system settings** → **Environment Variables**

2. Find `Path` in the **System variables** list and double-click to open it

3. Click **New**, then add the folder path where `ncli.exe` is located:

   ```bash
   # Example
   D:\nexusOpenCLI\.venv\Scripts
   ```

## License

MIT
