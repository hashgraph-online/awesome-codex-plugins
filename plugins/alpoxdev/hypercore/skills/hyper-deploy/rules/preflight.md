# Preflight

Use this rule in `preflight` mode and for the readiness step of `deploy`. It owns the bundled readiness scripts, how their results are read, triage, the tracked state for complex fixes, and delegated lanes. A passing readiness run is a verdict, never approval to deploy.

## 1. Scripts

Run from the target root; if the target is a subdirectory, keep the paths correct or use absolute paths.

| Script | Purpose |
|---|---|
| `bash skills/hyper-deploy/scripts/stack-detect.sh` | Prints detected stacks (`node`, `rust`, `python`); exit `1` when none is supported |
| `bash skills/hyper-deploy/scripts/deploy-check.sh [--parallel\|--sequential]` | Full proof: quality checks plus build, concurrent by default |
| `bash skills/hyper-deploy/scripts/lint-check.sh` | Stack-specific quality checks |
| `bash skills/hyper-deploy/scripts/build-run.sh` | Stack-specific build phase |
| `bash skills/hyper-deploy/scripts/pm-detect.sh` | Node package manager detection (`npm`/`yarn`/`pnpm`/`bun`) |

Reading the result:

- `deploy-check.sh` exits `0` when every executed check passed, `1` when one failed, `2` when nothing was executed, and `64` on a usage error.
- Exit `2` is a failed verdict, not a pass: nothing was configured or installed, so readiness is unproven.
- Every run prints `PRE_DEPLOY_SUMMARY executed=<n> skipped=<m>`. Quote that line in the report; it is the coverage claim.
- A skipped gate means "not configured" or "tool not installed". It is never counted as passed.
- Node checks use the project's own scripts, then a project-local `node_modules/.bin` binary. A missing tool is a skip, never an implicit `npx` install.
- `cargo fmt` needs `rustfmt`; without it the format gate is skipped. Clippy denies warnings through `CARGO_BUILD_WARNINGS=deny` on Cargo 1.97 and later, and through `-- -D warnings` on older toolchains.
- Python gates are optional: `ruff` or `flake8`, then `mypy` or a `compileall` fallback.
- `lint-check.sh` already runs Node typecheck and lint concurrently; do not fan out lanes for those two.
- Use `--sequential` or `PRE_DEPLOY_MODE=sequential` when concurrent toolchains contend for memory, CPU, or a shared build cache.

## 2. Phases

| Phase | Action | Required evidence |
|---|---|---|
| Scope | Confirm the target root, read the request as validate-only or fix-capable, run `stack-detect.sh` | Detected stacks, or the unsupported-stack stop |
| Baseline | Run the full `deploy-check.sh` once before any edit | Exit code, summary line, the exact failing output |
| Triage | Group failures by stack, command, and priority; pick a shape (section 3) | Failure groups with owner and evidence |
| Fix | Change only what the reproduced failure requires; rerun the narrowest command | Diff scope and the rerun output |
| Prove | Run the full `deploy-check.sh` again after the last edit, in the leader context | Exit `0` with `executed` above zero |

Do not skip the baseline because the failures look obvious, and do not treat a passing narrow rerun as the verdict. In validate-only mode, stop after the baseline and report.

## 3. Triage Shapes

Classify upward when unsure.

| Shape | Signals | Path |
|---|---|---|
| Simple | One stack, one failing command, one clear owner | Direct fix, no state file |
| Medium | Several failures in one stack, fixable one at a time | Direct fix with tracked state (section 4) |
| Complex | Multiple stacks, shared config, a build graph, or an unknown repair strategy | Tracked state |
| Laned | Failures disjoint by stack or file, each with its own success condition | Tracked state plus lanes (section 5), at most three |

Fix the first root failure before chasing errors that exist only because an earlier step failed.

## 4. Tracked State

For Medium, Complex, and Laned shapes, keep `.hyper/deploy/<slug>/flow.json`, updated at every phase change:

```json
{
  "version": 1,
  "target_root": ".",
  "current_phase": "baseline",
  "stacks": ["node"],
  "max_fix_attempts": 3,
  "phase_history": [{ "phase": "detect", "status": "complete", "evidence": "stack-detect.sh output", "updated_at": "ISO-8601" }],
  "baseline": { "command": "bash skills/hyper-deploy/scripts/deploy-check.sh", "exit_code": 1, "summary": "PRE_DEPLOY_SUMMARY executed=2 skipped=1" },
  "failure_groups": [{ "id": "node-typecheck", "stack": "node", "command": "npm run typecheck", "priority": 1, "owner": "leader", "status": "open", "attempts": 0, "evidence": "exact failure excerpt" }],
  "fixes": [],
  "validation_history": [],
  "verdict": null
}
```

- Increment `attempts` before running the targeted check, so an interrupted run cannot hide a try. Resuming never resets it.
- At `max_fix_attempts` with the same root cause, set the group to `exhausted` and report it as `exhausted`, never `done`. A new root cause is a new group.
- The checker is the targeted command or `deploy-check.sh`, never the agent's own reading of its diff.
- On resume, read the file first and continue from the earliest incomplete phase. Reset to baseline only when the target root, the stack set, the package manager, or the validation command changed.
- `verdict` ends as `ready`, `unproven`, `exhausted`, or `handoff`.

## 5. Lanes

Delegate only when failures are independent by stack or file and a delegation capability exists; otherwise run the same work sequentially.

Never split when two lanes would touch the same file, lockfile, manifest, build config, or CI or deploy config, or when the next leader step is blocked on that result.

Every lane prompt carries: objective, scope (stack, command, files, target root), ownership (read-only or the exact writable files), forbidden actions (destructive commands, external side effects, unrelated cleanup, edits outside ownership), output (files, command output, result, blockers), and stop condition. Each lane inherits its group's attempt bound.

After the lanes return, the leader inspects every changed file and runs the final full `deploy-check.sh` itself. Readiness is never delegated.

## 6. Forbidden

- Making a check pass by weakening it: `|| true`, `continue-on-error`, a lowered lint level, a deleted assertion, or an edit to the bundled scripts.
- Installing or upgrading a dependency, or changing a lockfile or manifest, without explicit approval. Dependency fetching by the project's own build is expected; turning a missing tool into an install is not.
- Claiming readiness from code review, a narrow rerun, a lane's prose, or a run older than the last edit.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| The scripts, their exit codes, the summary line, triage shapes, tracked state, and lane contract, carried over from the former standalone readiness package of this repository (last present at commit `3b8576d`) | user instruction, 2026-11-07; repository history |
| A failure group stops at a declared attempt bound and is reported as `exhausted` | `instructions/loop-engineering/LOOP_ENGINEERING.md` |
| The checker is separate from the actor; a skipped check is never a pass | `instructions/harness-engineering/HARNESS_ENGINEERING.md` |
| Clippy's warning-deny configuration on Cargo 1.97 and later | <https://doc.rust-lang.org/clippy/usage.html> |

### Evidence grade

`LOCAL` - this rule restates this package's own readiness workflow; the attempt bound and the lane cap are its chosen bounds.
