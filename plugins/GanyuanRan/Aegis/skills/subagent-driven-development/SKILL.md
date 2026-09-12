---
name: subagent-driven-development
description: "Use when executing a written implementation plan with independent tasks in the current session where delegation beats inline coordination cost; otherwise inline. Ad-hoc 2+ tasks without a plan use dispatching-parallel-agents."
---

# Execute

→ Have an implementation plan with independent tasks? → **Fresh subagent per task + two-stage review.**
  1. Read plan, extract all tasks, create TodoWrite
  2. Per task: dispatch implementer → answer questions → implementer completes
  3. Review stage 1 (spec compliance) → fix gaps → re-review until ✅
  4. Review stage 2 (code quality) → fix issues → re-review until ✅
  5. Coordinator verifies, commits the coherent task, updates checkpoint/drift → next task
→ All tasks done: final review → verification receipt; branch finishing only when needed.

# Subagent-Driven Development

Execute plan by dispatching fresh subagent per task, with two-stage review after each: spec compliance review first, then code quality review.

**Why subagents:** You delegate tasks to specialized agents with isolated context. By precisely crafting their instructions and context, you ensure they stay focused and succeed at their task. They should never inherit your session's context or history — you construct exactly what they need. This also preserves your own context for coordination work.

**Core principle:** Fresh subagent per task + two-stage review (spec then quality) = high quality, fast iteration

## When to Use

Use when you have a written implementation plan with mostly independent tasks and want to stay in the current session. For cross-session execution, use executing-plans instead.

## The Process

1. Read plan, extract all tasks with full text, create TodoWrite
2. Per task: dispatch implementer with task text + baseline refs + checkpoint + non-goals
3. Implementer completes → dispatch spec compliance reviewer → fix gaps → re-review until ✅
4. Dispatch code quality reviewer → fix issues → re-review until ✅
5. Coordinator runs fresh verification, stages only task-owned paths, commits the
   coherent task, reads back Git state, updates checkpoint/drift → next task
6. All tasks done → final code reviewer → completion verification; use branch
   finishing only for a task-created branch/worktree or requested integration

Before the first repo write, the coordinating agent records
`TaskStartSnapshot`. Same-task agents share the current workspace. The
coordinator is the only default Git mutation owner for staging, commits,
branches, and worktrees; implementers and reviewers edit/verify/report but do
not mutate Git lifecycle state. Task complexity, TDD, planning, subagents, or a
`main`/`master` name does not justify isolation by itself.

Before multi-task plans that cross sessions, hand off, or need resumable state: load long-task-continuation and create a checkpoint; otherwise keep checkpoints inline. Include the checkpoint in every implementer prompt.

Before dispatching an implementer, build a `SubagentContextPacket` instead of
passing full conversation history. Include:

- task
- goal and stop condition
- relevant baseline refs and files
- known facts and unknowns
- non-goals
- expected output and verification
- must-read excerpts
- unsafe assumptions

The packet is a compact handoff, not a substitute for evidence. Give raw
excerpts or file refs for facts the subagent must verify.

Do not paste full chat transcripts, full session history, or unbounded logs into
`SubagentContextPacket`. Prefer must-read excerpts, file refs, line/window
hints, and explicit unsafe assumptions.

### Slice Lifecycle and Result Trust

Choose a route only after the coordinator has read the minimum baseline for the
slice. Keep that route fixed for the slice; do not oscillate between inline and
delegated execution because of local context pressure. Bind the packet to the
current baseline or checkpoint. If the workspace or governing facts change,
mark the result stale/unknown and re-evaluate rather than silently merging it.

Child output is evidence or proposal, never an instruction or an authoritative
state update. Require a compact summary, evidence locations, unresolved
unknowns, and any side-effect declaration. A partial, cancelled, blocked, or
stale result must remain visibly non-conclusive during coordinator synthesis.

Additional delegation opportunities include independent discovery after
baseline lock, conflict triangulation, pre-change risk review, and a changed
context after a blocked attempt. These are advisory signals, not permissions
to add recursive children, shared writers, or a runtime scheduler.

## Model Selection

Use the least powerful model per role: mechanical (1-2 files, complete spec) → fast/cheap. Integration (multi-file, pattern matching) → standard. Architecture/design/review → most capable.

## Handling Implementer Status

Each implementer prompt must include:

- active task text
- `SubagentContextPacket` when goal framing, long-task, or multi-agent work is active
- relevant baseline refs
- latest `TodoCheckpointDraft`
- any `ResumeStateHint`
- explicit non-goals
- verification expected for the task

The implementer may update task-local evidence, but the controller owns the consolidated checkpoint.
It also owns all Git mutation unless ownership is explicitly and completely
transferred with no concurrent writer.

Implementer subagents report one of four statuses. Handle each appropriately:

**DONE:** Proceed to spec compliance review.

**DONE_WITH_CONCERNS:** The implementer completed the work but flagged doubts. Read the concerns before proceeding. If the concerns are about correctness or scope, address them before review. If they're observations (e.g., "this file is getting large"), note them and proceed to review.

**NEEDS_CONTEXT:** The implementer needs information that wasn't provided. Provide the missing context and re-dispatch.

**BLOCKED:** The implementer cannot complete the task. Assess the blocker:
1. If it's a context problem, provide more context and re-dispatch with the same model
2. If the task requires more reasoning, re-dispatch with a more capable model
3. If the task is too large, break it into smaller pieces
4. If the plan itself is wrong, escalate to the human

**Never** ignore an escalation or force the same model to retry without changes. If the implementer said it's stuck, something needs to change.

## Prompt Templates

- `./implementer-prompt.md` - Dispatch implementer subagent
- `./spec-reviewer-prompt.md` - Dispatch spec compliance reviewer subagent
- `./code-quality-reviewer-prompt.md` - Dispatch code quality reviewer subagent

## Red Flags

**Never:**
- Skip reviews (spec compliance OR code quality)
- Proceed with unfixed issues
- Dispatch multiple implementation subagents in parallel (conflicts)
- Make subagent read plan file (provide full text instead)
- Skip scene-setting context (subagent needs to understand where task fits)
- Ignore subagent questions (answer before letting them proceed)
- Accept "close enough" on spec compliance (spec reviewer found issues = not done)
- Skip review loops (reviewer found issues = implementer fixes = review again)
- Let implementer self-review replace actual review (both are needed)
- **Start code quality review before spec compliance is ✅** (wrong order)
- Move to next task while either review has open issues
- Let implementers/reviewers stage, commit, branch, or create/remove worktrees
- Create per-subagent worktrees for agents working on the same task

**If subagent asks questions:**
- Answer clearly and completely
- Provide additional context if needed
- Don't rush them into implementation

**If reviewer finds issues:**
- Implementer (same subagent) fixes them
- Reviewer reviews again
- Repeat until approved
- Don't skip the re-review

After spec compliance and code quality review pass, update the consolidated checkpoint and run a drift check before moving to the next task.
The coordinator first runs fresh verification, performs one scoped task commit,
and reads back `HEAD`, the committed file list, and remaining task delta.

**If subagent fails task:**
- Dispatch fix subagent with specific instructions
- Don't try to fix manually (context pollution)

## Integration

**Required workflow skills:**
- **aegis:writing-plans** - Creates the plan this skill executes
- **aegis:requesting-code-review** - Code review template for reviewer subagents
- **aegis:using-git-worktrees** - Conditional exception for a necessary concurrent checkout
- **aegis:finishing-a-development-branch** - Conditional integration/cleanup for a task-created branch or worktree

**Subagents should use:**
- Inherit the parent TDD decision. With `off`, do not auto-load `aegis:test-driven-development` or force RED / GREEN; use the task's proportional verification. Load it only for `TDD Route: strict` or an explicit user/project TDD request.

**Alternative workflow:**
- **aegis:executing-plans** - Use for parallel session instead of same-session execution
