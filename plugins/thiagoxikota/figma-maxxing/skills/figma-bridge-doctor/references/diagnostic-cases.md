# diagnostic cases

Use only the section relevant to the current operation. Inline `scripts/` and `references/` paths are relative to this skill’s directory unless a link says otherwise. Existing authorization and the entrypoint contract govern these recipes.

## Plugin version: THREE layers, and the banner does not say the direction

Field note, 2026-09. The plugin panel can show `Plugin update available`. **Never re-import because of that banner without measuring first:** run `figma-status.sh` and read `plugin_drift`. `true` means the disk is NOT the newest bundle: a server started from an old npx cache can rewrite `~/.figma-console-mcp/plugin/` with its own, older bundle, and following the banner would install that downgrade for good. `Connected to N AI apps` counts live servers in 9223-9232, not files, and is not a sign of a problem.

The three version layers, the trap, the five rules and the full fix recipe: [references/plugin-version-drift.md](plugin-version-drift.md). Load it whenever the banner appears or `plugin_drift=true`.

## Step T: TRIGGER-only (when Figma is already open)

```bash
osascript <<'OSA'
tell application "Figma" to activate
delay 0.5
tell application "System Events"
  tell process "Figma"
    set frontmost to true
    delay 0.5
    click menu item "Figma Desktop Bridge" of menu 1 of menu item "Development" of menu 1 of menu bar item "Plugins" of menu bar 1
  end tell
end tell
OSA
sleep 4
```

Idempotent. Validated 2026-05-23. macOS only, needs the Accessibility permission, assumes the English Figma UI.

## After reconnecting in a WRITE session: rival-write audit (mandatory)

Field note, 2026-06: during the disconnect window the plugin may have served ANOTHER Claude Code session, which wrote into the file. After reconnecting in the middle of write work, run the audit in [references/rival-write-audit.md](rival-write-audit.md) before the next write: compare `page.children` with your inventory from before the drop, archive rival debris (never delete it), do not adopt a rival write into a deliverable, and treat a write that re-injects after you archive it as a live loop that only closing the other window stops.

## The active file DRIFTS on its own in the middle of a write

Field note, 2026-08. With two files paired at the same time, the active target changes without you asking (the designer clicks another tab, another Claude Code session re-triggers the plugin). Symptoms, in the order they appear:

1. `figma_execute` dies with `in setCurrentPageAsync: Expected node, got undefined`, because `figma.root.children.find(p => p.name === '<your page>')` returned `undefined`: you are in the wrong file, the page was not deleted. **Always check `fileContext.fileName` in the return value.**
2. `figma_take_screenshot` falls to REST and returns `403 Invalid token`, which looks like an expired personal access token (see "Failure surface to track" below) but here it is only a consequence of the wrong target.

**Fix in two steps, in this order:**

- **Write:** pass an explicit `fileKey` to `figma_execute`. It runs against that file without touching the active target, so it works even with the bridge pointing somewhere else.
- **Visual read:** `figma_navigate({url, lock: true})`. The `lock` PINS the target; without it the drift comes back. After pinning, `figma_capture_screenshot` (plugin, exportAsync) works with no token at all.

**Before any conclusion about a leak:** sweep the intruder file for nodes with the names from YOUR plan before assuming damage. In the incident of 2026-08-17 the write died at `setCurrentPageAsync`, which comes BEFORE any `create*`, and nothing leaked into the other file, confirmed by a sweep of its 8 pages, not by assumption.

## Manual checklist (escalation step 4 only)

Surface this when auto-recovery has exhausted its retries:

```
Bridge still down after 4 attempts. Manual steps:

1. Figma DESKTOP (not browser) running with a file open
2. Plugins > Development > "Figma Desktop Bridge" (the one WITHOUT the warning icon) > Run
   - If not listed, import from ~/.figma-console-mcp/plugin/manifest.json
3. Leave the plugin window OPEN
4. Reply "bridge is up" and I will re-probe.
```

After the user confirms, re-probe ONCE. Do not loop further.

## Failure surface to track (cheap diagnostics first)

Before running any recovery script, if `figma_get_status` returns disconnected, glance at:

- `pgrep -x Figma`: is Figma even running?
- `claude mcp list | grep figma-console` (Claude Code, server registered as `figma-console`): is the MCP server installed?
- `lsof -t -i tcp:9223-9232 -s TCP:LISTEN`: which servers hold which ports?

If `pgrep` shows zero Figma, the recovery is just OPEN (not RESTART). If the MCP server is not listed, surface the install instructions (https://github.com/southleft/figma-console-mcp) and stop. If multiple servers hold ports across the range, read `figma-status.sh`: pids under `orphans=` are leftovers with no live owner (deep recovery clears them), pids under `other_sessions=` are the multi-session race: close the other Claude Code windows.

**Not every Figma failure is the bridge: REST token vs OAuth (validated 2026-06-14).** `figma_take_screenshot` (figma-console) renders via the Figma REST API, which uses the MCP server's `FIGMA_ACCESS_TOKEN` (the personal access token). When that token expires it returns `403 "Invalid token"` / `403 "Token expired"`: this is **NOT a bridge failure**, do NOT run resets. The WebSocket bridge (writes and `figma_capture_screenshot`) and the **official Figma MCP server (remote, OAuth, separate auth)** keep working. To screenshot or export anyway, use the official server: `download_assets(fileKey,nodeId,defaultScale:2)` or `get_screenshot(fileKey,nodeId)` return a short-lived `figma.com/api/mcp/asset/...` URL, then `curl -o file.png "<url>"` (no token, no base64). `whoami` confirms the OAuth identity even with the token dead. Refreshing the token (Figma > Settings > Security) is the long-term fix but is a USER action.

As of figma-console-mcp v1.40.8, `figma_take_screenshot` uses the Desktop Bridge plugin when it is connected and falls back to the REST API, so the 403 shows up when the call goes through REST (bridge down, or pointing at another file). `figma_capture_screenshot` always uses the plugin runtime and needs the bridge.

**`figma_get_comments` is also gated by the REST token**: same 403 when the token expires (seen 2026-06-18). Worse: **comments are NOT in the Figma Plugin API at all**, so the bridge and `figma_execute` can never read them. To read comments with a dead token: the official Figma MCP server (OAuth) if it is connected, else ask the user to paste the comments or refresh the token. Do not promise to read a stakeholder's comments without checking the token first.

## The TWO bridge layers (do not conflate them)

This skill mostly fixes layer 2. Layer 1 failures look identical from the user's chair ("the bridge will not connect") but have a different fix and **cannot be fixed mid-session by this skill**, because this skill works THROUGH the figma-console tools, which do not exist if layer 1 failed.

1. **MCP server registration in the agent session** (boot-time). Claude Code handshakes each MCP server ONCE at session start and freezes the tool list. If `figma-console` crashed at boot, its tools are absent for the whole session, and re-registration requires the USER to run `/mcp` and reconnect, or to restart Claude Code.
2. **Bridge plugin + WebSocket inside Figma Desktop** (runtime). This is what `figma_get_status`, `figma-open.sh` and the osascript menu click own. The agent CAN fix this layer itself.

When the figma-console tools are entirely missing (not just disconnected), load [references/layer1-recovery.md](layer1-recovery.md): how to confirm a layer 1 boot crash, the corrupted npx cache fix, the opt-in `scripts/mcp-direct/` fallback and what to tell the user. Do NOT loop the plugin-trigger osascript for a layer 1 failure: the plugin layer was never the problem.
