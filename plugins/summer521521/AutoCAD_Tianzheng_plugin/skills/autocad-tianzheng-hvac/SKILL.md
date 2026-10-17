---
name: autocad-tianzheng-hvac
description: Use when controlling AutoCAD 2026 with Tianzheng HVAC T30 through the autocad_tianzheng MCP server, including connecting the THvac30V1 profile, reading or creating DWG engineering files, scanning layers/entities/blocks/text into SQLite/JSON/XLSX, running Tianzheng HVAC commands, loading Tianzheng ARX modules, or diagnosing Tangent path issues.
---

# AutoCAD 2026 + 天正暖通 HVAC

## 适用范围

用这个 skill 处理本机 AutoCAD 2026 + 天正暖通 T30V1 的连接、读图、建图、保存、导出和排障。默认 MCP server 是 `autocad_tianzheng`；在 Codex 设置页的 MCP servers 里，它显示在 "From plugins" 列表下，不一定出现在手动 "Servers" 列表里。

机器相关路径从环境变量读取：

- AutoCAD: `AUTOCAD_EXE`，例如 `<AutoCAD 2026 install>\acad.exe`
- 天正暖通根目录: `TIANZHENG_ROOT`，例如 `<Tangent THvacT30V1 root>`
- 天正 profile: `THvac30V1`
- COM 自动化 profile: `CodexAutomation`
- AutoCAD 2026 COM ProgID: `AutoCAD.Application.25.1`
- MCP 工程: `AUTOCAD_TIANZHENG_MCP_ROOT`，指向本机 `multiCAD-mcp` 工作树
- Python 解释器: `AUTOCAD_TIANZHENG_PYTHON`，可选；未设置时使用当前环境里的 `python`
- 默认输出: 优先放在 MCP 工程外的用户指定工作目录；不要写入插件仓库

## 标准连接流程

1. 先连接指定 CAD 类型，不要依赖自动探测。稳定自动化模式通过 `CodexAutomation` 启动干净 AutoCAD 2026；如果用户已手动打开天正，则可只附加当前运行会话。

```json
[{"action":"connect","cad_type":"tianzheng_hvac"}]
```

把上面的 JSON 字符串传给 `manage_session`。

2. 连接后立刻探测天正状态：

```json
[{"action":"probe"}]
```

把上面的 JSON 字符串传给 `manage_tianzheng`。重点看 `current_profile`、`tangent_root_exists`、`missing_paths`、`support_path`、`trusted_paths` 和三个 ARX 文件是否存在。

常见正常状态：

- 用户手动打开天正时，`current_profile` 通常是 `THvac30V1`
- Codex 自动化冷启动时，`current_profile` 通常是 `CodexAutomation`

3. 做天正命令前再显式加载暖通 ARX：

```json
[{"action":"load_arx"}]
```

默认加载 `Tch_HvacCmd.arx`、`Tch_PipeBase.arx`、`tch_pipewire.arx`。不要把 `auto_load_arx` 改成默认开启；历史上自动加载天正核心 ARX 可能触发 AutoCAD 崩溃。

## 读图与索引

读取工程图时先用普通 CAD 工具查询图层、块、实体，再用天正索引补充可检索数据。扫描 ModelSpace 到 SQLite：

```json
[{
  "action":"scan_index",
  "db_path":"<output-root>\\index\\autocad_tianzheng_index.sqlite",
  "json_path":"<output-root>\\index\\autocad_tianzheng_index.json",
  "xlsx_path":"<output-root>\\index\\autocad_tianzheng_index.xlsx"
}]
```

索引内容包括图纸路径、实体 handle、对象类型、图层、颜色、线型、文字、块名/名称、坐标 JSON。需要追溯对象时优先用 handle。

## 建图与保存

新建图纸先调用 `manage_files` 的 `new`，再用 `draw_entities` 画基础实体和文字。保存用绝对路径：

```text
save|<output-root>\drawings\smoke_autocad_tianzheng.dwg
```

复杂工程文件优先分层创建：轴网/墙体/风管/水管/设备/标注/文字分别放到清晰图层；块名、图层名、文字标注要可检索。不要在没有用户确认的情况下覆盖已有 DWG。

## 执行天正命令

通过 `manage_tianzheng` 的 `run_command` 执行低风险命令：

```json
[{"action":"run_command","command":"_ABOUT","timeout_sec":10}]
```

如果返回 `Command is still active or waiting for user input`，说明命令大概率需要人工点选、输入或对话框确认。不要继续盲目发送回车或坐标，先报告需要人工交互。

## 排障顺序

1. `manage_session` 连接失败：确认 AutoCAD 2026 路径存在，再看 `AutoCAD.Application.25.1` 是否可用。不要混用旧版 AutoCAD ProgID。
2. `probe` 显示 `tangent_root_exists=false` 或 ARX 文件不存在：确认 `TIANZHENG_ROOT` 指向正确的天正暖通安装目录。
3. `CodexAutomation` 下没有天正 `SupportPath/TRUSTEDPATHS` 是预期状态；只有用户手动打开天正 `THvac30V1` 时才应看到天正路径。
4. ARX 加载失败：确认文件在 `TIANZHENG_ROOT\SYS25x64` 下，再用 `load_arx` 单独加载具体路径。
5. Codex 看不到 MCP 工具：先确认设置页 "From plugins" 里有 `autocad_tianzheng`，再重启 Codex，让新环境变量和缓存插件重新加载。
