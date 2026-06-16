---
name: eval-outcomes
description: "Run eval outcomes."
---

# eval-outcomes — moved to Mount Olympus (2026-06-10)

## Holdout scenario management (absorbed from scenario, ag-s43tg)

Author and manage holdout scenarios with the `ao` CLI: `ao scenario add "<title>"`
creates a scenario in `.agents/holdout/` (ID `s-YYYY-MM-DD-NNN`, acceptance
vectors, 0.8 default satisfaction threshold); `ao scenario validate` checks the
holdout set's schema and link graph. Linked scenarios feed directive fitness via
`ao goals scenarios` (see the `$goals` skill and `docs/adr/ADR-0003`).

Canonical home: the mt-olympus repository, project skill `eval-outcomes`
(`~/dev/mt-olympus/` repo, project skills directory). Read and follow the
canonical SKILL.md there. This stub preserves routing and twin parity until
the catalog closer updates the registry (skill-prune Lane A,
evidence/skill-prune-recon.md).
