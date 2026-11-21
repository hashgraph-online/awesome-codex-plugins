# Run, Resume, and Gate

Use this rule at every checkpoint, every resume, when a steering verb arrives, when the failure bound is reached, and before writing `final-gate.json`.

## 1. Checkpoints

A checkpoint is the moment a goal's evidence is judged, not the moment the work feels finished.

- Non-final checkpoint: every `essential` criterion of the goal passes on fresh evidence, and every goal in `depends_on` is `complete`. Non-essential criteria may stay pending here; they may not at the final gate.
- Run the verifier first: `bash <skill-dir>/scripts/verify-loop-state.sh --goal <id> --dir .hyper/loop/<slug>`. Exit 0 is the condition to append a checkpoint row; exit 1 means the checkpoint does not exist yet.
- The verifier writes nothing. After exit 0, append the checkpoint row and update the goal status in `goals.json` yourself; a validator run is not a state change.
- A checkpoint that adds a failing criterion, or that passes only after a passing criterion broke, is not a checkpoint. Revert the fix and report it.

## 2. Failure Bound

The family convention is three attempts with the same failure signature, then a block.

| Signal | Meaning |
|---|---|
| Failure signature | The normalized identity of a failure: the failing command, the error class, and the failing assertion or exit code, with volatile parts like timings and paths removed |
| Attempt | One capture that failed under that signature |
| Cycle | One pass over the goal's criteria, regardless of which criteria failed |

Rules:

- Three attempts with the same signature, or five cycles without the goal's required criteria passing, produce a `failed` or `blocked` goal whose row records the signature.
- A different signature resets the attempt count for the new signature; it does not reset the cycle count.
- A blocked goal names the missing dependency, capability, credential, or decision, and what would unblock it. "Blocked" with no unblocking step is a `failed` goal with an unclear diagnosis.
- The run does not retry a blocked goal in the same run unless the unblocking step actually happened and is recorded.

## 3. Steering

A steering verb is how a mid-run request changes the plan without falsifying the record. Every verb changes `pending` goals only.

| Verb | Effect | Required fields |
|---|---|---|
| `add_subgoal` | Add a goal that the evidence showed is in scope; a defect outside the original scope stays a finding | `title`, `objective`, `depends_on`, `criteria`, `evidence`, `rationale` |
| `split_subgoal` | Replace one pending goal with several smaller ones that keep its criteria | `targetGoalId`, `childGoals` (each with `title`, `objective`, `criteria`), `evidence`, `rationale` |
| `reorder_pending` | Change the order of pending goals without breaking real dependencies | `pendingOrder`, `evidence`, `rationale` |
| `revise_criterion` | Correct a pending criterion's scenario, expected evidence, or pass condition | `goalId`, `criterionId`, at least one of `scenario`, `expected_evidence`, `pass_condition`, plus `evidence`, `rationale` |
| `mark_blocked_superseded` | Retire a blocked goal, optionally replacing it with child goals, keeping the old evidence | `targetGoalId`, optional `childGoals`, `evidence`, `rationale` |

Invariants, checked before applying a verb:

- A verb may not target a `complete` goal or a criterion that already passed.
- A verb may not turn a `fail` or `stale` capture into a `pass`, and may not delete the row that recorded it.
- A revised `pass_condition` is a new criterion in effect: its old proof is not evidence for the new condition, so the criterion returns to `pending` with fresh capture required.
- Ids stay unique; dependencies stay acyclic; no verb rewrites the objective in `brief.md`.

Record the proposal once as a `steering` row with its decision (accepted or rejected) and rationale, then apply the accepted change in `goals.json`. Steering is a local file change with an evidence trail, not a runtime feature request.

## 4. Final Gate

Completion is a file plus a passing check, never an announcement.

`final-gate.json` carries:

| Field | Contract |
|---|---|
| `status` | Exactly one of `complete`, `blocked`, `paused`. Only `complete` can pass the gate |
| `tree`, `diff_sha256` | The fingerprint the gate was written against, copied from a snapshot taken after the last change |
| `surfaceEvidence` | One row per criterion proof: `criterionRef` (`<goal-id>:<criterion-id>`), `surface`, `invocation`, `verdict: "passed"`, `artifactRefs` |
| `criteriaCoverage` | `totalCriteria`, `passCount`, `originalIntent`, `desiredOutcome`, `userOutcomeReview` |
| `review` | `{"by": "<reviewer identity>", "recommendation": "approve", "evidence": "..."}` when an independent reviewer ran; `{"by": "deterministic", "recommendation": "approve"}` plus the verifier command when the runtime provided none |
| `blockers` | Empty for `complete`; otherwise the goal, the signature, and the unblocking step |

Rules:

- Every criterion in every goal, including `essential: false`, needs a passing `surfaceEvidence` row and a fresh ledger row. A criterion that passed its checkpoint and then went stale is not covered.
- Every distinct `surface` declared by any goal needs at least one passing row on that surface. A declared surface with no row fails the gate.
- The gate's own fingerprint must equal a snapshot taken now. A fix after the gate was written invalidates the gate, so write it last.
- An independent reviewer is used when the runtime provides one. Recording `review: deterministic` is honest only when no reviewer was available; it is not a way to skip review that was available.
- `bash <skill-dir>/scripts/verify-loop-state.sh --final .hyper/loop/<slug>/final-gate.json` exits 0 for a complete, covered, snapshot-bound gate with status `complete`; exit 1 lists what is missing; exit 2 means the file itself is unusable.

## 5. Ending the Run

| Ending | When | Record |
|---|---|---|
| `complete` | The gate passed | Run status `complete`, gate status `complete` |
| `blocked` | The failure bound was hit, or a needed decision, credential, or capability is missing | Run status `blocked`, gate status `blocked`, the goal and signature named |
| `paused` | The user paused the run | Run status `paused`, gate status `paused`; the paused goal keeps `in_progress` and resumes only on the user's direction |

The closing briefing names the state directory, the goals that finished with the evidence each rests on, the goals that did not with the reason, and anything the run deliberately left alone. A run that ends `blocked` or `paused` is a reported outcome, not a failure of the process.

## 6. Delivery Boundary

Commit inside a goal when the repository's own conventions call for it, so the tree and the record stay aligned. This run never pushes, merges, opens a pull request, releases, or otherwise delivers remotely; that is a separate step with its own decision. When the user asks for delivery in the same request, finish the loop, report the gate, and let the delivery step own the remote work.

## Sources

> Checked 2026-11-09.

Source paths below are given from the source repository's skill root (its `skills` directory).

| Claim | Source |
|---|---|
| Non-final checkpoints on essential criteria, final completion on every criterion plus a typed gate file | `dbc-hbin/omp-ulw@74df40f ulw-loop/SKILL.md` and `references/full-workflow.md` (mechanism reference, re-authored) |
| The steering verb set and the rule that steering cannot turn failing evidence into a pass | `dbc-hbin/omp-ulw@74df40f ulw-loop/references/full-workflow.md` (mechanism reference, re-authored) |
| Three same-signature attempts before a failed checkpoint, and five cycles without the required criteria | `dbc-hbin/omp-ulw@74df40f ulw-loop/references/full-workflow.md` (mechanism reference, re-authored) |
| `surfaceEvidence` coverage and the `review: deterministic` fallback when no independent reviewer exists | `dbc-hbin/omp-ulw@74df40f ulw-loop/references/full-workflow.md`, adjusted to this package's `complete`/`blocked`/`paused` gate status |

### Evidence grade

`LOCAL` - the gate field set, the status names, and the delivery boundary are this package's choices. The status names `complete`, `blocked`, and `paused` are fixed by the run contract, not free text. The source repository carries no license; the mechanism was re-authored, not copied.