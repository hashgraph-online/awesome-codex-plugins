# BurpSuite MCP Bridge

[English](./README.md) | 简体中文

**把 Burp Suite 的流量、重放、改写规则、UI 选中消息和证据导出能力接入 MCP / Codex / AI Agent。**

本项目面向真实混合环境：Burp 可以跑在 Windows，Codex/AI Agent 可以跑在 WSL、Windows 或 macOS。默认使用 stdio MCP，并在 TOML 中用一个完整 URL 指向 Burp 扩展 bridge。

---

## v1.1.0 新增内容

- 统一 MCP 返回和错误结构。
- 改写规则动作真正落地：`modify`、`drop`、`spoof`。
- 规则作用面支持：`proxy`、`tool`、`all`。
- 接入 Burp 2026.4.x 运行时能力：
  - command palette / HotKey 捕获 UI selection
  - 可用时使用官方 internal-tool request drop/spoof
  - BCheck 导入
  - Bambda 导入
- 新增目标视角工作流：`burp_target_overview(host=...)`。
- 新增分级帮助：`burp_mcp_list(section=..., topic=...)`。
- 增强 Burp UI：自检状态、MCP 命令速查复制、规则 UX。
- 简化配置：不再需要 wrapper 脚本。

已用 **Burp Suite Professional 2026.4.2** 测试。编译基线仍保持 `montoya-api 2025.10`，新版能力运行时检测，尽量保持兼容。

---

## 包含文件

```text
burp-plugin/
  burpsuite-mcp-bridge-1.1.0-all.jar
  burpsuite-mcp-bridge-latest.jar
wsl-mcp/
  server.py
config-examples/
  codex-wsl-mirrored.toml
  codex-wsl-nat.toml
  codex-windows.toml
  codex-macos.toml
requirements-wsl.txt
```

---

## 快速开始

### 1）加载 Burp 扩展

在 Burp Suite 中加载：

```text
burp-plugin/burpsuite-mcp-bridge-latest.jar
```

推荐设置：

```text
Bind host: 127.0.0.1
Port: 9639
Max live/logger entries: 1500
Max body preview bytes: 32768
Ignore static: on
```

如果是 WSL NAT，需要把 Burp Bridge 绑定到 Windows 局域网 IP 或 `0.0.0.0`，然后在 `BURP_MCP_BRIDGE_URL` 里使用这个局域网 IP。

### 2）安装 MCP runtime 依赖

```bash
python3 -m pip install -r requirements-wsl.txt
```

Windows 环境使用本机 Python 安装同样依赖即可。

### 3）配置 Codex / MCP

默认 stdio 配置直接启动 `wsl-mcp/server.py`，不需要 wrapper 脚本。

WSL mirrored / 本机 loopback：

```toml
[mcp_servers.burpsuite-mcp-bridge]
command = "python3"
args = ["/mnt/d/AI_project/burpsuite-mcp-bridge-release/wsl-mcp/server.py"]

[mcp_servers.burpsuite-mcp-bridge.env]
BURP_MCP_BRIDGE_URL = "http://127.0.0.1:9639"
```

WSL NAT 示例：

```toml
[mcp_servers.burpsuite-mcp-bridge]
command = "python3"
args = ["/mnt/d/AI_project/burpsuite-mcp-bridge-release/wsl-mcp/server.py"]

[mcp_servers.burpsuite-mcp-bridge.env]
BURP_MCP_BRIDGE_URL = "http://192.168.1.100:9639"
```

更多环境参考 `config-examples/`。

---

## Codex 插件市场准备状态

本仓库已经包含有效的 `.codex-plugin/plugin.json`、图标资源、发布版 JAR 和直接启动 MCP 的配置示例。它可以提交到 `awesome-codex-plugins` 这类社区 Codex 插件目录获取曝光，同时也可以直接从本仓库安装使用。

---

## 主要 MCP 工具

### 状态与帮助

- `burp_bridge_status`
- `burp_config_get`
- `burp_mcp_list`

### 目标和流量

- `burp_target_overview`
- `burp_live_poll`
- `burp_live_overview`
- `burp_history_search`
- `burp_logger_poll`
- `burp_logger_overview`
- `burp_extension_activity_overview`
- `burp_selection_poll`
- `burp_flow_get`
- `burp_logger_flow_get`
- `burp_selection_get`

### 重放和证据

- `burp_replay_flow`
- `burp_send_raw_request`
- `burp_send_to_repeater`
- `burp_export_flow`
- `burp_export_flow_bundle`

### 自动化

- `burp_rules_list`
- `burp_rule_upsert`
- `burp_rule_delete`
- `burp_bcheck_import`
- `burp_bambda_import`

---

## 推荐工作流

1. 先用 `burp_target_overview(host="target.example")` 做目标画像。
2. 挑一个候选 flow 拉完整详情：
   - `burp_flow_get(..., source="history" | "live")`
   - `burp_logger_flow_get(...)`
   - `burp_selection_get(...)`
3. 用 `burp_replay_flow` 一次只改一个变量验证。
4. 用 `burp_export_flow_bundle` 导出决定性原始证据。
5. 如果模式可复用，再沉淀成 rewrite rule、BCheck 或 Bambda。

---

## Body 处理

JSON 详情接口只内联 body preview，避免撑爆 MCP 上下文和拖慢 Burp/UI。完整原始请求/响应请使用：

```python
burp_export_flow_bundle(flow_id=123, source="history")
```

---

## 可选 Streamable HTTP MCP

默认示例使用 stdio MCP。如需 Streamable HTTP，可手工启动：

```bash
BURP_MCP_BRIDGE_URL=http://127.0.0.1:9639 \
python3 wsl-mcp/server.py --transport streamable-http --host 127.0.0.1 --port 9640 --path /mcp
```

默认 URL：

```text
http://127.0.0.1:9640/mcp
```
