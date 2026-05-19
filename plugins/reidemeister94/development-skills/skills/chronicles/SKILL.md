---
name: chronicles
description: "Use when starting a new development task to capture context, or when finalizing a task to document discoveries and decisions."
---

# Chronicles

**Announce:** "I'm using the chronicles skill to capture task context."

## Philosophy

A chronicle is a **project snapshot** — months later, a reader should understand:

- **What the user wanted** — full context, not a summary
- **Why decisions were made** — business context, trade-offs, rejected alternatives
- **What was discovered** — unexpected findings, gotchas, patterns
- **What changed** — references to key areas (not diffs)
- **Project state** — before and after

```
Code + Git = WHAT changed (diffs)
Plan docs  = HOW implemented (tasks, approaches)
Chronicles = WHY it happened, USER CONTEXT, PROJECT STATE
```

**Capture everything the user communicated.** Condense during finalization, but preserve ALL intent.

---

## Usage

### Within Workflow (Phase 2)

Read `shared/phases/phase-2-chronicle.md` for template and instructions.

### Standalone

Follow the same template. Create in `docs/chronicles/`. No workflow gates.

---

## When NOT Needed

ALL must apply: trivial fix, no new patterns, self-evident from diff, no business context worth preserving.

State: **"CHRONICLE: NOT NEEDED -- [reason]"**

---

## With Brainstorming

Create chronicle for the exploration. Document approaches considered and WHY each was accepted/rejected.

---

## Principles

- Capture the WHY — code shows what, chronicles explain why
- Capture the user's voice — most valuable signal
- Higher level than code — reference areas, don't paste diffs
- Condense, don't lose — summarize for readability, preserve intent
- Reference, don't repeat — point to locations, don't paste code
- Evolve continuously — update as you learn
- Promote insights — valuable discoveries belong in `AGENTS.md` (or `CLAUDE.md` if that's the project's primary)
