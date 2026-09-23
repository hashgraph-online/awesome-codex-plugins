---
name: dispatching-parallel-agents
description: "Use when facing 2+ independent tasks without a written plan, with no conflicting shared mutable state or sequential dependencies, where parallel delegation beats inline cost; otherwise inline. Planned tasks use subagent-driven-development."
---

# Dispatching Parallel Agents

## Purpose

Use parallel children for two or more ad-hoc, bounded tasks only when their
independence is already credible and concurrency is worth the coordination.
Parallelism changes elapsed time; it does not relax evidence, ownership, or
completion requirements.

## Dispatch Gate

Dispatch only when all are true:

- there are `2+` distinct tasks or evidence questions;
- one task's result is not needed to define or start another;
- the tasks do not require overlapping writes or the same mutable resource;
- a shared root cause is unlikely based on current evidence;
- each result can be returned with bounded evidence and unresolved unknowns;
- available concurrency and expected work justify coordination cost.

Keep work inline when decomposition is still exploratory, failures may share a
root cause, full-system context is required, or tasks are too small to repay the
handoff. A written implementation plan routes to
`aegis:subagent-driven-development`, not this ad-hoc workflow.

## Context And Ownership

Choose the live host's context inheritance mode deliberately. Give each child
the minimum sufficient instructions and evidence; do not rely on accidental
inheritance or assume that context must never be inherited.

Each task packet states:

- goal and question to resolve;
- allowed files, systems, and side effects;
- known facts and evidence locations;
- constraints, non-goals, and stop condition;
- expected result shape, including unknowns and verification refs.

Isolated model context does not imply an isolated filesystem, process, Git
repository, credential, rate limit, or external service. Prefer read-only
investigation. If children may edit, assign disjoint write ownership explicitly.
The coordinator owns staging, commits, branches, worktrees, integration, and other Git lifecycle mutations.

## Execution

1. Establish the minimum common baseline and record evidence for the task split.
2. Dispatch one bounded task per independent domain, within host concurrency
   limits.
3. Optionally continue coordinator work that does not race child reads or writes.
4. On return, check evidence freshness, unknowns, overlapping assumptions, and
   visible workspace changes.
5. Synthesize disagreements before acting. If results reveal coupling, stop
   parallel mutation and return the work to one owner.
6. For edits, run integrated verification after accepted changes are combined.
   For read-only work, validate the synthesis against the cited sources.

The coordinator owns the concurrency budget. Children do not delegate
recursively unless their packet explicitly permits it. A failed, cancelled, or
timed-out child contributes any available partial evidence; otherwise record no
result and the unresolved unknowns. Retry only with a materially different
packet or serialize the task.

Child output is evidence or a proposal, not a `GateDecision`, completion authority, or permission for external action.

## Common Failure Modes

- Separate files are treated as proof of separate root causes.
- Children receive broad conversation history instead of bounded task context.
- Multiple children edit the same owner or mutate shared services concurrently.
- A child report is accepted without inspecting evidence or current files.
- Parallel work is used for a written plan and bypasses its review checkpoints.
- The coordinator verifies each result alone but never checks the integrated
  state.

When any of these appears, narrow the packets, serialize the shared portion, or
return to the owning debugging or plan workflow.
