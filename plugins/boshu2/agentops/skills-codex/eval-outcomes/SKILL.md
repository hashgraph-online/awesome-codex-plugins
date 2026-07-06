---
name: eval-outcomes
description: Grade agent or model output against Outcomes
---
# eval-outcomes — moved to Mount Olympus (2026-06-10)

## Holdout scenario management (absorbed from scenario, ag-s43tg)

Author and manage holdout scenarios with the `ao` CLI: `ao eval scenario add "<title>"`
creates a scenario in `.agents/holdout/` (ID `s-YYYY-MM-DD-NNN`, acceptance
vectors, 0.8 default satisfaction threshold); `ao eval scenario validate` checks the
holdout set's schema and link graph. Linked scenarios feed directive fitness via
`ao goals scenarios` (see the `$goals` skill and `docs/adr/ADR-0003`).

## Absorbed skills (ag-s43tg)

- **scenario** — Manage holdout scenarios; author and manage holdout scenarios with measurable acceptance vectors and satisfaction scoring in `.agents/holdout/` for behavioral validation.

This skill encodes independent-verdict machinery and now lives with the outer
gate product. Canonical: `~/dev/mt-olympus/.codex/skills/eval-outcomes/SKILL.md` —
read and follow that file. This stub preserves fleet routing until the
using-agentops catalog closer updates the registry (skill-prune Lane A,
evidence/skill-prune-recon.md).

## Folded-In Trigger Surface (scenario)

eval-outcomes is the fold target for the retired standalone `scenario` skill
(skill-prune phase 2). Fire this skill for its use-cases:

- **Scenario — Manage holdout scenarios.** Author and manage holdout scenarios
  for behavioral validation: scenarios define **what** the system should do in
  narrative form, with measurable acceptance vectors and satisfaction scoring.
  They live in `.agents/holdout/*.json` so implementing agents cannot see them
  during development. When asked to author, manage, or score holdout scenarios,
  fire this skill.
