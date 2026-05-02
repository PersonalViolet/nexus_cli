# nexuscli 插件开发与发布指南

本指南面向两类开发者：

- 插件开发者：扩展新命令并独立发布插件
- 核心维护者：发布 nexuscli 主程序

快速上手实操请先看：

- [docs/plugin_dev_publish_quickstart.md](docs/plugin_dev_publish_quickstart.md)

## 1. 设计目标

nexuscli 的插件机制遵循以下目标：

- 低耦合：插件以独立 Python 包发布
- 可治理：通过 Entry Points 标准机制接入
- 可隔离：单个插件失败不影响其他命令
- 可热插拔：新增或升级插件在下一次 CLI 调用生效

## 2. 插件契约

插件必须实现 `CliPluginBase`，并提供 `CommandMetadata` 与 `typer_app`。

契约定义位于：

- `src/nexuscli/core/plugin_contract.py`

### 2.1 必填元数据字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `plugin_id` | `str` | 插件唯一 ID，全局不可重复 |
| `command_name` | `str` | 挂载到 CLI 的命令名 |
| `command_group` | `str \| None` | 可选命令组。为空时挂载在根级 |
| `help_text` | `str` | 帮助信息 |
| `version` | `str` | 插件版本号 |
| `min_cli_version` | `str` | 兼容的 CLI 版本约束（PEP 440） |
| `dependencies` | `tuple[str, ...]` | 运行时依赖约束（PEP 508） |

### 2.2 生命周期钩子

- `on_load(context)`：注册成功后回调
- `on_error(error)`：插件激活失败时回调

回调必须幂等，并避免抛出未处理异常。

### 2.3 命名约定（建议）

- `plugin_id` 推荐格式：`<team>.<domain>-<name>`
- 示例：`acme.file-rename-plus`
- `command_name` 使用短横线命名：`batch-report`
- `command_group` 使用业务域：`file`、`calc`、`ops`

## 3. 加载、校验与冲突策略

插件总加载链路在：

- `src/nexuscli/plugins/manager.py`

### 3.1 加载顺序

1. 内置插件
2. Entry Points 插件（默认）
3. 本地目录插件（仅在 `enable_folder_loader=true` 时启用）

### 3.2 兼容性校验

激活前会执行：

- `plugin_id` 非空且不重复
- `command_name` 非空
- `min_cli_version` 可被 `packaging.specifiers.SpecifierSet` 解析
- 当前 CLI 版本满足 `min_cli_version`
- `dependencies` 中每一项都已安装且版本满足约束

### 3.3 命令冲突策略

冲突检测在：

- `src/nexuscli/plugins/registry.py`

策略由 `conflict_policy` 控制：

- `error`（默认）：冲突直接报错，插件记为失败
- `skip`：跳过冲突插件，CLI 继续运行

### 3.4 热插拔语义

nexuscli 是短生命周期进程。插件“热插拔”语义为：

- 安装/升级/删除插件后，下一次执行 `nexuscli` 自动生效
- 不支持同一进程内安全热重载

## 4. 配置约定

配置由用户级 JSON 文件与环境变量共同决定，定义在：

- `src/nexuscli/config.py`

关键配置项：

- `entrypoint_group`：默认 `nexuscli.command`
- `conflict_policy`：`error` 或 `skip`
- `enable_folder_loader`：是否启用目录扫描
- `plugin_dirs`：目录扫描列表
- `disabled_plugins`：禁用插件 ID 列表

对应环境变量：

- `NEXUSCLI_ENTRYPOINT_GROUP`
- `NEXUSCLI_CONFLICT_POLICY`
- `NEXUSCLI_ENABLE_FOLDER_LOADER`
- `NEXUSCLI_PLUGIN_DIRS`
- `NEXUSCLI_DISABLED_PLUGINS`

## 5. 最小插件示例

### 5.1 目录结构

```text
acme-nexuscli-hello/
  pyproject.toml
  src/
    acme_nexuscli_hello/
      __init__.py
      plugin.py
```

### 5.2 插件代码

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

### 5.3 Entry Points 声明

```toml
[project]
name = "acme-nexuscli-hello"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["nexuscli>=0.1.0", "typer>=0.12,<1"]

[project.entry-points."nexuscli.command"]
acme-hello = "acme_nexuscli_hello.plugin:HelloPlugin"
```

说明：Entry Point 指向对象时，当前加载器支持三种返回形式：

- `CliPluginBase` 子类（推荐）
- `CliPluginBase` 实例
- 可调用对象，调用后返回 `CliPluginBase` 实例

## 6. 本地开发流程

在 Windows PowerShell 下，建议这样联调：

```powershell
# 1) 在 nexuscli 根目录安装开发依赖
D:/Develop/Python/3.10.6/python.exe -m pip install -e .[dev]

# 2) 在插件项目目录安装插件
D:/Develop/Python/3.10.6/python.exe -m pip install -e .

# 3) 运行主 CLI
$env:PYTHONPATH = "src"
D:/Develop/Python/3.10.6/python.exe -m nexuscli.main --help
D:/Develop/Python/3.10.6/python.exe -m nexuscli.main plugin list
```

## 7. 插件发布流程（第三方开发者）

### 7.1 发布前检查

1. 更新插件版本号（遵循语义化版本）
2. 校验 `min_cli_version` 与 `dependencies`
3. 本地运行测试与静态检查
4. 使用 `nexuscli plugin list` 验证插件可见

### 7.2 构建与校验

```powershell
D:/Develop/Python/3.10.6/python.exe -m pip install build twine
D:/Develop/Python/3.10.6/python.exe -m build
D:/Develop/Python/3.10.6/python.exe -m twine check dist/*
```

### 7.3 发布到包仓库

```powershell
# 公开 PyPI
D:/Develop/Python/3.10.6/python.exe -m twine upload dist/*

# 如果是内部源，替换为你的仓库 URL
# D:/Develop/Python/3.10.6/python.exe -m twine upload --repository-url <internal-url> dist/*
```

### 7.4 发布后验证

1. 在干净环境安装 `nexuscli` + 插件
2. 运行 `nexuscli --help` 检查命令是否出现
3. 运行插件命令做冒烟验证
4. 记录兼容矩阵（插件版本 -> 支持的 CLI 版本）

## 8. 核心 CLI 发布流程（维护者）

1. 更新 `src/nexuscli/__init__.py` 与 `pyproject.toml` 版本号
2. 运行：

```powershell
$env:PYTHONPATH = "src"
D:/Develop/Python/3.10.6/python.exe -m pytest -q
```

3. 构建并检查分发包：

```powershell
D:/Develop/Python/3.10.6/python.exe -m build
D:/Develop/Python/3.10.6/python.exe -m twine check dist/*
```

4. 发布后执行回归：

- 内置命令：`plugin`、`file`
- 插件冲突策略：`error`、`skip`
- 禁用/启用流程：`plugin disable`、`plugin enable`

## 9. 故障排查

### 9.1 插件未出现

1. 检查插件是否注册到 `nexuscli.command`
2. 运行 `nexuscli plugin list --failed --skipped`
3. 检查插件是否在禁用列表（`plugin inspect <plugin_id>`）

### 9.2 依赖报错

- 查看失败信息：`Missing dependency` 或 `Dependency mismatch`
- 修正插件 `dependencies`，重新安装插件

### 9.3 命令冲突

- 调整 `command_name` 与 `command_group`
- 或将 `conflict_policy` 改为 `skip` 以临时绕过

## 10. 团队协作建议

- 每个插件维护独立仓库，使用统一模板
- PR 必须包含：
  - 元数据字段完整性检查
  - 至少一个命令可执行测试
  - 兼容版本变更说明
- 发布时维护 Changelog，标明破坏性变更
