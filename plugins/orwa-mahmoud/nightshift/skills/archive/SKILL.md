---
name: archive
description: File finished shift state into a dated archive so the live files stay lean.
license: MIT
---

Archive the finished paperwork for the host-opened project. This files records — it never does
shift work, never ticks a box, never touches the contract.

The four state files and what each holds are in
`$NIGHTSHIFT_PLUGIN_ROOT/skills/nightshift/references/shift/state-map.md`. Archive each by its own lifecycle; never reclassify one as another.

Resolve the installed plugin root to an absolute `$NIGHTSHIFT_PLUGIN_ROOT` — `${CLAUDE_PLUGIN_ROOT}`
on Claude Code, `$PLUGIN_ROOT` on Codex when set, otherwise the absolute path this skill was
attached from (`skills/archive/SKILL.md`). Run every command below through
`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns"` — native Windows: `& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\ns.ps1"`
in the PowerShell tool, same verbs — which resolves the host and the workspace; `ns help` lists the
verbs, and `ns bind` prints the six resolved facts (`TASK_ROOT`, `NIGHTSHIFT_WORKSPACE`, `NS`,
`NIGHTSHIFT_PLUGIN_ROOT`, `HOST`, `SOURCE`); `$NS` below is that `NS`. Never a bare relative path: the working
directory persists between calls.

Read `$NS/state-version` first. Legacy (missing) and current (`1`) may be archived.
A newer or malformed marker fails closed — file nothing, rewrite nothing, and never migrate.
`state-version` itself stays live; it is not an archive record.

In artifact mode the work target is a persistent folder, not a Git repository. File the same
Nightshift records; do not require a work-target commit that cannot exist. Copy live receipts with
`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" archive-receipts`.
Missing or empty receipts create no dated receipts folder.
A receipts path that is not a usable directory is a refuse, not an empty skip.

If `$NS/.pending-filing` exists, a shift asked for filing at clock-out. It carries `date=` and
`shiftId=` lines naming that shift — use them — and an `asked=1` line once the gate has held the
session to ask for it. Delete the marker once filing is done, and only then. Nothing else about it
is special: file the same way you would on any explicit Archive.

`$NS/.ended` names the shift that finished and where it files, in `shiftId=`, `archiveRoot=` and
`archiveLayout=` lines. Those are what a later Archive follows: clock-out has already archived
the policy that carried them.

**Filing is a copy. Removing a live record is a separate decision, and it is yours to make.**
The helper retires only what you name, and only once the shift has ended: `--retire` with one
record name, repeated once per record on POSIX; on native Windows, `-Retire` takes the names as a
single comma-separated list. Without a name it copies
and removes nothing, which is the right answer whenever you are unsure.

Before naming anything, read `$NS/punch-list.md` and the records themselves and decide which
belong to work that is finished with. A shift can end with items still open — `STOP` and the
deadline both do that — so a terminal marker says nothing about any particular record. Keep a
record live when an open item, an unanswered parking decision or work carried into the next shift
still needs it, and when you cannot tell who owns it. Rejected work is filed with its rejection,
never erased. A name the helper did not file is refused and told back to you.

## Where it goes

Everything lands under the archive root, which is `archive.root` in the resolved policy, in
`<YYYY-MM-DD>/` or `shift-<id>/` according to `archive.layout`. Left alone those give the default
`$NS/archive/<YYYY-MM-DD>/`, and receipts land in `archive/<YYYY-MM-DD>/receipts/` under it.
Today's date is `date +%Y-%m-%d` on POSIX, or `Get-Date -Format yyyy-MM-dd` on native Windows.
One folder per archive run; create parents, and re-running on the same day appends to that day's
files.

**The receipts keep working from where they land.** The helper repoints their links: a record that
travelled with them stays a sibling, a record that stayed live is reached back through the archive.
That rewriting changes bytes, so the untouched original is preserved beside each rewritten file,
under the same name with an "original" suffix. Do not hand-edit either one.

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
- **Receipts — the ticked ones.** A receipt travels when its item is ticked; the receipt of an item
 that is still open stays live with its box, and `archive-receipts` rebuilds `receipts/README.md`
 on both sides of the move so each index lists only the receipts in its own folder.
- **Shift log → the archive, whole.** Move `$NS/shift-log.md` into
 the folder and start a fresh one
 with the same one-line header. The journal is mechanical; its lines belong to the dates they
 happened.
- **Snag log — only what's handled.** `archive-receipts` moves entries that carry a disposition
 (fixed, ignored, answered, rejected-because, accepted-tradeoff) from `$NS/snag-log.md` into the
 archive dest that `archive.root` and `archive.layout` resolve, then appends one
 `Filed:` pointer (label: date or shift id; target: relative path to the archived file)
 on the live file. Filing nothing
 writes no pointer and creates no empty archive file. Do not hand-copy those entries.
 Entries still awaiting the owner stay live: an open question is not history yet.
- **Parking lot — only what's answered.** Same helper, same pointer rule on `$NS/parking-lot.md`.
 Parking-lot questions unanswered stay. Read live entries first; when checking whether a finding or decision
 was already handled, follow the pointer and search the linked file by topic or identifier.
 Historical decisions are evidence, not fresh authorization. A broken pointer is reported in the
 snag log; never guess or delete history.
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
"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" retain-history
```

Print that preview verbatim — every eligible path, its age, and the governing rule
(`retention.runtimeLogDays` or `retention.archiveDays`). Both default to `0` (keep forever);
a preview that lists nothing is success, not a prompt to invent a number.

Deletion is a second, explicit step. If the preview lists paths and the owner confirms in this
interactive session, run the same command with `--apply` (POSIX) or `-Apply` (native Windows). If the shift is armed, the owner
does not confirm, or either rule is `0`, stop after the preview. `--apply`/`-Apply` deletes only the
allowlisted runtime log (`scheduled.log`) and dated `archive/YYYY-MM-DD/` directories that
are old enough, resolved under `$NS/`, not symlinks, and free of still-open work.

Never call `ns retain-history` from start, hooks, status, Doctor, or recovery. Never call `ns archive-receipts` from start, hooks, status, Doctor, or recovery. Never delete
the live punch list, drafting table, parking lot, rules, current shift files, or owner-authored
files.

## Index

After filing, write a lightweight private index of archived shifts for later comparison
using the history-context template in
`$NIGHTSHIFT_PLUGIN_ROOT/skills/nightshift/references/receipts/cycle-specialist-evidence.md`.
The index lists each archived shift's objective, contracts, host, work target, outcome, evidence
locators, verification, commits or artifacts, duration, and ending. Corrupt or missing fields are
recorded — never invented. Compare prior shifts from that index to reuse evidence locators and
plans only; never replay side effects. Render audience-specific handoffs from one evidence truth.

## Summarize

Print the archive path and one line per file moved or trimmed — and what stayed live and why.
If a retention preview ran, include whether anything was eligible and whether the owner
confirmed a delete.
