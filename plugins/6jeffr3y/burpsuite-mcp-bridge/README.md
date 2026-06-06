# BurpSuite MCP Bridge

English | [简体中文](./README_CN.md)

**MCP bridge for Burp Suite traffic, replay, rewrite automation, UI selection handoff, and evidence export.**

This release is designed for real mixed-environment workflows: Burp can run on Windows while Codex/AI agents run in WSL, Windows, or macOS. The default setup uses stdio MCP and points the Python MCP server at the Burp extension bridge with one explicit URL.

---

## What's new in v1.1.0

- Unified MCP response/error shape.
- Rewrite rules now support real `modify`, `drop`, and `spoof` actions.
- Rule scope supports `proxy`, `tool`, and `all`.
- Burp 2026.4.x runtime-detected integrations:
  - command palette / HotKey selection capture
  - official internal-tool request drop/spoof when available
  - BCheck import
  - Bambda import
- New target-centric workflow: `burp_target_overview(host=...)`.
- New staged help: `burp_mcp_list(section=..., topic=...)`.
- Better Burp UI diagnostics, quick MCP command copy panel, and rewrite-rule UX.
- Simplified configuration: no wrapper scripts are required.

Tested with **Burp Suite Professional 2026.4.2**. Compile baseline remains `montoya-api 2025.10`; newer features are runtime-detected for compatibility.

---

## Included files

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

## Quick start

### 1) Load the Burp extension

In Burp Suite, load:

```text
burp-plugin/burpsuite-mcp-bridge-latest.jar
```

Recommended bridge settings:

```text
Bind host: 127.0.0.1
Port: 9639
Max live/logger entries: 1500
Max body preview bytes: 32768
Ignore static: on
```

For WSL NAT, bind Burp Bridge to the Windows LAN IP or `0.0.0.0`, then use that LAN IP in `BURP_MCP_BRIDGE_URL`.

### 2) Install MCP runtime dependency

```bash
python3 -m pip install -r requirements-wsl.txt
```

On Windows, use your normal Python installation and install the same requirement.

### 3) Configure Codex / MCP

Default stdio setup directly starts `wsl-mcp/server.py`; no wrapper script is required.

WSL mirrored / local loopback:

```toml
[mcp_servers.burpsuite-mcp-bridge]
command = "python3"
args = ["/mnt/d/AI_project/burpsuite-mcp-bridge-release/wsl-mcp/server.py"]

[mcp_servers.burpsuite-mcp-bridge.env]
BURP_MCP_BRIDGE_URL = "http://127.0.0.1:9639"
```

WSL NAT example:

```toml
[mcp_servers.burpsuite-mcp-bridge]
command = "python3"
args = ["/mnt/d/AI_project/burpsuite-mcp-bridge-release/wsl-mcp/server.py"]

[mcp_servers.burpsuite-mcp-bridge.env]
BURP_MCP_BRIDGE_URL = "http://192.168.1.100:9639"
```

See `config-examples/` for WSL mirrored, WSL NAT, Windows, and macOS variants.

---

## Codex plugin marketplace readiness

This repository ships a valid `.codex-plugin/plugin.json`, icon assets, release JARs, and direct MCP configuration examples. It is suitable for submission to community Codex plugin directories such as `awesome-codex-plugins` for discovery, while remaining installable directly from this repository.

---

## Core MCP tools

### Status and help

- `burp_bridge_status`
- `burp_config_get`
- `burp_mcp_list`

### Target and traffic

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

### Replay and evidence

- `burp_replay_flow`
- `burp_send_raw_request`
- `burp_send_to_repeater`
- `burp_export_flow`
- `burp_export_flow_bundle`

### Automation

- `burp_rules_list`
- `burp_rule_upsert`
- `burp_rule_delete`
- `burp_bcheck_import`
- `burp_bambda_import`

---

## Recommended workflow

1. Start with `burp_target_overview(host="target.example")`.
2. Inspect one candidate flow with the matching getter:
   - `burp_flow_get(..., source="history" | "live")`
   - `burp_logger_flow_get(...)`
   - `burp_selection_get(...)`
3. Replay one controlled mutation with `burp_replay_flow`.
4. Export decisive raw evidence with `burp_export_flow_bundle`.
5. If a behavior is reusable, promote it to a rewrite rule, BCheck, or Bambda.

---

## Body handling

JSON detail calls inline body previews only. Large bodies are capped to avoid MCP context bloat and Burp/UI pressure. For full raw request/response bytes, use:

```python
burp_export_flow_bundle(flow_id=123, source="history")
```

---

## Optional Streamable HTTP MCP

The default release examples use stdio MCP. If you need Streamable HTTP, start it manually:

```bash
BURP_MCP_BRIDGE_URL=http://127.0.0.1:9639 \
python3 wsl-mcp/server.py --transport streamable-http --host 127.0.0.1 --port 9640 --path /mcp
```

Default URL:

```text
http://127.0.0.1:9640/mcp
```
