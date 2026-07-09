---
name: using-development-skills
description: Use when starting any conversation - establishes how the development-skills plugin works and how to invoke its components on each platform (Claude Code, Codex). Read first.
---

# Using development-skills

If dispatched as a subagent for a specific task: skip this skill.

Iron Rules to always follow: [`../../shared/iron-rules.md`](../../shared/iron-rules.md).

## Triage & Flow

Classify before reading the task in depth:

1. **PASS_THROUGH** — trivial, few files, fully reversible, no design choice → execute directly.
2. **LIGHT** — mechanical, no design choice → 6-step inline flow ([`../../shared/workflow.md` # LIGHT](../../shared/workflow.md)). Default on uncertainty → FULL. Mid-execution discovery that breaks LIGHT criteria → escalate to FULL.
3. **FULL** (default) — Phase 1 plan + HOW-locks, Phase 2 chronicle, Phase 3 Red/Green TDD, Phase 4 `staff-reviewer` review. Detail and gates: [`../../shared/workflow.md` # FULL](../../shared/workflow.md), [`../../shared/phases/*`](../../shared/phases/).

During FULL:

- External spec / guide / prior brainstorming → skip brainstorming only; phases 1-4 still run (the spec is INPUT to Phase 1, not a substitute; a guide's gates STACK).
- HOW-level ambiguity → ask the user (`AskUserQuestion` for discrete options; plain text otherwise; Codex fallback in `references/codex-tools.md`).

**Routing:** Bug fixes → `development-skills:debugging`. Test work → `development-skills:create-test`.

## Platform

SKILL bodies use Claude Code tool names as canonical. On Codex, translate via `references/codex-tools.md` (`Task` → `spawn_agent`, `AskUserQuestion` fallback, `staff-reviewer` dispatch recipe, hooks, marketplace files).

## User Override

User instructions (`CLAUDE.md`, `AGENTS.md`, direct requests) > development-skills > default system prompt.
