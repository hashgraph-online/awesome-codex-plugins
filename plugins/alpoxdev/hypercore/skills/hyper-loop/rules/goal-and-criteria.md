# Goal and Criteria

Use this rule before writing `brief.md` or `goals.json`, and whenever a goal, criterion, dependency, or status changes.

## 1. Files and Ownership

One run owns one directory, `.hyper/loop/<slug>/`, where `<slug>` is a short lowercase kebab-case name taken from the request. The run itself is the only writer of its four files.

| File | Role | Writing rule |
|---|---|---|
| `brief.md` | The request, the intended outcome, constraints, and the run id | Written once; amended by append only |
| `goals.json` | Goals with status, dependencies, and criteria | Rewritten as a whole; ids never reused |
| `ledger.jsonl` | Append-only history of captures, checkpoints, steering, and failures | Append only; never edited or truncated |
| `final-gate.json` | Completion record with surface evidence | Written once at the final checkpoint |

Evidence files live beside them, usually under `.hyper/loop/<slug>/evidence/`. A different slug is a different run; never merge two runs into one directory, and never delete a finished run's directory.

## 2. The Goal

A goal is one finishable piece of the request that other goals can depend on.

| Field | Required | Contract |
|---|---|---|
| `id` | yes | Unique across the run, for example `G1`; never reused after a goal is superseded |
| `title` | yes | One line, the user's words where possible |
| `objective` | yes | What is true when this goal is done, in observable terms |
| `status` | yes | `pending`, `in_progress`, `complete`, `failed`, `blocked`, or `cancelled` |
| `depends_on` | yes | Array of goal ids that must be `complete` before this goal may start; empty when there is none |
| `criteria` | yes | At least one criterion; see §3 |
| `surfaces` | no | Array of user-visible surfaces this goal touches, for example `cli`, `http`, `browser`, `data`; the final gate needs a row for each distinct surface |
| `attempt` | no | Count of attempts spent on the current failure signature |
| `cycles` | no | Count of run cycles spent on this goal |

Dependency rules:

- Every id in `depends_on` exists in the same file.
- The graph is acyclic. A cycle is a planning error: split the goals rather than loop them.
- A dependency is ready only when its goal is `complete`; `failed`, `blocked`, and `cancelled` dependencies do not unlock a dependent goal.
- A goal that turns out larger than one finishable unit is split with `split_subgoal`, keeping its evidence.

The run root also carries `schema_version`, `objective`, `status` (`active`, `paused`, `blocked`, `failed`, `complete`, `cancelled`), and `current_goal_id`. The exact shape is in [references/state-schemas.md](../references/state-schemas.md).

## 3. The Criterion

A criterion is one binary check a person could re-run.

| Field | Required | Contract |
|---|---|---|
| `id` | yes | Unique within its goal, for example `C1` |
| `scenario` | yes | The observable situation: what is run, with what input, in what environment |
| `pass_condition` | yes | A single statement that is either true or false; no "mostly", no percentage |
| `expected_evidence` | yes | Path to the file the capture writes; the file must be non-empty for the criterion to pass |
| `essential` | yes | `true` when a non-final checkpoint may not proceed without it; `false` when it may wait for the final gate |
| `cleanup` | yes | The teardown this criterion owns, or an explicit statement that it created nothing to remove |
| `adversarial_classes` | no | Array of `{name, status: "pass"|"not_applicable", evidence?, reason?}`; a `pass` entry needs captured evidence, a `not_applicable` entry needs a reason |
| `status` | no | `pending`, `in_progress`, `pass`, `fail`, `blocked`, or `cancelled`; the ledger row is the durable truth |

Rules that keep a criterion provable:

- A condition containing "and" between independent outcomes is two criteria. Split it, so one failure does not hide behind the other.
- A condition that cannot be false is not a criterion. "Code is written" and "tests exist" fail this test; "the command exits 0 and its output contains the order id" passes it.
- The `expected_evidence` path is written before the capture, not derived from whatever the capture happened to produce.
- When no adversarial class applies, record one `not_applicable` entry with the reason instead of leaving the array absent and unexplained.
- A criterion whose proof depends on a user-visible surface declares it on the goal's `surfaces`, so the final gate has to show that surface.

## 4. Statuses and Transitions

| From | To | Condition |
|---|---|---|
| `pending` | `in_progress` | The resume rule selected it |
| `in_progress` | `complete` | Every essential criterion passes on fresh evidence and every dependency is `complete` for a checkpoint, or every criterion passes for the final gate |
| `in_progress` | `failed` | The failure bound was reached with a recorded signature |
| `in_progress` | `blocked` | A dependency is unmet, a capability is missing, or the user must decide something |
| `in_progress` | `cancelled` | The user cancelled; cleanup is recorded |
| `blocked` | `pending` | The unblocking step happened and the user or the record says to retry |
| `pending` | `cancelled` | The user cancelled a goal that had not started; cleanup is recorded |
| `blocked` | `cancelled` | Retired by `mark_blocked_superseded`, which keeps the old evidence |

`paused` belongs to the run, not to a goal: a paused goal keeps `in_progress` and resumes only on the user's direction. A cancelled goal never resumes automatically.

## 5. Resume Selection

On every resume, including after a context compaction, read `brief.md`, `goals.json`, and the tail of `ledger.jsonl` before touching code, then reconcile what actually exists on disk with what the ledger claims.

The selection order is fixed:

1. A goal with status `in_progress` that the user has not paused.
2. Otherwise the first `pending` goal, in file order, whose `depends_on` are all `complete`.
3. Otherwise nothing is selectable: record the run as `blocked`, naming the goals blocking progress.

A paused goal is not resumed by this rule; it needs the user's direction in the current conversation. Replaying finished goals, re-running their captures, or rewriting their rows is not part of a resume.

## 6. Brief

`brief.md` is short and stable: the request as the user stated it, the outcome the run binds itself to, the constraints (branch, forbidden actions, deadlines), the slug, and the run id. It is the file that keeps an objective from drifting when intermediate goals reveal new work; a goal that would change the objective is a conversation with the user, not a silent edit.

## Sources

> Checked 2026-11-09.

Source paths below are given from the source repository's skill root (its `skills` directory).

| Claim | Source |
|---|---|
| The goal, criterion, and status field set, and the durable state directory | `dbc-hbin/omp-ulw@74df40f ulw-loop/references/omp-ledger.md` (mechanism reference, re-authored) |
| Status transitions at goal and run level | `dbc-hbin/omp-ulw@74df40f ulw-loop/references/full-workflow.md` (mechanism reference, re-authored) |
| Resume by `in_progress` first, then the first dependency-ready pending goal | `dbc-hbin/omp-ulw@74df40f ulw-loop/SKILL.md` (mechanism reference, re-authored) |
| Splitting a condition with independent outcomes into separate criteria | this package's design, chosen so a single failure cannot be masked |

### Evidence grade

`LOCAL` - field names, the status table, and the selection order are this package's re-authoring of the cited mechanism, adapted to JSON files a plain shell script can check. The source repository carries no license; no text or code was copied.