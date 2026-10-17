---
name: archive
description: File a finished shift into its own archive folder, laid out like the live site, so the live files keep only open work.
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
directory persists between calls. Each `$NS/...` path below is where the current layout keeps that file;
`ns path <key>` prints where this workspace keeps it, and `ns path --list` names every key.

Read `$NS/state-version` first. Legacy (missing), `1` and the current `2` may be archived.
A newer or malformed marker fails closed — file nothing, rewrite nothing, and never migrate.
`state-version` itself stays live; it is not an archive record.

In artifact mode the work target is a persistent folder, not a Git repository. File the same
Nightshift records; do not require a work-target commit that cannot exist. Copy live receipts with
`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" archive-receipts`, and pass `--retire <receipt-name>` once
per ticked item (native Windows: `-Retire` with those names as one comma-separated list).
Missing or empty receipts create no dated receipts folder.
A receipts path that is not a usable directory is a refuse, not an empty skip.

If `$NS/run/.pending-filing` exists, a shift asked for filing at clock-out. It carries `date=` and
`shiftId=` lines naming that shift — use them — and an `asked=1` line once the gate has held the
session to ask for it. Delete the marker once filing is done, and only then. Nothing else about it
is special: file the same way you would on any explicit Archive.

`$NS/run/.ended` names the shift that finished and where it files, in `shiftId=`, `archiveRoot=`,
`archiveLayout=`, `shiftName=` and `archiveFolder=` lines. Clock-out claimed that folder for the
shift, and every later Archive of it returns there, whatever day it runs.

**Only what is closed is filed.** Each record lives in one place: filed once it is closed, live
while it is open. Filing is a copy: nothing leaves live storage until its filed copy reads back.
A ticked item's receipt leaving live storage is a separate step, and the
agent running Archive takes it from `$NS/punch-list.md` — not later, not the owner, and not by
guessing.
`--retire` with one record name, repeated once per ticked item on POSIX; on native Windows,
`-Retire` takes those names as a single comma-separated list. Receipts of open items are never
named: they stay live and are not filed. The morning receipt is named only when that shift
has ended and no open item still needs it. Once the shift has ended, the helper also retires every
ticked item's receipt it filed, even if a name was missed. It will not retire an open item's
receipt.

Before naming anything, read `$NS/punch-list.md` and the records themselves. A shift can end with
items still open — `STOP` and the deadline both do that — so `.ended` is not a reason to leave a
ticked receipt live, and it is not a reason to pull an open one. Keep a record live when an open
item, an unanswered parking decision or work carried into the next shift still needs it, and when
you cannot tell who owns it. Rejected work is filed with its rejection, never erased. A name the
helper did not file is refused and told back to you.

## Where it goes

Each shift has one folder under the archive root (`archive.root` in the resolved policy), named by
`archive.layout`:

- `date` (the default): `<YYYY-MM-DD>/`, and a later shift that day `<YYYY-MM-DD>-shift-2/`,
  `-shift-3/` and so on.
- `shift`: `shift-<id>/`.
- `name`: the name on the punch list's title line, as in `# Punch List — Archive follow-ups`, so
  `archive-follow-ups/`.
- `date-name`: both, `<YYYY-MM-DD>-archive-follow-ups/`.

A shift with no name files by date under `name` and `date-name`, and a second shift under the same
name takes `-shift-2`. The folder records its shift in `.shift-id`; another shift never writes into
it, and filing the same shift again returns to it. `archive-receipts` prints the folder; receipts
land in its `receipts/`, which is `archive/<YYYY-MM-DD>/receipts/` by default. A shift that never
reached clock-out has no claimed folder yet and files by today's date: `date +%Y-%m-%d` on POSIX,
or `Get-Date -Format yyyy-MM-dd` on native Windows.

**The folder is laid out like the live site.** Every record sits at the path it has under `$NS/`:

```text
archive/<folder>/
├── .shift-id
├── punch-list.md            the contract and the ticked items
├── receipts/                the receipts of ticked items, the morning page, and an index of this folder
├── inbox/
│   ├── parking-lot.md       the answered decisions
│   └── snag-log.md          the findings with a disposition
└── run/
    ├── shift-policy.json    filed by clock-out
    ├── shift-log.md
    ├── usage/               the shift's usage readings
    └── evidence/findings.jsonl   filed by clock-out, when the shift used it
```

Links between those records keep working as written. A link to a record that stayed live — the
drafting table, a receipt of an open item still being worked — is repointed back to it in the filed
page, which is the only copy. Do not hand-edit it.

## What moves, what stays

- **Punch list → filed by the runtime.** Once the shift has ended, `archive-receipts` files the
 contract and the ticked items, then takes the ticked items out of `$NS/punch-list.md`.
 Open items, the contract and the gates stay live; an item ticked later joins the same filed list
 on the next Archive. Do not move items by hand. When the owner is present
 and no open box is left, ask whether to keep the contract for the next shift or change it. In
 unattended filing (a `.pending-filing` from clock-out) do not ask: append one reminder under
 `## Notes` (create the heading below `## Items` if it is missing):
 leftover Shift contract and Gates still bind the next Hunt or Start cut; review them before
 composing a new campaign; Archive does not reset them. Skip the note when open work remains, when the same sentence is already
 present, or if adding it would require an open checkbox. Never write `- [ ]` here and never edit
 above `## Items`.
- **Receipts — the ticked ones filed and retired.** For each ticked item, pass `--retire <receipt-name>`;
 receipts of open items stay live and are not filed.
 `archive-receipts` rebuilds `receipts/README.md` on both sides of the move so each index lists
 only the receipts in its own folder.
- **Shift log, usage, policy → filed by the runtime.** Once the shift has ended, the helper moves
 `$NS/run/shift-log.md` into the folder and starts a fresh one under the same heading, moves the
 shift's usage readings, and moves a policy of that shift that is still live. A `usage-<id>/`
 folder the Start preflight set aside goes to the folder of the shift it belongs to. Do not move
 any of these by hand.
- **Snag log — the handled entries filed, only the open entries stay.** `archive-receipts` files
 each `- ` bullet entry of `$NS/inbox/snag-log.md` that carries a disposition (`fixed`, `ignored`,
 `answered`, `rejected-because`, `accepted-tradeoff`), takes those entries out of the live file,
 and appends one `Filed:` pointer to the filed copy (label: the folder's name, or the shift id in the `shift`
 layout; target: relative path to the filed file). A file with no entry files nothing. Do not
 hand-copy entries. Entries still awaiting the owner stay live: an open question is not history
 yet. Text written as a paragraph instead of a bullet is never filed; Doctor names it by file and
 line.
- **Parking lot — the answered entries filed, only the unanswered stay.** Same helper, same pointer rule on
 `$NS/inbox/parking-lot.md`. The owner answers an entry by appending ` · answered: <decision>`; an
 answered entry is filed, never deleted. Parking-lot questions unanswered stay. Read live entries
 first; when checking whether a finding or decision was already handled, follow the pointer and
 search the linked file by topic or identifier. Historical decisions are evidence, not fresh
 authorization. A broken pointer is reported in the snag log; never guess or delete history.
- **Work orders — only what's spent.** Pending orders are open boxes; they stay.
 A `## Work order` heading with no remaining box is leftover shell from a cut — delete it,
 do not file it. File only an order whose box was ticked in place, into the folder's
 `staging/work-orders.md`.
- **Product research → the archive after its shift.** When no shift is active, append the completed
 entries from `$NS/product/product-research.md` to the folder's `product/product-research.md`,
 preserving their dates, sources, evidence, and conclusions; then restore the live file from the
 shipped template. During an active shift, leave all research live. Research is evidence, so never
 summarize it away or strip its source URLs while filing it.
- **Opportunity map — only terminal outcomes.** Move `shipped` and `rejected` entries from
 `$NS/product/opportunity-map.md` into the folder's `product/opportunity-map.md`, preserving their
 evidence links and reasons. Keep `candidate`, `building`, and `parked` entries live: they can still
 affect a future cycle or need the owner. Restore the shipped headings if moving the last terminal
 entry leaves an empty section. Never renumber or silently change a status during archive.

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
allowlisted runtime log (`scheduled.log`) and shift folders — dated `archive/YYYY-MM-DD/` and
`archive/YYYY-MM-DD-shift-N/`, and any folder a shift claimed in its `.shift-id` — that are old
enough, resolved under `$NS/`, not symlinks, and free of still-open work. A claimed folder's punch
list is a copy whose open items stayed live, so it never holds work back.

Never call `ns retain-history` from start, hooks, status, Doctor, or recovery. Never call `ns archive-receipts` from start, hooks, status, Doctor, or recovery. Never delete
the live punch list, drafting table, parking lot, rules, current shift files, or owner-authored
files.

## Index

After filing, add the shift to the private history index: `history-index.md` at the top of the
archive root (`archive/history-index.md` by default), one file and one shape on every host. When it
does not exist but an `index.md` there opens with `# Archived shifts`, that file is the index under
an older name: rename it to `history-index.md` and say so. Any other `index.md` is left alone. With
neither, create the file with its heading:

~~~markdown
# Archived shifts

One entry per archived shift, from the history-context template. Fields not on record read unavailable.
~~~

Each shift is one entry in this shape. Its block is the history-context template in
`$NIGHTSHIFT_PLUGIN_ROOT/skills/nightshift/references/receipts/cycle-specialist-evidence.md`:

~~~markdown
## <shift id, or unavailable> — <one-line objective> (<plugin version>)

```text
# history-context / preset
objective: <text>
contracts: <ids>
verification: <profile>
sources: <allowed locators>
limits: <hours, elevation>
```
host: <host> · work target: <target, mode> · branch <branch> from <commit>
outcome: <ticked of total; pull request, merge, release>
evidence: <locators under the archive root>
commits: <count and tip, or the artifacts>
duration: <start> → <end>
ending: <how the shift ended>
record gaps: <what is missing or corrupt, or none>
~~~

Filing a shift again updates its entry instead of adding a second. Corrupt or missing fields are
recorded — never invented. Compare prior shifts from that index to reuse evidence locators and
plans only; never replay side effects. Render audience-specific handoffs from one evidence truth.

## Summarize

Print the shift's folder and one line per file moved or trimmed — and what stayed live and why.
If a retention preview ran, include whether anything was eligible and whether the owner
confirmed a delete.
