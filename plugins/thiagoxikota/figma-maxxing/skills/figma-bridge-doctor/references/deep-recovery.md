# figma-bridge-doctor: deep recovery (rare, multi-session or marathon session)

Rare procedures that do not need to load on every invocation of the skill. Load this file at
escalation attempt 3 (attempt 1 failed and attempt 2 failed or was declined, in a
multi-session scenario), or after hours of session with orphan ports.

Everything here is macOS only (`lsof`, `kill`, `osascript`). The menu click needs the Accessibility
permission on the app that runs the command and assumes the English Figma UI. Script names refer to
this skill's `scripts/` directory. "The harness respawns the server" describes Claude Code, which
restarts a dead MCP server on the next tool call.

## Which servers may be killed without asking

`scripts/figma-status.sh` sorts every listener on 9223-9232 into three groups:

| Line | Meaning | Kill without asking? |
|---|---|---|
| `my_mcp_pid=` | This session's server (its nearest agent ancestor is this session's). | Yes, when a step below says so. |
| `orphans=` | No live owner: from the server up to launchd (pid 1) there is only the server and its own npx wrapper, so the session that started it is gone. | Yes. Only these pids. |
| `other_sessions=` | Anything else: a different live agent process, or another live owner such as another agent app or an `mcp-direct` daemon. | **Never.** Ask the user first, every time. |

`orphans=` and `other_sessions=` hold `port:pid` pairs. Never move a pid from `other_sessions=` to the no-consent group by your own reasoning ("it is probably a leftover"): only the script's `orphans=` line grants that.

A note on the attach model. The procedures below date from 2026-05 and 2026-06 and describe the
plugin attaching to ONE server (the first or lowest-numbered responder). Later field notes (2026-08
and 2026-09, in `SKILL.md`) saw the plugin hold one WebSocket per live server in the range. The two
observations were never reconciled. Do not assume either: probe with `figma_get_status` before and
after each step.

## Tight-loop atomic re-attach (escalation step 3, multi-session race fix)

Validated 2026-05-25. When multiple Claude Code windows are open, each spawns its own MCP server on ports 9223-9232. The plugin scans the range and attaches to the FIRST responder, which is rarely yours. Kill all rival MCP servers AND trigger the plugin click in the SAME bash command, so rivals cannot respawn in the gap (typical respawn window: ~1-2s).

Identify MY MCP server pid (e.g. via `lsof -i tcp:9224 -s TCP:LISTEN` if your port is 9224 per `figma_get_status`). List every listener the loop would touch with `lsof -nP -iTCP -sTCP:LISTEN | grep -E '922[3-9]|923[0-2]'` (pid, command and port) and name them in the consent question below. Then:

```bash
MY_PID=<your-mcp-pid>
# atomic: kill rivals AND trigger plugin in one bash invocation
for pid in $(lsof -t -i tcp:9223-9232 -s TCP:LISTEN 2>/dev/null); do
  # only node / figma-console servers: the same name filter figma-bridge-reset.sh uses
  ps -p "$pid" -o comm= 2>/dev/null | sed 's|.*/||' | grep -qiE 'node|figma-console' || continue
  [ "$pid" != "$MY_PID" ] && kill -9 "$pid" 2>/dev/null && echo "killed rival pid=$pid"
done
osascript <<'OSA'
tell application "Figma" to activate
delay 0.3
tell application "System Events"
  tell process "Figma"
    set frontmost to true
    delay 0.3
    click menu item "Figma Desktop Bridge" of menu 1 of menu item "Development" of menu 1 of menu bar item "Plugins" of menu bar 1
  end tell
end tell
OSA
sleep 5
```

Then `figma_get_status probe:true`: it should now show `transport.active = "websocket"` with `connectedFile`.

**Why it works:** the plugin click runs while only YOUR MCP server is alive. Rivals respawn AFTER the plugin already bound to you. The plugin holds that connection until the next plugin restart.

**Do not kill your own MCP server** (it serves the current conversation). Identify it by port from `figma_get_status` first.

**Collateral damage: MANDATORY user consent gate.** This kills rival MCP servers belonging to OTHER active Claude Code sessions. Those sessions LOSE their bridge mid-work without warning, and the user has to re-run the plugin click manually in each one. **DO NOT execute this trick without explicit user consent** when `figma-status.sh` reports `other_sessions_count >= 1`. Pids under `orphans=` do not count toward that gate: they have no live owner. Required surface BEFORE running:

> "You have N other Claude Code sessions open with an active bridge (ports X, Y, Z; pids A, B, C). To connect my bridge I need to kill their MCP servers: they will have to re-click the plugin. May I?"

Only proceed if the user replies with an explicit yes. If the user says no, escalate to the manual checklist (step 4) instead. Validated as a required guardrail on 2026-05-25, after killing 6 rival pids without surfacing the cost: those sessions lost work-state silently.

## Respawn-low: win the attach race WITHOUT killing other sessions (preferred when the plugin is DETACHED)

Validated 2026-06-15. When `figma_get_status` shows `transport.active = "none"` (plugin attached to NOBODY) and orphan or rival servers hold ports BELOW yours, you do NOT need the kill-all trick or the consent gate. The plugin binds to the LOWEST-numbered responding server on launch, so just get YOUR server onto the lowest free port:

1. `figma-status.sh`: read `orphans=`, `other_sessions=` and `my_mcp_pid=`.
2. `kill -9` only the pids under `orphans=` AND your own server (`my_mcp_pid`). LEAVE every pid under `other_sessions=` alone.
3. Call any figma-console tool: the harness respawns YOUR server on the lowest free port (e.g. 9223).
4. Trigger the plugin (osascript menu click, file open first): it scans ascending and binds YOU first because you now hold the lowest port. The other session keeps its higher-port server, untouched.
5. Verify with `figma_get_status probe:true`.

If an `other_sessions=` pid holds a port below the one you would get, this does not work without killing it: that is the consent-gated trick above, not this one.

**Why this is better than kill-all:** the plugin was already detached (no active session loses its bridge) and you never kill another session's server, so NO consent gate. Use the kill-rivals atomic re-attach trick (above) ONLY when the plugin is actively bound to a RIVAL and you must steal it. Detached means respawn-low: skip the collateral damage.

Gotcha from that session: `figma_take_screenshot` went through REST and returned 403 on an expired personal access token even with the bridge up. That is not a bridge failure: route exports through the official Figma MCP server (OAuth), as described under "Failure surface to track" in `SKILL.md`. As of figma-console-mcp v1.40.8, `figma_take_screenshot` uses the Desktop Bridge plugin when it is connected and falls back to the REST API; `figma_capture_screenshot` always uses the plugin runtime and needs the bridge.

## Orphan-MCP port exhaustion (self-inflicted, long sessions)

`figma_get_status` reports `startupError: EADDRINUSE ... All ports in range 9223-9232 are in use`, listing 8-10 `otherInstances`. In a long session with many bridge reconnects and plugin re-triggers, each reconnect can leave an **orphan `figma-console-mcp` node process** holding a port. After ~10 they exhaust the whole 9223-9232 range, so YOUR server cannot bind and the bridge can never come up. Verified 2026-05-29 (20 processes, 9 holding ports, all orphans from one session's churn).

- Distinguish from the genuine multi-session race with `figma-status.sh`: leftovers from THIS session's churn show up under `orphans=`, live servers of other sessions under `other_sessions=`.
- **Step 1, no consent needed: clear the orphans.** Kill only the pids listed under `orphans=`: `kill <pid>` for each, `kill -9 <pid>` for any that is still listening after a second. Then restart your own server too: it started while the range was full, and figma-console-mcp (checked on v1.40.8) does not retry the bind once it runs without the WebSocket transport. `figma-status.sh` shows its pid as `my_mcp_pid=` with `my_mcp_note=this session's server holds no port in 9223-9232`; `kill` that pid.
- **Step 2, only if the ports are still full: consent gate (mandatory).** What is left belongs to `other_sessions=`, and killing it takes down the bridge of any genuinely active other session. ASK first: "N servers are holding the ports (ports and pids from `other_sessions=`). Is another Claude Code window using Figma right now, or can I clear them?" Only proceed on an explicit yes. Then `pkill -9 -f "figma-console-mcp"` clears ALL of them; the pattern matches any process whose command line contains `figma-console-mcp`, so list the matches first with `pgrep -fl "figma-console-mcp"` and include that list in the question.
- **Then:** call any figma-console tool: the harness respawns YOUR server, now binding a freed port (9223). Re-trigger the plugin (osascript menu click) so it attaches to your server. Verify with `figma_get_status probe:true`.
- Prevention: this only piles up across many manual reconnects in one marathon session; a fresh session never has it.
