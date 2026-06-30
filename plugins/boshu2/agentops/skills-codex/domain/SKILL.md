---
name: domain
description: Canonical vocabulary for human-AI software
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

- [references/domain.feature](references/domain.feature) — Executable spec: load-on-demand corpus, draft→canonical ratchet, vocabulary root (soc-qk4b)
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
- [`references/behavior-shaping.md`](references/behavior-shaping.md) — Behavior Shaping: the ABC register (antecedent/behavior/consequence/reinforcement/extinction/shaping); building agent capability is operant conditioning, not specification
- [`references/primitive-selection.md`](references/primitive-selection.md) — Primitive Selection: when to use a Skill vs CLI subcommand vs runtime hook vs local cockpit gate vs CI backstop (CLI is the deterministic core; gates are trigger surfaces that call it)
- [`references/reach.md`](references/reach.md) — Reach: the blast-radius tier of a knowledge entry (`bead`/`pull`/`always`), orthogonal to maturity; `always` is computed from verification-earned canon, never authored

Loop family (the operating loop — "one loop body, two drivers, one inner tick, one config"; doctrine in `docs/architecture/canonical-loop-model.md`):

- [`references/loop.md`](references/loop.md) — Loop: the umbrella; the same five-beat tick at every scale
- [`references/evolve.md`](references/evolve.md) — Evolve: the in-session driver (AgentOps-shipped, zero-dependency)
- [`references/factory.md`](references/factory.md) — Factory: the out-of-session driver (substrate-owned; AgentOps deleted its daemon)
- [`references/rpi.md`](references/rpi.md) — RPI: the inner tick, one research-plan-implement-validate cycle over one bead
- [`references/autodev.md`](references/autodev.md) — Autodev: the config/intent layer the loop reads each tick (NOT a loop)
- [`references/context-compiler.md`](references/context-compiler.md) — Context-Compiler: turns the corpus into the working set and absorbs the tick's exhaust

Verification membrane:

- [`references/silent-contract-violation.md`](references/silent-contract-violation.md) — Silent Contract Violation: tool-use code that runs clean, raises no exception, and is still wrong (wrong routing / output shape / argument provenance); the four contract-check categories that name where it lands (RubricRefine)

Catalog:

- [`references/INDEX.md`](references/INDEX.md) — full corpus index

## Domain as a scoped operating-loop contract

The `Slice` primitive above has a runtime counterpart: a **domain slice** can
scope an operating-loop run. A *domain* is a named vertical slice with an
explicit boundary contract — a manifest at
`docs/domains/<name>/manifest.yaml` listing the Primitives the slice may touch,
its goal, and its decision gate.

Use `$scaffold domain <name>` to write the manifest template, then fill in the
boundary before running the operating loop with that manifest as explicit scope.
For out-of-session execution, dispatch the scoped loop through NTM plus Agent
Mail reservations so write ownership and the slice boundary are visible. The
manifest schema and resolution rules are in `docs/adr/ADR-0004`; the `$scaffold`
skill documents the bootstrap step.

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
