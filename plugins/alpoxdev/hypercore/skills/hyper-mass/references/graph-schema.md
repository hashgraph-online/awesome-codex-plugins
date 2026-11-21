# Graph Schema

Use this reference while writing the run definition and the journal. `graph.json` is the contract; `run.jsonl` is the record of what happened to it. Both live under `.hyper/mass/<run-key>/`.

## Contents

- Run Directory
- `graph.json`
- Node Object
- Justification Object
- Node Prompt
- Self-Check
- `run.jsonl`
- Resume Matrix
- Worked Example
- Key and Path Rules

## Run Directory

```text
.hyper/mass/<run-key>/
├── graph.json              # the definition, written before start
├── run.jsonl               # append-only event journal
└── nodes/
    ├── <node-id>.md        # one handoff per node
    └── ...
```

The leader writes `graph.json` and `run.jsonl`. Nodes write only their own handoff, and only inside `nodes/`. A node that needs scratch space uses a temporary directory and removes it before finishing.

## `graph.json`

| Field | Type | Required | Meaning |
|---|---|---|---|
| `key` | string | yes | Run identity. Lowercase kebab-case, at most 48 characters. Same key plus same definition is a resume. |
| `name` | string | yes | Human label for reports. |
| `goal` | string | yes | One sentence naming the deliverable this run produces. |
| `success_criteria` | array of strings | yes | Each criterion names its evidence: the command and expected result, or the file and required content. |
| `justification` | object | yes | The six-field record from `rules/graph-planning.md` §4. |
| `nodes` | array of objects | yes | 1-32 node objects. |
| `phase` | string | no | The checkpoint this run covers, when an outer loop owns the goal. |
| `caps` | object | no | User-given overrides for nodes, concurrency, retries, or amends. |

Unknown fields are ignored; the six above are validated by the self-check.

## Node Object

| Field | Type | Required | Meaning |
|---|---|---|---|
| `id` | string | yes | Unique inside the run; lowercase kebab-case; used in the handoff file name. |
| `tier` | `low` \| `medium` \| `high` | yes | Difficulty. `low` is the default; one-line reason for anything higher. |
| `kind` | `writing` \| `visual` \| `git` | no | Specialty kind, chosen by the kind of work, never by difficulty. |
| `dependsOn` | array of strings | yes, may be empty | Node ids that must complete first. Orders work; carries no data. |
| `reads` | array of strings | yes, may be empty | Exact paths or globs the node may read. |
| `writes` | array of strings | yes | Exact paths or globs the node may change, including its handoff. |
| `handoff` | string | yes | `.hyper/mass/<run-key>/nodes/<id>.md`. Must be inside the run directory. |
| `prompt` | string | yes | The complete node prompt with the five markers. |
| `reason` | string | when `tier` is not `low` | One line explaining the escalation. |
| `solutionSpace` | array of strings | no | Short approach names this node may choose between. When present, the node prompt lists it and the node **MUST** pick only from the list; a node that uses an approach outside the list fails the self-check. |
| `resolvedModel` | string | no | The model that actually ran. It is written only from the observed result, never predicted before dispatch. |

`dependsOn` and `reads` serve different purposes: an edge orders two nodes, a read path names what a node consumes. A path in `reads` that no edge produces is either leader-supplied context or a mistake; decide which before starting.

When `solutionSpace` is present, the node prompt lists it under a `SOLUTION SPACE:` line (or inside `TASK`/`SCOPE`) so the worker sees the allowed approaches. The node names the approach it used in its handoff; the leader checks that the named approach belongs to the list before the node counts as complete. Without `solutionSpace` the node is free to choose; with it the choice is bounded and checked.

## Justification Object

```json
{
  "ceiling_removed": "",
  "topology": "",
  "state": "",
  "bounds": "",
  "approval": "",
  "rollback": ""
}
```

Validation rules:

- Every field is a non-empty string.
- `approval` is either the approval answer for each irreversible node or the literal `not required`.
- `rollback` names the concrete undo: branch, commit range, paths to revert, or "no files changed".
- `bounds` repeats the caps in force, including user overrides.

## Node Prompt

```text
TASK: <one imperative sentence>
DELIVERABLE: <artifact: files, report shape, evidence>
SCOPE: <exact read paths; exact write paths; what is out of scope>
VERIFY: <literal command and expected result>
STOP WHEN: <one observable condition>
```

A prompt missing any marker fails the self-check. A prompt that names a handoff but not the path, or a path outside the run directory, fails it too.

## Self-Check

Run before `run.created`:

1. `key` matches `^[a-z0-9]+(-[a-z0-9]+)*$`, is at most 48 characters, and contains no `..`, `/`, or absolute path.
2. `goal` is one sentence; `success_criteria` is non-empty and every entry names evidence.
3. `justification` has six non-empty fields.
4. Node count is within the cap; at most one node has `tier: high`.
5. Every `id` is unique and matches `^[a-z0-9]+(-[a-z0-9]+)*$`.
6. Every `dependsOn` id exists in the graph.
7. The graph is acyclic. A cycle is rejected before start; it is never repaired during a run.
8. Every wave has at least one runnable node.
9. No two nodes that can run in parallel share a `writes` path. Overlap means serialize or merge.
10. Every `handoff` equals `.hyper/mass/<key>/nodes/<id>.md` and is also listed in `writes`.
11. Every `prompt` carries TASK, DELIVERABLE, SCOPE, VERIFY, and STOP WHEN.
12. At least one terminal verification or review node depends on every producer.
13. The graph changes code: the terminal node's VERIFY names the real test or build command.
14. Every `solutionSpace` entry is a non-empty string, every approach a node reports using belongs to its own list, and every `resolvedModel` value came from an observed result rather than a prediction.

## `run.jsonl`

One JSON object per line, append-only. Common fields: `ts` (ISO 8601 UTC), `event`, `run`.

| Event | Additional fields |
|---|---|
| `run.created` | `mode`, `nodes`, `definition_digest`, `justification` |
| `run.resumed` | `from_event`, `reused_nodes` |
| `node.started` | `node`, `attempt` |
| `node.completed` | `node`, `handoff`, `evidence`, `resolvedModel` (the model observed in the result, run journal only); `verifier` on verification nodes (`self (no subagent capability)` in sequential mode) |
| `node.failed` | `node`, `attempt`, `error` |
| `node.retried` | `node`, `attempt`, `reason` |
| `node.sent` | `node`, `boundary` |
| `node.cancelled` | `node`, `reason` |
| `run.amended` | `changed`, `reason` |
| `run.settled` | `status`, `reason`, `criteria`, `landed` |

Example:

```json
{"ts":"2026-11-03T09:00:00Z","event":"run.created","run":"checkout-refactor-2026-11-03","mode":"waves","nodes":6,"justification":{"ceiling_removed":"serialized latency","topology":"5 components","state":"handoffs and worktree","bounds":"6 nodes, 4 concurrent","approval":"not required","rollback":"revert branch"}}
{"ts":"2026-11-03T09:00:05Z","event":"node.started","run":"checkout-refactor-2026-11-03","node":"audit","attempt":1}
{"ts":"2026-11-03T09:04:10Z","event":"node.completed","run":"checkout-refactor-2026-11-03","node":"audit","handoff":".hyper/mass/checkout-refactor-2026-11-03/nodes/audit.md","evidence":"13 call sites listed"}
{"ts":"2026-11-03T09:04:11Z","event":"node.started","run":"checkout-refactor-2026-11-03","node":"api","attempt":1}
{"ts":"2026-11-03T09:30:00Z","event":"node.failed","run":"checkout-refactor-2026-11-03","node":"api","attempt":1,"error":"handoff missing; node exited before writing"}
{"ts":"2026-11-03T09:31:00Z","event":"node.retried","run":"checkout-refactor-2026-11-03","node":"api","attempt":2,"reason":"missing handoff, rerun with write-first instruction"}
{"ts":"2026-11-03T10:20:00Z","event":"run.settled","run":"checkout-refactor-2026-11-03","status":"completed","reason":"all criteria pass","criteria":["checkout tests exit 0","e2e log attached"],"landed":["9f2c1ab","41d7e02"]}
```

Rules:

- `node.completed` is written after the leader opens the handoff, not when the node replies. The leader sets `resolvedModel` from the observed result (the runtime's report of which model ran) at that moment; it is never written before dispatch and never predicted from the `tier`.
- A node whose `solutionSpace` is present names the approach it used in its handoff. The leader checks it against the list before `node.completed`; a match outside the list is a failed self-check, not a completion.
- `run.settled` is written once per run; a resumed run appends a new settlement only after a new dispatch wave.
- Timestamps are UTC; the report may render local time, but the journal does not.

## Resume Matrix

| Journal state | Handoff file | Resume as |
|---|---|---|
| `node.completed` | exists and non-empty | completed, do not re-run |
| `node.completed` | missing or empty | failed; attempt count unchanged |
| `node.started` only | any | pending; dispatch again in the ready set |
| `node.failed` | any | failed; retry only if attempts remain |
| `node.retried` after `node.failed` | any | failed with a higher attempt count |
| `node.cancelled` | any | cancelled; retry only when the goal is re-opened |
| no event | any | pending |

A resumed run journals `run.resumed` before dispatching anything.

## Worked Example

A five-component refactor, one phase:

```json
{
  "key": "checkout-refactor-2026-11-03",
  "name": "Checkout refactor",
  "goal": "Move checkout onto the new payment client without changing user-visible behavior.",
  "success_criteria": [
    "`npm test -- checkout` exits 0 and its output is captured in nodes/verify.md",
    "`npm run e2e -- checkout` exits 0 and its log is captured in nodes/verify.md"
  ],
  "justification": {
    "ceiling_removed": "serialized latency: three independent surfaces plus one integration proof",
    "topology": "C1 audit, C2 API adapter, C3 UI copy, C4 docs, C5 end-to-end proof",
    "state": "handoff files and the working tree only; no shared in-memory state",
    "bounds": "6 nodes, at most 4 concurrent, 2 retries per node, 3 amends",
    "approval": "not required: no deploy, spend, or external send in this phase",
    "rollback": "revert the branch commits listed in nodes/verify.md; no data migration"
  },
  "nodes": [
    {
      "id": "audit",
      "tier": "low",
      "dependsOn": [],
      "reads": ["src/checkout/**", "src/payments/**"],
      "writes": [".hyper/mass/checkout-refactor-2026-11-03/nodes/audit.md"],
      "handoff": ".hyper/mass/checkout-refactor-2026-11-03/nodes/audit.md",
      "prompt": "TASK: List every checkout call site that uses the old payment client.\nDELIVERABLE: `.hyper/mass/checkout-refactor-2026-11-03/nodes/audit.md` containing a table with file, line, current call, and replacement call.\nSCOPE: read src/checkout/** and src/payments/** only. Write only `.hyper/mass/checkout-refactor-2026-11-03/nodes/audit.md`.\nVERIFY: every row names an existing file and line; run `grep -rn oldPayment src` and paste the count.\nSTOP WHEN: every call site in those directories is listed or marked read-only."
    },
    {
      "id": "api",
      "tier": "low",
      "dependsOn": ["audit"],
      "reads": ["src/payments/**", ".hyper/mass/checkout-refactor-2026-11-03/nodes/audit.md"],
      "writes": ["src/payments/**", ".hyper/mass/checkout-refactor-2026-11-03/nodes/api.md"],
      "handoff": ".hyper/mass/checkout-refactor-2026-11-03/nodes/api.md",
      "prompt": "TASK: Replace the old payment client with the new adapter at every call site listed in nodes/audit.md.\nDELIVERABLE: changed files plus a handoff listing each replacement and the command output.\nSCOPE: write only src/payments/** and nodes/api.md. Do not touch src/checkout/ui/** or tests/**.\nVERIFY: run `npm test -- payments` and paste the exit code and the final summary line.\nSTOP WHEN: the test exits 0 and every audit row is replaced."
    },
    {
      "id": "ui",
      "tier": "medium",
      "kind": "visual",
      "reason": "copy and state changes across four checkout screens",
      "solutionSpace": ["copy-update", "state-map", "a11y-pass"],
      "dependsOn": ["audit"],
      "reads": ["src/checkout/ui/**", ".hyper/mass/checkout-refactor-2026-11-03/nodes/audit.md"],
      "writes": ["src/checkout/ui/**", ".hyper/mass/checkout-refactor-2026-11-03/nodes/ui.md"],
      "handoff": ".hyper/mass/checkout-refactor-2026-11-03/nodes/ui.md",
      "prompt": "TASK: Update the checkout screens to the new payment states named in nodes/audit.md.\nDELIVERABLE: changed components plus a handoff listing each screen and its state mapping.\nSCOPE: write only src/checkout/ui/**. Do not touch src/payments/** or tests/**.\nVERIFY: run `npm run build` and paste the exit code; confirm each mapped state appears in the built bundle.\nSTOP WHEN: the build exits 0 and every listed screen has a mapped state."
    },
    {
      "id": "docs",
      "tier": "low",
      "kind": "writing",
      "dependsOn": ["audit"],
      "reads": ["docs/checkout.md", ".hyper/mass/checkout-refactor-2026-11-03/nodes/audit.md"],
      "writes": ["docs/checkout.md", ".hyper/mass/checkout-refactor-2026-11-03/nodes/docs.md"],
      "handoff": ".hyper/mass/checkout-refactor-2026-11-03/nodes/docs.md",
      "prompt": "TASK: Update docs/checkout.md to describe the new payment client and its states.\nDELIVERABLE: the edited page plus a handoff listing each changed section.\nSCOPE: write only docs/checkout.md and nodes/docs.md. Do not change code.\nVERIFY: every code identifier in the page exists in src/; paste the check command and its output.\nSTOP WHEN: every stale identifier is replaced and the check passes."
    },
    {
      "id": "e2e",
      "tier": "medium",
      "reason": "integration surface across API and UI",
      "dependsOn": ["api", "ui"],
      "reads": ["tests/e2e/**", "src/payments/**", "src/checkout/ui/**"],
      "writes": ["tests/e2e/**", ".hyper/mass/checkout-refactor-2026-11-03/nodes/e2e.md"],
      "handoff": ".hyper/mass/checkout-refactor-2026-11-03/nodes/e2e.md",
      "prompt": "TASK: Add and run the end-to-end checkout test for the new payment client.\nDELIVERABLE: the test file plus a handoff with the command, exit code, and log path.\nSCOPE: write only tests/e2e/** and nodes/e2e.md. Do not change product code; report a product defect instead.\nVERIFY: run `npm run e2e -- checkout` and paste the exit code and the last 20 log lines.\nSTOP WHEN: the suite exits 0 or the failing assertion is written to the handoff."
    },
    {
      "id": "verify",
      "tier": "medium",
      "reason": "independent judgment over every producer",
      "dependsOn": ["audit", "api", "ui", "docs", "e2e"],
      "reads": [".hyper/mass/checkout-refactor-2026-11-03/nodes/**"],
      "writes": [".hyper/mass/checkout-refactor-2026-11-03/nodes/verify.md"],
      "handoff": ".hyper/mass/checkout-refactor-2026-11-03/nodes/verify.md",
      "prompt": "TASK: Verify the checkout refactor against the run's success criteria.\nDELIVERABLE: nodes/verify.md with each criterion, the literal command, exit code, and captured output.\nSCOPE: read every handoff and the repository; write only nodes/verify.md. Do not fix product code.\nVERIFY: `npm test -- checkout` and `npm run e2e -- checkout` both exit 0; every producer handoff exists and is non-empty.\nSTOP WHEN: every criterion has a captured result, or a failing criterion names the producer and the exact failure."
    }
  ]
}
```

The audit fans out to three disjoint surfaces, `e2e` joins the two code producers, and `verify` depends on every producer, `audit` included because its handoff feeds all three surfaces. No second `high` node exists, and no two parallel nodes share a write path.

## Key and Path Rules

- `key` and `id` use lowercase ASCII kebab-case: `^[a-z0-9]+(-[a-z0-9]+)*$`. Reject `..`, `/`, and absolute paths.
- Paths in `reads`, `writes`, and `handoff` are repository-relative or absolute, exactly as the node will see them. Globs are allowed in `reads` and `writes`, never in `handoff`.
- The handoff lives inside the run directory so a resumed run can find it without guessing.
- One run, one directory. Never reuse a directory for a different key or a changed definition; that is what `amend` is for.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| The run directory shape, node fields, dependency rules, wave execution, journal events, and recovery semantics, adapted from the `mass-ulw` skill and its planning reference | <https://github.com/code-yeongyu/oh-my-openagent/tree/0d80470e4201925727e88afbafcdf24d7801a588> |
| Cycle bounds, missing is not empty, a verifier separate from the producer, and fan-out caps | `instructions/graph-engineering/GRAPH_ENGINEERING.md` |
| Checkpoint resume tested rather than assumed, and the transition record for a dynamic path | `instructions/graph-engineering/GRAPH_ENGINEERING.md` |
| Evidence file or it did not happen, and `SKIP` is not a pass | `instructions/harness-engineering/HARNESS_ENGINEERING.md` |
| The family contract's `.hyper/mass/<run-key>/` paths and the six justification fields | family contract, 2026-11-03 |
| Node `solutionSpace` bounds, approach-outside-list failure, `resolvedModel` from observed results, cluster digest with a token bound and handoff citations, and the final reducer reading digests only | `dbc-hbin/omp-ulw @ 74df40f` (2026-11-09), re-authored; the source repository has no license file and nothing was copied |

### Evidence grade

`LOCAL` - the schemas are this package's implementation of the family contract. Field names match the contract; `run.resumed`, `node.sent`, `node.cancelled`, `phase`, `caps`, and `reason` are additive and documented here.
