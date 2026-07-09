# Changelog

## 1.1.0

### Highlights
- Added target-centric traffic overview via `burp_target_overview`.
- Added staged MCP help via `burp_mcp_list`.
- Implemented real rewrite-rule actions: `modify`, `drop`, and `spoof`.
- Added rule scope control: `proxy`, `tool`, and `all`.
- Added Burp 2026.4.x runtime-detected integrations:
  - command palette / HotKey selection capture
  - official internal-tool request drop/spoof when available
  - BCheck import
  - Bambda import
- Added Burp UI diagnostics, command copy helpers, and improved rewrite-rule UX.
- Simplified configuration: examples directly start `wsl-mcp/server.py` and set `BURP_MCP_BRIDGE_URL`; wrapper scripts were removed from the release package.

### Stability / Compatibility
- Compile baseline remains `montoya-api 2025.10`.
- Optional 2026.4.x features are detected at runtime.
- JSON detail responses keep preview-first body handling; full raw evidence is exported via bundle files.

### Tested Baseline
- Burp Suite Professional 2026.4.2

## 1.0.0

### Highlights
- Initial release for Windows Burp ↔ WSL Codex / Agent AI / MCP CLI / IDE communication.
- Reads Burp Proxy traffic and logger-like internal HTTP tool traffic.
- Supports replay, rewrite rules, Repeater handoff, and raw bundle export.
