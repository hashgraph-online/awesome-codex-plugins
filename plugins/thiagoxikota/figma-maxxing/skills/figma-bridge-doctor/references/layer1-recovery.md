# Layer 1 recovery: the figma-console tools are missing from the session

Loaded from the `figma-bridge-doctor` SKILL.md when the figma-console tools are entirely MISSING from the session, not just disconnected. Paths written `scripts/...` are in this skill's `scripts/` directory; run the commands from this skill's directory (the folder that holds SKILL.md).

## Opt-in

The `scripts/mcp-direct/` fallback below is opt-in. It starts `daemon.mjs`, a local HTTP proxy for figma-console-mcp that binds `127.0.0.1` only and requires a bearer token written to `<state-dir>/mcp-direct-<HTTP_PORT>.token` (mode 0600). Before starting it, tell the user in one line what it is and wait for an explicit yes. Stop it when the task is done. Never start it to work around a permission prompt, and never bind it to another interface. When the path of figma-console-mcp is known, set `FIGMA_MCP_ENTRY` to its `dist/local.js` so the daemon does not scan the npx cache.

## The TWO bridge layers (do not conflate them)

This skill mostly fixes layer 2. Layer 1 failures look identical from the user's chair ("the bridge will not connect") but have a different fix and **cannot be fixed mid-session by this skill**, because this skill works THROUGH the figma-console tools, which do not exist if layer 1 failed.

1. **MCP server registration in the agent session** (boot-time). Claude Code handshakes each MCP server ONCE at session start and freezes the tool list. If `figma-console` crashed at boot, its tools are absent for the whole session: in Claude Code, with the server registered as `figma-console`, `ToolSearch "select:mcp__figma-console__figma_get_status"` returns nothing, and there is **no in-session tool** to re-register them. Re-registration requires the USER to run `/mcp` and reconnect, or to restart Claude Code.
2. **Bridge plugin + WebSocket inside Figma Desktop** (runtime). This is what `figma_get_status`, `figma-open.sh` and the osascript menu click own. The agent CAN fix this layer itself.

**Diagnostic when the figma-console tools are entirely missing (not just disconnected):**

- `claude mcp list | grep figma-console` (server registered as `figma-console`) shows `Failed to connect`: layer 1 boot crash.
- Most common cause seen: **corrupted npx install cache**. The server crashes on spawn with `npm error ENOTEMPTY: directory not empty, rename '.../_npx/<hash>/node_modules/...'`.
- Reproduce + read the real error, with `FIGMA_ACCESS_TOKEN` already in the environment: `cd /tmp && (echo "" | npx -y figma-console-mcp@latest 2>&1 & P=$!; sleep 15; kill $P) | head -40`. A healthy boot logs `All MCP tools registered successfully` + `MCP server started successfully on stdio transport`.
- **Fix the cache:** move the corrupted dir aside: `NPX="$(npm config get cache)/_npx"; mv "$NPX/<hash>" "$NPX/<hash>.corrupt.bak"` (prefer `mv` over `rm -rf`; the latter is often permission-gated in agent setups). Re-test the boot command; it should now register the tools. The fix is **permanent**: future sessions connect clean.
- **Do NOT stop here: there is an opt-in fallback that does NOT depend on a `/mcp` reconnect by the user (validated 2026-08-20: 16 screens written with zero native Figma tool).** It starts a local HTTP daemon, so start it only after the user says yes (see "Opt-in" at the top of this file). The tools vanish from the session, the SERVER does not: it is an ordinary stdio MCP server, so start an instance of your own and speak JSON-RPC to it.
  `WS_PORT=<free port> HTTP_PORT=8791 node scripts/mcp-direct/daemon.mjs &`,
  then the plugin trigger osascript (Step T of SKILL.md), and call it through
  `python3 scripts/mcp-direct/fx.py <file.js>` (figma_execute) and
  `python3 scripts/mcp-direct/shot.py <nodeId> <out.png> [scale>=0.5]` (screenshot). The plugin connects to ALL live servers in the 9223-9232 range, one WebSocket per server, so this **does not steal the bridge** from another session. Free port: `lsof -nP -iTCP -sTCP:LISTEN | grep -E '922[3-9]|923[0-2]'`. `fx.py` and `shot.py` read `HTTP_PORT` like the daemon does. The HTTP endpoint is local and token gated: it refuses requests with an `Origin` header, wants `content-type: application/json` and a bearer token that the daemon writes to `<state-dir>/mcp-direct-<HTTP_PORT>.token` at boot; `fx.py` and `shot.py` send both. Stop the daemon when the work is done. Details in [scripts/mcp-direct/README.md](../scripts/mcp-direct/README.md). Only escalate to the user if THIS also fails.
- **Then tell the user (only they can finish it this session):** "The MCP cache is repaired and the server boots clean now. Run `/mcp`, pick figma-console, Reconnect (keeps this session), or restart Claude Code, then say go." Do NOT loop the plugin-trigger osascript for this: the plugin layer was never the problem.
