# share-cli 插件开发与发布实操（Quickstart）

本实操文档用于快速完成一次完整闭环：

- 开发一个可被 share-cli 发现的插件
- 在本地验证插件命令可用
- 构建并检查可发布制品
- 按发布流程上传到包仓库

示例插件使用仓库内已实现的外部包：

- plugins/example_release_plugin

## 1. 前置条件

- Python 3.10+
- 已安装 pip
- 当前仓库路径：D:/My-Project/share-cli

可选但推荐：

- 使用虚拟环境（避免污染全局环境）

## 2. 示例插件结构

示例插件目录如下：

- plugins/example_release_plugin/pyproject.toml
- plugins/example_release_plugin/src/example_release_plugin/plugin.py
- plugins/example_release_plugin/tests/test_plugin_contract.py

这个插件通过 Entry Points 注册到组：

- share_cli.command

并提供命令路径：

- hello greet

## 3. 本地开发与联调

### 3.1 安装主项目与示例插件

PowerShell：

1. cd D:/My-Project/share-cli
2. D:/Develop/Python/3.10.6/python.exe -m pip install -r requirements.txt
3. D:/Develop/Python/3.10.6/python.exe -m pip install -e .
4. D:/Develop/Python/3.10.6/python.exe -m pip install -e ./plugins/example_release_plugin

### 3.2 验证插件是否被发现

验证包是否加载到venv中：

```
(.venv) D:\My-Project\share-cli>pip list -e
```

验证插件是否被发现

1. $env:PYTHONPATH = "src"
2. D:/Develop/Python/3.10.6/python.exe -m share_cli.main plugin list

期望在输出中看到：

- example.release-hello

### 3.3 运行示例命令

1. D:/Develop/Python/3.10.6/python.exe -m share_cli.main hello greet Copilot
2. D:/Develop/Python/3.10.6/python.exe -m share_cli.main hello greet Copilot --style formal
3. D:/Develop/Python/3.10.6/python.exe -m share_cli.main hello greet Copilot --style excited

## 4. 开发你自己的插件（方法）

你只需复用示例插件的三部分：

1. 插件类：继承 CliPluginBase
2. 元数据：返回 CommandMetadata（plugin_id、command_name、version 等）
3. 注册声明：在 pyproject.toml 中写 entry points 到 share_cli.command

建议做法：

1. 复制 plugins/example_release_plugin 为新目录
2. 修改包名、plugin_id、command_name
3. 修改命令逻辑和测试
4. 本地 editable 安装后反复联调

## 5. 测试方法

### 5.1 运行主仓库测试

1. cd D:/My-Project/share-cli
2. $env:PYTHONPATH = "src"
3. D:/Develop/Python/3.10.6/python.exe -m pytest -q

### 5.2 运行示例插件测试

1. cd D:/My-Project/share-cli
2. D:/Develop/Python/3.10.6/python.exe -m pytest -q plugins/example_release_plugin/tests

## 6. 构建与发布方法

### 6.1 构建前检查

在 plugins/example_release_plugin 中确认：

1. pyproject.toml 的 version 已更新
2. min_cli_version 与 dependencies 合理
3. 测试已通过

### 6.2 构建并检查包

PowerShell：

1. cd D:/My-Project/share-cli/plugins/example_release_plugin
2. D:/Develop/Python/3.10.6/python.exe -m pip install build twine
3. D:/Develop/Python/3.10.6/python.exe -m build
4. D:/Develop/Python/3.10.6/python.exe -m twine check dist/*

### 6.3 上传发布

公开 PyPI：

1. D:/Develop/Python/3.10.6/python.exe -m twine upload dist/*

私有仓库：

1. D:/Develop/Python/3.10.6/python.exe -m twine upload --repository-url <your-index-url> dist/*

## 7. 发布后验证

1. 在干净环境安装 share-cli 与插件
2. 运行 share-cli --help，确认 hello 命令组出现
3. 运行 hello greet 做冒烟验证
4. 记录插件版本与兼容的 share-cli 版本

## 8. 常见问题

### 8.1 插件未被加载

排查顺序：

1. 是否正确声明 share_cli.command entry point
2. 是否安装到当前 Python 环境
3. plugin list 中 failed/skipped 原因
4. 是否被 plugin disable 过

### 8.2 命令冲突

如果 command_name 与已有命令重复：

- conflict_policy=error：插件失败
- conflict_policy=skip：插件被跳过

建议直接更改 command_name 或 command_group。

### 8.3 依赖不兼容

若提示 Missing dependency 或 Dependency mismatch：

1. 修正插件 dependencies 约束
2. 重新安装插件
3. 再次执行 plugin list 验证

## 9. 下一步建议

- 为你的插件增加更多子命令与参数校验
- 增加 CI 自动执行 pytest/build/twine check
- 维护 changelog 与版本兼容矩阵
