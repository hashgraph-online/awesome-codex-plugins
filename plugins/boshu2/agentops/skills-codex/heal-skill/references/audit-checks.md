# Deep Skill Audit Checks

`audit.sh` runs the structural `heal.sh --check --strict` pass, eight content
checks, and an advisory quality score. The checks protect usability without
rewarding ceremony or package size.

Executable thresholds and severities come from
`skills/skill-builder/references/skill-conformance-profiles.yaml`.

## Verdicts

| Severity | Result |
|---|---|
| FAIL | The skill contract is incomplete or unsafe. |
| WARN | A concrete usability issue should be reviewed. |
| PASS | No configured defect was found. |

`--strict` makes WARN exit nonzero. Advisory scoring never changes the verdict.

## Checks

### `description-has-triggers` and `trigger-clarity` (WARN)

The frontmatter description must state when the skill should load. Accepted
forms are an inline or block `Triggers:` / `Use when:` marker, or—for the first
check only—a `metadata.triggers` list accepted by the active profile.

### `constraints-frontloaded` (WARN)

Skills longer than 100 lines need an early `Constraints` or `⚠️` section within
the first 80 body lines. Concise kernels pass without a ceremonial section
because their boundaries are already visible in one read.

### `rationale-present` (WARN)

When a constraints section contains bullets, at least half should explain why
the constraint exists. A skill with no constraint bullets passes this check.

### `verification-checkpoints` (WARN)

A workflow with two or more named subphases should contain a checkpoint or an
explicit verify-before boundary. One-step procedures pass without a checkpoint.

### `output-spec-explicit` (FAIL)

A nonempty frontmatter `output_contract` passes. Skills without that AgentOps
field must instead provide one output section containing every component
required by the selected profile. This lets small inline adapters declare a
sentence-shaped result without inventing an artifact directory, filename,
schema, validator, and downstream controller.

### `quality-rubric` (WARN)

Skills longer than 100 lines need at least three bullets under `Quality`,
`Checks`, `Checklist`, `Rubric`, `Best Practices`, or `Acceptance`. Concise
kernels pass because their evidence and stop conditions are directly visible.

### `references-modularization` (WARN)

The canonical repo-runtime kernel limit is 250 lines. Move genuinely detailed
material into linked references instead of expanding the always-loaded kernel.

## Calibration rule

Before tightening a check, run it across every canonical skill. A proposed
rule that fails valid concise skills is miscalibrated unless the repository
contract itself requires those skills to change. Do not add boilerplate solely
to satisfy a heuristic.

```bash
for skill in skills/*; do
  [[ -f "$skill/SKILL.md" ]] || continue
  bash skills/heal-skill/scripts/audit.sh "$skill" >/dev/null
done
```
