---
type: reference
parent_skill: standards
title: SKILL.md tier-specific line caps
---

# SKILL.md Tier-Specific Line Caps

Source of truth: `tests/skills/lint-skills.sh:65-77` (case statement). The PreToolUse hook warns at 248 lines globally, but the binding cap is per-tier. A 260-line `meta`-tier skill is broken; a 260-line `execution`-tier skill is fine.

## Caps by tier

| Tier | Cap (lines) |
|---|---|
| `library`, `meta` | 250 |
| `background` | 300 |
| `execution`, `experimental` | 800 |
| `judgment`, `product`, `session`, `knowledge`, `contribute`, `cross-vendor`, `orchestration` | 1050 |

## Why per-tier instead of global

- `meta` and `library` skills are short reference contracts; long bodies indicate misuse.
- `background` skills are autoloaded — long bodies bloat the always-loaded context.
- `execution` skills run multi-step workflows; their bodies legitimately need more room for steps and examples.
- `judgment`/`product`/`session` skills carry decision frameworks and personas that benefit from narrative depth.

## How to plan trimming work

1. Read the skill's `tier:` frontmatter.
2. Look up the tier's cap in the table above.
3. If `wc -l SKILL.md` exceeds the cap, plan trimming. Otherwise no work needed.

The 248-line PreToolUse warning is global pre-lint awareness only — it does not mean the skill is in violation.

## Cross-references

- Lint enforcement: `tests/skills/lint-skills.sh:65-77`
- Schema enum: `scripts/validate-skill-schema.sh:174-178` (the binding `metadata.tier` enum)
- Narrative tier categories: `skills/SKILL-TIERS.md` (note: "utility category" there is a grouping, not a binding tier value)
