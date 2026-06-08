# Unified SKILL.md Template + Auditor Checklist

> **Source:** `anthropics/financial-services` @ commit `bb4a2b3e53cf27f8900b33ed6a2d95ed32e57f1d` (cloned 2026-05-06). Re-extract diff if upstream restructures.
> **Methodology:** Combines content discipline from financial-services (front-loaded constraints, verification checkpoints, output spec, quality rubric) with AgentOps' structured frontmatter (skill_api_version, context, metadata, output_contract).

This is the canonical template `skill-builder` materializes and `skill-auditor` validates against. Two artifacts in one document because both skills need identical truth.

---

## 1. Canonical SKILL.md template

```markdown
---
name: <slug-with-hyphens>
description: |
  <one-line: verb + object + domain>

  **Use when:**
  - <Trigger 1>
  - <Trigger 2>

  **Perfect for:**
  - <Scenario 1>

  **Not ideal for:**
  - <Anti-scenario 1>
skill_api_version: 1
user-invocable: <true|false>
context:
  window: <isolated|fork|inherit>
  intent:
    mode: <none|task|questions>
  sections:
    exclude: [HISTORY]
  intel_scope: <none|topic|full>
metadata:
  tier: <judgment|execution|library|session|product|contribute|meta|background|orchestration|cross-vendor|knowledge>
  dependencies: [<other-skill-names>]
  stability: <experimental|stable>
output_contract: <path-to-schema-or-description>
---

# <Title matching slug>

<1-2 sentence purpose paragraph>

## Overview / When to Use

<Detailed explanation of what + why + when>

## ⚠️ Critical Constraints

<Safety rules, data quality, governance — front-loaded, NOT buried>

- **Rule N:** <constraint>. **Why:** <rationale tied to a real consequence>

## Workflow / Methodology

<Step-by-step with verification checkpoints between phases>

### Phase 1: <name>
<instructions>
**Checkpoint:** <what to confirm before next phase>

### Phase 2: <name>
...

## Output Specification

<Format + filename + structure — explicit>

**Format:** <markdown | json | excel | etc.>
**Filename:** <naming convention>
**Structure:** <key sections / fields>

## Quality Rubric

<Checklist of deliverable criteria + sanity checks + common mistakes>

- [ ] <Check 1>
- [ ] <Check 2>

## Examples

<Usage scenarios>

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|

## See Also / References

<Cross-skill links + references/*.md links>
```

---

## 2. Auditor 15-check checklist

Audits run in **two passes**. Pass 1 runs `heal-skill --check --strict` for structural hygiene and gates on the exit code. Pass 2 adds 8 NEW checks not covered by heal.

### Pass 1 — delegated to heal-skill (7 checks)

| Check | heal.sh code | Severity |
|-------|--------------|----------|
| Frontmatter `name` present | MISSING_NAME | FAIL |
| Frontmatter `description` present | MISSING_DESC | FAIL |
| `name` matches directory | NAME_MISMATCH | FAIL |
| All `references/*.md` linked from SKILL.md | UNLINKED_REF | WARN |
| References point at existing files | DEAD_REF | WARN |
| Scripts referenced exist | SCRIPT_REF_MISSING | WARN |
| User-invocable in catalog | CATALOG_MISSING | WARN |

### Pass 2 — 8 NEW checks beyond heal-skill

> The check id `description-has-triggers` (NOT `description-multiline`) is the canonical name. AgentOps' established convention is single-line `description: '...'`; the auditor must NOT false-fail that style. Three valid forms are accepted (any one passes).

| # | Check id | What passes | Severity |
|---|----------|-------------|----------|
| 1 | `description-has-triggers` | ANY of: (a) YAML `\|` block scalar in `description`, (b) body of `description` contains `Triggers:` / `Use when:` / `Perfect for:` markers, (c) `metadata.triggers` array with 3+ items | FAIL |
| 2 | `constraints-frontloaded` | First H2 within 80 lines after closing frontmatter `---` contains `Constraints` or `⚠️` | WARN |
| 3 | `rationale-present` | Each constraint bullet contains `why`, `because`, `this matters`, or similar rationale token | WARN |
| 4 | `verification-checkpoints` | If skill has multi-phase Workflow/Methodology, body contains `Checkpoint`, `confirm`, or `Wait for` markers between phases | WARN |
| 5 | `output-spec-explicit` | Has `## Output` / `## Deliverables` / `## Returns` H2 mentioning format AND filename/path convention | FAIL |
| 6 | `quality-rubric` | Has `## Quality` / `## Checklist` / `## Rubric` / `## Best Practices` H2 with 3+ bullet items | WARN |
| 7 | `references-modularization` | If SKILL.md > 400 lines, `references/` subdirectory exists | WARN |
| 8 | `trigger-clarity` | Frontmatter `description` contains explicit `Use when:` or `Triggers:` markers an LLM can match | FAIL |

### Verdict rule

```
fails > 0   → FAIL
warns > 0   → WARN
otherwise   → PASS
```

---

## 3. PRODUCT.md alignment mapping

Each NEW Pass-2 check maps to AgentOps' design principles in PRODUCT.md, so the auditor enforces architectural intent rather than arbitrary stylistic preferences.

| Auditor check | PRODUCT.md anchor |
|---------------|-------------------|
| `constraints-frontloaded` (⚠️ near top) | Operational Principle #6 (atomic changes compose) — constraint visibility prevents large rework |
| `rationale-present` | Operational Principle #1 (agents are ephemeral; system carries state) — rationale must be inside the artifact, not in human memory |
| `verification-checkpoints` | Operational Principle #5 (two-tier execution) — checkpoints prevent worker drift between phases |
| `output-spec-explicit` | Pillar #4 (Kubernetes control loops) — declared state must be machine-readable |
| `quality-rubric` | Operational Principle #3 (context quality determines output quality) |
| `references-modularization` | Finding `f-2026-05-01-025` (SKILL.md churn budget — every Skill() invocation reloads 5-15KB) |
| `trigger-clarity` | Operational Principle #1 (agents are ephemeral) — invocation criteria must be in artifact |
| `description-has-triggers` (renamed from `description-multiline`) | Pillar #6 (knowledge flywheel) — searchability requires structured description. Three valid forms preserve AgentOps' single-line convention. |

---

## 4. Section spine — REQUIRED order

```
H1 title
└── Overview / When to Use
└── ⚠️ Critical Constraints      ← MUST appear within first 80 lines after frontmatter
└── Workflow / Methodology       ← MUST contain checkpoints between phases when multi-phase
└── Output Specification         ← MUST include format + filename
└── Quality Rubric               ← MUST contain 3+ bullets
└── Examples
└── Troubleshooting
└── See Also / References
```

The `## Examples` and `## Troubleshooting` sections are recommended but not enforced (heal-skill catches missing references; the auditor leaves these to taste).

---

## 5. Frontmatter requirements (cross-reference)

Validates against `schemas/skill-frontmatter.v1.schema.json`. Required fields:

- `name` (string, lowercase-hyphen, must match directory)
- `description` (string, see check #1 for accepted forms)
- `skill_api_version` (integer, const: 1)

Plus expected:

- `metadata.tier` (one of the 11 enum values)
- `context.window` (one of: `isolated`, `fork`, `inherit`)
- `output_contract` (path to JSON Schema or description string)

---

## 6. Codex parity contract (per learning `2026-05-03-codex-skill-shape-is-dual-file`)

For every shipped AgentOps skill, both files must exist:

- `skills-codex/<name>/SKILL.md` — slim frontmatter (NO `skill_api_version`)
- `skills-codex/<name>/prompt.md` — short Execution Profile (~10-20 lines)

`scripts/audit-codex-parity.sh` is a content scanner; it will NOT catch frontmatter shape violations. Explicit grep checks (no `skill_api_version:` in codex SKILL.md; `prompt.md` exists) belong in the skill's own validation block.

---

## 7. Out-of-scope for v1 (stocktake territory)

The following deeper audits are described in `skills/heal-skill/references/skill-stocktake.md` but NOT yet implemented anywhere — defer to v2:

- Actionability (does it produce concrete artifacts?)
- Scope fit (right tier for the task?)
- Uniqueness (overlap with other skills?)
- Currency (referenced tools/APIs still current?)
- LLM-decidable trigger clarity (deeper than `trigger-clarity` check above)
