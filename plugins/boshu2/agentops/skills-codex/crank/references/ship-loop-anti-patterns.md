# /ship-loop anti-patterns

Nine observed patterns to avoid when shipping in the bot-paired fast lane.

## 1. Shipping an inventory-touching PR without the regen sweep

**Pattern:** A PR adds a new skill, new contract file, new schema, or any inventory artifact. Operator pushes without running the regen sweep (sync-skill-counts, codex-hashes, domain-map, context-map, registry, sync-hooks). CI then fires ~15 inventory validators and 5+ of them fail.

**Why it costs:** Each CI failure becomes a cycle of (read failure → fix → push → wait 5-10 min for CI → next failure surfaces). 15 fixes through CI re-runs is ~60-90 minutes of operator attention. The same 15 fixes via the regen sweep at write-time is seconds.

**Rule:** Use `scripts/ship.sh` (mechanical regen sweep) for any PR that adds:
- A new skill (touches `skills/`, `skills-codex/`, `SKILL-TIERS.md`, `skill-dispositions.yaml`, `registry.json`, manifest, marker, catalog, etc.)
- A new contract (`docs/contracts/*.md` or `*.yaml`)
- A new schema (`schemas/*.json`)
- Any docs that get auto-indexed (`docs/learnings/`, `docs/architecture/`)

`ship.sh` detects these surfaces and runs the regen sweep preemptively — it removes the operator's choice to skip the rule (mechanical enforcement). For non-inventory PRs (single-file logic change, doc typo, dependency bump), skip `ship.sh` and just push; routine release authority is the local cockpit/pre-push proof path, with CI as PR/tag/manual backstop telemetry.

**Evidence:** PR #332 (`soc-b0nn`, this skill's own first PR) hit 15 distinct registries-drift failures on CI. Each was mechanical, but the sequential discovery turned a 30-min PR into a 90-min PR. **The skill that codifies the discipline burned the discipline learning the lesson.** Mechanically fixed by `scripts/ship.sh` (soc-33uy, PR #346).

## 2. Bundling pre-existing fixes

**Pattern:** Pre-push surfaces a WARN/FAIL in content you didn't change. Tempting to fix it inline since you're already there.

**Why it costs:** Other concurrent branches will hit the same pre-existing issue and apply the same fix inline. Result: 3 PRs each fixing the same line; the latter two are merge-conflict cleanup.

**Rule:** File the side-quest fix as its OWN atomic PR. Push it. Let it merge. Rebase your feature branch onto fresh main. Then continue your feature work.

**Evidence:** 2026-05-18 session — `../../AGENTS.md` broken link from PR #306 was fixed inline in PRs #322, #324, #325 before settling. Tracked as failure-mode F2.

## 3. Keeping copied variables after a rewrite

**Pattern:** Rewriting a script as a thin wrapper. The new code doesn't use `REPO_ROOT` / `TMP_DIR` / etc., but the rewrite preserves the old variable declarations "to be safe".

**Why it costs:** shellcheck SC2034 fires on the very next pre-push gate, requiring a cleanup PR.

**Rule:** After any script rewrite, the FIRST self-check is "are all top-level variable declarations referenced in the new body?" Run `shellcheck <path>` before commit, not after.

**Evidence:** PR #322 (`soc-3oij`) left `REPO_ROOT` unused; PR #325 cleaned it up. Tracked as failure-mode F1; mechanically closed by PR #326 (unconditional shellcheck on staged `.sh`).

## 4. Asserting local-only state in CI tests

**Pattern:** Writing a bats test that checks `[ -f .agents/learnings/<file>.md ]` to anchor the rationale.

**Why it costs:** `.agents/` is gitignored. The file does NOT exist in CI's fresh clone. The test fails in CI even though it passes locally.

**Rule:** Assert the rationale REFERENCE in the script body via `grep -q '<slug>' "$SCRIPT"`. Same intent (regression-guard the rationale link), doesn't depend on local state.

**Evidence:** Self-bug discovered mid-session on PR #326 + #329; both fixed in flight by replacing the file check with a grep on the script body.

## 5. Branches off out-of-date main

**Pattern:** Creating a feature branch when `git log main..HEAD` shows you're behind origin.

**Why it costs:** The branch needs `update-branch` immediately to catch up, and on multi-author repos the bot may attempt forward-ports of files it can't write (e.g., `.github/workflows/claude.yml`), entering a self-revert loop.

**Rule:** `git checkout main && git pull --rebase` BEFORE creating the feature branch. If `git pull --rebase` fails due to local stash/dirt, stash + retry.

**Evidence:** PR #270 sat 6 days because its branch was 195+ files behind main; the bot's claude.yml forward-port hit the `workflows: write` perm gate, the bot reverted its own merge, and `claude-review` stayed failing. Fixed by force-pushing a locally-rebased branch.

## 6. Skipping the failing-test-first step

**Pattern:** Writing the implementation first, then adding tests after — or worse, writing tests that pass after the implementation without ever having failed.

**Why it costs:** False confidence. A test that has never failed is not regression-guarding; it might assert the wrong thing entirely.

**Rule:** Per `.claude/rules/{go,python}.md`: L2-first/L1-always. Write the test that demonstrates the failure (reproduces SC2034, or the path-traversal, or the empty-Raw bug). Confirm it fails for the right reason. Then write the minimal fix that makes it green.

**Evidence:** PR #326's commit body explicitly reproduced SC2034 with a synthetic fixture before adding the fix. PR #324's tests covered 10 path-traversal subcases each rejected with `errors.Is(err, ErrInvalidRunID)`.

## 7. Claiming a gate fix lands without re-running the gate at post-merge HEAD

**Pattern:** A PR changes gate/validator/CI behavior. Operator ships it based on fast-gate green + diff-reading confidence, but never re-runs the targeted gate against the canonical post-merge state. Later discovery: the fix was ineffective and the gate still fails.

**Why it costs:** One self-correction PR per ineffective fix. Three self-corrections in a single session is real; the worst case is the operator declares success and walks away, leaving silent gate-drift on main until the next full-gate run discovers it.

**Rule:** For every PR that changes a gate, validator, or CI behavior:
1. Before opening the PR, run the affected gate locally and capture the targeted output line.
2. Include that line verbatim in the PR body as **Evidence**.
3. After merge, run the affected gate on the canonical HEAD and verify the output still matches the claim.
4. If it doesn't: file an atomic follow-up immediately; do NOT wait for someone else to notice.

**Falsifiable test:** if your PR claims "X is now skipped," then `grep "X.*skipped" <post-merge-gate-log>` must return a match.

**Mechanical enforcement (soc-o5kq + soc-eqjd):** `scripts/verify-gate-claim.sh <ref> "<claim>"` greps a gate log for the claim verbatim. The `validate-pr-evidence-claims` CI job in `.github/workflows/validate.yml` (soc-eqjd, PR #358) calls it automatically against every `Evidence:` line in the open PR body, against the workflow run's logs. A false claim now blocks the PR at CI time. (The original local pre-push wiring from soc-o5kq's check #39 was retired with the local gate itself; the CI job is the durable surface.)

**Evidence:** PR #350 (`soc-nmhp`) claimed eval-canaries were skipped on non-eval diffs; merged. Cycle 4 of `/evolve` re-ran the full gate on canonical post-merge HEAD and saw the same FAIL the fix was supposed to remove. Root cause: relied on `HAS_EVAL=1`, which is default-1 outside the `FAST_MODE` block (see anti-pattern #8 / learning `2026-05-19-default-true-flags-are-path-filter-footguns.md`). Shipped #352 as the actual fix. Tracked as the self-verify discipline in `2026-05-19-self-verify-before-claiming-fix-lands.md`. AP#7 became mechanical on 2026-05-19 — see `scripts/verify-gate-claim.sh` + `tests/scripts/verify-gate-claim.bats`.

## 8. Editing a gate/validator script without running its bats locally

**Pattern:** Operator changes a script under `scripts/` confident the diff is "obviously correct." Pushes. CI's `bats-tests` job fails because a regression test specifically guards the semantic the change broke.

**Why it costs:** A CI-roundtrip discovers what `bats tests/scripts/<file>.bats` would have caught in <60 seconds locally. The bats suite is the fast oracle for shell-config changes — running it costs nothing at write-time.

**Rule:** When editing any `scripts/*.sh` that has a matching bats suite under `tests/scripts/`:

```bash
bats tests/scripts/<name>.bats
```

Run BEFORE `git commit`. Fix any failures in the same commit. Treat the bats suite as the regression-guard contract for the script's documented semantics.

**Evidence (historical):** PR #352 (`soc-98o8`) first push removed an explicit fast-mode skip branch in the (now-retired) `scripts/pre-push-gate.sh` eval-canary trigger logic. A bats test in `tests/scripts/pre-push-gate.bats` ("skips eval canaries by default for eval changes in local fast mode") FAILed on CI. Local bats run would have caught it pre-push. Re-pushed with semantics preserved; all 55 tests then green. The lesson generalizes beyond pre-push-gate.sh: any gate/validator script with a sibling bats file gets the same treatment.

## 9. Closing a bead on push output alone under direct-push-to-main

**Pattern:** Under direct-push-to-main with concurrent lanes running, the operator runs `git push`, sees a success line, and closes the bead on that output alone.

**Why it costs:** `git push` success output lies about what actually landed. Another lane can win the race to the tip, so a bead closed on push output alone can be closed against a commit that never became reachable from `origin/main` — the tracker reads "done" while the work is not on main.

**Rule:** After push, prove the landing before closing the bead:
1. `git fetch origin`
2. `git merge-base --is-ancestor <landed-sha> origin/main` MUST pass (exit 0) — the deterministic proof the commit is reachable from the canonical tip.
3. Only then close via `ao done <bead-id> --sha <landed-sha>`, so the close carries the commit-bound verdict stamp.

**Evidence:** Seen live 2026-07-01 under parallel-lane churn on this repo's hot main — a `git push` reported success but the pushed tip lost the race and never became an ancestor of `origin/main`.

## When you've violated one of these

Don't hide it. Note it in the commit body — "this PR also includes an inline fix for the F2 pre-existing-blocker (see PR #X); should have been atomic, ate the cost this time." Naming it keeps the discipline honest.
