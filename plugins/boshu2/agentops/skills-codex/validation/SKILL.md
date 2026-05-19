---
name: validation
description: 'Run post-implementation validation.'
---
# $validation — Full Validation Phase Orchestrator

**YOU MUST EXECUTE THIS WORKFLOW. Do not just describe it.**

## Strict Delegation Contract (default)

Validation delegates to `$vibe`, `$post-mortem`, `$retro`, and `$forge` (plus lifecycle skills `$test`, `$deps`, `$review`, `$perf`) as **separate skill invocations**. Strict delegation is the **default**.

**Anti-pattern to reject:** spawning judges directly in place of `$vibe`, inlining post-mortem analysis, skipping `$forge`. See [`../shared/references/strict-delegation-contract.md`](../shared/references/strict-delegation-contract.md) for the full contract and supported compression escapes (`--quick`, `--no-retro`, `--no-forge`, `--no-lifecycle`, `--no-behavioral`, `--allow-critical-deps`).

See [`docs/learnings/orchestrator-compression-anti-pattern.md`](../../docs/learnings/orchestrator-compression-anti-pattern.md) for the live compression signature.

## DAG — Execute This Sequentially

### Step 0: Load Prior Validation Context

Before running the validation pipeline, pull relevant learnings from prior reviews:

```bash
if command -v ao &>/dev/null; then
    ao lookup --query "<epic or goal context> validation review patterns" --limit 5 2>/dev/null || true
fi
```

**Apply retrieved knowledge (mandatory when results returned):**

If learnings are returned, do NOT just load them as passive context. For each returned item:
1. Check: does this learning apply to the current validation scope? (answer yes/no)
2. If yes: include it as a `known_risk` — what pattern does it warn about? does the code exhibit it?
3. Cite applicable learnings by filename when they influence a validation finding

After applying, record each citation:
```bash
ao metrics cite "<learning-path>" --type applied 2>/dev/null || true
```

Skip silently if ao is unavailable or returns no results.

**Run every step in order. Do not stop between steps.**

```
STEP 1  ──  $vibe recent [--quick]
              Use --quick for fast/standard. Full council for full.
              PASS/WARN? → continue
              FAIL?      → write summary, output <promise>FAIL</promise>, stop
                           (validation cannot fix code — caller decides retry)

STEP 1.5 ── Four-Surface Closure (mandatory)
              Read `skills/validation/references/four-surface-closure.md` for the mandatory four-surface closure check.
              Check all four surfaces: Code, Documentation, Examples, Proof.
              All 4 pass? → continue
              if --strict-surfaces:
                Any surface fails? → FAIL, write summary, output <promise>FAIL</promise>, stop
              else (default):
                Code passes, others fail? → WARN, continue
                Code fails? → BLOCK, write summary, output <promise>FAIL</promise>, stop

STEP 1.6 ── Test pyramid coverage audit (advisory, append to summary)
              Check L0-L3 + BF1/BF4 per modified file. WARN only, not FAIL.

STEP 1.6b ── Validation lane budget guard (mandatory)
              If the execution packet or repo profile has `validation_lanes`,
              select the smallest proof set where `read_only=true`,
              `writes_artifacts=false`, `release_only=false`, `cost_class` is
              `cheap` or `standard`, and `auto_select` is `default` or matches
              the changed surface.

              Do not run `expensive`, `explicit`, or `release-only` lanes
              unless the operator explicitly requested them, the plan
              acceptance criteria name the command, or the objective is release
              readiness. Honor each selected lane's `timeout_seconds`; on
              timeout, write `[TIME-BOXED]` and continue with narrower evidence
              unless that lane was the only code-surface proof.

              For unclassified commands, treat `go test -race`, `-shuffle`,
              `-count=N` where `N > 1`, eval runners, retrieval bench,
              headless runtime smoke, and release gates as explicit-only.

STEP 1.7 ── Lifecycle Checks (advisory except critical dependency findings)
              Skip entire step if: --no-lifecycle flag.
              Each sub-step uses --quick mode to limit context consumption.
              On budget expiry: skip remaining sub-steps, write [TIME-BOXED].

              a) if lifecycle tier >= minimal AND test_framework_detected:
                   $test coverage --quick
                   Append coverage delta to phase summary.

              b) if lifecycle tier >= standard AND dependency_manifest_exists:
                   $deps vuln --quick
                   CRITICAL vulns (CVSS >= 9.0): **FAIL** (block shipping). Opt-out: `--allow-critical-deps` for acknowledged risk acceptance.
                   Non-critical: advisory note only.

              c) if lifecycle tier >= standard:
                   $review --diff --quick
                   Append review findings to summary as advisory.

              d) if lifecycle tier == full AND modified_files_touch_hot_path:
                   $perf profile --quick
                   Append perf findings to summary as advisory.
                   Hot path detection: modified files match benchmark files
                   or patterns (handler, middleware, router, parser, engine,
                   worker, pool, codec).

STEP 1.7.5 ── Release-Readiness Gates (MANDATORY when IS_RELEASE_CONTEXT=1)

              Release-context detection: branch name matches release/*,
              v*-prep, v*-evolve-run, or v\d+\.\d+*; OR --release-context
              flag; OR CLI/contracts/hooks/schemas/skills changes AND the
              caller intends to recommend `$release`.

              When IS_RELEASE_CONTEXT=1, this step is MANDATORY — failure
              to run any of the gates below MUST emit a FAIL verdict with
              "release gates not run" reason. Validation MUST NOT recommend
              `$release` until all three (a/b/c) pass.

              a) Full pre-push gate (NOT --fast):
                   bash scripts/pre-push-gate.sh
                   (--fast covers ~5-10 checks; full runs ~33 including
                   doc-release, mkdocs strict, hooks/docs parity, shellcheck,
                   CHANGELOG sync, headless runtime smokes)

              b) CI-local release gate:
                   bash scripts/ci-local-release.sh
                   (If script doesn't exist, log SKIP and continue;
                   if it exists and fails, treat as FAIL)

              c) CLI reference docs regen (when CLI surface changed):
                   Detect: diff contains cli/cmd/**.go with additions of
                   cobra.Command{ or .Flags() or Use:/Short: lines
                   Then: bash scripts/generate-cli-reference.sh &&
                         git diff --quiet cli/docs/COMMANDS.md
                   If diff is non-empty after regen → FAIL
                   ("CLI reference out of sync — commit the regen before
                   declaring release-ready")

              Phase summary records each as a checkbox row:
                [✅] full pre-push gate
                [✅] ci-local-release.sh
                [✅] generate-cli-reference.sh (or [N/A] if no CLI surface change)

              When IS_RELEASE_CONTEXT=0, skip silently.

              Skip suppression: --skip-release-gates (operator risk-accept)

STEP 1.8 ── Stage 4: Behavioral Validation (holdout scenarios + agent-built specs)
            Skip if: no .agents/holdout/ directory AND no .agents/specs/ directory
            Skip if: --no-behavioral flag set
            
            Sub-steps:
              a) List active scenarios and agent-built specs:
                   ao scenario list --status active 2>/dev/null
                   find .agents/specs -name "*.json" -type f 2>/dev/null
              a.5) For each agent-built spec in .agents/specs/, treat as a scenario
                   with source="agent". Validate against scenario schema (auto-* id
                   pattern). Add to evaluation set alongside holdout scenarios.
              b) If 0 scenarios AND 0 specs → skip with note "No behavioral validation artifacts found"
              c) Spawn evaluator council with AGENTOPS_HOLDOUT_EVALUATOR=1
                 Pass scenarios + implementation diff as judge context
              d) Each judge evaluates: "Does the implementation satisfy the scenario's
                 expected_outcome? Score each acceptance_vector dimension 0.0-1.0."
              e) Compute satisfaction_score per scenario (mean of dimension scores)
              f) Aggregate: mean satisfaction across all scenarios
              g) Gate:
                   mean >= scenario.satisfaction_threshold → PASS
                   mean >= 0.5 → WARN ("Partial satisfaction — review scenarios")
                   mean < 0.5 → FAIL ("Implementation does not satisfy holdout scenarios")
              h) Write results to .agents/rpi/scenario-results.json
              i) Include satisfaction_score in validation_state
            
            PASS/WARN? → continue to STEP 2
            FAIL? → write summary, output <promise>FAIL</promise>, stop

STEP 2  ──  if epic_id:
              $post-mortem <epic-id> [--quick]
            else:
              $post-mortem recent [--quick]
              Use --quick for fast/standard. Full council for full.
              PASS/WARN? → continue
              FAIL?      → write summary, output <promise>FAIL</promise>, stop

STEP 3  ──  if not --no-retro:
              $retro

STEP 4  ──  if not --no-forge AND ao available:
              if [ -n "${CODEX_THREAD_ID:-}" ] || [ "${CODEX_INTERNAL_ORIGINATOR_OVERRIDE:-}" = "Codex Desktop" ]; then
                ao codex ensure-stop --auto-extract 2>/dev/null || true
              else
                ao forge transcript --last-session --queue --quiet 2>/dev/null || true
              fi

STEP 5  ──  write phase summary to .agents/rpi/phase-3-summary-YYYY-MM-DD-<slug>.md
              ao ratchet record vibe 2>/dev/null || true
              output <promise>DONE</promise>
```

**That's it.** Steps 1→2→3→4→5. No stopping between steps.

---

## Setup Detail

Track state inline: `epic_id`, `complexity`, `no_retro`, `no_forge`, `strict_surfaces`, `vibe_verdict`, `post_mortem_verdict`. Load execution packet (if available): read `complexity`, `contract_surfaces`, and `done_criteria` from `.agents/rpi/execution-packet.json`. When a current `run_id` is known, prefer the matching `.agents/rpi/runs/<run-id>/execution-packet.json` archive over the latest alias.

## Gate Detail

**Validation has multiple blocking conditions.** Validation cannot fix code — it can only report and fail closeout when the lifecycle contract is not met.

- **Blocking FAIL conditions:** `$vibe` FAIL, code-surface failure in STEP 1.5, `--strict-surfaces` failure on any closure surface, CVSS >= 9.0 dependency findings in STEP 1.7b unless `--allow-critical-deps`, **STEP 1.7.5 release-readiness gate failure when IS_RELEASE_CONTEXT=1** (full pre-push-gate, ci-local-release.sh, or CLI-reference-staleness), and post-mortem FAIL in STEP 2. For release-context runs, validation MUST NOT recommend `$release` in its report unless all STEP 1.7.5 gates passed.
- **PASS/WARN:** Log verdicts, continue through the remaining steps.
- **FAIL:** Extract findings from the latest evaluator output, write phase summary with FAIL status, output `<promise>FAIL</promise>` with findings attached. Suggest: `"Validation FAIL. Fix findings, then re-run $validation [epic-id]"`.

**Why no internal retry:** Retries require re-implementation (`$crank`). The caller (`$rpi` or human) decides whether to loop back.

## Phase Summary Format

See [references/phase-summary-format.md](references/phase-summary-format.md).

## Phase Budgets

| Sub-step | `fast` | `standard` | `full` |
|----------|--------|------------|--------|
| Vibe | 2 min | 3 min | 5 min |
| Post-mortem | 2 min | 3 min | 5 min |
| Retro | 1 min | 1 min | 2 min |
| Forge | skip | 2 min | 3 min |

On budget expiry: allow in-flight calls to complete, write `[TIME-BOXED]` marker, proceed.

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--complexity=<level>` | auto | Force complexity level (fast/standard/full) |
| `--no-lifecycle` | off | Skip ALL lifecycle checks in STEP 1.7 (test, deps, review, perf) |
| `--lifecycle=<tier>` | matches complexity | Controls which lifecycle skills fire: `minimal` (test only), `standard` (+deps, +review), `full` (+perf) |
| `--no-retro` | off | Skip retro step only |
| `--no-forge` | off | Skip forge step only |
| `--no-budget` | off | Disable phase time budgets |
| `--strict-surfaces` | off | Make all 4 surface failures blocking (FAIL instead of WARN). Passed automatically by `$rpi --quality`. |
| `--release-context` | auto | Force STEP 1.7.5 release-readiness gates on. Auto-detected from branch name. |
| `--skip-release-gates` | off | Bypass STEP 1.7.5 (operator-acknowledged risk) |
| `--allow-critical-deps` | off | Allow shipping with CVSS >= 9.0 vulnerabilities (acknowledged risk acceptance) |

## Expensive Command Policy

Routine validation is targeted by default. Broad proof commands such as
`go test -race`, `go test -shuffle`, `go test -count=N` with `N > 1`, eval
runners, retrieval bench, headless runtime smoke, and release gates require
explicit operator/release/acceptance-criteria context. If one is run, record the
reason and timeout in the phase summary.

## Quick Start

```bash
$validation ag-5k2                        # validate epic with full close-out
$validation                               # validate recent work (no epic)
$validation --complexity=full ag-5k2      # force full council ceremony
$validation --no-retro ag-5k2             # skip retro only
$validation --no-forge ag-5k2             # skip forge only
```

## Output Specification

**Format:** markdown summary to stdout + on-disk artifacts. Files written: `.agents/rpi/phase-3-summary-YYYY-MM-DD-validation.md` (phase summary), `.agents/post-mortems/YYYY-MM-DD-<topic>.md`, `.agents/learnings/<slug>.md`, `.agents/findings/registry.jsonl` (appended), `.agents/ratchet/state.json`. **Exit signal:** completion marker — see below.

## Completion Markers

```
<promise>DONE</promise>    # Validation passed, learnings captured
<promise>FAIL</promise>    # Vibe failed, re-implementation needed (findings attached)
```

## Troubleshooting

See [references/troubleshooting.md](references/troubleshooting.md).

## Reference Documents

- [references/four-surface-closure.md](references/four-surface-closure.md) — four-surface closure validation (code + docs + examples + proof)
- [references/forge-scope.md](references/forge-scope.md) and [references/idempotency-and-resume.md](references/idempotency-and-resume.md) — forge scoping, rerun behavior, standalone mode
- [references/remote-and-multi-repo-validation.md](references/remote-and-multi-repo-validation.md)
