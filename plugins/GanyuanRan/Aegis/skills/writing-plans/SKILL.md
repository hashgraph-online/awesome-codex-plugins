---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching code
---

# Execute

→ Have an existing parent plan/spec and a tiny execution slice? → **Use Planless Slice Lane.**
  1. Emit a compact Slice Card: goal, parent plan/spec, files, boundary, verification, stop
  2. Update the parent workstream checkpoint/evidence/drift state if persistent state is needed
  3. Do not save a new plan for the micro-slice
→ Have approved spec/requirements for a new workstream or an escalation trigger? → **Write implementation plan. Assume engineer has zero context.**
  1. Scope check: fact/assumption/unknown, baseline, Ripple Signal Triage, compatibility boundary, dual-track needs
  2. File map: what files created/modified, clear boundaries, follow existing patterns
  3. Bite-sized tasks (2-5 min each): exact file paths, complete code, exact commands, expected output
  4. Self-review: spec coverage, placeholders, type consistency, compatibility, verification, dual-track
  5. Save → offer execution choice (subagent-driven or inline)
→ Plan must answer: problem, baseline, files, compat, verification, risks, retirement.
→ Escalate from Planless Slice Lane to a durable plan when the slice adds a new owner, contract, schema, public API, architecture boundary, migration, persistence, security/permission, distribution/release surface, or unclear verification boundary.

# Writing Plans

## Overview

Write comprehensive implementation plans assuming the engineer has zero context for our codebase and questionable taste. Document everything they need to know: which files to touch for each task, code, testing, docs they might need to check, how to test it. Give them the whole plan as bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume they are a skilled developer, but know almost nothing about our toolset or problem domain. Assume they don't know good test design very well.

This skill is the canonical planning workflow for multi-step implementation work. Use it to convert approved specs or requirements into plans that are executable, testable, impact-aware, and bounded by compatibility and authority constraints.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**Context:** This should be run in a dedicated worktree (created by brainstorming skill).

**Input:** approved requirements, a Spec Brief, or a Design Spec.

**Save plans to:** `docs/aegis/plans/YYYY-MM-DD-<feature-name>.md`
Plan always goes to `plans/` — never to `work/`.
(User preferences for plan location override this default.)

Exception: if an existing parent plan/spec already owns the current tiny
execution slice, use `Planless Slice Lane`. Do not save a new plan. Emit a
compact `Slice Card` in the conversation or the active long-task checkpoint
instead:

```text
Slice Card:
- Goal:
- Parent plan/spec:
- Files:
- Boundary:
- Verification:
- Stop:
```

If `docs/aegis/` does not exist and configured Aegis workspace support is
available, initialize the target project first:

```bash
python <aegis-workspace-helper> init --root <target-project-root>
```

If installed Aegis workspace support is unavailable, initialize the workspace manually:
  1. Create `docs/aegis/README.md` and `docs/aegis/INDEX.md`
  2. Create `docs/aegis/BASELINE-GOVERNANCE.md` from template
  3. If the project has code, create `docs/aegis/baseline/YYYY-MM-DD-initial-baseline.md`
Then save the plan and append to `docs/aegis/INDEX.md`. Prefer:

```bash
python <aegis-workspace-helper> append-index --root <target-project-root> --path docs/aegis/plans/<filename>.md --kind plan --title "<title>"
python <aegis-workspace-helper> check --root <target-project-root>
```

## Scope Check

If the input is a Spec Brief, keep the plan scoped to the pinned
what/why/acceptance and do not expand into a formal design unless new
architecture, contract, migration, or cross-module uncertainty appears.

Compact output contract before writing the plan: `Plan Basis`, `Files`,
`Compatibility`, `Architecture Integrity Lens`, `Plan Pressure Test`,
`Plan-Time Complexity Check`, `Tasks`, `Risks`, and `Retirement`. Expand only
where the approved scope, risk, or verification surface requires it.

Use the `Architecture Integrity Lens` before task decomposition when an
executable plan may still encode responsibility overlap, a wrong canonical
owner, a caller-side fallback, a stale path carrying real logic, or a missed
higher-level owner / contract / source-of-truth simplification. Keep it compact:
invariant, canonical owner / contract, responsibility overlap, higher-level
simplification, retirement / falsifier, and verdict.

Use a compact `Plan Pressure Test` before task decomposition:

```text
Plan Pressure Test:
- Owner / contract / retirement:
- Architecture integrity / higher-level path:
- Verification scope:
- Task executability:
- Pressure result: proceed | revise plan | return to design
```

The pressure test is not an approval gate and should not redesign an approved
spec without cause. It exists to catch owner / contract / retirement risk,
missing verification, and tasks that are too vague to execute safely.

Use a compact `Plan-Time Complexity Check` before writing task steps when the
plan changes maintained source files, core owners, handlers, routers, managers,
shared utilities, adapters, or fallback paths:

```text
Plan-Time Complexity Check:
- Target files:
- Existing size / shape signals:
- Owner fit:
- Add-in-place risk:
- Better file boundary:
- Recommendation: edit-in-place | extract helper | add owner file | split task | defer refactor
```

Signals: 800+ line files, 80+ line blocks, deep nesting, mixed reasons to
change, owner mismatch, or new branches/fallbacks/adapters. Advisory only. If
the best answer is a new file, define its owner and contract; do not merely move
complexity sideways.

If the spec covers multiple independent subsystems, suggest breaking into
separate plans. Before writing tasks, check: fact/assumption/unknown, baseline
docs, compatibility boundary, whether dual-track (repair + retirement) applies.
If approved requirements or the design carried an ADR signal, preserve the ADR
signal, source refs, real alternatives, compatibility boundary, and expected
baseline-sync questions for completion so ADR Auto Backfill can run without
rediscovering the decision from scratch.

If task decomposition would encode a new owner, duplicate owner, fallback,
adapter, compat-only carrier, delete-first question, unverified assumption, or
long-term stability claim that the spec did not already settle, use
`first-principles-review` and its `Decision Hygiene Review` or `Architecture
Integrity Lens` before task decomposition.

When the plan must decide between deleting old internal paths, retaining compat
for a proven external boundary, or stopping for persistent-state confirmation,
compose `anti-entropy-governance`. Keep it as a narrow classification and
guardrail owner; it does not authorize destructive execution.

Use `Planless Slice Lane` before writing or saving a plan when all of these are
true:

- a parent spec or parent plan already defines the workstream
- the current request is executing or refining one bounded task from that
  parent
- no new owner, contract, schema, public API, architecture boundary, migration,
  persistence, security/permission, distribution/release surface, or unclear
  verification boundary appears
- the slice can be described by a `Slice Card`

The lane preserves long-task continuity without turning execution bookkeeping
into durable planning artifacts.

## Aegis Project Workspace

Workspace creation is triggered by the plan save step. See `using-aegis/SKILL.md` Rule 3 for the hard binary rule. If the project already has docs/adr/ or architecture docs, reference them — do not duplicate authority.

## File Structure

Map files before defining tasks. Design units with clear boundaries and single responsibilities. Files that change together should live together. Follow existing codebase patterns. Each task should produce self-contained, independently reviewable changes.

## Required Planning Outputs

Before you leave this workflow, the written plan must make these items answerable:

1. **What problem or approved scope this plan is implementing**
2. **Which baseline docs, ADRs, or requirements shaped the plan**
3. **What files own the change**
4. **What compatibility boundary must hold**
5. **Whether the architecture integrity check found a higher-level owner /
   contract path before task decomposition**
6. **What plan-time complexity pressure exists and which edit boundary is safer**
7. **What verification proves each major slice**
8. **What risks, rollback surface, old owner/fallback handling, ADR signal preservation, and baseline-sync signals remain**

## Bite-Sized Task Granularity

**Each step is one action (2-5 minutes):**
- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test pass" - step
- "Run the tests and make sure they pass" - step
- "Commit" - step

## Plan Document Header

Every plan MUST start with: Goal, Architecture, Tech Stack, Baseline/Authority Refs, Compatibility Boundary, Verification. See template in this directory.

## Task Structure

Each task: Files (create/modify/test paths), Why (user/business value), Impact/Compatibility, Verification (exact commands), then 5 checkbox steps: Write test → Verify RED → Minimal code → Verify GREEN → Commit. Every step must include complete code and exact commands.

For bug fixes, refactors, contract changes, or governance cleanup, add Repair
Track (root cause, canonical owner, minimal sufficient stable repair, compat
boundary, verification) and Retirement Track (old owner/fallback, active status,
keep reason or deletion trigger) inside the relevant task. If Ripple Signal
Triage fired, include the affected downstream consumers and expanded
verification path in the same task.

## No Placeholders

Never write: "TBD", "TODO", "implement later", "fill in details", "Add appropriate error handling", "Write tests for the above" without actual test code, "Similar to Task N" without repeating code. Every step must contain complete, copy-paste-ready content.

## Self-Review

Check plan against spec: 1) Spec coverage — can you point to a task for each
requirement? 2) Placeholder scan — any TBD/TODO/vague instructions? 3) Type
consistency — do signatures match across tasks? 4) Compatibility — invariants,
non-goals, stable interfaces marked? 5) Plan-time complexity and minimality —
lowest-entropy owner/file boundary that fixes the bug class, not just the
smallest textual diff? 6) Architecture integrity — any higher-level owner /
contract / source-of-truth simplification skipped? 7) Verification — exact
commands? 8) Dual-track, decision hygiene, and ADR/baseline-sync signals
preserved where needed?

Fix issues inline. Re-review is not needed — just fix and move on.

## Execution Handoff

After saving the plan, offer execution choice:

**"Plan complete and saved to `docs/aegis/plans/<filename>.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?"**

**If Subagent-Driven chosen:**
- **REQUIRED SUB-SKILL:** Use aegis:subagent-driven-development
- Fresh subagent per task + two-stage review

**If Inline Execution chosen:**
- **REQUIRED SUB-SKILL:** Use aegis:executing-plans
- Batch execution with checkpoints for review

## Planning Boundaries

- A plan can define implementation slices, verification, rollback surface, and retirement expectations
- A plan cannot grant authoritative completion
- A plan should prepare runtime-ready execution, not pretend to be runtime authority
