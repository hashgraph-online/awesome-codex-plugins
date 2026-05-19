---
name: domain
description: 'Shared agent-work vocabulary.'
---
# Domain Skill — Ubiquitous Language for Human-AI Software Building

This is a **library skill**. It doesn't run standalone — it holds the shared
vocabulary that you, the agent, and other skills cite when describing work.

## Why this exists

AgentOps's existing skills (research, plan, crank, validate, ...) are verbs.
This skill holds the nouns and the discipline they operate on. When a session
talks about "this is a tracer bullet" or "we need a vertical slice through the
eval surface," the meaning is fixed here, not improvised.

## Status

**Tracer bullet shape with one canonical operating concept.** This skill currently holds:

- 6 structural primitives (Entry, Index, Citation, Primitive, Slice, Anti-Pattern)
- 1 test entry (Tracer Bullet) written using only citations to the 6 primitives
- 1 canonical operating concept (Context Density Rule)

If the test entry can describe its own concept using only the primitives, the
shape works and we grow the corpus by adding more entries — never new
structural primitives without operator consent.

## How to use this skill

1. Read `references/INDEX.md` first — it lists every entry by kind and status.
2. Load only the entries relevant to the current work. Do not preload the
   whole corpus — that defeats the JIT purpose.
3. When applying an entry, cite it: include the entry slug in your output, plan,
   commit message, or `bd` issue body so future sessions can trace the
   reasoning.
4. When you find a concept missing or misnamed, add a draft entry under
   `references/` and update `INDEX.md`. Promotion from `draft` to `canonical`
   requires operator approval.

## Entries (tracer-bullet set)

Structural primitives (the architecture):

- [`references/entry.md`](references/entry.md) — Entry: the atomic concept doc
- [`references/index-primitive.md`](references/index-primitive.md) — Index: the discovery surface (concept)
- [`references/citation.md`](references/citation.md) — Citation: how Entries reference each other and how agents claim use

Vocabulary nouns (the working units):

- [`references/primitive.md`](references/primitive.md) — Primitive: atomic capability (skill, hook, CLI command, eval suite)
- [`references/slice.md`](references/slice.md) — Slice: vertical work unit cutting through multiple Primitives
- [`references/anti-pattern.md`](references/anti-pattern.md) — Anti-Pattern: documented mistake with cost when ignored

Test entry:

- [`references/tracer-bullet.md`](references/tracer-bullet.md) — Tracer Bullet: described using only citations to the six primitives above

Operating discipline:

- [`references/context-density-rule.md`](references/context-density-rule.md) — Context Density Rule: every context token carries intent, boundary, evidence, decision, constraint, or next action

Catalog:

- [`references/INDEX.md`](references/INDEX.md) — full corpus index

## What's NOT here

- Procedural how-tos (those live in other skills)
- Repo conventions (those live in `skills/standards/`)
- Findings, learnings, patterns (those live in `.agents/`)
- Product framing (lives in `PRODUCT.md`)

## See also

- `skills/standards/SKILL.md` — repo coding standards (sibling library skill)
- `docs/architecture/primitive-chains.md` — concrete AgentOps primitive layers
  (Mission/Discovery/Risk/Execution/Validation/Learning/Ratchet/Continuity)
  that compose the domain into chains
