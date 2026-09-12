---
name: reset
description: Drop the runtime markers and deadline without deleting the owner's work or evidence.
license: MIT
---

Reset runtime mechanics for the host-opened project. This recovers from damaged or confusing
runtime state. It does not delete the punch list, rules, history, or `.nightshift/` itself.

Resolve the installed plugin root to an absolute `$NIGHTSHIFT_PLUGIN_ROOT` — `${CLAUDE_PLUGIN_ROOT}`
on Claude Code, `$PLUGIN_ROOT` on Codex when set, otherwise the absolute path this skill was
attached from (`skills/reset/SKILL.md`). Run every command below through
`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns"` — native Windows: `& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\ns.ps1"`
in the PowerShell tool, same verbs — which resolves the host and the workspace; `ns help` lists the
verbs, and `ns bind` prints the six resolved facts (`TASK_ROOT`, `NIGHTSHIFT_WORKSPACE`, `NS`,
`NIGHTSHIFT_PLUGIN_ROOT`, `HOST`, `SOURCE`); `$NS` below is that `NS`. Never a bare relative path: the working
directory persists between calls.

Run the trusted helper. Do not delete runtime files by hand:

```bash
"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" reset-shift
```

The helper first performs Stop (pause and disarm), then removes the current deadline, leftover
`STOP`, and temporary session, recovery, watchman, lease, and mutex markers. It preserves the punch
list and unfinished items, rules, parking lot, work orders, receipts, archives, research,
opportunities, snag log, shift log, and workspace configuration such as work-target and work-mode.
A second Reset is safe. It never deletes `.nightshift/`.

Report that the deadline was removed and that durable files remain. The plugin install is
untouched. Start after Reset writes a new deadline only when Hunt, a work order, or the owner
supplies one — it does not invent a time budget.
