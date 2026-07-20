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
  1. Scope check: fact/assumption/unknown, baseline, Requirement Ready Check, Ripple Signal Triage, compatibility boundary, dual-track needs
  2. File map: what files created/modified, clear boundaries, follow existing patterns
  3. Bite-sized tasks (2-5 min each): exact file paths, complete code, exact commands, expected output
  4. Self-review: spec coverage, placeholders, type consistency, compatibility, verification, dual-track
  5. Save → offer execution choice (subagent-driven or inline)
→ Plan must answer: problem, baseline, files, compat, verification, risks, retirement.
→ Escalate from Planless Slice Lane to a durable plan when the slice adds a new owner, contract, schema, public API, architecture boundary, migration, persistence, security/permission, distribution/release surface, or unclear verification boundary.

# Writing Plans

## Overview

Write comprehensive implementation plans assuming the engineer has zero context for our codebase and questionable taste. Document everything they need to know: which files to touch for each task, code, testing, docs they might need to check, how to test it. Give them the whole plan as bite-sized tasks. DRY. YAGNI. Chosen TDD route. Frequent commits.

Assume they are a skilled developer, but know almost nothing about our toolset or problem domain. Assume they don't know good test design very well.

This skill is the canonical planning workflow for multi-step implementation work. Use it to convert approved specs or requirements into plans that are executable, testable, impact-aware, and bounded by compatibility and authority constraints.

Strict RED / GREEN steps belong only to an explicit user/project TDD request or
`TDD Route: strict`. With TDD mode `off` and no strict route, plan the minimum
implementation and proportional regression/verification steps; do not prescribe
a TDD cycle from risk alone.

### TDD Route Guard

Before task decomposition, every plan that includes implementation work must
record:

```text
TDD Route:
- Mode: off | auto
- Decision: strict | light | skipped
- Strict authority: explicit user/project request | recorded auto decision | not applicable
- Test posture: diagnostic reproduction | post-change regression | strict RED test
- Reason:
- Verification:
```

In `off`, record `Decision: skipped` unless an explicit user/project strict
request overrides it. The record makes the boundary reviewable; it does not
load `test-driven-development`. An approved plan, bug label, architecture risk,
contract risk, or shared-module label is not strict authority.

Only `Decision: strict` with stated strict authority may prescribe `Write
failing test`, `Verify RED`, `GREEN`, or `REFACTOR` as task steps. Otherwise,
write the minimum change plus diagnostic reproduction or post-change regression
as appropriate. In `auto`, if the plan lacks a recorded decision, return to
route selection before writing implementation tasks; never infer `strict`
during decomposition.

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

Compact output contract before writing the plan: `Aegis Visibility`, `Plan Basis`,
`BaselineUsageDraft`, `Requirement Ready Check`, `Files`, `Compatibility`,
`Change Necessity`, `Existence Check`, `Architecture Integrity Lens`,
`Plan Pressure Test`, `Plan-Time Complexity Check`,
`Execution Readiness View`, `Tasks`, `Risks`, and `Retirement`. Expand only
where the approved scope, risk, or verification surface requires it.

`Aegis Visibility` for this workflow states which owner, contract, retirement,
compatibility, or verification pressure makes planning useful before execution.
Use one natural sentence for ordinary plans; reserve structured trace for audit,
debug, release, long-task review, or explicit user request.

Use a compact `BaselineUsageDraft` whenever the plan depends on specific
baseline docs or current-authority refs:

```text
BaselineUsageDraft:
- Required baseline refs:
- Delivered context refs:
- Acknowledged before plan refs:
- Cited in plan refs:
- Missing refs:
- Decision: continue | needs-baseline-readback | needs-verification | pause-for-user | blocked
```

`Delivered context refs` is optional host-projected bookkeeping only. It is not
authoritative proof that a host injected or the model internally consumed a
context payload. The artifact exists to make baseline/context attention drift
visible before and during planning.

Use a compact `Requirement Ready Check` before task decomposition unless the
input is already an approved plan/spec whose acceptance boundary is explicit:

```text
Requirement Ready Check:
- Requirement source refs:
- Goals and scope refs:
- User / scenario refs:
- Requirement item refs:
- Acceptance / verification criteria refs:
- Open blocker questions:
- Decision: ready | needs-source | needs-goal-alignment | needs-scenario | needs-acceptance-criteria | needs-clarification | needs-user-decision | blocked
```

If the decision is not `ready`, do not create implementation tasks. Return to
the requirement/spec owner with the smallest missing evidence or decision. A
task intent, conversation, or agent inference can be cited as a candidate
source, but it is not durable requirement authority by itself.

Use a compact `Change Necessity` before task decomposition when the plan would
endorse any new source-code path or non-trivial source edits. This is the
"should code change at all?" check; it is not a new artifact or a
`using-aegis` hot-path expansion.

This is behavior-triggered, not prompt-triggered. If the plan is about to add
any new source-code path or create non-trivial source-edit tasks, expose a
natural readback even when the user did not ask for it. A tiny helper, small
guard, new branch, fallback, adapter, or owner is not exempt. Example: "Code
necessity check: a non-code path is insufficient because <reason>; the minimum
change boundary is <owner/files>, so the decision is code-change."

```text
Change Necessity:
- User-visible need:
- No-change / non-code option:
- Why code change is necessary:
- Minimum change boundary:
- Decision: no-change | docs/config-only | code-change | needs-clarification
```

If the decision is `no-change`, do not write code-edit tasks. If the decision
is `docs/config-only`, narrow the plan to that surface. If the decision is
`needs-clarification`, return to the requirement/spec owner. If the decision is
`code-change`, carry the minimum boundary into `Files`, task steps, and
verification. Approved requirements do not by themselves prove that a new
source-code path is necessary.

Use a compact `Existence Check` before task decomposition when a plan would add
a new owner, skill, artifact, host adapter, fallback, compatibility path,
workflow step, or benchmark metric. Use
`docs/current/AEGIS_MINIMALITY_REFERENCE.md` as the reference and keep the check
advisory. Do not force it onto plans that only reuse existing owners and
surfaces.

```text
Existence Check:
- Proposed new surface:
- Existing owner / reuse candidate:
- Why existing surface is insufficient:
- Creation proof:
- Entropy / retirement impact:
- Decision: reuse-existing | add-with-proof | defer | reject | needs-first-principles-review
```

If the decision is `reuse-existing`, write tasks against the existing owner
instead of creating a new surface. If the decision is `add-with-proof`, carry
the proof, verification signal, and any retirement trigger into the relevant
task.

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

Render an `Execution Readiness View` before handing a medium/high,
subagent-driven, handoff-prone, long-running, architecture, contract,
compatibility, or retirement-sensitive plan to execution. This view is a
human-readable projection of existing runtime-ready drafts and plan content. It
is not a new JSON artifact type, approval gate, authoritative `GateDecision`,
`PolicySnapshot`, or completion authority.
The view must expose Intent Lock, Scope Fence, and Baseline Lock before any
task batch is handed to execution.

```text
Execution Readiness View:
- Intent Lock:
- Scope Fence:
- Baseline Lock:
- Approved Behavior:
- Owner / Contract Constraints:
- Compatibility Boundary:
- Retirement Boundary:
- Task Batches:
- Test Obligations:
- Review Gates:
- Drift / Rewind Rules:
- Evidence Required Before Completion:
- Advisory Boundary: method-pack execution guidance only; not GateDecision, PolicySnapshot, or completion authority
```

Use existing inputs for the view: `TaskIntentDraft`, `BaselineUsageDraft`,
`ImpactStatementDraft`, `GateInputPack`, the plan's task batches,
compatibility / retirement sections, and verification commands. Skip the view
for tiny fast-path tasks unless the user asks for an execution handoff readback.

Use a compact `Plan-Time Complexity Check` before writing task steps when the
plan changes maintained source files, core owners, handlers, routers, managers,
shared utilities, adapters, or fallback paths:

Use `using-aegis/references/complexity-governance.md` for the shared artifact
classes, pressure signals, and over-budget handling rules.

```text
Complexity Budget:
- Artifact class:
- Target files / artifacts:
- Current pressure:
- Projected post-change pressure:
- Budget result: within-budget | at-risk | over-budget
- Planned governance:

Plan-Time Complexity Check:
- Target files:
- Existing size / shape signals:
- Owner fit:
- Add-in-place risk:
- Better file boundary:
- Recommendation: edit-in-place | extract helper | add owner file | split task | defer refactor
```

If the projected budget result is `over-budget`, do not write an atomic task
that silently assumes add-in-place growth. Revise the task boundary, add
governance work, or explicitly mark the slice as requiring follow-up before
implementation begins.

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
`Existence Check` first. If the new surface is still justified but the owner,
contract, or retirement decision remains risky, use `first-principles-review`
and its `Decision Hygiene Review` or `Architecture Integrity Lens` before task
decomposition.

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

Workspace creation is triggered by the plan save step. See the workspace support
rule in `using-aegis/SKILL.md` for the hard binary rule. If the project already
has docs/adr/ or architecture docs, reference them — do not duplicate authority.

## File Structure

Map files before defining tasks. Design units with clear boundaries and single responsibilities. Files that change together should live together. Follow existing codebase patterns. Each task should produce self-contained, independently reviewable changes.

For non-trivial project plans, passively read the relevant active language from
`CONTEXT-MAP.md`/`CONTEXT.md` when present. Use canonical terms consistently in
the plan title, tasks, acceptance language, and owner references. If planning
discovers a resolved semantic change, ambiguity, or conflict, compose
`establishing-project-context` instead of recording a glossary decision only in
the plan. Passive reads alone do not load active modeling.

## Required Planning Outputs

Before you leave this workflow, the written plan must make these items answerable:

1. **What problem or approved scope this plan is implementing**
2. **Which baseline docs, ADRs, or requirements shaped the plan**
3. **Whether the Requirement Ready Check is ready, or which requirement source,
   scenario, acceptance, clarification, or user decision is still missing**
4. **Which required baseline refs were explicitly acknowledged before planning and which were actually cited in the plan**
5. **What files own the change**
6. **What compatibility boundary must hold**
7. **Why a code change is necessary, or why the plan is narrowed to no-change,
   docs/config-only, or clarification**
8. **Whether any new surface passed an Existence Check or was routed to an
   existing owner**
9. **Whether the architecture integrity check found a higher-level owner /
   contract path before task decomposition**
10. **What plan-time complexity pressure exists and which edit boundary is safer**
11. **Whether an `Execution Readiness View` is needed for this handoff, and if
   needed, which intent, scope, baseline, compatibility, retirement, testing,
   review, and drift boundaries it renders**
12. **What verification proves each major slice**
13. **What risks, rollback surface, old owner/fallback handling, ADR signal preservation, and baseline-sync signals remain**

## Bite-Sized Task Granularity

**Each step is one action (2-5 minutes):**
- Under `TDD Route: strict`: write the failing test → verify RED → implement minimal code → verify GREEN.
- Otherwise: make the minimum change → run the focused regression or verification that proves it.
- Commit.

## Plan Document Header

Every plan MUST start with: Goal, Architecture, Tech Stack, Baseline/Authority Refs, Compatibility Boundary, TDD Route, Verification. See template in this directory.

## Task Structure

Each task: Files (create/modify/test paths), Why (user/business value), Change Necessity (why source edits are needed and the minimum boundary), Impact/Compatibility, Verification (exact commands), then steps matching the TDD route. Strict routes use Write test → Verify RED → Minimal code → Verify GREEN → Commit; `off`, light, and skipped routes use the minimum change plus proportional regression/verification → Commit. Every step must include complete code and exact commands.

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
non-goals, stable interfaces marked? 5) Change necessity — any code-edit task
states why no-change or docs/config-only is insufficient and names the minimum
boundary? 6) Existence check — any new owner,
artifact, adapter, fallback, workflow step, or benchmark metric has proof and a
reuse decision? 7) Plan-time complexity and minimality —
lowest-entropy owner/file boundary that fixes the bug class, not just the
smallest textual diff? 8) Architecture integrity — any higher-level owner /
contract / source-of-truth simplification skipped? 9) Verification — exact
commands? 10) Dual-track, decision hygiene, and ADR/baseline-sync signals
preserved where needed?

Fix issues inline. Re-review is not needed — just fix and move on.

## Execution Handoff

After saving the plan, render the `Execution Readiness View` when the handoff
criteria above apply. Then offer execution choice:

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
- `Execution Readiness View` can make implementation start conditions,
  verification obligations, and drift / rewind rules visible before execution
- A plan cannot grant authoritative completion
- A plan should prepare runtime-ready execution, not pretend to be runtime authority
