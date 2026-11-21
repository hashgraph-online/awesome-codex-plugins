# Journal Format

Use this reference before opening the journal directory for a default, deep, or parallel run. `--quick` keeps the ledger and query log inside the report instead.

## Contents

- Directory layout
- `brief.md`
- `sources.md`
- `queries.md`
- `expansion.md`
- `claims.md`
- `debate.md`
- `verify-<slug>.md`
- Writing rules

## Directory Layout

```text
.hyper/research/
├── [NN].slug.md          # the saved report
└── [NN].slug/            # the journal, same stem
    ├── brief.md
    ├── sources.md
    ├── queries.md
    ├── expansion.md
    ├── claims.md
    ├── debate.md         # high-risk claim attacks, when any
    ├── report-state.json # repair passes and the outcome manifest
    ├── outcome.json      # written by report-state.sh finish
    └── verify-<slug>.md  # one per execution check, when any
```

The leader writes every file. Lanes return text; they never write here.

## `brief.md`

```markdown
# Brief: <topic>

Run started: YYYY-MM-DD HH:MM | Depth: default | Parallel: no

## Analysis
Core question:
Axes:
- A1 <axis> - <what, where, why>
Expected truths:
- E1 <statement> - status: true | violated | unknown
Entity: <canonical name, first-party URL, confidence>
Codebase relevant: | External: | Execution checks likely: | Precision demand:

## Fidelity
as of: latest at run start, YYYY-MM-DD (answered_by: default)
source floor: standard (answered_by: default)
derived numbers: allowed (answered_by: default)
asked: <fields asked, or none>

## Steering
- <exact user wording> - <wave it took effect>

## Deliverable
format: md (answered_by: default | user | request)
path: .hyper/research/[NN].slug.md
```

The `Deliverable` promise names what the run promises to deliver: the format (`md` by default), its path, and the `answered_by` value that chose the format. When the user asked for a different format, that answer is folded into the `Fidelity` block like the other fields; otherwise `answered_by: default` stands.

## `sources.md`

One row per source the moment it is opened. `S<n>` ids are stable for the whole run and are what the report cites.

```markdown
| # | Source | URL/path | Publisher | Published/updated | Accessed | Version/freshness | Channel | Grade | Role | Relevant claim | Used? | Caveat |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 | | | | | | | | S/A/B/C | lead/primary-evidence/supporting/conflict/rejected | | yes/no | |
```

- Grade: S for primary, official, standard, or first-party; A for independent methodology or major institutions; B for practitioner or vendor material; C for promotional, unattributed, outdated, or lead-only.
- A row written from a snippet or a lane's summary is marked `unverified` in `Caveat` until the artifact is opened.
- Under each high-risk row, keep the exact quoted span or line the claim rests on.
- A source reached through a blocked-page route records the route and its provenance label in `Channel`, a snapshot timestamp in `Version/freshness`, and the access report path in `Caveat` (`references/channel-selection.md`, Blocked Sources). An unreachable source keeps its row with `Used?` `no` and the blocking signal in `Caveat`.

## `queries.md`

```markdown
| # | Query / command | Channel | Axis or lead | Why this query | Result | Follow-up |
|---|---|---|---|---|---|---|
```

No identical or semantically equivalent query twice. Counter-searches for the claim gate are logged here with `counter:` in the `Why` column.

## `expansion.md`

```markdown
## Wave 1
Searches or lanes: <list>
Returns:
- <lane or axis>: <digest>
  ## EXPAND (verbatim)
Leads opened: L1 <lead>, L2 <lead>
Leads closed: L0 duplicate of ... | dead end because ...

## Excursions
| id | parent claim or axis | trigger | budget | depth | exit rule | changed in the answer |
|---|---|---|---|---|---|---|

## Run state
converged | exhausted (cap, open leads, last result, extension plan) | blocked (missing access)
```

## `claims.md`

```markdown
## verified-claims
- C1: <statement>

## Claim table
| claim_id | statement | risk | sources | domains | primary | counter-search | dates (published / accessed / valid as of) | lineage | status |
|---|---|---|---|---|---|---|---|---|---|
| C1 | | high | S1, S4 | 2 | S1 | Q7: none stronger | | MEASURED | supported |

## Unresolved
- C5: <statement> - <what evidence is missing>

## Refuted
- C6: <statement> - <the counter-evidence, with S ids>
```

Status is `supported`, `partial`, `refuted`, or `unresolved`. Only `## verified-claims` rows may be asserted as high-risk statements in the report.

## `debate.md`

One row per attack on a high-risk claim, in the slot order `rules/claim-verification.md` §7 fixes:

```markdown
| claim id | attack | attacker perspective | defense | verdict (holds, weakened, withdrawn) | change to the claim |
|---|---|---|---|---|---|
| C1 | <the objection> | evidence quality | <the rebuttal> | holds | |
| C1 | <the objection> | source independence | <the rebuttal> | weakened | narrowed to the surveyed segment |
```

Two attacks count only when their `attacker perspective` values differ. A high-risk claim with fewer than two rows here stays `unverified` and out of `## verified-claims`, and the report's `## Debate record` annex lists each claim's verdict.

## `report-state.json` and `outcome.json`

`scripts/report-state.sh` owns these two files; never hand-edit them. `repair` appends each pass and its defect codes to `report-state.json`. `finish` refuses delivery while a gate is unset, a blocker remains, or the report or ledger is empty, and writes `outcome.json` beside the state file only when it accepts the run. `briefing` prints the counted facts from `outcome.json` for the closing effort line.

## `verify-<slug>.md`

```markdown
# Verify: <claim>
Claim id: C3 | Source: S2 | Contradiction: S5
Environment: <OS, runtime, dependency versions>
## Code
## Output
## Verdict
CONFIRMED | REFUTED | PARTIAL - <grounded in the output above>
Cleanup: <temporary directory removed, path>
```

## Writing Rules

- Append when an event happens, never in an end-of-run batch.
- Never rewrite a past row to change what was observed; add a new row and mark the old one `rejected` or `conflict` with the reason.
- Keep absolute dates everywhere; no relative dates.
- Store distilled claims with their source and date, never raw retrieved page text.

## Sources

> Checked 2026-11-03.

| Claim | Source |
|---|---|
| A leader-owned session journal written in real time, with separate source, expansion, claim, and verification files, adapted from the `ulw-research` skill | <https://github.com/code-yeongyu/oh-my-openagent/tree/0d80470e4201925727e88afbafcdf24d7801a588> |
| Ledger columns, grades, roles, the query log, and agent rows staying unverified until opened | `instructions/sourcing/references/source-ledger.md` |
| Never persist raw retrieved text into durable state | `instructions/sourcing/references/retrieval-safety.md` |

### Evidence grade

`LOCAL` - this file states this package's own journal layout. File names and columns are this package's choices; the upstream skill uses a different file set.
