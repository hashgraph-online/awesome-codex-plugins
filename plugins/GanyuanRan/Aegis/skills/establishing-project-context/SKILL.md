---
name: establishing-project-context
description: Use when entering a project for the first time, or when the user asks to establish shared language, define domain terms, or create a project glossary.
---

# Establishing Project Context

## Overview

Maintain a `CONTEXT.md` file at the project root that defines the project's domain language — a single source of truth for terminology shared between the agent and the human. Borrowed from Domain-Driven Design's "ubiquitous language" principle.

CONTEXT.md is about the user's project domain, NOT about Aegis governance. For Aegis governance docs, see `docs/current/` and `docs/adr/`.

## Where CONTEXT.md Lives

- **Single project**: `<project_root>/CONTEXT.md`
- **Monorepo / multiple bounded contexts**: `<project_root>/CONTEXT-MAP.md` maps context names to their locations:

  ```
  ordering → src/ordering/CONTEXT.md
  billing  → src/billing/CONTEXT.md
  ```

  System-wide terms still go in root `CONTEXT.md`.

Create files lazily — only when you have something to write.

## When to Use

**On first entering a project:**

1. Check if `CONTEXT.md` (or `CONTEXT-MAP.md`) exists
2. If not, ask briefly: "Want me to set up a shared language glossary for this project?"
3. If yes, start with 3-5 core domain terms, then iterate

**During brainstorming / planning / debugging:**

- When user uses a vague or overloaded term, propose a precise canonical term
- Check against existing CONTEXT.md glossary before proposing
- Write each term resolution immediately — don't batch

## CONTEXT.md Format

See `CONTEXT-FORMAT.md` in this directory for the canonical template.

Key rules:
- Only include terms meaningful to domain experts
- Don't couple CONTEXT.md to implementation details
- Each term: name, one-sentence definition, and what to avoid calling it
- Record resolved ambiguities so they aren't re-litigated

## Integration with Aegis Workflows

- **brainstorming**: Reads CONTEXT.md in Step 1 (Explore project context), tightens terminology during Step 4 (Ask clarifying questions)
- **writing-plans**: Uses CONTEXT.md terms in plan task descriptions
- **systematic-debugging**: References CONTEXT.md for canonical component names

## Boundary: CONTEXT.md vs baseline/

CONTEXT.md and `docs/aegis/baseline/` serve different purposes:

| | CONTEXT.md | baseline/ |
|---|-----------|-----------|
| What | Domain language, ubiquitous terminology | Technical architecture snapshot |
| Audience | Domain experts + agents | Agents + developers |
| Content | Terms, definitions, resolved ambiguities | Ownership, contracts, dependencies, anti-patterns |
| Updates | Immediately on term resolution | After architecture review or material change |
| Trigger | establishing-project-context skill | brainstorming, writing-plans, code-review, systematic-debugging |

Do NOT put implementation details in CONTEXT.md.
Do NOT put domain glossary terms in baseline/.

## Red Flags

- Don't turn CONTEXT.md into architecture documentation (that's ADRs)
- Don't add implementation details (class names, file paths, config keys)
- Don't batch term updates — write immediately when resolved
- Don't create CONTEXT.md without user consent
