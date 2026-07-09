---
name: using-hotl
description: Use when the user explicitly asks for HOTL routing or needs guidance choosing the right HOTL workflow skill.
---

## When to Use HOTL Skills

HOTL skills are for **code-changing tasks that require planning** — new features, refactors, and significant changes. Not every task needs a skill.

**Answer directly without invoking a skill:**
- Code understanding questions — "how does this work?", "where is this defined?", "explain this error"
- Quick fixes — typos, config values, import paths, obvious one-line corrections
- Error tracing — "what does this error mean?", "which file throws this?"

**Use `hotl:systematic-debugging` (no brainstorm/plan needed):**
- Bug investigations, test failures, unexpected behavior

**Use the full HOTL workflow (brainstorm → plan → execute):**
- New features, significant refactors, architectural changes

## Available HOTL Skills

Invoke any of these when appropriate:

| Skill | When to Use |
|---|---|
| `hotl:brainstorming` | Before any feature work — design with HOTL contracts |
| `hotl:writing-plans` | After design approval — produces `docs/plans/YYYY-MM-DD-<slug>-workflow.md` |
| `hotl:governed-execution` | Preferred execution entry point — selects host driver/profile while preserving renewable ownership, bounded loops, effect evidence, and receipts |
| `hotl:executing-plans` | Linear execution with human checkpoints |
| `hotl:loop-execution` | Execute a workflow file with loops + auto-approve |
| `hotl:subagent-execution` | Delegated step runner over the loop execution engine — delegates eligible steps to fresh subagents |
| `hotl:dispatch-agents` | 2+ independent tasks that can run in parallel |
| `hotl:finishing-a-development-branch` | After execution — merge back, publish/PR, keep, or discard the execution branch/worktree |
| `hotl:tdd` | Before writing any implementation code |
| `hotl:systematic-debugging` | When encountering any bug or unexpected behavior |
| `hotl:skill-authoring` | When creating, editing, or reviewing HOTL skills, agents, commands, or behavior-shaping instructions |
| `hotl:document-review` | Optional — review existing docs, external specs, or hand-authored plans |
| `hotl:requesting-code-review` | Dispatched by executors at review checkpoints — standardizes what context the reviewer receives |
| `hotl:receiving-code-review` | Invoked when review findings arrive — verify, evaluate against contracts, then implement |
| `hotl:code-review` | After completing implementation, before merging |
| `hotl:pr-reviewing` | Review a PR across multiple dimensions — description, code, scan, tests |
| `hotl:resuming` | Resume an interrupted workflow run with verify-first effect recovery and explicit ownership takeover/handoff |
| `hotl:verification-before-completion` | Before claiming work is done |
| `hotl:setup-project` | To generate adapter files for Codex, Cline, Cursor, Copilot |

## Red Flags (You Are Over-Routing)

- Routing a code question through brainstorming → just answer it
- Creating a plan for a typo fix → just fix it and verify
- Brainstorming before debugging → use systematic-debugging directly
- Skipping brainstorming for a real feature → invoke the skill

## HOTL Operating Principles

**Human-on-the-Loop:** Set intent + constraints upfront. AI executes autonomously within guardrails. Human reviews final output.

**Long-running harness contract:** Host goals, automations, background agents, hooks, and handoffs provide scheduling and liveness only. HOTL's renewable controller, serialized state, runtime loop/budget stops, effect reconciliation, explicit finish disposition, and sufficient receipt remain authoritative.

**Three contracts every implementation workflow should define:**
1. **Intent contract:** objective, constraints, success criteria
2. **Verification contract:** how to confirm each step worked
3. **Governance contract:** approval gates, risk level, rollback strategy
