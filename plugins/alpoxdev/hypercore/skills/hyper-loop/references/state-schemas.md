# State Schemas

Exact JSON shapes for the four state files and for the verifier's output. Read this while writing a state file, not before.

## Contents

1. `goals.json`
2. `ledger.jsonl` rows
3. `final-gate.json`
4. Verifier commands, output, and exit codes

## 1. `goals.json`

```json
{
  "schema_version": 1,
  "run_id": "orders-refactor-2026-11-09",
  "objective": "Split the orders module into four dependent goals and finish all of them",
  "status": "active",
  "current_goal_id": "G1",
  "goals": [
    {
      "id": "G1",
      "title": "Move order pricing into one module",
      "objective": "Every pricing call site uses the new module, and the old path is gone",
      "status": "in_progress",
      "depends_on": [],
      "surfaces": ["cli", "http"],
      "attempt": 0,
      "cycles": 1,
      "criteria": [
        {
          "id": "C1",
          "scenario": "run `npm test -- orders` on a clean worktree",
          "pass_condition": "the command exits 0",
          "expected_evidence": ".hyper/loop/orders-refactor-2026-11-09/evidence/g1-c1.log",
          "essential": true,
          "cleanup": "no resources created",
          "adversarial_classes": [
            {"name": "empty cart", "status": "pass", "evidence": "evidence/g1-c1.log:12"}
          ],
          "status": "pass"
        }
      ]
    }
  ]
}
```

| Level | Field | Type | Notes |
|---|---|---|---|
| root | `schema_version` | number | `1` |
| root | `run_id` | string | Stable across a resume; recorded in `brief.md` |
| root | `objective` | string | The binding outcome |
| root | `status` | string | `active`, `paused`, `blocked`, `failed`, `complete`, `cancelled` |
| root | `current_goal_id` | string or null | The goal selected by the resume rule |
| goal | `id`, `title`, `objective` | string | `id` unique across the run |
| goal | `status` | string | `pending`, `in_progress`, `complete`, `failed`, `blocked`, `cancelled` |
| goal | `depends_on` | array of string | Existing ids, acyclic |
| goal | `criteria` | array | At least one |
| goal | `surfaces` | array of string | Optional; drives the gate's surface check |
| goal | `attempt`, `cycles` | number | Counters for the failure bound |
| criterion | `id` | string | Unique within the goal |
| criterion | `scenario` | string | What is run, with input and environment |
| criterion | `pass_condition` | string | One binary statement |
| criterion | `expected_evidence` | string | Path; must resolve to a non-empty file to pass |
| criterion | `essential` | boolean | Required; missing is read as `true` |
| criterion | `cleanup` | string | Teardown owned by this criterion |
| criterion | `adversarial_classes` | array | Optional; `pass` needs evidence, `not_applicable` needs a reason |
| criterion | `status` | string | `pending`, `in_progress`, `pass`, `fail`, `blocked`, `cancelled` |

## 2. `ledger.jsonl` Rows

One JSON object per line, appended, never edited. Field `event` selects the row kind.

Evidence row:

```json
{"event":"evidence","goal_id":"G1","criterion_id":"C1","verdict":"pass",
 "tree":"4f0c…","diff_sha256":"9ab1…","command":"npm test -- orders",
 "evidence":"exit 0, 42 tests passed","artifacts":["evidence/g1-c1.log"],
 "rationale":"the criterion's scenario is exactly this command"}
```

Checkpoint row:

```json
{"event":"checkpoint","goal_id":"G1","tree":"4f0c…","diff_sha256":"9ab1…",
 "criteria":["C1","C2"],"rationale":"every essential criterion fresh; dependencies complete"}
```

Steering row:

```json
{"event":"steering","verb":"revise_criterion","decision":"accepted",
 "goal_id":"G2","criterion_id":"C3","evidence":"…","rationale":"…"}
```

Failure row:

```json
{"event":"failure","goal_id":"G2","signature":"npm test -- billing :: AssertionError: total",
 "attempts":3,"cycles":2,"rationale":"same signature three times"}
```

`verdict` is `pass`, `fail`, or `blocked`. A row with no `event` is read as an evidence row.

## 3. `final-gate.json`

```json
{
  "status": "complete",
  "tree": "4f0c…",
  "diff_sha256": "9ab1…",
  "surfaceEvidence": [
    {"criterionRef": "G1:C1", "surface": "cli", "invocation": "npm test -- orders",
     "verdict": "passed", "artifactRefs": ["evidence/g1-c1.log"]},
    {"criterionRef": "G2:C1", "surface": "http", "invocation": "curl -s localhost:3000/orders",
     "verdict": "passed", "artifactRefs": ["evidence/g2-c1.txt"]}
  ],
  "criteriaCoverage": {
    "totalCriteria": 2,
    "passCount": 2,
    "originalIntent": "split the orders module and finish every goal",
    "desiredOutcome": "one pricing module, no legacy path, tests green",
    "userOutcomeReview": "each criterion has a fresh capture and the surfaces were exercised"
  },
  "review": {"by": "deterministic", "recommendation": "approve",
             "evidence": "bash <skill-dir>/scripts/verify-loop-state.sh --final … exited 0"},
  "blockers": []
}
```

| Field | Contract |
|---|---|
| `status` | `complete`, `blocked`, or `paused`; only `complete` passes |
| `tree`, `diff_sha256` | Must equal a snapshot taken after the last change |
| `surfaceEvidence[].criterionRef` | `<goal-id>:<criterion-id>`; a bare criterion id counts only when no other goal uses that id, because one bare row would otherwise cover several criteria |
| `surfaceEvidence[].verdict` | `passed` for a passing row |
| `surfaceEvidence[].surface` | Matches a declared surface, for example `cli`, `http`, `browser`, `data` |
| `criteriaCoverage` | Counts include `essential: false` criteria |
| coverage rule | Every criterion needs one passing `surfaceEvidence` row, and every surface declared in `goals.json` needs at least one passing row of its own |
| `review` | `deterministic` only when no independent reviewer was available |
| `blockers` | Empty only for `complete` |

## 4. Verifier Commands, Output, and Exit Codes

```bash
bash <skill-dir>/scripts/verify-loop-state.sh snapshot [--dir <loop-dir>] [--repo <path>] [--limit <n>]
bash <skill-dir>/scripts/verify-loop-state.sh --goal <goal-id> --dir <loop-dir> [--repo <path>]
bash <skill-dir>/scripts/verify-loop-state.sh --final <final-gate.json> [--dir <loop-dir>] [--repo <path>]
bash <skill-dir>/scripts/verify-loop-state.sh --self-test
bash <skill-dir>/scripts/verify-loop-state.sh --help
```

`--dir` is the loop directory holding `goals.json` and `ledger.jsonl`; it is excluded from the fingerprint. `--repo` defaults to the worktree containing `--dir`. For `--final`, `--dir` defaults to the gate file's directory. `--limit` caps the listed untracked entries in `snapshot` output, default 200.

| Mode | Prints | Exit 0 | Exit 1 | Exit 2 |
|---|---|---|---|---|
| `snapshot` | `status`, `tree`, `diff_sha256`, `untracked[]`, `excluded` | fingerprint computed | — | not a repository, git failure |
| `--goal` | per-criterion `state` (`pass`, `stale`, `failing`, `missing`, `missing-evidence-file`), `essential_fresh`, `summary` | every essential criterion fresh | an essential criterion is not fresh | missing goal, missing or invalid `goals.json`, missing `--dir` |
| `--final` | per-criterion `evidence` and `surface`, `surfaces[]`, `snapshot_bound`, `gate_status` | complete gate, all criteria fresh, all surfaces covered, snapshot bound | any of those fails | missing or invalid gate file, unknown `status` |
| `--self-test` | `{"ok":true,…}` plus the checks it ran | all self-test cases behaved | a self-test case misbehaved | git missing, temp directory unusable |

Errors print one object, `{"status":"error","code":"<CODE>","message":"<text>"}`, and exit 2.

## Sources

> Checked 2026-11-09.

Source paths below are given from the source repository's skill root (its `skills` directory).

| Claim | Source |
|---|---|
| The four state files and the criterion field names | `dbc-hbin/omp-ulw@74df40f ulw-loop/references/omp-ledger.md` (mechanism reference, re-authored) |
| The gate fields `surfaceEvidence` and `criteriaCoverage` | `dbc-hbin/omp-ulw@74df40f ulw-loop/references/full-workflow.md` (mechanism reference, re-authored) |
| The command surface, the JSON output, and the exit codes | `skills/hyper-loop/scripts/verify-loop-state.sh`, verified by its `--self-test` |
| The gate status vocabulary `complete`, `blocked`, `paused` | the run contract for this package, 2026-11-09 |

### Evidence grade

`LOCAL` - the schemas match the bundled script, which is the executable definition; the self-test proves the states `pass` and `stale` and the gate's rejection of an uncovered criterion. Any field the script does not read is documentation for a human reviewer, not a constraint the script enforces.