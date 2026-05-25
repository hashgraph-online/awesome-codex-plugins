---
name: skill-auditor
description: 'Audit a SKILL.md (15 checks).'
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
- **Pass 1 delegates, never reimplements.** The auditor calls `$heal-skill --check <target>` and parses its output. **Why:** PR-006 (cross-layer consistency) — heal-skill's checks are the source of truth for structural hygiene; reimplementation creates drift.
- **Pass 2 must accept AgentOps' existing conventions.** Specifically `description-has-triggers` accepts THREE valid forms (YAML `|` block scalar OR `Triggers:`/`Use when:` markers OR `metadata.triggers` array with 3+ items). **Why:** finding `f-2026-05-06-auditor-checks-must-fit-host-conventions` — auditor checks must validate against the host substrate's existing valid artifacts before promotion to required gate.
- **Verdict aggregation rule:** any check returns `fail` → FAIL; otherwise any returns `warn` → WARN; otherwise PASS. **Why:** prevents silent severity downgrade.
- **Density coverage is advisory-only.** Missing density fields never changes
  the PASS/WARN/FAIL verdict and does not satisfy packet-boundary enforcement
  in `soc-2c1p.1`. **Why:** the hard Context Density Rule belongs at execution
  packet boundaries; this skill only helps reviewers find low-signal prose.

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
verbatim from `docs/reference/skill-quality-rubric.md`: `trigger_quality`,
`kernel_clarity`, `progressive_disclosure`, `helper_scripts`, `validation`,
`self_test`, `assets_templates`, `subagents_roles`, `safety_boundaries`,
`packaging`. Each scores 0-3 with a reason; total 0-30, rating C/B/A/S. The
score is **advisory** — it never changes the PASS/WARN/FAIL verdict.

Standalone markdown for picking the smallest productization patch:

```bash
python3 skills-codex/skill-auditor/scripts/score_agentops_skill.py skills/<name> --markdown
```

## Execution Steps

### Step 1: Pass 1 (heal-skill delegation)

```bash
bash skills/heal-skill/scripts/heal.sh --check <target>
```

Capture stdout. Each line `[CODE] <path>: <msg>` becomes one Pass-1 finding.

### Step 2: Pass 2 (8 NEW checks)

For each `check_*` function in `scripts/audit.sh`, run against `<target>/SKILL.md`. Each emits `pass`, `warn`, or `fail` to stdout.

**Checkpoint:** Pass 2 must run independently of Pass 1 (no shared state); a heal.sh failure does NOT short-circuit Pass 2.

### Step 3: Pass 3 (rubric scoring)

`audit.sh` runs `python3 scripts/score_agentops_skill.py <target> --audit-block`
and embeds the result under the report's `rubric` key (10 categories, 0-3 each,
0-30 total, C/B/A/S rating). Emitted as `null` if `python3`/scorer is missing.

**Checkpoint:** Pass 3 is advisory — its score is computed but NOT counted in the verdict.

### Step 4: Aggregate verdict

```
fails > 0  → FAIL
warns > 0  → WARN
otherwise  → PASS
```

Density coverage and the Pass-3 rubric are computed before emission but are NOT counted in the verdict.

### Step 5: Emit report

JSON conforming to `schemas/audit-report.json` to stdout (or to file with `--json <path>`); markdown summary to stderr.

## Output Specification

**Format:** JSON conforming to `schemas/audit-report.json` (default) plus markdown text summary.
**Filename:** typically `.agents/audits/<skill-name>-audit.json` when `--json <path>` is supplied; otherwise stdout.
**Exit code:** 0 for PASS or WARN; 1 for FAIL; 2 for usage error or missing target.

**Density advisory:** JSON includes `density.status`, `density.fields[]`, and
`density.summary`. Treat missing fields as review prompts, not gates.

## Quality Rubric

- [ ] Auditor never modifies target SKILL.md or any other file
- [ ] Pass 1 invokes heal.sh with `--check` (NOT `--fix`)
- [ ] All 8 Pass-2 checks emit one of: `pass`, `warn`, `fail`, `n/a`
- [ ] `description-has-triggers` accepts all three valid forms (verified by running auditor against AgentOps' existing single-line-description skills like `forge`, `heal-skill`, `council`)
- [ ] Aggregate verdict applies max-severity rule (no silent downgrade)
- [ ] Density advisory reports all six fields without changing the aggregate verdict
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
| heal.sh exits 1 even with `--check` | heal.sh has its own `--strict` mode | The auditor calls heal.sh WITHOUT `--strict`; if heal.sh exits non-zero, capture findings but continue Pass 2 |
| `references-modularization` fails on a 200-line skill | Check applies only when SKILL.md > 400 lines | Verify line count; status should be `n/a` for short skills |

## See Also

- heal-skill — Pass 1 delegate; structural hygiene only
- skill-builder — companion; produces skills the auditor validates
- red-team — complementary; probes USABILITY (does the workflow actually work) vs auditor (is the structure correct)

## Local Resources

### references/

- [references/skill-template.md](references/skill-template.md) — canonical SKILL.md template (copy of skill-builder's; per CLAUDE.md no-symlinks rule)
- [references/audit-checks.md](references/audit-checks.md) — per-check detection logic + accepted forms + PRODUCT.md mapping
- [references/context-density-checks.md](references/context-density-checks.md) — advisory density coverage logic and false-positive handling

### scripts/

- `scripts/audit.sh`
- `scripts/score_agentops_skill.py`
- `scripts/validate.sh`
