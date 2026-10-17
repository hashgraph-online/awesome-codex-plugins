---
name: onboard
description: Use when taking over an existing codebase that has no living document. Produces a factual record of what already exists.
---
# Onboard

Goal: read the codebase, produce living documentation. No code changes. No plans. No gap analysis.

## living documentation

- `README.md` : project overview, what it is, who it's for, how to use it.
- `docs/tech-spec.md` : main technical specification (core backbone, ≤300 lines).
- `docs/specs/*.md` : modular subsystem details split out when bulky (>15 lines). Referenced by path.

Technical specification is declarations only: current ground truth facts (atemporal, no narrative, no history, no plans).

## Steps

1. **Explore** entry points, public interfaces, key dependencies, test patterns, file structure. Read, don't guess.
2. **Ask the user** about anything ambiguous — never invent architecture.
3. **Write** `docs/tech-spec.md` using the canonical format (field meanings: `archive` skill, "tech-spec format"):

```
purpose / user / use-case / architecture / stack / entry /
contract / flow / invariant / constraint / convention
```

   - Omit `milestone` — onboard makes no plans.
   - Details >15 lines (schemas, algorithms, protocol states) go to `docs/specs/<topic>.md`.
   - Keep declarations atomic (≤25 words/sentence) with structured lists/tables; no text walls.

4. **Confirm** with user.

<gate>`docs/tech-spec.md` must contain: `stack` + at least one `contract` + at least one `convention` (covering quality baseline — lint/format/typecheck tools, error-handling, security — read from code; see `../references/quality.md`) before done.</gate>

## Don't
- Invent facts not found in code or README.
- Add gap analysis, temporal/historical narratives, plans, or code changes.
- Paste large code blocks or schemas — reference by path or modularize into `docs/specs/`.

## After
`docs/tech-spec.md` on disk → user continues with normal `design → plan → tdd`.
