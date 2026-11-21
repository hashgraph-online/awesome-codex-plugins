# State And Ledger

Use this reference before writing `state.json` or `ledger.jsonl`, and immediately after any compaction or interruption. It owns the on-disk schemas, the event vocabulary, the completion block template, and the resume checklist.

## Contents

- Directory layout
- `state.json`
- `ledger.jsonl`
- Event vocabulary
- Example lines
- Completion block template
- Resume checklist

## Directory Layout

```text
.hyper/execute/<slug>/
├── state.json          # current position, one object, overwritten in place
├── ledger.jsonl        # append-only, one JSON object per line
└── evidence/           # artifacts copied out of each wave worktree
```

`<slug>` is the plan slug: lowercase ASCII kebab-case, `^[a-z0-9]+(-[a-z0-9]+)*$`, at most 48 characters. The plan is at `.hyper/plans/<slug>.md` and is never copied here.

Every path in this directory resolves against `main_root`, the main checkout's absolute path recorded in `state.json`. `.hyper/` may be gitignored and absent inside a wave worktree, so nothing here is read or written through a worktree-relative path. Checkbox flips edit the plan at `<main_root>/.hyper/plans/<slug>.md`.

## `state.json`

One object, overwritten at every phase boundary. It is the run's position, not its history.

| Field | Type | Meaning |
|---|---|---|
| `schema_version` | integer | `1` |
| `slug` | string | Plan slug |
| `plan_path` | string | Path to the plan, resolved against `main_root` |
| `main_root` | string | Absolute path of the main checkout; every plan, state, ledger, and evidence path resolves here |
| `integration_base` | string | Branch name, or sha when detached, recorded at phase 0 |
| `delivery` | string | `local`, `make-pr`, or `ship` |
| `status` | string | `active`, `paused`, `blocked`, or `complete` |
| `current_wave` | integer or null | Wave being executed, null before the first wave |
| `worktree_path` | string or null | Absolute path of the current wave worktree |
| `lane_worktrees` | array of strings, optional | Absolute per-lane worktree paths, in lane join order, when the wave runs parallel lanes |
| `wave_bases` | object | Map from wave number to the branch that wave started from: `"1": "main"`, `"2": "hyper/billing-retry/w1"` |
| `started_at` | string | ISO 8601 timestamp |

Optional fields, when the runtime or the run needs them: `updated_at`, `goal_id`, `subagent_capability` (`available` or `none`), `isolation` (`worktree`, `in-place`, or `in-place (no vcs)`), `stop_reason`, `rows` (a map from row number to `{ "state": "open|in_progress|done|blocked", "attempts": 0, "checkpoint_opened_at": null }`).

```json
{
  "schema_version": 1,
  "slug": "billing-retry",
  "plan_path": ".hyper/plans/billing-retry.md",
  "main_root": "/Users/me/dev/shop",
  "integration_base": "main",
  "delivery": "local",
  "status": "active",
  "current_wave": 2,
  "worktree_path": "/Users/me/dev/shop/.hyper/worktree/billing-retry-w2",
  "wave_bases": { "1": "main", "2": "main" },
  "started_at": "2026-11-03T09:10:00+09:00"
}
```

`state.json` is never the only record of a fact. When it disagrees with the ledger, the ledger is the history and the plan is the set of open rows.

## `ledger.jsonl`

Append-only. One JSON object per line. Every line carries the full key set below; a field that does not apply is `null` or `[]`, never omitted. This keeps the file readable by a single filter regardless of event type.

| Field | Type | Meaning |
|---|---|---|
| `event` | string | One value from the event vocabulary |
| `ts` | string | ISO 8601 timestamp |
| `task` | string or null | Row number and title, or the wave label |
| `attempt` | integer or null | Attempt number for the row, 1-based |
| `checkpoint_opened_at` | string or null | ISO 8601 timestamp of the row's first dispatch |
| `commands` | array of strings | Commands run, verbatim, with their result line |
| `artifact` | array of strings | Evidence paths |
| `adversarial_classes` | array of objects | `{ "class": "...", "result": "...", "reason": "..." }` |
| `cleanup` | array of strings | Teardown receipts, or the reason a resource was kept |
| `verdict` | object or null | `{ "verdict": "...", "failure_class": "...", "signature": "..." }` |

Extra keys such as `wave`, `tier`, `worker`, `write_scope`, `commit`, `pr`, `state`, and `reason` are allowed and are what makes the ledger useful during a resume.

## Event Vocabulary

| Event | Written when |
|---|---|
| `run.started` | The plan, base, and delivery mode are recorded |
| `goal.registered` | The session goal is set, or the goal id is recorded |
| `resume` | A run continues from disk after a pause, compaction, or crash |
| `wave.started` | A wave opens, with its rows, acceptance lines, and worktree |
| `dispatch` | A worker task is dispatched, or a row's work restarts |
| `verdict` | A verifier returns any verdict, including `needs-fix` |
| `row.closed` | A row flips to `[x]` with its gate artifacts |
| `row.blocked` | A row flips to `[~]` with its `Unmet:` line and signature |
| `landed` | A wave lands on its own base: a local merge, or a pull request opened, with the landed sha or the pull-request URL |
| `delivery` | A push, pull request, or merge is performed or skipped, with the reason |
| `cleanup` | A worktree, branch, or directory is removed or kept |
| `stop` | The run stops early, with the reason and the open rows |

## Example Lines

```json
{"event":"dispatch","ts":"2026-11-03T09:20:00+09:00","task":"2. Add retry budget","attempt":1,"checkpoint_opened_at":"2026-11-03T09:20:00+09:00","commands":[],"artifact":[],"adversarial_classes":[{"class":"stale_state","result":"pending","reason":"row regenerates a cache"}],"cleanup":[],"verdict":null,"wave":2,"tier":"medium","write_scope":"src/billing/retry.ts"}
{"event":"verdict","ts":"2026-11-03T10:02:00+09:00","task":"2. Add retry budget","attempt":1,"checkpoint_opened_at":"2026-11-03T09:20:00+09:00","commands":["bun test src/billing -> 41 pass"],"artifact":[".hyper/execute/billing-retry/evidence/2-gates-curl.txt"],"adversarial_classes":[{"class":"stale_state","result":"pass","reason":"second run reused state without a stale read"}],"cleanup":["port 4310 closed"],"verdict":{"verdict":"confirmed","failure_class":"none","signature":null}}
{"event":"row.blocked","ts":"2026-11-03T11:40:00+09:00","task":"5. Migrate ledger backfill","attempt":3,"checkpoint_opened_at":"2026-11-03T10:10:00+09:00","commands":["bun run migrate -> duplicate key on ledger_id"],"artifact":[],"adversarial_classes":[],"cleanup":["temp database dropped"],"verdict":{"verdict":"needs-fix","failure_class":"product","signature":"duplicate key on ledger_id"}}
```

## Completion Block Template

Print this once, after the final verification wave.

```text
HYPER EXECUTE COMPLETE - <slug>
Plan: <plan_path>
Main root: <main_root>
Delivery: <local | make-pr | ship>   Base: <integration_base>   Status: <complete | blocked>
CI: <green | failing | unverified | not-applicable>
Rows: <n> done, <m> blocked
Blocked:
  - <row number and title>: <gap>  (signature: <signature>, attempts: <n>)
Verification:
  - <command> -> <result>
  - <command> -> <result>
Artifacts: <evidence directory>, <artifact paths that matter>
Landed commits: <sha> <subject> (per wave)
Pull requests: <url> (<state>) | none
Removed: <worktree paths>, <merged branches>, <repo-wt directory if removed>
Kept: <path>: <reason>
Residual risk: <one or two lines, or "none identified">
```

Filling rules: read every number from the ledger, not from memory. Name each `- [~]` row with its gap. Say `none` rather than leaving a line empty. `CI: failing` is mandatory when the CI repair cap stopped a pull request, and the pull-request URL must appear on the `Pull requests:` line. When maker-checker was unavailable, add a line naming the rows that rest on deterministic checks.

## Resume Checklist

1. Read the plan, then `state.json`, then `ledger.jsonl`. Do not read the conversation for state.
2. Resolve every path against `main_root`, and confirm `slug`, `plan_path`, `integration_base`, and `wave_bases` match the plan and the branches on disk.
3. Recompute each open row's attempts and `checkpoint_opened_at` from the ledger.
4. Run `git worktree list --porcelain` and compare it with `worktree_path`.
5. Check the four-hour bound on every row whose `checkpoint_opened_at` is set, and close any that passed it as `[~]`.
6. Confirm which evidence files exist under `evidence/`, and never re-claim an artifact you cannot open.
7. Append a `resume` event with what was read and where the run continues.
8. Continue at the phase the state names, without asking whether to continue.

## Sources

> Checked 2026-11-03.

| Claim | Source |
|---|---|
| The ledger and state split, the per-row attempt and checkpoint fields, and the completion block content, adapted from the `ulw-execute` skill | <https://github.com/code-yeongyu/oh-my-openagent/tree/0d80470e4201925727e88afbafcdf24d7801a588> |
| Keep the authoritative plan and progress outside the context window and re-read them after compaction | `instructions/context-engineering/CONTEXT_ENGINEERING.md` |
| An evidence file or it did not happen | `instructions/harness-engineering/HARNESS_ENGINEERING.md` |
| Numeric caps on every stop condition | `instructions/loop-engineering/LOOP_ENGINEERING.md` |

### Evidence grade

`LOCAL` - this file defines this package's own file formats. The field set on every ledger line is this package's choice, made so a single filter reads any event without special-casing; the upstream ledger used a per-event field subset.
