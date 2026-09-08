---
name: stop
description: Issue a stop-work order: pause the shift now, leaving unfinished items open.
license: MIT
---

Pause the host-opened project immediately so the owner can edit the punch list and resume later.

Resolve the installed plugin root to an absolute `$NIGHTSHIFT_PLUGIN_ROOT` — `${CLAUDE_PLUGIN_ROOT}`
on Claude Code, `$PLUGIN_ROOT` on Codex when set, otherwise the absolute path this skill was
attached from (`skills/stop/SKILL.md`). Run every command below through
`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns"` — native Windows: `& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\ns.ps1"`
in the PowerShell tool, same verbs — which resolves the host and the workspace; `ns help` lists the
verbs, and `ns bind` prints the six resolved facts (`TASK_ROOT`, `NIGHTSHIFT_WORKSPACE`, `NS`,
`NIGHTSHIFT_PLUGIN_ROOT`, `HOST`, `SOURCE`); `$NS` below is that `NS`. Never a bare relative path: the working
directory persists between calls.

Run the trusted helper. Do not write `$NS/STOP` by hand, do not delete `$NS/.shift-armed`, and do
not kill `$NS/.watchman` yourself — the helper performs the safe teardown:

```bash
"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" stop-shift
```

The helper writes `$NS/STOP` with a reason and UTC timestamp, appends `stopped by owner` to
`$NS/shift-log.md`, and kills only a verified live Nightshift watchman. It does not remove
`$NS/.shift-armed`. Open boxes stay open as the record. Hardhat stays until clock-out writes
`$NS/.ended`. Reset is the manual escape. The deadline, punch list, rules, parking lot, work
orders, receipts, archives, research, opportunities, and shift history stay on disk. Do not wait
for a later Stop event to write the marker — the helper writes it now.

Report the helper's `open-items` count and that the deadline was preserved. A second Stop is safe.

Resume later with Start (`/nightshift:start` on Claude Code, or ask Nightshift to start on Codex).
Start clears the pause markers and begins a new ownership lease. A future preserved deadline
remains the deadline. An expired preserved deadline is not silently renewed: write a new UNIX epoch
to `$NS/deadline`, or run Reset then Start.

This works from the bound conversation, from a helper conversation, and when a failed clock-out left a recovery nonce that still fences the recorded conversation.

**Panic form (does not disarm immediately):** from any POSIX terminal,
`touch "$NS/STOP"`. In native Windows PowerShell, run
`New-Item -ItemType File -Force "$NS\STOP"`. That marker is honored at the next Stop event or
watchman wake. Prefer the helper when the model is stuck — it does not wait for that event.
