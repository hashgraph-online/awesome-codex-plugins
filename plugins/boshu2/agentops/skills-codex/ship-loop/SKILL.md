---
name: ship-loop
description: "Run ship loop."
---

# $ship-loop — Bot-paired fast lane PR cycle

> **Codex orchestration default:** when the operator types `$ship-loop`, run the 9-step cycle below. For fork-based OSS contributions use `$pr-implement` and the `$pr-*` family instead (different tier).

Capture of the discipline that lands single-scenario internal PRs at ~15-30 min median time-to-merge in repos with an auto-review bot workflow and `gh pr merge --auto` enabled.

## When to use

| Use ship-loop when... | Use something else when... |
|---|---|
| Coherent-arc internal PR in your own repo (one closable bead or small-epic slice) | Fork-based OSS contribution → `$pr-implement` |
| PR is the atomic-revert unit; scenarios ship-or-revert together | Large epic (15+ child beads) / multi-wave → `$crank` |
| Closing a harvested next-work item | Architecture / contract change → slow lane / human review |
| Mechanical drift fix or regression closure | Scenarios have independent rollback → split into separate arcs |

## The 9-step cycle

1. **Claim.** `bd ready` → pick highest-severity unblocked, OR read `.agents/rpi/next-work.jsonl` for harvested items. `bd update <id> --claim`.
2. **Branch off fresh main.** `git checkout main && git pull --rebase`. Then `git checkout -b <type>/<slug>-<bead-id>`. Never stack off siblings.
3. **First failing test.** BDD scenario or unit test. Must fail for the right reason (asserting expected behavior). Per the project's L2-first/L1-always rule.
4. **Minimal implementation.** Smallest code change that makes the test green. Resist scope creep.
5. **`scripts/ship.sh`** (recommended) — auto-detects inventory-touching changes, runs the regen sweep, opens the PR. **Mechanical fix for anti-pattern #1.** CI (`.github/workflows/validate.yml`) is the sole authoritative push gate per `docs/contracts/local-pre-push-gate-retirement.md` (soc-g2r9, PR #357); the previous `scripts/pre-push-gate.sh` local mirror was retired. For per-tool sanity before push: `cd cli && make test`, `bats tests/scripts/<file>.bats`, `scripts/regen-codex-hashes.sh`. If a pre-existing blocker appears in unchanged-from-base content, file an atomic side-quest fix PR first (don't bundle). **For PRs that change gate/validator/CI behavior**: capture the targeted output line in PR body as `Evidence:`; the `validate-pr-evidence-claims` CI job (`scripts/verify-gate-claim.sh`, soc-o5kq + soc-eqjd) verifies each Evidence line against the workflow run's logs and blocks the PR if any claim is absent (mechanical AP#7).
6. **Commit with conventional-commit scope.** `feat(<scope>):`, `fix(<scope>):`. Body reproduces the failure mode the test catches.
7. **Push + `gh pr create`.** Body cites the bead, validation, and a learning-anchor reference in the script body (not a `.agents/learnings/` file — that breaks CI).
8. **`gh pr merge <num> --squash --auto`.** Immediately. The bot fires the review check automatically on PR open.
9. **Close the bead.** `bd close <id> --reason "Merged via PR #<num>"`. For multi-PR chains: wait for each predecessor to merge, then run `gh api repos/<owner>/<repo>/pulls/<num>/update-branch -X PUT` on BEHIND successors.

## Gate sequence

| Gate | Enforces |
|---|---|
| Per-tool local checks (optional) | `cd cli && make test` for Go; `bats tests/scripts/<file>.bats` for shell; only what your diff touches |
| Review-bot workflow (auto on PR open) | Bot half of the pair — no mention required |
| `.github/workflows/validate.yml` | **Sole authoritative push gate** (soc-g2r9, PR #357). Full 60+ job suite incl. `validate-pr-evidence-claims` (AP#7). |
| `gh pr merge --squash --auto` | Auto-merge when all required checks pass |
| Manual update-branch fallback | Chain N PRs through auto-merge with `gh api repos/<owner>/<repo>/pulls/<num>/update-branch -X PUT` on BEHIND successors |

## Failure-mode mapping (F1-F5 + meta)

| ID | Failure | Mechanical guard |
|---|---|---|
| F1 | Script rewrite leaves dead variables | Unconditional shellcheck on staged `.sh` |
| F2 | Pre-existing blocker compounds across branches | **Open.** Rule: fix as atomic side-quest PR first |
| F3 | `--auto` doesn't auto-rebase BEHIND branches | Manual `update-branch` API call on BEHIND successors |
| F4 | Bot trigger doc claimed mention-only | Doc corrected; observed auto-fire on PR open |
| F5 | Stale `~/.config/evolve/KILL` silently blocks `$evolve` | `EVOLVE_KILL_TTL_DAYS=7` auto-expire |
| meta | Tests asserting local-only file existence | `grep -q '<slug>' "$SCRIPT"` instead of `[ -f .agents/learnings/<x>.md ]` |

## Anti-patterns

1. **Adding inventory artifacts without running the regen sweep** — new skill, contract, or schema → run `scripts/ship.sh` (auto-detects); CI catches what you missed
2. **Bundling pre-existing fixes** — file each as its own atomic PR
3. **Keeping copied variables after a rewrite** — first self-check after rewrite is "are all variable declarations used?"
4. **Asserting local-only state in CI tests** — grep the reference, don't check the file
5. **Branches off out-of-date main** — `git pull --rebase` at branch creation
6. **Skipping the failing-test-first step** — adding a test after the fix gives false confidence
7. **Claiming a gate fix lands without verifying at HEAD** — capture the target output line as PR `Evidence:`; the `validate-pr-evidence-claims` CI job verifies it against the workflow run's logs
8. **Editing a gate/validator script without running its bats** — the bats suite (under `tests/scripts/`) is the fast oracle; run `bats` on it before commit

## Session scope (sister rule to coherent-arc)

Coherent-arc governs the *shape* of a single PR; session-scope governs the *count* of consecutive PRs.

- **Default: 2-4 PRs per autonomous session.**
- **≥5 PRs in flight or merged in one session triggers a mandatory post-mortem before continuing.** Reactive-PR spirals (PR-fixes-fallout-from-prior-PR) dominate the back-half of long sessions.
- **Post-mortem shape:** which PRs were planned vs reactive, self-correction count, marginal PR = discovery or churn.

Derivation: 2026-05-19 session shipped 6 PRs with 3 self-corrections; PRs #5–#6 fixed fallout from #1–3. (soc-waxr)

## Pair mechanics

- The review-bot workflow fires automatically on `pull_request: opened/synchronize`. No mention required.
- If `IN_PROGRESS`, wait. If silent, check workflow permissions (`workflows: write` for forward-port scenarios).
- Self-revert loop (bot reverting its own forward-port): rebase the branch locally onto fresh main and force-push.

## Anti-Patterns (DO NOT)

| Anti-Pattern | Why It's Wrong | Correct Behavior |
|---|---|---|
| Stack feature branches on each other | Auto-merge serialization fails; conflicts compound | Always branch off fresh main |
| Bundle a pre-existing fix into a feature PR | Other branches will hit + duplicate the same fix | File atomic side-quest PR first, rebase |
| Assert `.agents/learnings/<x>.md` exists in CI | `.agents/` is gitignored; test fails in fresh clone | `grep -q '<slug>' "$SCRIPT"` (reference assertion) |
| Add tests after the fix without seeing them fail | False confidence | Write the failing test FIRST, see it red |
| Push without `--auto` enabled immediately | Operator becomes the merge bottleneck | `gh pr merge --squash --auto` on PR open |

## Examples

**User says:** `$ship-loop` after picking `soc-<bead-id>` from `bd ready`
Run the 9-step cycle: branch, first failing test, minimal impl, pre-push --fast, commit, push, auto-merge, bd close.

**User says:** "ship this fix from the post-mortem"
Read the harvested item from `.agents/rpi/next-work.jsonl`, run the 9-step cycle.

**User says:** "land the 4 PRs we have open"
After all 4 PRs are open with auto-merge enabled, wait for each predecessor to merge; if a successor becomes BEHIND, run `gh api repos/<owner>/<repo>/pulls/<num>/update-branch -X PUT`.

## See Also

- `$pr-implement` — fork-based OSS contribution (different tier; different use case)
- `$crank` — multi-wave epic execution
- `$rpi` — full lifecycle orchestrator
- `$post-mortem` — harvests next-work items that ship-loop consumes
- `$beads` — task tracker that drives the claim step
