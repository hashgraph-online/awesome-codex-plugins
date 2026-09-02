---
name: status
description: Read-only shift status — open vs ticked items, parked decisions, snag-log summary, deadline remaining, and any STOP/stall state. Starts no work.
---

Report the shift status for the host-opened project **without starting or changing anything** —
this is read-only.

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
Resolve the installed plugin root as Doctor does: `${CLAUDE_PLUGIN_ROOT}` on Claude Code;
`$PLUGIN_ROOT` on Codex when available, otherwise derive it from this skill's absolute path.

On native Windows, use the PowerShell tool and native paths throughout. Resolve the same values
from `$env:CLAUDE_PROJECT_DIR`, `$env:CODEX_PROJECT_DIR`, and `$env:PLUGIN_ROOT`, with
`[Environment]::CurrentDirectory` as the Codex cwd fallback. Do not route Status through WSL or Git
Bash.

Read `$NS/` and print:

- **Schema** — `$NS/state-version`: missing means legacy `0`, `1` is current. Report a
 newer or malformed marker and stop there; never rewrite it and never run migration from status.
- **Work mode** — `$NS/work-mode` (`repository` or `artifact`; missing means repository) and the
 resolved work target from Doctor's `work mode` / `work target` facts. Artifact mode is a
 persistent folder, not a Git repository. When Doctor warns `work mode is unset; Setup would propose artifact`, say so. Name the confirm action to persist the proposed artifact mode with Setup.
 When Doctor warns `work mode is malformed; treating the site as unusable until Setup rewrites it`, say so.
 When Doctor warns `work target could not be resolved; treating workspace as the code root`, say so.
 In artifact mode, also report Doctor's
 `artifact receipts N` fact — completion receipts under `$NS/receipts/`, not work-target commits.
 When Doctor prints `latest artifact receipt`, name that most recently written file; do not invent a git log.
 When Doctor warns `artifact mode has ticked items but no receipts`, say so — ticked boxes without
 a receipt are not reviewable completion.
 When Doctor warns `artifact receipts path is not a usable directory`, say so — a planted file or symlink is not an empty night. Name the confirm action to replace that path; do not also report empty ticks for it.
 Dated copies from Archive live under `$NS/archive/<YYYY-MM-DD>/receipts/` and do not replace the live files Status reports.
 Missing or empty receipts create no dated receipts folder.
- **Shift** — whether one is running: `$NS/.shift-armed` exists. Without it the punch list
 is a to-do file and nothing is holding it, however many boxes are open — say so plainly and name
 Start as what begins the shift (`/nightshift:start` on Claude Code, or ask Nightshift to start on
 Codex).
- **Items** — ticked vs open counts from `$NS/punch-list.md`, counted **below the `## Items`
 heading only** (open = lines matching a dash + bracketed space; ticked = bracketed x), and the
 title of the current open item. A checkbox above that heading is contract prose, not work, and
 the gate does not count it either. When no open boxes remain, say plainly that the leftover
 Shift contract and Gates still bind the next Hunt or Start cut — Archive files ticked items
 and never resets those sections. If ticked items are still in the list, name Archive.
- **Parked** — the count and one-line titles of entries in `$NS/parking-lot.md`.
- **Staged** — known later items in `$NS/drafting-table.md`, separately from pending timed
 Hunt orders in `$NS/work-orders.md`. Count drafting-table boxes only after the first
 markdown `---` rule so the fenced item-shape example is not a staged draft. Count open
 `- [ ]` boxes in `work-orders.md` as parked Hunt orders. If either count is non-zero and
 the punch list is empty, say Start will offer them.
- **Snag log** — the last few dispositions from `$NS/snag-log.md`, if any.
- **Product evolution** — when `$NS/product-research.md` or
 `$NS/opportunity-map.md` contains more than its template headings, report the most recent
 research entry and the counts of candidate, building, shipped, rejected, and parked
 opportunities. If one opportunity is building, show its title, current phase, exact Next action,
 and Verify remaining. Flag multiple building entries as inconsistent without changing them.
 Do not turn the map into work or change a status.
- **Deadline** — if `$NS/deadline` exists, the time remaining until quitting time (it holds a
 UNIX epoch; compare with `date +%s` on POSIX, or `Get-NSUnixTime` after
 `Import-Module "$NIGHTSHIFT_PLUGIN_ROOT\lib\Nightshift.psm1" -Force` on native
 Windows). Otherwise "no deadline (finite list)".
 When Doctor warns `deadline path is not a usable file`, say so — a planted symlink is not quitting time.
 When Doctor warns `ended path is not a usable file`, say so — a planted symlink is not a clock-out.
- **State** — whether `$NS/STOP` is present (and its reason), and the current
 `$NS/.stall` attempt count if any.
 If `$NS/STOP` is present and the shift is unarmed, the run is paused: Start resumes it, Reset
 drops the deadline, and Purge deletes project Nightshift state. None of those uninstall the plugin.
 When Doctor warns `stall path is not a usable file`, say so — a planted symlink is not a stall count.
 When Doctor warns `session-end path is not a usable file`, say so — a planted symlink is not a clean exit.
 When Doctor warns `shift-pulse path is not a usable file`, say so — a planted symlink is not a liveness pulse.
 When Doctor warns `shift-session path is not a usable file`, say so — a planted symlink is not a recorded session.
 When Doctor warns `watchman pidfile path is not a usable file`, say so — a planted symlink is not a live watchman.
 When Doctor warns `terminal clock-out failed without releasing the shift`, say so and relay whether the recorded conversation can reclaim or is still blocked.
 If a shift is running, the bound session from
 `$NS/.shift-session` (never print the session id). Also report
 `$NS/.shift-lease` as absent, malformed, interactive, or recovered; for a valid lease
 show its host, generation, and whether its recorded process is alive. Obtain session
 process liveness, watchman pid liveness, and lease facts by running
 `"$NIGHTSHIFT_PLUGIN_ROOT/runtime/doctor.sh" --project "$NIGHTSHIFT_WORKSPACE"`
 (on native Windows, `& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\doctor.ps1" -Project "$NIGHTSHIFT_WORKSPACE"`)
 and reading its `recorded pid`, `watchman pid`, and Process lease lines; do not
 reimplement liveness, and do not read the runtime-owned lease file directly. The
 inspector validates it with the shared library and never prints its session scope or ownership
 capability.
- **Watchman** — if `$NS/.watch-reason` exists, print line 1 (the stable code) and the
 same human label Doctor prints (`ns_reason_label` in the shared library; on native
 Windows, `Get-NSReasonLabel` after the same module import). Do not print
 transcript paths, session ids, prompts, or any other payload. Line 2 is optional non-sensitive
 detail only.

Keep it a compact glanceable summary. Do not modify any file, do not begin work.
