---
name: init
description: "Initialize KERNEL links and AgentDB in a confirmed Vaults directory."
user-invocable: true
allowed-tools: Bash
disable-model-invocation: true
kernel:
  kind: operator
  version: 1
  side_effects: writes_repo
  confirmation: always
---

# KERNEL init

Explicit, once-per-machine setup. This skill never moves or replaces the whole
`~/.claude` directory.

## Requirements

Git, SQLite 3, `jq`, Python 3, and Bash. Install the plugin first with the exact ID:

```text
/plugin marketplace add ariaxhan/kernel-claude
/plugin install kernel@kernel-marketplace
/reload-plugins
```

## Detection and confirmation

Locate the runtime selector at
`$HOME/.claude/plugins/cache/kernel-marketplace/kernel/current`, source its
`hooks/scripts/common.sh`, and call `kernel_validate_runtime_root` on the selected
root. Stop if validation fails.

Call `detect_vaults`. Its order is: an existing valid `KERNEL_VAULTS`,
`$HOME/Documents/Vaults`, `$HOME/Vaults`, `$HOME/Downloads/Vaults`, then the
reported `$HOME/Documents/Vaults` fallback.

Before writing, show the exact Vaults path and ask:

> Set up KERNEL in this Vaults directory?

Continue only after confirmation. A different path must be exported as
`KERNEL_VAULTS` and detected again.

## Writes

After confirmation, create only these directories when absent:

```text
$VAULTS/_meta/agentdb
$VAULTS/_meta/research
$VAULTS/_meta/plans
$VAULTS/_meta/handoffs
$VAULTS/_meta/checkpoints
$VAULTS/_meta/retrospectives
$VAULTS/_meta/agents
$VAULTS/_meta/logs
$VAULTS/.claude/kernel
$VAULTS/.local/bin
```

Call `kernel_update_current`, then use `kernel_init_host_link` for exactly:

```text
$VAULTS/.local/bin/agentdb          -> $CACHE/current/orchestration/agentdb/agentdb
$VAULTS/.claude/kernel/orchestration -> $CACHE/current/orchestration
$VAULTS/.claude/kernel/hooks         -> $CACHE/current/hooks
```

Missing links may be created. Correct links are unchanged. Recognizable numbered
KERNEL links may be repaired. A regular file, directory, malformed link, or unrelated
link is preserved and stops setup with an actionable message. Never force-replace links.

Initialize the database through the shared helper, which pins AgentDB to the selected
Vaults even when init was invoked from another directory:

```bash
kernel_init_agentdb "$VAULTS" "$CACHE"
```

Do not edit a shell startup file automatically. If `$VAULTS/.local/bin` is not on
`PATH`, print this line for the user to add to their chosen shell configuration:

```bash
export PATH="${KERNEL_VAULTS:-$HOME/Documents/Vaults}/.local/bin:$PATH"
```

## Verify

```bash
"$VAULTS/.local/bin/agentdb" status
readlink "$HOME/.claude/plugins/cache/kernel-marketplace/kernel/current"
readlink "$VAULTS/.local/bin/agentdb"
```

Report every directory and link created. Existing AgentDB data, manifests, receipts,
project configuration, and unrelated files are not rewritten.

## Legacy `~/.claude` consolidation

This is not part of init. Moving an existing `~/.claude` can affect plugins,
credentials, settings, and other tools. If a user explicitly requests consolidation,
make a dated backup, show a complete move plan and rollback command, and ask for a
separate confirmation before any move. There is no one-line migration.

## Recovery

- Missing plugin: install `kernel@kernel-marketplace`, then reload.
- Wrong Vaults: export `KERNEL_VAULTS` to the existing root and rerun init.
- Unsafe host path: inspect the named object; KERNEL will not overwrite it.
- Intentional runtime rollback: run `scripts/select-runtime.sh /path/to/runtime` from
  a trusted KERNEL checkout. It selects code only; it does not convert state formats.
