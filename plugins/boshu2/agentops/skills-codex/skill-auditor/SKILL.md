---
name: skill-auditor
description: Audit SKILL.md files against the AgentOps
---
# $skill-auditor — Three-pass skill quality audit

Validates a skill's SKILL.md against the unified AgentOps template. Pass 1
wraps `heal-skill` for structural hygiene; Pass 2 adds 8 content-discipline
checks not covered by heal; Pass 3 folds the 10-category Skill Quality Rubric
(`docs/reference/skill-quality-rubric.md`) into the report as a deterministic
0-30 productization score (advisory). The report also includes an advisory
Context Density Rule block for intent, boundary, evidence, decision,
constraint, and next action coverage.

## ⚠️ Critical Constraints

- **Auditor is read-only.** Reports findings; never modifies the target. **Why:** PR-002 (external validation) — the auditor must remain a separate gate from the implementer. To repair findings: use `heal-skill --fix` for Pass-1 issues, hand-edit for Pass-2 issues.
- **Pass 1 delegates, never reimplements.** The auditor calls `heal-skill --check --strict <target>` and gates on its exit code; parsing output is report-only. **Why:** PR-006 (cross-layer consistency) — heal-skill's checks are the source of truth for structural hygiene; reimplementation creates drift.
- **Pass 2 must accept AgentOps' existing conventions.** Specifically `description-has-triggers` accepts THREE valid forms (YAML `|` block scalar OR `Triggers:`/`Use when:` markers OR `metadata.triggers` array with 3+ items). **Why:** finding `f-2026-05-06-auditor-checks-must-fit-host-conventions` — auditor checks must validate against the host substrate's existing valid artifacts before promotion to required gate.
- **Verdict aggregation rule:** any check returns `fail` → FAIL; otherwise any returns `warn` → WARN; otherwise PASS. **Why:** prevents silent severity downgrade.
- **Density coverage is advisory-only.** Missing density fields never changes
  the PASS/WARN/FAIL verdict and does not satisfy packet-boundary enforcement
  in `soc-2c1p.1`. **Why:** the hard Context Density Rule belongs at execution
  packet boundaries; this skill only helps reviewers find low-signal prose.
- **Pass 3 rubric is advisory-only.** The 0-30 rubric score never changes the
  PASS/WARN/FAIL verdict. **Why:** Pass 1+2 gate *template conformance* (does
  this ship); the rubric measures *market-facing maturity* (is this
  product-grade) — a low rubric score on a structurally-clean skill is a
  productization backlog signal, not a ship blocker (soc-ads5v).
- **Pass 3 scoring is deterministic and rubric-sourced.** The 10 categories
  come verbatim from `docs/reference/skill-quality-rubric.md`; each gets a 0-3
  score plus an explainable reason derived only from the skill directory
  contents. **Why:** an explainable, reproducible score is auditable; an
  LLM-graded one is not.

## What It Detects

### Pass 1 — delegated to heal-skill

| heal.sh code | Check |
|--------------|-------|
| MISSING_NAME | frontmatter `name` present |
| MISSING_DESC | frontmatter `description` present |
| NAME_MISMATCH | frontmatter name matches directory |
| UNLINKED_REF | `references/*.md` linked from SKILL.md |
| DEAD_REF | linked references actually exist |
| SCRIPT_REF_MISSING | scripts referenced exist |
| CATALOG_MISSING | user-invocable skills in `using-agentops/` catalog |

### Pass 2 — 8 NEW checks

| # | Check id | Severity |
|---|----------|----------|
| 1 | `description-has-triggers` | WARN (downgraded from FAIL after pilot) |
| 2 | `constraints-frontloaded` | WARN |
| 3 | `rationale-present` | WARN |
| 4 | `verification-checkpoints` | WARN |
| 5 | `output-spec-explicit` | FAIL |
| 6 | `quality-rubric` | WARN |
| 7 | `references-modularization` | WARN (conditional, only if SKILL.md > 400 lines) |
| 8 | `trigger-clarity` | WARN (downgraded from FAIL after pilot) |

Full check definitions and accepted forms in [references/audit-checks.md](references/audit-checks.md).

### Advisory density report

The JSON report includes a separate `density` block with six report-only fields:
`intent`, `boundary`, `evidence`, `decision`, `constraint`, and `next_action`.
Read [references/context-density-checks.md](references/context-density-checks.md)
for detection rules, limits, and false-positive handling.

### Pass 3 — rubric scoring (10 categories, advisory)

`audit.sh` runs `scripts/score_agentops_skill.py --audit-block` and folds the
result into `audit-report.json` under a `rubric` key. The 10 categories come
verbatim from [`docs/reference/skill-quality-rubric.md`](../../docs/reference/skill-quality-rubric.md)
(read it for the per-score `0/1/2/3` definitions): `trigger_quality`,
`kernel_clarity`, `progressive_disclosure`, `helper_scripts`, `validation`,
`self_test`, `assets_templates`, `subagents_roles`, `safety_boundaries`,
`packaging`.

Each category scores 0-3 (`0` missing/unsafe → `3` product-grade and
mechanically validated) with an explainable `reason`. Total 0-30 maps to a
rating band: `C` (0-10), `B` (11-20), `A` (21-26), `S` (27-30). The score is
**advisory** — it never changes the PASS/WARN/FAIL verdict.

Standalone (markdown) for picking the smallest productization patch:

```bash
python3 skills/skill-auditor/scripts/score_agentops_skill.py skills/<name> --markdown
```

Use it to pick the smallest patch (`SELF-TEST.md`, linked references, helper
scripts, assets, subagents, safety boundaries, or validation), then re-run this
auditor and `heal-skill`.

## Execution Steps

### Step 1: Pass 1 (heal-skill delegation)

```bash
bash skills/heal-skill/scripts/heal.sh --check --strict <target>
```

Gate on the exit code. Each stdout line `[CODE] <path>: <msg>` becomes one Pass-1 finding for the report.

### Step 2: Pass 2 (8 NEW checks)

For each `check_*` function in `scripts/audit.sh`, run against `<target>/SKILL.md`. Each emits `pass`, `warn`, or `fail` to stdout.

**Checkpoint:** Pass 2 must run independently of Pass 1 (no shared state); a heal strict failure does NOT short-circuit Pass 2, but it DOES force the aggregate verdict to FAIL.

### Step 3: Pass 3 (rubric scoring)

```bash
python3 scripts/score_agentops_skill.py <target> --audit-block
```

`audit.sh` calls this and embeds the result under the report's `rubric` key.
Each of the 10 rubric categories gets a 0-3 score + reason; total 0-30, rating
band C/B/A/S. If `python3` or the scorer is unavailable, `rubric` is emitted as
`null` (fail-open) and the JSON stays valid.

**Checkpoint:** Pass 3 is advisory — its score is computed but NOT counted in the verdict.

### Step 4: Aggregate verdict

```
fails > 0  → FAIL
warns > 0  → WARN
otherwise  → PASS
```

Density coverage and the Pass-3 rubric are computed before emission but are NOT counted in the verdict.

### Step 5: Emit report

JSON conforming to `schemas/audit-report.json` to stdout (or to file with `--json <path>`); markdown summary (including the Pass-3 rubric line) to stderr.

## Output Specification

**Format:** JSON conforming to `schemas/audit-report.json` (default) plus markdown text summary.
**Filename:** typically `.agents/audits/<skill-name>-audit.json` when `--json <path>` is supplied; otherwise stdout.
**Exit code:** 0 for PASS or WARN; 1 for FAIL (including any Pass-1 strict failure); 2 for usage error or missing target.

**Density advisory:** JSON includes `density.status`, `density.fields[]`, and
`density.summary`. Treat missing fields as review prompts, not gates.

**Rubric (Pass 3):** JSON includes `rubric.total_score`, `rubric.max_score`,
`rubric.rating`, `rubric.advisory` (always `true`), and `rubric.categories[]`
(10 entries, each `{category, score, reason}`). Emitted as `null` if the scorer
is unavailable. Treat the score as a productization backlog signal, not a gate.

## Quality Rubric

- [ ] Auditor never modifies target SKILL.md or any other file
- [ ] Pass 1 invokes heal.sh with `--check --strict` (NOT `--fix`) and gates on exit code
- [ ] All 8 Pass-2 checks emit one of: `pass`, `warn`, `fail`, `n/a`
- [ ] `description-has-triggers` accepts all three valid forms (verified by running auditor against AgentOps' existing single-line-description skills like `forge`, `heal-skill`, `council`)
- [ ] Aggregate verdict applies max-severity rule (no silent downgrade)
- [ ] Density advisory reports all six fields without changing the aggregate verdict
- [ ] Pass 3 emits all 10 rubric categories (0-3 + reason) under `rubric` without changing the aggregate verdict
- [ ] Report JSON validates against `schemas/audit-report.json`

## Examples

**Audit a single skill:**

```bash
$skill-auditor skills/forge
# stdout: VERDICT: WARN (3 Pass-2 warns)
# exit: 0
```

**Audit a candidate before promotion:**

```bash
bash skills/skill-auditor/scripts/audit.sh skills/my-new-skill --json /tmp/audit.json
# JSON report at /tmp/audit.json
```

**Strict mode (any finding → FAIL):**

```bash
bash skills/skill-auditor/scripts/audit.sh --strict skills/my-skill
# exits 1 on any WARN-level finding
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| All AgentOps skills fail check #1 | Auditor using old `description-multiline` logic | Verify check fn is `check_description_has_triggers`; should accept single-line + Triggers/Use-when markers + metadata.triggers array (per pre-mortem F1) |
| heal.sh exits 1 in Pass 1 | `--strict` found structural issues | Capture findings, continue Pass 2 for a complete report, and force aggregate FAIL |
| `references-modularization` fails on a 200-line skill | Check applies only when SKILL.md > 400 lines | Verify line count; status should be `n/a` for short skills |

## See Also

- [heal-skill](../heal-skill/SKILL.md) — Pass 1 delegate; structural hygiene only
- [skill-builder](../skill-builder/SKILL.md) — companion; produces skills the auditor validates
- [red-team](../red-team/SKILL.md) — complementary; probes USABILITY (does the workflow actually work) vs auditor (is the structure correct)

## References

- [references/skill-template.md](references/skill-template.md) — canonical SKILL.md template (copy of skill-builder's; per CLAUDE.md no-symlinks rule)
- [references/audit-checks.md](references/audit-checks.md) — per-check detection logic + accepted forms + PRODUCT.md mapping
- [references/context-density-checks.md](references/context-density-checks.md) — advisory density coverage logic and false-positive handling
- [references/skill-auditor.feature](references/skill-auditor.feature) — Executable spec: Pass 1 heal-skill delegation, Pass 2 structural checks, density report + productization score (soc-qk4b)

## Scripts

- `scripts/audit.sh`
- `scripts/score_agentops_skill.py`
- `scripts/validate.sh`
