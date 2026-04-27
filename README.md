# share-cli

A Typer-based extensible CLI with a plugin architecture.

## Developer Docs

- Beginner learning guide (ZH): [docs/面向初次接触者的该项目学习指南.md](docs/面向初次接触者的该项目学习指南.md)
- Plugin dev and publish quickstart (ZH): [docs/plugin_dev_publish_quickstart.md](docs/plugin_dev_publish_quickstart.md)
- Plugin contract and release workflow (ZH): [docs/plugin_developer_guide.md](docs/plugin_developer_guide.md)
- Plugin contract and release workflow (EN): [docs/plugin_developer_guide_en.md](docs/plugin_developer_guide_en.md)

## Example External Plugin

- Example package path: [plugins/example_release_plugin](plugins/example_release_plugin)

## Quick Start

```powershell
D:/Develop/Python/3.10.6/python.exe -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
D:/Develop/Python/3.10.6/python.exe -m share_cli.main --help
```
