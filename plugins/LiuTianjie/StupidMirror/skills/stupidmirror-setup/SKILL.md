---
name: stupidmirror-setup
description: Set up or repair the StupidMirror Codex plugin and its real iPhone or Android connection. Use for plugin installation, missing tools, device discovery or connection errors; ordinary phone tasks use stupidmirror-device-use.
---

# StupidMirror setup

StupidMirror is a local macOS app. The plugin starts its signed MCP helper, which opens the app and connects to its authenticated loopback MCP service. Phone agents, signing, USB/Wi-Fi sessions and mirroring belong to that app.

1. If StupidMirror tools are available, call `list_devices` and `get_diagnostics` before changing configuration. Reuse healthy device sessions.
2. The normal installation path is **StupidMirror → Settings → MCP Automation → Connect Codex**, followed by a new Codex chat with the StupidMirror plugin selected. The app includes everything needed for the plugin, and can use the desktop client's bundled CLI. If the helper is missing, install a newer StupidMirror build. Developers working in its source repo can build with `bash scripts/build-app.sh`, install the resulting app, then run `bash scripts/install-codex-plugin.sh`. Do not run release/upload scripts for local setup. For a custom app location, the installer remembers the app path; the launch script also accepts `STUPIDMIRROR_APP`.
3. In the app, Settings → MCP must be enabled. The app manages its own port and Bearer token; never print or copy `~/Library/Application Support/StupidMirror/MCP/connection.json` into chat, the repository or the plugin cache. Do not disable authentication or open the listener to the network.
4. After plugin installation or replacement, reconnect or open a new Codex chat to load tools and skills. If tools remain missing, inspect the plugin's installation status. An older manually configured `mcp_servers.stupidmirror` entry can override the plugin; inspect its transport without exposing headers, and migrate only that entry if needed. Preserve unrelated MCP configuration.
5. With several devices, select the user's intended device and pass its `device_id`. Call `show_screen` to open the embedded Codex preview, then `connect_control` only when actions or native hierarchy are needed. Do not open a native mirror window unless explicitly requested. A USB mirror alone can provide a frame without a control session.

For initial iPhone setup, use StupidMirror's iPhone setup guide with the user's own Xcode team and bundle identifier. Apple account login, device trust, Developer Mode and unlocking may need the user. Existing paired devices should not be rebuilt just to recover a connection. Do not start a second WDA/Appium stack alongside StupidMirror. Android requires USB debugging and the phone's authorization prompt.

Verify tool availability separately from device readiness: `list_devices` proves the plugin can reach the app; `observe_screen` proves an actual frame is available; a user-authorized reversible action followed by observation proves control. If no device is attached, report that boundary without claiming a successful phone test.

The normal screen is the MCP App inside Codex. It reuses a panel in the same chat and supports device selection, refresh, pause/resume, Home and copying a frame. Preview frames are for the user; the model still calls `observe_screen` for visual reasoning. StupidMirror can run in the background without any mirror window.
