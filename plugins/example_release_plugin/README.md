# nexuscli example release plugin

This package demonstrates how to develop and publish an external plugin for nexuscli.

## Features

- Provides `hello greet` command.
- Implements nexuscli plugin contract (`CliPluginBase`).
- Registers through entry point group `nexuscli.command`.

## Local development

1. Install the core project in editable mode.
2. Install this plugin in editable mode.
3. Run `nexuscli plugin list` and confirm `example.release-hello` is loaded.

PowerShell example:

```powershell
cd D:/My-Project/nexuscli
D:/Develop/Python/3.10.6/python.exe -m pip install -e .
D:/Develop/Python/3.10.6/python.exe -m pip install -e ./plugins/example_release_plugin
$env:PYTHONPATH = "src"
D:/Develop/Python/3.10.6/python.exe -m nexuscli.main plugin list
D:/Develop/Python/3.10.6/python.exe -m nexuscli.main hello greet Copilot --style formal
```

## Build and publish

```powershell
cd D:/My-Project/nexuscli/plugins/example_release_plugin
D:/Develop/Python/3.10.6/python.exe -m pip install build twine
D:/Develop/Python/3.10.6/python.exe -m build
D:/Develop/Python/3.10.6/python.exe -m twine check dist/*
# D:/Develop/Python/3.10.6/python.exe -m twine upload dist/*
```
