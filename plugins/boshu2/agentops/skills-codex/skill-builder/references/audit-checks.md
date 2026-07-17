# Deep Skill Audit Checks

`audit.sh` runs the structural `heal.sh --check --strict` pass, eight content
checks, an advisory quality score, and advisory craft instrumentation. The
checks protect usability without rewarding ceremony or package size.

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

## Craft instrumentation (Pass 4, advisory)

`craft_score.py` adds three advisory blocks to the report. None of them ever
changes the verdict or exit code; they name gaps for the author and the fresh
validator to judge.

- **Craft score** — presence of the 12 craft elements enumerated in
  [skill-template.md](skill-template.md) section 7, reported as
  `craft n/12; missing: <element-ids>`. Detection is cheap pattern matching
  over authored prose (HTML comments are stripped, so `init.sh` scaffold stubs
  never count). Presence, never quality.
- **Provenance resolution** — repo paths and `.agents/ao` verdict/intent digest
  citations (full or abbreviated `prefix...suffix`) extracted from prose must
  resolve against the repository; each dead citation is a named finding.
  Fenced code blocks are treated as examples, not citations.
- **Loop safety** — any section with iteration prose (`repeat`, `iterate`,
  `loop`) must contain a checkable stop-condition phrase (`stop after`,
  `at most N`, `until ... exit 0`); an agent-dispatch loop must also carry a
  budget phrase. Vague goals ("until it feels done") do not count as stop
  conditions.

The scorer's detection power is itself mutation-tested:

```bash
bash skills/skill-builder/scripts/test-craft-mutations.sh
```

## Authoring prose scan (Pass 5, advisory)

`authoring_scan.py` adds an advisory `authoring` block naming mechanical
suspects for three failure modes from
[authoring-doctrine.md](authoring-doctrine.md). Like density and craft, it
never changes the verdict or exit code — the no-op test is model-relative and
prohibitions are sometimes correct guardrails, so a human (or fresh validator)
owns the judgment.

- **`noop-phrase`** — phrasing the model already obeys by default ("be
  thorough", "make sure to", "carefully"), reported with the offending line.
  The fix is a sharper, behavior-changing instruction, not a louder wish.
- **`negation-without-positive`** — a bullet/paragraph whose every clause
  prohibits ("Never edit generated files.") with no positive counterpart in
  the same unit. Pairing the prohibition with the target behavior ("Edit the
  source and regenerate; never edit generated files directly.") clears it.
- **`step-missing-done-condition`** — a `###` subphase under a
  Workflow/Process/Methodology/Execution section with no checkable
  done-condition phrasing ("Done when", "Checkpoint:", "Stop after",
  "until ... exit 0"). One finding per offending subphase.

Detection power is mutation-tested:

```bash
bash skills/skill-builder/scripts/test-authoring-mutations.sh
```

## Calibration rule

Before tightening a check, run it across every canonical skill. A proposed
rule that fails valid concise skills is miscalibrated unless the repository
contract itself requires those skills to change. Do not add boilerplate solely
to satisfy a heuristic.

```bash
for skill in skills/*; do
  [[ -f "$skill/SKILL.md" ]] || continue
  bash skills/skill-builder/scripts/audit.sh "$skill" >/dev/null
done
```
