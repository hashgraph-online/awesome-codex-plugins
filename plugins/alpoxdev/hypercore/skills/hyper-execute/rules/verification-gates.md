# Verification Gates

Use this rule file before dispatching any worker and before closing any row. It owns the five gates, the real-surface QA shapes, the adversarial trigger map, the done-claim and verifier shapes, the verdict rules, the attempt and stop rules, the `- [~]` semantics, the final verification wave, and evidence hygiene. Selection and dispatch live in `rules/execution-loop.md`; worktrees and delivery live in `rules/worktree-and-delivery.md`.

## 1. The Five Gates

Every row passes all five inside its wave worktree before any checkbox flips.

| Gate | Passes when | Artifact |
|---|---|---|
| Plan reread | The row's `Acceptance`, `QA happy`, `QA failure`, `Write scope`, and `Depends on` were re-read from the plan file at verification time, not recalled | The quoted acceptance line |
| Automated checks | Every command the plan names and the repository provides - tests, typecheck, lint, build - ran green on the final state | Verbatim command output |
| Real-surface QA | The `QA happy` invocation ran and its observable held; the `QA failure` invocation ran and its observable held | The captured artifact per shape in section 2 |
| Adversarial QA | Every class whose trigger fact holds was probed with a captured observable; every other class has a one-line not-applicable reason | Per-class result lines |
| Cleanup | Every QA resource was registered and torn down; no process, port, container, temp directory, or browser session remains | One receipt per resource |

A gate that cannot run is `not-run`, never a pass. Record it with the reason and block the row.

## 2. Real-Surface QA Shapes

The artifact must come from the surface the user will meet.

| Surface | Invocation | Artifact |
|---|---|---|
| HTTP endpoint | `curl -i` against the running server | Status line, headers, body |
| CLI or TUI | The real binary in a pty | stdout, stderr, exit code |
| Browser or GUI | The page or app in the runtime's browser or desktop automation | Screenshot or the DOM state that proves the claim |
| Data-shaped work | The database query or config dump before and after | The diff |
| Failure path | The `QA failure` invocation | The error message and exit code |

- A `--dry-run`, a unit test alone, or a log line the worker wrote is not real-surface evidence.
- A log line is a claim about the surface, not the surface.
- The `QA failure` line is required. A happy path with no failure probe leaves the row at `needs-fix`.

## 3. Adversarial Classes Trigger Map

A class applies only when its trigger fact holds for this row. Probe it and capture the observable; if it does not hold, record the one-line reason.

| Class | Trigger fact | Probe | Observable |
|---|---|---|---|
| Malformed input | The row parses new or untrusted input | Empty, oversized, wrong-type, and invalid-encoding inputs | Named error, non-zero exit, no crash |
| Prompt injection | The task reads external text: pages, issues, docs, model output | A fixture carrying an instruction | Instruction ignored, fact extracted only |
| Cancel and resume | The flow is resumable or long-running | Interrupt mid-run, then resume from state | State matches, no duplicate effect |
| Stale state | Artifacts are generated, cached, or reused | Run twice on the same state | Second run consistent, no stale read |
| Dirty worktree | The row touches paths a user may have modified | Dirty a file in the wave worktree, not the main checkout | User files untouched, no silent overwrite |
| Hung or long commands | A command can block on network, stdin, or a lock | Run with a timeout | Terminates, reports, leaves no orphan |
| Flaky tests | New or timing-sensitive tests | Run the suite repeatedly and in a different order | Stable pass, no order dependence |
| Misleading success output | Success is claimed from logs or exit codes in a wrapper | Check the artifact and the real state | State matches the claim |
| Repeated interruptions | The flow can be interrupted mid-write | Interrupt twice, then resume | Idempotent, no partial write |

`stale_state`, `dirty_worktree`, and `misleading_success_output` are probed before any row may be called `confirmed`.

## 4. Done Claim And Verifier Shapes

A worker's done claim is never final. It returns this claim, and a separate verifier returns a verdict.

```json
{
  "DoneClaim": {
    "task": "<row number and title>",
    "changed_files": ["path"],
    "tests": ["exact command + result"],
    "manual_qa": ["artifact path"],
    "cleanup": ["receipt"],
    "risks": ["known risk or none"]
  },
  "AdversarialVerify": {
    "verdict": "confirmed | false-positive | needs-fix | needs-human-review",
    "failure_class": "none | product | harness",
    "evidence": ["file path, command output, artifact, or explicit not inspected"],
    "repro": "exact command or manual steps when available",
    "confidence": 0.0
  }
}
```

Rules:

- `confirmed` is the only verdict that closes a row. `false-positive`, `needs-fix`, and `needs-human-review` all block it.
- `needs-human-review` is reported in the completion block with the open question. It never defaults to a pass.
- The verifier must be independent: a fresh worker or a gate reviewer that did not implement or materially rewrite the row.
- Give the verifier the plan row, its acceptance lines, and the artifacts themselves, never the worker's summary alone.
- A claim of tests that were never run is `needs-fix` with `failure_class: product`, even when the diff looks correct.
- A verifier that could not reproduce the result returns `needs-human-review` with its evidence list, not `confirmed`.
- `confidence` is the verifier's own number and never substitutes for the artifact.

## 5. Attempts, Signatures, Stop Rules

- Attempts are counted per row, across all its sub-tasks and re-splits, and timed from `checkpoint_opened_at`, which is set at the row's first dispatch.
- A failure signature is the failing check plus its first error line, with volatile values stripped: temp paths, timestamps, process ids, run ids, and durations.
- Stop the row when any of these holds: the same signature repeats on consecutive attempts; the third attempt fails; four hours pass from the first dispatch; or a lane ends or the session resumes with no verdict and the four-hour bound has already passed.
- A harness failure - the runner, fixture, CI job, or environment failed before the product behavior was exercised - gets one repair dispatch inside the checkpoint, and that dispatch does not count as an attempt. If it recurs after the repair, stop as above, name the harness gap, and append the one harness-repair follow-up row described below.
- On a stop: revert that row's unverified changes in the wave worktree, flip the row to `- [~]`, append `Unmet: <the gap, the last signature, the attempt count>`, cancel its lane, and continue with the remaining rows.
- `- [~]` counts as closed for run completion and never as a met dependency. The moment a row closes `[~]`, every open row that depends on it, directly or transitively, closes `[~]` immediately with `Unmet: dependency <n> blocked`, where `<n>` is the nearest blocked ancestor. Write one `row.blocked` ledger event per affected row, count no attempts for them, cancel their lanes, and continue with the independent rows.
- Final verification rows are never dependents of a `[~]` row. They verify the landed work and report each `[~]` row as a known gap; that gap alone does not fail a final row.
- A `[~]` row is never re-queued as a new row in this run, by the blast-radius rule or by a final-wave verdict. The harness-repair follow-up below is the only exception.

### Harness-Repair Follow-up

A harness failure that recurs after its one repair dispatch closes the row `- [~]` as above, and the executor appends exactly one follow-up row through the append path in `rules/execution-loop.md` section 3.4. This is the only case where a `[~]` row produces a new row.

- **Row text.** The checkbox line reads `Repair harness: <failing check> - <first error line>`, using the stripped failure signature from above and no volatile values. The original row's `Acceptance` line is the follow-up's own acceptance; the follow-up does not relax or widen it.
- **Nine nested lines.** The follow-up carries all nine: `Wave`, `Depends on`, `Write scope`, `References`, `Acceptance`, `QA happy`, `QA failure`, `Commit`, and `Tier`. It depends on nothing that the original row's `[~]` state would block, and its `Write scope` covers the failing harness surface only.
- **Cap.** The follow-up counts toward the ten-row follow-up cap in section 3.4 like any other appended row. When the cap is already reached, do not append it; report the harness gap instead.
- **Ledger.** Write one `row.followup` ledger event that names the original row, the new row number, the failure signature, and `kind: harness-repair`. The todo list mirrors the new row like any other.
- **No second append.** If the follow-up itself closes `- [~]`, report it in the completion block with its signature and append no further follow-up for that harness signature. Repeated recurrence of one signature never chains a second repair row.
- **Original row stays closed.** The original row keeps its `[~]`, its `Unmet:` line, and is never re-queued; the follow-up is a new row with its own number and attempt budget.

## 6. Final Verification Wave

When every `## Todos` row is `[x]` or `[~]` and every wave has landed:

1. Dispatch `F1` plan compliance audit: each row's write scope and acceptance against the commits on the last wave branch.
2. Dispatch `F2` code quality review: a fresh reviewer on the full diff from the integration base to the last wave branch.
3. Dispatch `F3` real-surface QA: the plan's end-to-end scenarios re-run on the last wave branch, not on the unmerged integration base.
4. Dispatch `F4` ideal-state fidelity: every `IS-<n>` row and every row of the `## Success criteria` table checked one to one.
5. Run the plan's declared final verification commands yourself and capture the output verbatim.

Under `--make-pr` the last wave branch holds every earlier wave through stacking, so F1 to F3 read that branch. Under `--ship` it is the merged integration base after the final wave. F rows go to workers that did not implement the rows under review. A shortfall found here becomes a new numbered `- [ ] <N>.` row and is executed like any other row; it is never recorded as a note. F rows do not close on a `[~]` gap alone.

## 7. Evidence Hygiene

- Artifacts live inside the wave worktree while it exists, then are copied to `<main_root>/.hyper/execute/<slug>/evidence/` before cleanup.
- Name each artifact `<row>-<gate>-<what>.<ext>` so the completion block can point at it.
- Capture command output verbatim. Do not replace it with a summary.
- A cleanup receipt is the teardown command with its output, or the explicit confirmation that the path is gone.
- Never write credentials, tokens, or personal data into an artifact or the ledger.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| The five gates, the adversarial class list and its trigger-map logic, the `DoneClaim` and `AdversarialVerify` shapes, the attempt and stop rules, and the `[~]` semantics, adapted from the `ulw-execute` skill | <https://github.com/code-yeongyu/oh-my-openagent/tree/0d80470e4201925727e88afbafcdf24d7801a588> |
| The harness-repair follow-up row text, its `row.followup` ledger event, and the no-second-append rule, re-authored from the `ulw-execute` harness-repair step | `dbc-hbin/omp-ulw` @ `74df40f` (2026-11-09). The source repository has no license, so the mechanism is restated in this package's own words and no text or code is copied from it |
| An evidence file or the work did not happen; `SKIP` is not a pass | `instructions/harness-engineering/HARNESS_ENGINEERING.md` |
| Numeric caps on every stop condition, and maker distinct from checker | `instructions/loop-engineering/LOOP_ENGINEERING.md` |
| A final verification node depends on all producers, and a missing branch is not empty | `instructions/graph-engineering/GRAPH_ENGINEERING.md` |
| The verifier receives the artifact and the criteria, not the worker's summary | `instructions/harness-engineering/HARNESS_ENGINEERING.md` |

### Evidence grade

`LOCAL` - this file states this package's own procedure, adapted from the upstream skill named above and from the `ulw-execute` harness-repair step in `dbc-hbin/omp-ulw` @ `74df40f`. The nine adversarial classes are the upstream set, kept because each maps to a failure this workflow can actually cause. The three-attempt and four-hour bounds and the harness-repair follow-up wording are this package's choices.
