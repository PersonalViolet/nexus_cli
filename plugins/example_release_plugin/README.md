# share-cli example release plugin

This package demonstrates how to develop and publish an external plugin for share-cli.

## Features

- Provides `hello greet` command.
- Implements share-cli plugin contract (`CliPluginBase`).
- Registers through entry point group `share_cli.command`.

## Local development

1. Install the core project in editable mode.
2. Install this plugin in editable mode.
3. Run `share-cli plugin list` and confirm `example.release-hello` is loaded.

PowerShell example:

```powershell
cd D:/My-Project/share-cli
D:/Develop/Python/3.10.6/python.exe -m pip install -e .
D:/Develop/Python/3.10.6/python.exe -m pip install -e ./plugins/example_release_plugin
$env:PYTHONPATH = "src"
D:/Develop/Python/3.10.6/python.exe -m share_cli.main plugin list
D:/Develop/Python/3.10.6/python.exe -m share_cli.main hello greet Copilot --style formal
```

## Build and publish

```powershell
cd D:/My-Project/share-cli/plugins/example_release_plugin
D:/Develop/Python/3.10.6/python.exe -m pip install build twine
D:/Develop/Python/3.10.6/python.exe -m build
D:/Develop/Python/3.10.6/python.exe -m twine check dist/*
# D:/Develop/Python/3.10.6/python.exe -m twine upload dist/*
```
