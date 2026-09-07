---
name: stop
description: Issue a stop-work order — pause the shift immediately, leaving unfinished items open.
---

Pause the host-opened project immediately so the owner can edit the punch list and resume later.

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
it from the absolute path attached to this skill (`skills/stop/SKILL.md`). Substitute that
absolute path below; never search for the plugin.

On native Windows, use the PowerShell tool and native paths throughout. Resolve the same values
from `$env:CLAUDE_PROJECT_DIR`, `$env:CODEX_PROJECT_DIR`, and `$env:PLUGIN_ROOT`, with
`[Environment]::CurrentDirectory` as the Codex cwd fallback. Do not route Stop through WSL or Git
Bash.

Run the trusted helper. Do not write `$NS/STOP` by hand, do not delete `$NS/.shift-armed`, and do
not kill `$NS/.watchman` yourself — the helper performs the safe teardown:

```bash
"$NIGHTSHIFT_PLUGIN_ROOT/runtime/stop-shift.sh" --project "$NIGHTSHIFT_WORKSPACE"
```

On native Windows:

```powershell
& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\stop-shift.ps1" -Project "$NIGHTSHIFT_WORKSPACE"
```

The helper writes `$NS/STOP` with a reason and UTC timestamp, appends `stopped by owner` to
`$NS/shift-log.md`, kills only a verified live Nightshift watchman, removes `$NS/.shift-armed`,
releases the process lease, and drops runtime ownership markers. Open boxes stay open. The
deadline, punch list, rules, parking lot, work orders, receipts, archives, research, opportunities,
and shift history stay on disk. Hooks remain installed; without `.shift-armed` they are inert. Do
not wait for a later Stop event.

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
