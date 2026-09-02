---
name: doctor
description: Read-only Nightshift diagnosis — workspace, rules, markers, session, process lease, watchman, deadline, and classified next actions. Use when a shift looks wrong, recovery is unclear, or the owner asks what Nightshift sees. Never repairs by being invoked.
---

Diagnose the host-opened project **without changing anything**. Doctor is deeper than status: it
explains what Nightshift resolved and which failures that implies. It does not arm, stop, revive,
rewrite, or delete.

**State map:** `punch-list.md` → owner-approved work active in this shift;
`drafting-table.md` → known work staged for a later shift; `parking-lot.md` → unresolved owner
decisions plus the default chosen so work continues; `work-orders.md` → timed catalog work composed
only through Hunt. Report these as different categories; do not merge or move them.

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
Never search or guess.
The shell's working directory persists between Bash calls, so never use a bare path.

Resolve the installed plugin root to an absolute `$NIGHTSHIFT_PLUGIN_ROOT`: use
`${CLAUDE_PLUGIN_ROOT}` on Claude Code; on Codex use `$PLUGIN_ROOT` when available, otherwise derive
it from the absolute path attached to this skill (`skills/doctor/SKILL.md`). Substitute that
absolute path in every command below; never search for the plugin.

On native Windows, use the PowerShell tool and native paths throughout. Resolve the same values
from `$env:CLAUDE_PROJECT_DIR`, `$env:CODEX_PROJECT_DIR`, and `$env:PLUGIN_ROOT`, with
`[Environment]::CurrentDirectory` as the Codex cwd fallback. Do not route Doctor through WSL or Git
Bash.

Report `$NS/state-version` as current (`1`), legacy (missing = `0`), malformed, or future.
Offer `"$NIGHTSHIFT_PLUGIN_ROOT/runtime/migrate-state.sh" --project "$NIGHTSHIFT_WORKSPACE"` as `[confirm]` only for unarmed legacy
workspaces; never run it because Doctor was invoked. On native Windows, offer
`& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\migrate-state.ps1" -Project "$NIGHTSHIFT_WORKSPACE"`
instead. Future versions are `[blocked]` — never
downgrade.

Report `$NS/deadline` as `deadline=none` when the file is missing, remaining seconds when it is a
UNIX epoch, or a warning when it is not integer seconds. When the deadline path is a symlink, Doctor warns `deadline path is not a usable file` and does not report remaining time. When `.ended` is a symlink, Doctor warns `ended path is not a usable file` and does not report that the gate clocked the shift out. When `.stall` is a symlink, Doctor warns `stall path is not a usable file` and does not report a stall count. When `.session-end` is a symlink, Doctor warns `session-end path is not a usable file` and does not report a clean session-end marker. When `.shift-pulse` is a symlink, Doctor warns `shift-pulse path is not a usable file` and does not report a shift-pulse marker. When `.shift-session` is a symlink, Doctor warns `shift-session path is not a usable file` and does not report a recorded session. When `.watchman` is a symlink, Doctor warns `watchman pidfile path is not a usable file` and does not report a watchman pid. When Doctor warns `terminal clock-out failed without releasing the shift`, say whether the recorded conversation can operate or whether a recovery worker still holds the lease; do not tell the owner to reopen a conversation that would stay blocked. Watchmen compare epoch seconds; do not
rewrite the file.

## 1. Run the inspector

```bash
"$NIGHTSHIFT_PLUGIN_ROOT/runtime/doctor.sh" --project "$NIGHTSHIFT_WORKSPACE"
```

On native Windows:

```powershell
& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\doctor.ps1" -Project "$NIGHTSHIFT_WORKSPACE"
```

Print its report verbatim. Do not summarise away Facts, Warnings, or Actions. The script uses the
same workspace, work-mode, and work-target libraries as the hooks. The report's `work mode`
fact is `repository` or `artifact`. When `$NS/work-mode` is missing and Setup would propose artifact, Doctor warns `work mode is unset; Setup would propose artifact` and offers `persist the proposed artifact mode with Setup; Doctor does not write work-mode`. When work-mode is unreadable, Doctor warns `work mode is malformed; treating the site as unusable until Setup rewrites it`. When the work target cannot be resolved, Doctor warns `work target could not be resolved; treating workspace as the code root`. In artifact mode the report also includes
`artifact receipts N` for files under `$NS/receipts/`. When at least one receipt exists, Doctor
also reports `latest artifact receipt` with the filename only of the most recently written receipt (no directory path). When ticked
items exist and the receipts directory is empty, Doctor warns
`artifact mode has ticked items but no receipts`.
When `$NS/receipts` exists but is not a usable directory, Doctor warns `artifact receipts path is not a usable directory` and offers `replace the unusable receipts path with a real directory so write-receipt can land; Doctor does not rewrite it`. Doctor does not also warn empty ticks for that path.
Dated copies from Archive live under `$NS/archive/<YYYY-MM-DD>/receipts/` and do not replace the live files Doctor counts.
Missing or empty receipts create no dated receipts folder.

## 2. Classify actions — do not execute them

The report tags every suggestion:

- `[safe]` — mechanical leftover with no live session (for example a stale watchman pid file whose
 process is already gone). Still do **not** apply it because Doctor was invoked; offer it.
- `[confirm]` — owner decision (broken link, missing setup, leftover STOP while they still want
 the night). During an **unattended active shift** (`$NS/.shift-armed` and open boxes), report that
 the recommendation should be parked with the default "leave in place until morning", but do not
 write the parking lot or ask—the Doctor invocation remains byte-identical.
- `[blocked]` — Nightshift cannot fix this here (non-resumable Codex id, malformed process lease,
 missing host binary, unverified wedge). Say so. Never guess a session id or print/edit a lease
 capability. For a stuck conversation or a fenced recorded session, name
 `"$NIGHTSHIFT_PLUGIN_ROOT/runtime/stop-shift.sh" --project "$NIGHTSHIFT_WORKSPACE"`
 (native Windows: `stop-shift.ps1 -Project`) — that pauses immediately without waiting for a Stop
 event. Do not run it from Doctor.

Invoking Doctor alone must leave the tree byte-identical. Never perform a repair merely because
Doctor was invoked.

## 3. After the report

Offer the classified repairs after the report. If the owner explicitly asks to apply a `[safe]`
leftover while no shift is armed, they are no longer in Doctor — follow stop/start/setup as those
skills specify. Until that explicit ask, change nothing. During an unattended shift, the offer is
informational only: continue the active work without asking or writing state.

Doctor may list local rule profiles and show a preview. Applying a profile is a separate
owner action
(`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/apply-profile.sh" --project "$NIGHTSHIFT_WORKSPACE"` on POSIX,
or `& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\apply-profile.ps1" -Project "$NIGHTSHIFT_WORKSPACE"`
on native Windows);
invoking Doctor never writes `rules.json`.

If the owner then explicitly asks to **Export support bundle**, they are no longer in Doctor.
Run
`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/export-support.sh" --project "$NIGHTSHIFT_WORKSPACE"`
on POSIX, or
`& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\export-support.ps1" -Project "$NIGHTSHIFT_WORKSPACE"`
on native Windows.
Print its path, included sections, and omitted categories. Do not upload, attach, transmit, or open
the file. Invoking Doctor alone must not create `$NS/support/`.
