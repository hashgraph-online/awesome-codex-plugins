---
name: using-development-skills
description: Use when starting any conversation - establishes how the development-skills plugin works and how to invoke its components on each platform (Claude Code, Codex). Read first.
---

# Using development-skills

If dispatched as a subagent for a specific task: skip this skill.

**If any skill might apply (even 1% chance), invoke it.** Skills are the disciplined entry points — the meta-rule (spirit beats letter) covers the rest.

## Iron Rules

14 principles (0-13) + 1 meta-rule (spirit beats letter). Canonical: `shared/iron-rules.md`. Do not duplicate.

## Triage & Flow

Classify the task before reading its content in depth:

1. **PASS_THROUGH** — trivial, 1 file, fully reversible, no design choice → execute directly.
2. **LIGHT** — mechanical, no design choice (full 4-criteria gate in `shared/workflow.md` # Tier selection) → follow the 6-step inline flow. **Default on uncertainty → FULL.**
3. **FULL** (default) — 4 phases, sequential, mandatory:
   - **Phase 1:** plan file `docs/plans/NNNN__YYYY-MM-DD__implementation_plan__slug.md` + HOW-level Q&A locks (data shapes · edge cases · error semantics · contract boundaries · test scope · rollback).
   - **Phase 2:** chronicle `docs/chronicles/NNNN__YYYY-MM-DD__topic.md` capturing initial decisions.
   - **Phase 3:** implement with Red/Green TDD.
   - **Phase 4:** `staff-reviewer` subagent review.

**Rules during FULL:**

- External spec / guide / prior brainstorming exists → skip brainstorming only. Phases 1-4 still run. The spec is INPUT to Phase 1, not a substitute. A guide's own gates STACK with the workflow.
- Ambiguity ≥1% on any HOW-level dimension → ask the user (`AskUserQuestion` for discrete options; plain text otherwise; Codex fallback in `references/codex-tools.md`).
- Phase skipping mid-execution → stop, rejoin at the missed phase, produce its artifact, continue.

**Rules during LIGHT:** Tier is qualitative (ambiguity / logic impact / new-pattern) — not file count. A 30-file mechanical rename is LIGHT; a 1-file new-caching-strategy is FULL. All Iron Rules still apply. Mid-execution discovery breaks LIGHT criteria → escalate to FULL per `shared/workflow.md` # LIGHT (final paragraph).

**Routing:** Bug fixes → `development-skills:debugging`. Test work → `development-skills:create-test`.

## Platform

SKILL bodies use Claude Code tool names as canonical. On Codex, translate via `references/codex-tools.md` (`Task` → `spawn_agent`, `AskUserQuestion` fallback, `staff-reviewer` dispatch recipe, hooks, marketplace files).

## User Override

User instructions (`CLAUDE.md`, `AGENTS.md`, direct requests) > development-skills > default system prompt.
