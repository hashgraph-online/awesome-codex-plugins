# State files

What each file under `.nightshift/` holds. One copy; every skill that stages, promotes or files
work points here.

- `punch-list.md` → owner-approved work active in this shift.
- `staging/drafting-table.md` → known work the owner stages for a later shift.
- `inbox/parking-lot.md` → unresolved owner decisions plus the default chosen so work continues.
- `staging/work-orders.md` → timed catalog work composed only through Hunt.

Ordinary plans belong in the drafting table, never in Hunt or the parking lot, and the drafting
table is the owner's: the agent writes it only when the owner asks. A bug found on a shift is fixed
on that shift and recorded in the snag log, never staged for later; only a fix that would change
behaviour users rely on becomes a parking-lot decision, with the default chosen and applied. Each
file keeps its own lifecycle; never reclassify one as another.

## Layout

`state-version` `2` groups `.nightshift/` by purpose, so the top holds only what the owner opens:
`punch-list.md`, `rules.json`, `state-version`, `STOP` while a stop-work order stands, the receipts
repository's `.gitignore` and `.git/`, and `support/` after an export. Each folder names what it
is for:

- `receipts/` — what the shift delivered.
- `inbox/` — what waits for the owner's verdict: the parking lot and the snag log.
- `staging/` — work waiting for a later shift: the drafting table and the work orders.
- `product/` — the product-evolution notebook: the opportunity map and the research notes.
- `archive/` — filed shifts.
- `run/` — everything the runtime owns: markers, locks, the lease and session, the policy
  snapshot, the work target, usage accounting, the ledger and the shift log.

A workspace at state-version `1`, or with no marker, keeps every file at the top of `.nightshift/`,
and the runtime reads and guards it there. `ns migrate-state` previews the move into the current
layout and makes it with `--apply` (`-Apply` on native Windows); Doctor and Setup describe it.
`lib/state-layout.tsv` is the one table both runtimes read, with every path each file has had, and
`ns path <key>` prints where a file sits in this workspace.

## Every file, and who writes it

**Written by** names who may change the file: the owner, the agent (the model working the shift or
running a skill), or the runtime (hooks, helpers and watchmen). **Rebuilt** says whether the
runtime can regenerate it from other records; a file that is not rebuilt is a record to keep.
While a shift is armed, hardhat refuses writes to `rules.json`, refuses deleting the punch list,
and refuses deleting or forging the control files: `STOP`, and in `run/` `.shift-armed`, `.ended`,
`.shift-session`, `.shift-worker`, `.shift-lease`, `.mutex-scope`, `work-target`, `work-mode`,
`shift-policy.json` and `deadline`, plus `shift-defaults.json`.

### Work and decisions

| File | Written by | Rebuilt | Changes | Leaves live storage | Governed by |
|---|---|---|---|---|---|
| `punch-list.md` | Owner, and the agent through Start, Hunt or Quality. The agent ticks boxes. The runtime adds each item's `<!-- id: … -->` comment when the shift policy is written, before arming. | No | Composed before arming; while armed only boxes tick | Once the shift has ended, `archive-receipts` files the whole list into the shift's folder at the same path, then keeps only the contract and the open items live | The contract above `## Items`; its digests in `run/shift-policy.json` |
| `staging/drafting-table.md` | The owner; the agent only when the owner asks, as Quality's "draft for later" and Import issues do | No | When work is staged, or cut into the punch list | Start moves an item out when it cuts it; never archived | — |
| `staging/work-orders.md` | Hunt; `ns scaffold work-orders` creates it the first time Hunt stages an order | No | Hunt composes; Start cuts | Archive files an order ticked in place and drops an empty heading | — |
| `inbox/parking-lot.md` | The agent parks decisions, including a fix that would change behaviour users rely on. The runtime adds permission gaps (`park-needs`) and watchman revival notices. An ordinary session or another agent may add one for the owner to review. The owner answers. | No | During the shift; answered in the morning | Archive files the whole file into the shift's folder at `inbox/parking-lot.md`, then keeps only unanswered entries live, with a `Filed:` pointer | One `- ` bullet per decision; ` · answered: <decision>` closes it |
| `inbox/snag-log.md` | The agent, for every bug it finds: fixed on the shift, with the fix as the disposition. The runtime adds a broken archive-pointer entry. An ordinary session or another agent may add one for the owner to review. | No | As findings are made and dispositioned | Archive files the whole file into the shift's folder at `inbox/snag-log.md`, then keeps only open entries live, with a `Filed:` pointer | One `- ` bullet: `finding · evidence · disposition · date` |
| `run/shift-log.md` | The runtime (gates, watchman, Stop and Reset) and the agent | No | Every cycle and control event | Archive moves it whole into the shift's folder at `run/shift-log.md`; past about 500 KB Start moves it into the last ended shift's folder the same way | — |
| `product/product-research.md` | The agent; `ns scaffold product` creates it when a product-evolution item is cut | No | Product-evolution cycles | Between shifts Archive appends its entries to the archive copy and restores the template | — |
| `product/opportunity-map.md` | The agent; `ns scaffold product` creates it when a product-evolution item is cut | No | Product-evolution cycles | Archive files `shipped` and `rejected` entries | Statuses in the template |
| `run/capabilities.json` | The agent, after a tooling commit lands | No; the agent reads the manifests again | After a tooling commit | Never | — |

A file in `staging/` or `product/` that is not there yet holds nothing: Status, Doctor and Start
read it as empty.

### Configuration

| File | Written by | Rebuilt | Changes | Leaves live storage | Governed by |
|---|---|---|---|---|---|
| `rules.json` | Setup, from the template; then the owner | Setup copies the template only when the file is missing; Start names a new template key and never adds it | Between shifts | Never | `nightshift-rules.schema.json` |
| `run/shift-policy.json` | The runtime: composition (`shift-policy.sh`), or the snapshot Start takes | No | Before arming; frozen while armed | The clock-out gate files it into the shift's folder at `run/shift-policy.json`, or Archive when no gate did; Reset drops it | `schemas/v1/shift-policy.json` |
| `shift-defaults.json` | Older workspaces only | — | Never written now | `shift-policy migrate` moves its choices into the `shift` block of `rules.json` and keeps `run/shift-defaults.json.bak` | `schemas/v1/shift-defaults.json` |
| `state-version` | The scaffold, into a `.nightshift/` it creates; `migrate-state`, last | No | On a state migration | Never | Current version `2` |
| `run/work-target`, `run/work-mode` | Setup | Setup writes them again | When the owner re-points the workspace | Never | — |
| `run/deadline` | Start, from the composed hours | No | When a shift with hours is cut | Start drops it once it has passed; Reset drops it | UNIX epoch seconds |
| `.gitignore` | Setup, with the receipts repository; `migrate-state` adds `run/` | Setup adds `STOP` and `run/` when missing | At Setup | Never | — |
| `.git/` | Setup, only when the owner asks for a receipts repository | No | Commits by the clock-out gate and Archive when `receiptsAutoCommit` is true, else by the owner | Never; never pushed | — |

### Records the runtime writes

| File | Written by | Rebuilt | Changes | Leaves live storage | Governed by |
|---|---|---|---|---|---|
| `receipts/<NN>-<slug>-<id>.md` | The agent writes the prose. The runtime keeps its `<!-- item: … -->` comment and a `Renamed from` line current, writes the Tokens and Time tables at the tick, and adds a Sessions row as each span on the item closes. The file name is the item's number, title and id; the runtime finds it by the id and, between shifts, renames it to follow a renumbered or retitled item. | No | From the first substantive work until the tick | `archive-receipts` copies it into the shift's folder at the same path, and retires it from live storage once the shift has ended and its item is ticked; an open item's is copied and stays | `references/receipts/` shapes; `receipts.*` settings |
| `receipts/README.md` | The runtime | Yes, from the punch list and receipts | Every tick, arming, clock-out, and archive | Archive rebuilds it on both sides of the move | — |
| `receipts/morning-<date>-<shiftId>.md` | The clock-out gate, unless the agent already wrote the page the owner's template asks for | Yes, while its records are live | Once, at clock-out | Archive copies it into the shift folder and retires it when it is named with `--retire` | `handoff.*` settings |
| `receipts/previous-report.md` | `migrate-state`, from the single page an older layout kept beside the punch list | No | Once | Archive copies it; it leaves live storage only when named | — |
| `run/usage/` (`segments.tsv`, `marks.tsv`, `pauses.tsv`, `active`, `window`, `previous-pulse`, `previous-ticked`, `.ticked-now`) | The runtime | No | Every pulse, tick, switch of item, and pause | Archive files it into the ended shift's folder at `run/usage/`; a Start before that renames it `run/usage-<shiftId>/`, and Archive files that into the folder of the shift it belongs to | — |
| `run/evidence/findings.jsonl` | The agent, through the ledger helper, which validates each record | No | Append-only during the shift | The clock-out gate appends it to the shift's folder at `run/evidence/findings.jsonl` and empties the live ledger | `schemas/v1/finding.json` |
| `archive/` | The clock-out gate, `archive-receipts`, the Archive skill | No | Each clock-out and each Archive | Only `retain-history --apply`, when the owner set `retention.archiveDays` | `archive.root`, `archive.layout` |
| `archive/history-index.md` | The Archive skill | No | One entry per archived shift, updated when the shift is filed again | Never | The Archive skill's `## Index` |
| `run/scheduled.log` | Scheduled runs | No | Each scheduled run | Only `retain-history --apply`, when the owner set `retention.runtimeLogDays` | — |
| `run/watchman.log` | `start-watchman`, from the watchman's own output: why it refused to arm, and any error after | No | Each watchman launch | Never; it holds only the watchman's own messages, not its revival sessions | — |
| `support/` | `export-support`, on request | Yes | On each export | Never automatically; the owner removes it | — |
| `run/provision-transaction.json`, `run/provision-baseline/`, `run/provision-surface` | `provision` | No | Around a provisioning step | Removed when the step commits or rolls back | — |

### Markers the runtime keeps

All of them are generated, and none is archived. Every one but `STOP` lives in `run/`, which the
receipts repository's `.gitignore` leaves out whole.

| File | Written by | Means | Removed |
|---|---|---|---|
| `run/.shift-armed` | Start | The site is on shift: the clock-out gate and hardhat apply | The clock-out gate, when the shift ends; Start clears a stale one before arming; Reset |
| `run/.shift-session`, `run/.shift-lease` | Hardhat, on the binding probe; the watchman advances the lease | The bound conversation, and the generation that may work | Stop drops the session; the clock-out gate releases the lease; Start and Reset clear both |
| `run/.shift-worker` | The Cursor watchman | The CLI worker a revival resumes | Start; Reset |
| `run/.ended` | The clock-out gate | The shift ended, with `shiftId=`, `archiveRoot=`, `archiveLayout=`, `shiftName=` and the `archiveFolder=` clock-out claimed for it | Start; Reset |
| `STOP` | Stop, or the owner's terminal command; the gate writes `deadline` or `stalled` | A stop-work order and its reason | Start; Reset |
| `run/.pending-filing` | The clock-out gate, when `archive.automatic` is true | Filing is due for that shift | Archive, once filing is done |
| `.stall`, `.notified`, `.clock-out-reminder`, `.context-reset`, `.receipt-due`, `.report-due` in `run/` | The clock-out gate, the pulse, and the session-start hook | Stall count, whistle sent, the reminder to repeat, a compaction to answer, a progress update due | By the step that consumes each; Start and Reset clear `.stall` and `.notified` |
| `.shift-pulse`, `.session-end`, `.watchman`, `.watchman-tick`, `.watch-reason`, `.mint-failed` in `run/` | The pulse, the session-end hook and the watchman | Liveness, a clean close, the watchman's pid, its last wake and reason, a failed worker mint | The watchman removes its pid file when it exits; Start and Reset clear `.shift-pulse`, `.session-end`, `.watchman-tick` and `.mint-failed`; Reset drops `.watch-reason` |
| `.lock.d/`, `.lease-lock.d/`, `.mutex-scope` in `run/`, and `*.tmp.*` beside a file | The runtime | Locks and atomic-write staging; `.mutex-scope` scopes native Windows mutexes | When the operation finishes; Start and Reset clear a stale lock |
