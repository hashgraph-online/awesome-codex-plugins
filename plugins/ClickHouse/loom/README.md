# Loom for Codex — ambient capture, memory primer, code shunt

The Codex build of Loom's coding-agent plugin. It is the [Claude Code
plugin](https://github.com/ClickHouse/loom/tree/main/integrations/claude-code-plugin) with different wiring: the same
hook scripts and seven skills, byte for byte (kept in sync by
`python scripts/codegen/agent_plugin_sync.py`, checked in CI), driven by Codex's
lifecycle hooks instead of Claude Code's.

What you get once it is installed:

- **A memory primer at session start** — `context.pack`, budgeted (~1,200
  tokens): pinned facts, your profile, the decisions and conventions that
  match this repository, the working-memory note of the last session, and
  the code map when the repository is loom-indexed. Off with
  `LOOM_INJECT_CONTEXT=false`.
- **Ambient capture** — every tool call, every edit, every failed command
  becomes an episodic observation; the session's turns go to the
  conversation plane and, at session end, to `memory.set_from_messages` so
  the server extracts the durable facts. No model call in the hooks.
- **loom-code-shunt** — in a loom-indexed repository, a `cat` of a whole file
  or an `rg` over the tree is denied with the `code.*` op to call instead.
- **Blast radius, file context, test gate, working memory, run ledger** — as
  in the Claude Code plugin; the README there documents every knob.

## Data handling

The hooks send prompts, tool inputs and outputs, file paths, repository identity,
session summaries and outlines of uncommitted diffs to the configured Loom server.
The server can keep conversation turns, extract memories from the session's last
200 turns, and pass text to the providers its operator configures. Users whose
grants allow them to read a stored row, and the server's operator, can read it.
Client-side redaction of common credentials is best effort; MCP tool arguments
and manually saved session briefs bypass it.

The plugin runs Node.js, Git and grep locally, keeps credentials and state under
`~/.loom/`, and writes temporary state that can contain prompt and reply text.
The test gate chooses a Python interpreter without starting it. At session start
the plugin tries to remove most temporary state untouched for a day; it can
remain longer, especially when no new session starts. Queued writes and the
shunt log have different retention rules. The `loom-status` skill can install Node.js after
you agree, and `improve-loom-for-my-repo` searches public issues and asks before
filing a report. The full
[data-handling disclosure](https://loom.clickhouse.com/docs/features/integrations/claude-code/#data-handling)
lists what each hook sends, local commands, retention, outside services and off
switches. Codex's capture differences are listed below; it does not run the
duplicate-entry check of `~/.claude.json`.

## Install

```bash
codex plugin marketplace add ClickHouse/loom        # or a path to a local clone
codex plugin add loom@loom
```

The plugin brings its own MCP entry (`.mcp.json`): the server URL with
`?toolset=core,coding,tracker,tasks`, authenticated by the header helper
`bin/loom-mcp-headers.mjs`. Do not run `codex mcp add loom` on top: an entry
with the same name replaces the plugin's, and one under another name lists
every tool twice.

The helper and the hooks read the token from `LOOM_API_KEY`; then, for an
agent (`LOOM_CLIENT_ID` with `LOOM_WORKLOAD_TOKEN` or
`LOOM_WORKLOAD_TOKEN_FILE`), the token its workload token is exchanged for,
and nothing else; otherwise `~/.loom/config.json`, then `~/.loom/token`. Org
and namespace come from the token's own claims. Codex plugins have no install-time options, so the
server URL is fixed in `.mcp.json` and `plugin-defaults.json`
(`http://localhost:7777`); for another server, see
[Codex setup](https://loom.clickhouse.com/docs/features/integrations/codex/) (a `[mcp_servers.loom]` override in
`~/.codex/config.toml`, or `loom install --client codex`).

## What differs from the Claude Code build

| Codex                                                                                                          | Effect                                                                                                                                                                                                                                                   |
| -------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| No `Read` / `Grep` tools; files are read and searched through the shell tool, whose input may be an argv array | The shunt watches the shell tool only (`cat`, `rg`, `grep`); `commandText` reads a string or an argv array.                                                                                                                                              |
| Edits go through `apply_patch` (the input is the patch text)                                                   | File context and blast radius read the target path out of the patch (`*** Update File:` / `*** Add File:`).                                                                                                                                              |
| `transcript_path` may be null, or point at a file in Codex's own shape                                         | The hooks keep a **turn journal**: `loom-run` records each prompt, `loom-conversation` records each reply from `last_assistant_message` at `Stop`; the working-memory note, the run's final text, the conversation plane and the session memory read it. |
| No per-turn token counters in a payload                                                                        | `loom-usage` is not wired; cost rows come from the server's own accounting.                                                                                                                                                                              |
| `SessionEnd` hooks get one second                                                                              | Only fire-and-forget scripts run there; the conversation hook does its work at `Stop`.                                                                                                                                                                   |
| Hooks run through `$SHELL -lc`, and through `cmd.exe` on Windows                                               | Each hook starts through `bin/loom-node`, which finds Node 18+ when PATH has none; on Windows `commandWindows` runs `node` from the system PATH; it needs Codex 0.131 or later, as an earlier build runs the `sh` command through `cmd.exe` and fails.   |
| Run ids                                                                                                        | `cx-<session_id>` (Claude Code: `cc-<session_id>`); session memories carry `source:codex`; hook-written rows default to agent `codex`.                                                                                                                   |

Everything else — the environment knobs, the safety model (fire-and-forget,
hard-bounded, fail-open), the project scoping, the skills — is documented
once, in the [Claude Code plugin README](https://github.com/ClickHouse/loom/tree/main/integrations/claude-code-plugin).

## Skills

`skills/` carries the same seven skills as the Claude Code plugin:
`loom-memory` (what to write and where, how to read what comes back, the
end-of-task review), `loom-code` (route-then-read on an indexed repository),
`loom-mentor` (which plane and op a hint points at), `loom-optimize` (rework
a namespace from its audit with redirects), `loom-session` (save or resume a
session brief, on request only), `loom-status` (why Loom is quiet) and
`improve-loom-for-my-repo`. Codex loads them from the plugin; invoke one by
name (`$loom-memory`) or let the description trigger it.

## Files

- `.codex-plugin/plugin.json` — the manifest (version stated once, equal to
  the Claude Code plugin's; a test checks).
- `hooks/hooks.json` — the Codex wiring. Each command names the client as
  the script's third argument (`… PostToolUse codex`).
- `.mcp.json`, `plugin-defaults.json` — the bundled MCP entry and the hooks'
  default server; host-specific, not generated.
- `hooks/*.mjs`, `bin/*.mjs`, `lib/*.mjs`, `skills/**`, `assets/` — **generated copies**. Edit the
  originals under `integrations/claude-code-plugin/` and run
  `python scripts/codegen/agent_plugin_sync.py`.
