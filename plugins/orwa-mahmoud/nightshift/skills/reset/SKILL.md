---
name: reset
description: Abandon current Nightshift runtime mechanics without deleting the owner's work or evidence.
---

Reset runtime mechanics for the host-opened project. This recovers from damaged or confusing
runtime state. It does not delete the punch list, rules, history, or `.nightshift/` itself.

Resolve the host-opened project folder to an absolute `$TASK_ROOT`: use `${CLAUDE_PROJECT_DIR}` on
Claude Code; on Codex honor Nightshift's `${CODEX_PROJECT_DIR}` recovery override when present,
otherwise capture `pwd -P` before any other shell call. Resolve `$TASK_ROOT/.nightshift-link` when
present and call the validated absolute target `$NIGHTSHIFT_WORKSPACE`; otherwise set
`NIGHTSHIFT_WORKSPACE="$TASK_ROOT"`.

Bind the Nightshift directory once: `NS="$NIGHTSHIFT_WORKSPACE/.nightshift"`. On native Windows,
`$NS = Join-Path $NIGHTSHIFT_WORKSPACE '.nightshift'`. After this bind, Nightshift files are
`$NS/<name>` for every read, write, and shell command. Catalog and owner-facing prose may use the
short names (`punch-list.md`, `parking-lot.md`, `STOP`). Never re-resolve. Helpers that take
`--project` or `-Project` still receive `"$NIGHTSHIFT_WORKSPACE"`.
Never search or guess. The shell's working directory persists
between Bash calls, so never use a bare path.

Resolve the installed plugin root to an absolute `$NIGHTSHIFT_PLUGIN_ROOT`: use
`${CLAUDE_PLUGIN_ROOT}` on Claude Code; on Codex use `$PLUGIN_ROOT` when available, otherwise derive
it from the absolute path attached to this skill (`skills/reset/SKILL.md`). Substitute that
absolute path below; never search for the plugin.

On native Windows, use the PowerShell tool and native paths throughout. Resolve the same values
from `$env:CLAUDE_PROJECT_DIR`, `$env:CODEX_PROJECT_DIR`, and `$env:PLUGIN_ROOT`, with
`[Environment]::CurrentDirectory` as the Codex cwd fallback. Do not route Reset through WSL or Git
Bash.

Run the trusted helper. Do not delete runtime files by hand:

```bash
"$NIGHTSHIFT_PLUGIN_ROOT/runtime/reset-shift.sh" --project "$NIGHTSHIFT_WORKSPACE"
```

On native Windows:

```powershell
& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\reset-shift.ps1" -Project "$NIGHTSHIFT_WORKSPACE"
```

The helper first performs Stop (pause and disarm), then removes the current deadline, leftover
`STOP`, and temporary session, recovery, watchman, lease, and mutex markers. It preserves the punch
list and unfinished items, rules, parking lot, work orders, receipts, archives, research,
opportunities, snag log, shift log, and workspace configuration such as work-target and work-mode.
A second Reset is safe. It never deletes `.nightshift/`.

Report that the deadline was removed and that durable files remain. The plugin install is
untouched. Start after Reset writes a new deadline only when Hunt, a work order, or the owner
supplies one — it does not invent a time budget.
