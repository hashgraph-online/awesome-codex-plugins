---
name: archive
description: File the finished part of the run state into a dated archive — shipped items, research, opportunities, the rotated journal, and handled snags. The live files stay lean; the facts stay on disk.
---

Archive the finished paperwork for the host-opened project. This files records — it never does
shift work, never ticks a box, never touches the contract.

**State map:** `punch-list.md` → owner-approved work active in this shift;
`drafting-table.md` → known work staged for a later shift; `parking-lot.md` → unresolved owner
decisions plus the default chosen so work continues; `work-orders.md` → timed catalog work composed
only through Hunt. Archive each by its own lifecycle; never reclassify one as another.

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
it from the absolute path attached to this skill (`skills/archive/SKILL.md`). Substitute that
absolute path below; never search for the plugin.

On native Windows, use the PowerShell tool and native paths throughout. Resolve the same values
from `$env:CLAUDE_PROJECT_DIR`, `$env:CODEX_PROJECT_DIR`, and `$env:PLUGIN_ROOT`, with
`[Environment]::CurrentDirectory` as the Codex cwd fallback. Do not route Archive through WSL or Git
Bash.

Read `$NS/state-version` first. Legacy (missing) and current (`1`) may be archived.
A newer or malformed marker fails closed — file nothing, rewrite nothing, and never migrate.
`state-version` itself stays live; it is not an archive record.

In artifact mode the work target is a persistent folder, not a Git repository. File the same
Nightshift records; do not require a work-target commit that cannot exist. Copy live receipts with
`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/archive-receipts.sh" --project "$NIGHTSHIFT_WORKSPACE"`
(native Windows: `& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\archive-receipts.ps1" -Project "$NIGHTSHIFT_WORKSPACE"`).
The helper writes `$NS/archive/<YYYY-MM-DD>/receipts/` when those files exist, and leave the live copies in
place so stall progress still sees them. Missing or empty receipts create no dated receipts folder.
A receipts path that is not a usable directory is a refuse, not an empty skip.
Never delete live receipts as part of Archive.

## Where it goes

Everything lands in `$NS/archive/<YYYY-MM-DD>/` — today's date (`date +%Y-%m-%d` on POSIX, or
`Get-Date -Format yyyy-MM-dd` on native Windows), one folder per archive
run (create parents; re-running on the same day appends to that day's files).

## What moves, what stays

- **Punch list → `shipped.md`.** Move every ticked `- [x]` line under `## Items` in
 `$NS/punch-list.md` into the
 archive's `shipped.md` under a `## Shipped <date>` heading — that file reads as the plain
 record of what actually landed. Open `- [ ]` items and everything above `## Items` (the
 contract, the gates) stay exactly where they are. When that move leaves zero open boxes,
 append one reminder under `## Notes` (create the heading below `## Items` if it is missing):
 leftover Shift contract and Gates still bind the next Hunt or Start cut; review them before
 composing a new campaign; Archive does not reset them. Skip the note when open work remains,
 when the same sentence is already present, or if adding it would require an open checkbox.
 Never write `- [ ]` here and never edit above `## Items`.
- **Shift log → the archive, whole.** Move `$NS/shift-log.md` into
 the folder and start a fresh one
 with the same one-line header. The journal is mechanical; its lines belong to the dates they
 happened.
- **Snag log — only what's handled.** Move entries that carry a disposition (fixed, ignored,
 answered) from `$NS/snag-log.md` into the archive's `snag-log.md`.
 Entries still awaiting the owner stay live: an
 open question is not history yet.
- **Parking lot — only what's answered.** Same rule on
 `$NS/parking-lot.md`: answered entries move, unanswered stay.
- **Work orders — only what's spent.** Pending orders are open boxes; they stay.
 A `## Work order` heading with no remaining box is leftover shell from a cut — delete it,
 do not file it. File only an order whose box was ticked in place.
- **Product research → the archive after its shift.** When no shift is active, append the completed
 entries from `$NS/product-research.md` to the archive's `product-research.md`, preserving their dates,
 sources, evidence, and conclusions; then restore the live file from the shipped template. During
 an active shift, leave all research live. Research is evidence, so never summarize it away or
 strip its source URLs while filing it.
- **Opportunity map — only terminal outcomes.** Move `shipped` and `rejected` entries from
 `$NS/opportunity-map.md` into the archive's `opportunity-map.md`, preserving their evidence links and
 reasons. Keep `candidate`, `building`, and `parked` entries live: they can still affect a future
 cycle or need the owner. Restore the shipped headings if moving the last terminal entry leaves an
 empty section. Never renumber or silently change a status during archive.

## Timing

Best between shifts. During an active shift with open boxes, say so and ask before moving
anything — the ticked lines are the night's scoreboard, and the owner may want the morning
review to see them in place. If the receipts repo exists (`$NS/.git`) **and**
`receiptsAutoCommit` is true in `$NS/rules.json` (or `NIGHTSHIFT_RECEIPTS_AUTO_COMMIT=true`),
commit after archiving so the move itself has history. Default is false — leave the tree dirty
for the owner. When committing, use the same headless identity the clock-out gate uses, and
turn signing off so a global `commit.gpgsign=true` cannot stall:

```bash
git -C "$NS" add -A
git -C "$NS" -c user.name=nightshift -c user.email=nightshift@localhost \
  -c commit.gpgsign=false commit -q -m "archive"
```

On native Windows the same `git -C` flags work in PowerShell. Nothing to commit is success.
Never add a remote, never push.

## Retention

After filing, preview generated history that the owner has opted in to prune. Run:

```bash
"$NIGHTSHIFT_PLUGIN_ROOT/runtime/retain-history.sh" --project "$NIGHTSHIFT_WORKSPACE"
```

On native Windows:

```powershell
& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\retain-history.ps1" -Project "$NIGHTSHIFT_WORKSPACE"
```

Print that preview verbatim — every eligible path, its age, and the governing rule
(`retention.runtimeLogDays` or `retention.archiveDays`). Both default to `0` (keep forever);
a preview that lists nothing is success, not a prompt to invent a number.

Deletion is a second, explicit step. If the preview lists paths and the owner confirms in this
interactive session, run the same command with `--apply` (POSIX) or `-Apply` (native Windows). If the shift is armed, the owner
does not confirm, or either rule is `0`, stop after the preview. `--apply`/`-Apply` deletes only the
allowlisted runtime log (`scheduled.log`) and dated `archive/YYYY-MM-DD/` directories that
are old enough, resolved under `$NS/`, not symlinks, and free of still-open work.

Never call `retain-history.sh` or `retain-history.ps1` from start, hooks, status, Doctor, or recovery. Never call `archive-receipts.sh` or `archive-receipts.ps1` from start, hooks, status, Doctor, or recovery. Never delete
the live punch list, drafting table, parking lot, rules, current shift files, or owner-authored
files.

## Summarize

Print the archive path and one line per file moved or trimmed — and what stayed live and why.
If a retention preview ran, include whether anything was eligible and whether the owner
confirmed a delete.
