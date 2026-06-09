# Wave Patterns

## The FIRE Loop

Crank follows FIRE for each wave:

|-------|-----------|--------------|
| **CHECK** | Wave acceptance check (2 inline judges) → PASS/WARN/FAIL | Same |
| **ESCALATE** | `bd comments add` + retry | Update task description + retry |

**With `--test-first` flag, FIRE extends with two pre-implementation phases:**

| Phase | Description |
|-------|-------------|
| **SPEC** | Generate contracts per issue → `.agents/specs/contract-<id>.md` |
| **TEST** | Generate failing tests from contracts → RED gate (all must fail) |

## Parallel Wave Model

### Beads Mode

```
Wave 1: bd ready → [issue-1, issue-2, issue-3]
        ↓
        ↓
        $swarm → spawns 3 fresh-context agents
                  ↓         ↓         ↓
               DONE      DONE      BLOCKED
                                     ↓
                               (retry in next wave)
        ↓
        bd update --status closed for completed

Wave 2: bd ready → [issue-4, issue-3-retry]
        ↓
        ↓
        $swarm → spawns 2 fresh-context agents
        ↓
        bd update for completed

Final vibe on all changes → Epic DONE
```


```
        ↓
        $swarm → spawns 3 fresh-context agents
                  ↓         ↓         ↓
               DONE      DONE      BLOCKED
                                     ↓
                               (reset to pending, retry next wave)

        ↓
        $swarm → spawns 2 fresh-context agents
        ↓

Final vibe on all changes → All tasks DONE
```


## Spec-First Wave Model (--test-first)

When `--test-first` is enabled, crank runs 4 wave types instead of 1:

```
SPEC WAVE (conditional on --test-first)
  Workers: 1 per spec-eligible issue
  Input: issue description + plan boundaries + codebase (read-only)
  Output: .agents/specs/contract-{issue-id}.md
  Gate: Lead validates completeness (all issues have contracts)
                    ↓
TEST WAVE (conditional on --test-first)
  Workers: 1 per spec-eligible issue
  Input: contract-{issue-id}.md + codebase types (NOT implementation code)
  Output: test files committed to repo
  Gate: RED confirmation — ALL new tests must FAIL
                    ↓
IMPL WAVE (standard, enhanced with GREEN mode)
  Workers: 1 per issue (full access)
  Input: failing tests + contract + issue description
  Output: implementation code
  Gate: GREEN confirmation — ALL tests must PASS + wave acceptance check
                    ↓
[Optional] REFACTOR WAVE
  Workers: 1 per changed file group
  Input: passing tests + implementation
  Output: diff-only cleanup
  Gate: All tests still PASS
```

### Category-Based Skip

Issues categorized as docs, chore, or ci skip SPEC and TEST waves entirely:
- **feature / bugfix / refactor** → full pipeline (SPEC → TEST → IMPL)
- **docs / chore / ci** → standard implementation waves only

### RED Confirmation Gate

After TEST WAVE, the lead runs the test suite. ALL new tests must FAIL:
- If a new test passes → the test validates existing behavior, not new requirements
- Tests that pass are removed or flagged for rewrite
- Only proceed to IMPL when all new tests are confirmed RED

### RED Gate Failure Recovery

When the RED gate detects unexpected test passes:

1. **Identify cause:** Tests that pass against current code validate existing behavior, not new requirements from the contract
2. **Retry:** Re-spawn test writer with the unexpected-pass list and "must fail" constraint (max 2 retries)
3. **Escalate:** After 2 retries, mark the issue as BLOCKER and fall back to standard IMPL (no TDD for that issue)
4. **Log:** Record RED gate failure in wave checkpoint for post-mortem analysis

```bash
# RED gate failure tracking
if [[ ${#UNEXPECTED_PASSES[@]} -gt 0 ]]; then
    bd comments add <issue-id> "RED GATE: ${#UNEXPECTED_PASSES[@]} tests passed unexpectedly. Retry $RETRY_COUNT/2." 2>/dev/null
fi
```

### GREEN Confirmation Gate

After IMPL WAVE, the lead runs the test suite. ALL tests must PASS:
- New tests (from TEST WAVE) must now pass
- Existing tests must still pass (no regressions)
- Standard wave acceptance check also applies

### Contract Validation

SPEC WAVE workers explore the codebase before writing contracts (not fully isolated). This prevents generic, ungrounded specs. Workers read:
- Existing types, interfaces, and patterns
- Related test files for style reference
- Module structure and dependencies

But do NOT read implementation details of the specific feature being specified.

## Wave Acceptance Check (MANDATORY)

> **Principle:** Verify each wave meets acceptance criteria before advancing. Uses lightweight inline judges — no skill invocations, no context explosion.

**After closing all beads in a wave, before advancing to the next wave:**

**Note:** SPEC WAVE has its own validation (contract completeness check) and TEST WAVE has the RED gate. The Wave Acceptance Check applies only to IMPL and REFACTOR waves.

1. **Compute wave diff** (WAVE_START_SHA recorded in Step 4):
   ```bash
   git diff $WAVE_START_SHA HEAD --name-only
   WAVE_DIFF=$(git diff $WAVE_START_SHA HEAD)
   ```

2. **Load acceptance criteria** for all issues closed in this wave:
   ```bash
   # For each closed issue in the wave:
   bd show <issue-id>  # extract ACCEPTANCE CRITERIA section
   ```

3. **Validate worker result evidence (FAIL-CLOSED):**

   For each issue closed in the wave, read `.agents/swarm/results/<issue-id>.json` and validate against:
   `docs/contracts/swarm-worker-result.schema.json`.

   Required evidence policy for IMPL/REFACTOR acceptance:
   - `full_suite` evidence is mandatory for every completed implementation issue.
   - `red_green` evidence is mandatory for issues that ran through TEST WAVE (`--test-first` path).
   - Every check listed in `evidence.required_checks` must exist in `evidence.checks` and have `verdict: PASS`.

   Any one of the following sets the wave verdict to **FAIL** immediately:
   - missing result file
   - schema validation failure
   - missing required evidence
   - required evidence check with `FAIL` verdict

4. **Spawn 2 inline judges** (Task agents, NOT skill invocations):

   ```
   # Judge 1: Spec compliance
   Parameters:
     subagent_type: "general-purpose"
     model: "haiku"
     description: "Wave N spec-compliance check"
     prompt: |
       Review this git diff against the acceptance criteria below.
       Does the implementation satisfy all acceptance criteria?
       Return: PASS, WARN (minor gaps), or FAIL (criteria not met) with brief justification.

       ## Acceptance Criteria
       <acceptance criteria from step 2>

       ## Git Diff
       <wave diff>

   # Judge 2: Error paths
   Parameters:
     subagent_type: "general-purpose"
     model: "haiku"
     description: "Wave N error-paths check"
     prompt: |
       Review this git diff for error handling and edge cases.
       Are error paths handled? Any unhandled exceptions or missing validations?
       Return: PASS, WARN (minor gaps), or FAIL (critical gaps) with brief justification.

       ## Git Diff
       <wave diff>
   ```

   **Dispatch both judges in parallel** (single message, 2 Task tool calls).

5. **Aggregate verdicts:**
   - If Step 3 fails evidence validation → **FAIL**
   - Else, both judges PASS → **PASS**
   - Else, any judge FAIL → **FAIL**
   - Otherwise → **WARN**

6. **Gate on verdict:**

   | Verdict | Action |
   |---------|--------|
   | **PASS** | Record verdict in epic notes. Advance to next wave. |
   | **WARN** | Create fix beads as children of the epic (`bd create`). Execute fixes inline (small) or as wave N.5 via swarm. Re-run acceptance check. If PASS on re-check, advance. If still WARN after 2 attempts, treat as FAIL. WARN is only for non-critical review gaps after evidence is complete. |
   | **FAIL** | Record verdict in epic notes. Output `<promise>BLOCKED</promise>` and exit. Human review required. Includes missing mandatory evidence. |

   ```bash
   # Record verdict in epic notes
   bd update <epic-id> --append-notes "CRANK_ACCEPT: wave=$wave verdict=<PASS|WARN|FAIL> at $(date -Iseconds)"
   ```

## CI-Policy Parity Gate

> **Principle:** When a wave touches GitHub Actions workflows, the AGENTS.md CI table and the workflow's `summary.needs:` / `summary.if:` fail-set MUST stay in three-way sync. A drift means the docs lie about which jobs are blocking — exactly the failure mode that produced commit `c587b361` (manual fix codex-team applied AFTER soc-lmww1 added `factory-claim-ledger-strict (advisory)` to validate.yml without updating AGENTS.md or `summary.needs:`).

The crank orchestrator runs `scripts/validate-ci-policy-parity.sh` as a conditional acceptance gate inside Step 5.5.

### Trigger detection

```bash
# Only trigger when wave actually touches a workflow YAML file.
# CODEOWNERS-only or markdown-only changes do NOT trigger this gate.
if git diff --name-only "$WAVE_START_SHA" HEAD -- | grep -qE '^\.github/workflows/.*\.ya?ml$'; then
    bash scripts/validate-ci-policy-parity.sh || exit 1
fi
```

The grep pattern is intentionally narrow:
- `^\.github/workflows/` anchors the trigger to the workflows directory (not `.github/CODEOWNERS`, not action templates elsewhere).
- `\.ya?ml$` matches `.yml` and `.yaml` only.

### Pre-fix state (simulating the c587b361 bug)

A worker adds `factory-claim-ledger-strict` as a new advisory job in `validate.yml` but does NOT add it to `summary.needs:` and does NOT add a row to the `### CI Jobs and What They Check` table in AGENTS.md.

The orchestrator's gate fires:

```
$ bash scripts/validate-ci-policy-parity.sh
CI_POLICY_PARITY: Job list drift detected (AGENTS table vs validate.yml summary.needs).
--- AGENTS jobs
+++ Workflow summary.needs jobs
+factory-claim-ledger-strict
Action: align AGENTS CI table entries or summary.needs job list.
CI_POLICY_PARITY: FAILED (1 drift group(s) detected)
$ echo $?
1
```

Wave verdict → **FAIL**.

### Post-fix state

Add the job to `summary.needs:` and add a row to AGENTS.md (mark `(non-blocking)` when the job has `continue-on-error: true`). The gate then passes:

```
$ bash scripts/validate-ci-policy-parity.sh
CI_POLICY_PARITY: PASS (47 jobs; 7 non-blocking)
$ echo $?
0
```

### Fix-it message format

When the gate fails, surface a concise summary to the operator:

```
[wave-acceptance] CI-policy parity drift detected (validate-ci-policy-parity exit 1).
  Drift kind: <Job list | Non-blocking policy | Blocking policy>
  Required edits:
    - <align AGENTS.md ### CI Jobs and What They Check table>
    - <align .github/workflows/validate.yml summary.needs and/or summary.if fail set>
  Re-run after fix:
    bash scripts/validate-ci-policy-parity.sh
```

### Why this gate exists

- Commit `c587b361 ci(reconcile): wire factory-claim-ledger-strict into summary + AGENTS parity` is the manual fix that motivated this gate (soc-lmww1 drift). PR-F (this gate) is the formalization of `finding-2026-05-07-ci-parity-as-wave-acceptance`.
- The validator (`scripts/validate-ci-policy-parity.sh`) is also wired into `scripts/pre-push-gate.sh`. Wave acceptance hits the same gate earlier — at wave-close time — so drift never escapes a wave.
- Narrow trigger keeps the gate cheap and prevents false positives from CODEOWNERS, README, or non-workflow YAML changes.
