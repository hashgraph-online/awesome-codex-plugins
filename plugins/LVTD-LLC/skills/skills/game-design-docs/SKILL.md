---
name: game-design-docs
description: Create lightweight, living game design documents for AI-built games. Use when writing a game design brief, system spec, feature contract, content schema, implementation handoff, decision log, or when a coding agent needs durable project memory.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Game Design Docs
  category: Game Development
  tags: game-design,documentation,specs,ai-agents,production
---

# Game Design Docs

Use this skill to create documents that help an AI game-building agent make consistent decisions across sessions. The document should be short enough to stay current and specific enough to constrain implementation.

## Source Traceability

Primary source: *The Art of Game Design: A Book of Lenses, Third Edition* by Jesse Schell, especially chapter 27 on design documents and team communication. The workflow is transformed and paraphrased.

Supporting source: the rest of the game skill pack, which turns design lenses into implementable briefs.

## Workflow

1. Decide the document's job: alignment, implementation, content production, tuning, playtest, or memory.
2. Keep stable intent separate from volatile implementation details.
3. Capture decisions, rejected alternatives, open questions, and validation evidence.
4. Link specs to code, data, assets, tests, and telemetry when possible.
5. Update docs after design decisions, not after every small code edit.

## Required Output

- `Doc Type`: brief, system spec, feature contract, tuning sheet, content schema, playtest report, or decision log.
- `Canonical Sections`: concise headings suited to the doc type.
- `Open Questions`: unresolved decisions with owner or next evidence.
- `Implementation Contract`: what the agent should build, avoid, test, and instrument.
- `Maintenance Rule`: when this doc must be updated.

## Local References

Before producing a design document, read:

- `references/core/guide.md`
- `workflows/living-design-doc.md`
