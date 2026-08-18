# Unified SKILL.md Template + Auditor Checklist

> **Authority:** Executable rule IDs, severities, trigger forms, output-handoff
> requirements, clean-room behavior, and the 250-line limit come from
> [skill-conformance-profiles.yaml](skill-conformance-profiles.yaml).

This is the canonical template `skill-builder` materializes and its deep audit mode validates against. Two artifacts in one document because both modes need identical truth.

This template governs *structure*. The prose inside that structure is governed
by [authoring-doctrine.md](authoring-doctrine.md) — the no-op test, negation,
completion criteria, leading words, description discipline, and the context
load vs cognitive load decision. Apply both when authoring or healing a skill.

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

<Complete executable handoff>

**Artifact directory:** <directory or path>
**Filename convention:** <naming convention>
**Serialization/schema format:** <format and schema>
**Validator command:** <exact validator invocation>
**Downstream handoff:** <consumer or next workflow>

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

Audits run in **two passes**. Pass 1 runs `heal.sh --check --strict` for structural hygiene and gates on the exit code. Pass 2 adds 8 NEW checks not covered by heal.

### Pass 1 — delegated to heal.sh (7 checks)

| Check | heal.sh code | Severity |
|-------|--------------|----------|
| Frontmatter `name` present | MISSING_NAME | FAIL |
| Frontmatter `description` present | MISSING_DESC | FAIL |
| `name` matches directory | NAME_MISMATCH | FAIL |
| All `references/*.md` linked from SKILL.md | UNLINKED_REF | WARN |
| References point at existing files | DEAD_REF | WARN |
| Scripts referenced exist | SCRIPT_REF_MISSING | WARN |
| User-invocable in dispositions ledger | MISSING_DISPOSITION | FAIL in strict mode |

### Pass 2 — 8 NEW checks beyond heal.sh

> The check id `description-has-triggers` (NOT `description-multiline`) is the canonical name. AgentOps' established convention is single-line `description: '...'`; the auditor must NOT false-fail that style. Three valid forms are accepted (any one passes).

| # | Check id | What passes | Severity |
|---|----------|-------------|----------|
| 1 | `description-has-triggers` | A profile-accepted marker inside the description value, or a metadata list meeting the profile minimum | Profile |
| 2 | `constraints-frontloaded` | Kernels over 100 lines put `Constraints` or `⚠️` within the first 80 body lines; concise kernels pass | Profile |
| 3 | `rationale-present` | Each constraint bullet contains `why`, `because`, `this matters`, or similar rationale token | Profile |
| 4 | `verification-checkpoints` | If skill has multi-phase Workflow/Methodology, body contains `Checkpoint`, `confirm`, or `Wait for` markers between phases | Profile |
| 5 | `output-spec-explicit` | Nonempty `output_contract`, or one output section supplies every profile-required component | Profile |
| 6 | `quality-rubric` | Kernels over 100 lines have 3+ bullets under Quality/Checks/Checklist/Rubric/Best Practices/Acceptance; concise kernels pass | Profile |
| 7 | `references-modularization` | SKILL.md is at or below the profile's 250-line kernel limit | Profile |
| 8 | `trigger-clarity` | Frontmatter `description` contains a profile-accepted marker an LLM can match | Profile |

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
└── Output Specification         ← MUST include the complete executable handoff
└── Quality Rubric               ← MUST contain 3+ bullets
└── Examples
└── Troubleshooting
└── See Also / References
```

The `## Examples` and `## Troubleshooting` sections are recommended but not enforced (heal.sh catches missing references; the auditor leaves these to taste).

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

## 7. The 12 craft elements (advisory Pass-4 instrumentation)

`scripts/craft_score.py` detects the presence of these 12 authoring elements
(never their quality) and reports an advisory `craft n/12` with named gaps in
the deep audit. `scripts/init.sh` scaffolds one `<!-- craft:<id> ... -->` stub
per element; the scorer strips HTML comments, so stubs never satisfy an
element — only authored prose counts.

| # | Element id | One-line authoring prompt |
|---|------------|---------------------------|
| 1 | `causal-insight-line` | State the one causal insight that makes this skill work (`Insight:` / `**Why:**` / a `because` clause). |
| 2 | `named-failure-mode` | Name the concrete failure mode this skill exists to prevent (`fails when`, `failure mode`, a Failure behavior section). |
| 3 | `frozen-prompts` | Provide any reusable prompt as a fenced block marked copy-paste-only. |
| 4 | `named-loop-stop-condition` | If the skill iterates, name the loop and give a checkable stop condition in the same section (`stop after`, `at most N passes`, `until ... exit 0`). |
| 5 | `quantified-rules` | Quantify at least one rule with a number and unit (`at most 3 attempts`, `250 lines`). |
| 6 | `negative-space` | State what this skill is NOT for (`non-goals`, `not for`, `do not use when`). |
| 7 | `anti-pattern-with-corrective` | Pair each anti-pattern with its corrective in the same section (`avoid X; instead Y`). |
| 8 | `provenance-citation` | Cite at least one resolvable source: a repo path or a `.agents/ao` verdict/intent digest (abbreviated `prefix...suffix` accepted). |
| 9 | `measurable-done` | Give a machine-checkable done signal (`done when`, `exit 0`, a validator command). |
| 10 | `router-shape` | Map trigger phrases to modes/entry points in a routing table or Modes section. |
| 11 | `trigger-rich-description` | Put `Triggers:` / `Use when` phrases callers actually say in the frontmatter description. |
| 12 | `runnable-commands` | Include at least one fenced block with runnable commands. |

---

## 8. Out-of-scope for v1 (stocktake territory)

The following deeper audits are described in a future `skills/skill-builder/references/skill-stocktake.md` but NOT yet implemented anywhere — defer to v2:

- Actionability (does it produce concrete artifacts?)
- Scope fit (right tier for the task?)
- Uniqueness (overlap with other skills?)
- Currency (referenced tools/APIs still current?)
- LLM-decidable trigger clarity (deeper than `trigger-clarity` check above)
