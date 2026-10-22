# local dispatch

Use only the section relevant to the current operation. Inline `scripts/` and `references/` paths are relative to this skill’s directory unless a link says otherwise. Existing authorization and the entrypoint contract govern these recipes.

## Platform and permissions

- **The automation is macOS only.** The scripts use `open`, `osascript`, `launchctl`, `lsof`, `pgrep` and `ps`. On any other OS each macOS-only script prints a short manual checklist and exits 1: follow the "Manual checklist" section with the user instead.
- **Accessibility permission.** The plugin is launched by a menu click through System Events. The app that runs the script (Terminal, iTerm, the IDE or whatever hosts the agent) needs the Accessibility permission: System Settings > Privacy & Security > Accessibility. Without it the click fails and the script prints `osascript click failed`. Granting it is a user action.
- **English Figma UI.** The click targets the menu items by name: `Plugins` > `Development` > `Figma Desktop Bridge`. If Figma runs in another language the names do not match and the click fails. Ask the user to switch Figma to English or to run the plugin by hand.
- **Prerequisites.** Figma Desktop, the figma-console MCP server (`figma-console-mcp`, by Southleft) registered in the agent, and its Desktop Bridge plugin imported once from `~/.figma-console-mcp/plugin/manifest.json`.

## State and environment

State files live under the state dir, `${FIGMA_MAXXING_STATE_DIR:-$HOME/.config/figma-maxxing}`, written `<state-dir>` below. The scripts create it on first run.

| File | What it holds |
|---|---|
| `<state-dir>/figma-files.json` | Alias registry. Starts as an empty JSON object (`{}`); entries live under the `files` key. The user grows it, nothing ships in it. |
| `<state-dir>/figma-bridge-last-url` | One line: the last URL opened. Starts empty. |
| `<state-dir>/figma-reconnect-signal` | Exists only while a plugin trigger is pending for the optional watchdog. |
| `<state-dir>/mcp-direct-<HTTP_PORT>.token` | Exists only while the `scripts/mcp-direct/` daemon runs: its bearer token, mode 0600. |

| Variable | Used by | Effect |
|---|---|---|
| `FIGMA_MAXXING_STATE_DIR` | all scripts | Moves the state dir. |
| `FIGMA_ACCESS_TOKEN` | the MCP server | Figma personal access token for REST backed tools. The same variable figma-console-mcp reads. Never print it, never write it to a file. |
| `FIGMA_FULL_RESET=1` | `figma-bridge-reset.sh` | Quit and relaunch Figma. Without it the script never quits Figma. Set it only after the user said yes to a restart (Step 5). |
| `FIGMA_NO_PLUGIN=1` | `figma-open.sh`, `figma-bridge-reset.sh` | Skip the plugin trigger. |
| `FIGMA_KILL_OTHER_SESSIONS=1` | `figma-bridge-reset.sh` | Also kill the MCP servers of other sessions. Only when solo. |
| `FIGMA_AGENT_PROCESS` | `figma-status.sh`, `figma-bridge-reset.sh` | Process name of the agent that spawns the MCP servers (default `claude`, the Claude Code process). Used to tell this session's server from the others. |
| `FIGMA_BRIDGE_DEFAULT_URL` | `figma-bridge-reset.sh` | Target when no argument is given (wins over the cached URL). |
| `WS_PORT`, `HTTP_PORT`, `FIGMA_MCP_ENTRY` | `scripts/mcp-direct/` | Ports and server entry of the direct client (defaults 9231 and 8791). |

## Connection layers

The figma-console MCP server needs the Bridge plugin running inside Figma Desktop to do writes. Bridge = a WebSocket connection between a `figma-console-mcp` node process (port 9223-9232) and the in-Figma plugin. It breaks for predictable reasons: plugin not yet launched after Figma opens, stale MCP server on the wrong port, Figma in a 0-window state, Accessibility permission missing on the terminal. Recovery is a small set of mechanical steps; this skill executes them and verifies.

The field notes below disagree on how the plugin attaches when several servers are alive. Notes from 2026-05 and 2026-06 saw it serve ONE server at a time (first or lowest port, last trigger wins). Notes from 2026-08 and 2026-09 saw one WebSocket per live server in the range. The two were never reconciled, so never assume which session the plugin is serving: read `figma_get_status`.

## The smart dispatch (state-aware, minimal-action)

The user prompts in natural language. They do not type commands or remember flags. You figure out intent + current state + the minimum action that gets them what they need. Pick the CHEAPEST action that achieves the goal.

### Step 1: probe current state FIRST (always)

Before any action, snapshot state:

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/figma-status.sh"   # local: my MCP port, other sessions, cached URL
```

Then call `figma_get_status` for the bridge view: is the WebSocket up, which file is paired, what port.

### Step 2: extract target file from user input

The user might give:
- **An alias** ("myapp", "ds", "ds-docs"): look it up in `<state-dir>/figma-files.json`.
- **A raw URL** (`https://www.figma.com/design/<fileKey>/...` or `/board/<fileKey>/`): extract the key, look it up in the registry by key.
- **A project name not in the registry** ("open the new-project file"): ask once for the URL.
- **No file mention** ("turn the bridge on", "is it connected?"): use the cached `<state-dir>/figma-bridge-last-url`, or surface "which file?" if the cache is empty.
- **The current paired file** (the user is asking about what is already loaded): use what `figma_get_status` returned.

### Step 3: URL paste auto-register (the project-agnostic part)

If the user pastes a `figma.com/(design|board|file)/<fileKey>` URL and the key is NOT in `<state-dir>/figma-files.json`:

1. Reuse the name in the request or let the script derive a harmless alias from the URL filename; ask only if a collision or ambiguous target matters.
2. Call `bash "${CLAUDE_SKILL_DIR}/scripts/figma-add.sh" "<url>" [optional-alias] [optional-label]`. The script extracts the key, derives the alias from the URL filename if none is given, and sets validated=null. Idempotent.
3. Proceed with the open via `figma-open.sh <alias>`.

If the user gives the URL WITH a clear name, like "open this one from the Acme project: https://...", you can pass the alias as arg 2: `bash "${CLAUDE_SKILL_DIR}/scripts/figma-add.sh" "<url>" acme`. Do not ask the question if the project name is unambiguous in the message.

**Never hardcode a project alias in your dispatch logic.** The registry is a JSON file the user grows. Every project is equal. `<state-dir>/figma-files.json` is the source of truth at any moment: re-read it each turn.

### Step 4: pick the MINIMUM action

Based on state + target:

| State | Target file | Action |
|---|---|---|
| Bridge UP, paired with target | (same) | **No-op.** Report "PASS already on <file>, port <N>". Done. |
| Bridge UP, paired with a different file | switch to <X> | `figma_navigate` if Figma has a tab for <X>, else `figma-open.sh <X>` to open + navigate |
| Bridge DOWN, Figma running with a file open | <X> | osascript menu click (Step T below) if last-opened was <X>, else `figma-open.sh <X>` |
| Bridge DOWN, Figma running but no file | <X> | `figma-open.sh <X>` |
| Bridge DOWN, Figma not running | <X> | `figma-open.sh <X>` (it opens Figma + waits + clicks) |
| Bridge UP but acting flaky / stale data | <X> | `figma_reconnect`, then verify; if still bad, `bash "${CLAUDE_SKILL_DIR}/scripts/figma-bridge-reset.sh" <X>` (gentle by default) |

In the observed v1.40.8 behavior, `figma_reconnect` was informational, not recovery. Do not add a no-op call ritual; inspect current tool behavior and use `figma_get_status` as proof.

### Step 5: verify + escalate (mandatory after any action except no-op)

```
sleep 3
figma_get_status probe:true

connected to target file -> DONE, report briefly: "bridge on <file>, port <N>, latency <ms>"
disconnected -> escalate:
  attempt 1: figma-bridge-reset.sh <alias> (gentle by default, Figma stays open)
  attempt 2: consent-gated full reset: ask first, then FIGMA_FULL_RESET=1
             figma-bridge-reset.sh <alias> (quit + relaunch); on no, go to attempt 3
  attempt 3: consent-gated tight-loop atomic re-attach (multi-session race fix, below)
  attempt 4: manual checklist to user, STOP
```

**Never quit Figma Desktop without asking.** The user may be working in it right now. `figma-bridge-reset.sh` never quits Figma unless `FIGMA_FULL_RESET=1` is set. Any step that quits Figma, today only the full reset of attempt 2, first asks one short question and waits for an explicit yes:

> "The bridge is still down. Can I quit and reopen Figma Desktop? Your open tabs come back after the relaunch."

An already explicit request to quit/restart Figma covers that action; otherwise wait for the one required confirmation. Silence is not consent. Never ask again for the same approved restart.

If a reset prints `WARN: no MCP listener on 9223-9232 after 15s` and `Skipping click`, it stopped before the plugin click on purpose because no server was listening. Typically it just killed this session's server (the only one when you work solo), and that server only respawns on the next MCP call, which cannot happen while the script runs. Do what the script says: call `figma_get_status` once (that respawns the server), run Step T, then verify. This completes the same attempt; it is not a new one.

Four escalations are an upper bound, not a required sequence. Stop after repeated same-class failure unless new state justifies a distinct recovery; do not consume every fallback by routine.

### Deep recovery (rare): references/deep-recovery.md

Tight-loop atomic re-attach (multi-session race), respawn-low (win the attach without killing other sessions) and orphan-MCP port exhaustion live in [references/deep-recovery.md](deep-recovery.md). Load it at escalation attempt 3 (attempt 1 failed and attempt 2 failed or was declined, with other Claude Code sessions alive), or when the ports are exhausted after a long session.

### Critical preconditions

- **Menu click only launches the plugin when a file is open in Figma.** Empty Figma + click = no-op. Always open first.
- **Multi-session safety**: `figma-bridge-reset.sh` defaults to killing ONLY this session's MCP server. Other Claude Code sessions on 9223-9232 are SKIPPED by a process-tree check: a server is this session's when its nearest ancestor named `claude` (or `$FIGMA_AGENT_PROCESS`) is the same process as the script's. Comparing whole ancestor chains is not enough, because every session started from the same terminal app shares the terminal's ancestors. If the script finds no such ancestor it kills nothing and says so. `figma-status.sh` uses the same check for `my_mcp_port`, and splits every other listener in two: `orphans=` (no live owner: the server and its own npx wrapper lead straight to launchd, so the session that started it is gone) and `other_sessions=` (anything else, such as another agent session). Set `FIGMA_KILL_OTHER_SESSIONS=1` to kill all of them (only when solo).
- **The full reset quits Figma.** It is a graceful quit that preserves the open tabs, then a relaunch. The script skips the quit by default and runs it only with `FIGMA_FULL_RESET=1`, which needs the user's yes first (Step 5). Never `killall Figma`: that leaves Figma in a 0-window state where no plugin can attach.
- **Initial connection check**: when the task actually needs the Bridge, reuse a valid current probe or call `figma_get_status`; run the local status script when process/port evidence is needed. Often you can answer "is it connected?" without any further input.
