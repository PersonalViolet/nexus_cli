# NexusOpenCLI

[English](../README.md) | [中文](README.zh-CN.md)

NexusOpenCLI 是一个可扩展的 Typer 命令行工具，启动时会自动加载内置与第三方插件，让你通过安装插件包来添加新命令。

## 特性

- 基于插件的命令体系，运行时发现
- 内置插件管理与批量重命名命令
- 可配置的插件来源（entry point 与可选的目录加载）
- 支持全局与单插件语言设置

## 快速开始

建议在指定目录的虚拟环境中使用`pip install nexus-open-cli`安装，并输入`ncli plugin list`查看目前命令组

<video src=".\video\show1.mp4"></video>

```bash
ncli --help
ncli plugin list
```

## 安装插件

以`pip install nexus-open-cli-doctor`为例，体验插件

<video src="video\show2.mp4"></video>

后续添加插件可通过 pip 安装本地文件夹或 PyPI 包：

```bash
# 安装本地插件目录
pip install /path/to/your-plugin

# 安装发布到 PyPI 的插件
pip install your-plugin-package
```

插件需要注册到 `nexuscli.command` entry point 组，NexusCLI 才能在启动时发现它们。安装插件后再次输入`ncli`可验证插件是否成功安装

## 配置

查看或更新插件设置：

```bash
ncli plugin config
ncli plugin config-path
```

通过交互式提示或 `--set-plugin-dir`、`--add-plugin-dir`、`--remove-plugin-dir` 选项管理插件目录。

注：

`ncli plugin config --folder-loader` 启用目录加载无效，该命令即将被弃用，不用管。

## 开发插件

你可以借助本仓库提供的`skill/ncli-plugi-dev-helper/SKILL.md`技能零基础快速开发第三方插件

## 开发

```bash
pip install -e ".[dev]"
pytest
```

## 许可证

MIT
