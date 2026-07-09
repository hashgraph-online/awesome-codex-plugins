# BurpSuite MCP Bridge v1.1.0

## Highlights

- Target-centric overview for real testing workflows: `burp_target_overview(host=...)`.
- Staged tool help: `burp_mcp_list(section=..., topic=..., detail=true)`.
- Rewrite rules now support real `modify`, `drop`, and `spoof` actions.
- Rule scope can target `proxy`, `tool`, or `all`.
- Burp 2026.4.x integrations:
  - command palette / HotKey selection capture
  - official internal-tool drop/spoof when available
  - BCheck import
  - Bambda import
- Improved Burp UI for diagnostics, MCP command copy, and rewrite-rule management.
- Simplified configs: direct `python3 wsl-mcp/server.py` plus `BURP_MCP_BRIDGE_URL`; no wrapper scripts in release.

## Included assets

- `burp-plugin/burpsuite-mcp-bridge-1.1.0-all.jar`
- `burp-plugin/burpsuite-mcp-bridge-latest.jar`
- `wsl-mcp/server.py`
- Four config examples:
  - WSL mirrored
  - WSL NAT
  - Windows
  - macOS

## Tested baseline

- Burp Suite Professional `2026.4.2`
- Compile baseline: `montoya-api 2025.10`

## Upgrade notes

- Replace the old Burp JAR with `burpsuite-mcp-bridge-latest.jar`.
- Update MCP config to start `wsl-mcp/server.py` directly.
- Use `BURP_MCP_BRIDGE_URL` instead of separate host/port values for clearer WSL NAT and multi-host setups.
