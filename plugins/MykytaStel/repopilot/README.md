# RepoPilot plugin

Snapshots the repository when a coding-agent session starts, and reviews
everything the session changed before the agent finishes. If the agent
skipped, focused, removed, or weakened a test, added a lint, type, coverage,
or RepoPilot suppression, relaxed a CI gate, removed an auth check, or let
request input reach SQL or a shell, the stop is blocked and the agent gets the
list with file and line. It must restore each check or explain why the change
is intended. Each signal is raised once per session. Other sensitive changes,
such as a dependency bump or an edited workflow, stay in the review report and
do not stop the agent.

The hooks list `.repopilot/snapshot.json` and `.repopilot/cache/` in the
repository's `.git/info/exclude`, so session state never shows up in
`git status`.

The same directory installs in Claude Code and Codex. It also registers the
local RepoPilot MCP server and a `review-session` skill.

## Requirements

The `repopilot` CLI, version 0.24 or newer, on `PATH`:
`npm install -g repopilot` or `cargo install repopilot`. Outside a Git
repository the hooks do nothing. Inside Git, a missing/old CLI or a failed
snapshot/review emits a diagnostic instead of silently implying a clean review.
Check `command -v repopilot` and `repopilot --version` in the terminal launching
your agent. The current stable release is 0.25.0; update an older installation
before starting a new session.

The scripts require a POSIX `sh`, Git, and standard shell utilities. They are
tested on Unix; native Windows CLI/MCP smoke tests do not verify shell hooks.
The `.repopilot` state directory must be writable; after a permission error,
restore write permission and start a new session to establish its baseline.
Keep one agent session per working tree; parallel sessions need separate Git
worktrees because each tree has one snapshot baseline.

## Install

Claude Code:

```text
/plugin marketplace add MykytaStel/repopilot
/plugin install repopilot@repopilot
```

Codex, then trust the two hooks once in `/hooks`:

```bash
codex plugin marketplace add MykytaStel/repopilot
codex plugin add repopilot@repopilot
```

## What runs

| Hook | Script | What it does |
|---|---|---|
| `SessionStart` | `scripts/snapshot.sh` | `repopilot snapshot` at the repository root |
| `Stop` | `scripts/guard.sh` | `repopilot review --since-snapshot --format json`; exit 2 with weakened checks not raised earlier in the session |

Everything runs locally. RepoPilot sends no source code anywhere and calls
no language model. The agent receives hook feedback and MCP results under its
own data-handling settings. To read the full report yourself, run
`repopilot review --since-snapshot --detail full` after the session's edits.

More: [Guard your agent runs](https://github.com/MykytaStel/repopilot/blob/main/docs/agent-guardrail.md).
