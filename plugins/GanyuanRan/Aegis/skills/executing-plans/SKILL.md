---
name: executing-plans
description: Use when you have a written implementation plan to execute in a separate session with review checkpoints
---

# Executing Plans

## Overview

Load plan, review critically, execute all tasks, report when complete.

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

For non-trivial plan execution, include `Aegis Visibility` in natural prose:
name why Aegis is keeping the current slice tied to the approved plan,
checkpoint, drift check, pre-edit governance, or verification boundary. This
visibility belongs to the active execution workflow; do not replace it with a
generic used-skills log.

**Note:** Tell your human partner that Aegis works much better with access to subagents. The quality of its work will be significantly higher if run on a platform with subagent support (such as Claude Code or Codex). If subagents are available, use aegis:subagent-driven-development instead of this skill.

## The Process

### Step 1: Load and Review Plan
1. Read plan file
2. If the plan or active checkpoint includes an `Execution Readiness View`,
   read it before implementation and compare the plan against its intent lock,
   scope fence, baseline lock, owner / contract constraints, compatibility
   boundary, retirement boundary, test obligations, review gates, drift /
   rewind rules, and evidence required before completion.
3. Review critically - identify any questions or concerns about the plan
4. If the view contradicts the plan, baseline, or current worktree evidence,
   return to plan review or refresh the advisory handoff before editing.
5. If concerns: Raise them with your human partner before starting
6. If no concerns: Create TodoWrite and proceed

### Step 1.5: Long-Task Checkpoint Setup

If the plan has multiple tasks, may span sessions, or includes architecture / contract / workflow changes:

1. Announce: "I'm using the long-task-continuation skill to keep this plan checkpointed and drift-aware."
2. Load aegis:long-task-continuation.
3. Create the initial checkpoint from the plan:
   - current todo
   - active task
   - completed tasks
   - evidence refs
   - blockers
   - next step
4. Before each task, restate the current checkpoint.
5. After each task, update checkpoint, evidence refs, and drift check.

### Step 2: Execute Tasks

For each task:
1. Mark as in_progress
2. Follow each step exactly (plan has bite-sized steps)
3. Before any new source-code path is added by a task, restate the plan's
   `Change Necessity` or create a compact one if the plan failed to carry it
   forward. Plan approval is not by itself proof that a new helper, small guard,
   new branch, fallback, adapter, or owner is necessary.

   ```text
   Change Necessity:
   - User-visible need:
   - No-change / non-code option:
   - Why code change is necessary:
   - Minimum change boundary:
   - Decision: no-change | docs/config-only | code-change | needs-clarification
   ```

   If the decision is not `code-change`, pause execution and return to plan
   review instead of editing. If the decision is `code-change`, carry the
   minimum boundary into the edit and verification scope.
4. Before any non-trivial source edit, run the plan's
   `Pre-Edit Complexity Check` or create a compact one:

   Use `using-aegis/references/complexity-governance.md` for shared artifact
   classes, pressure signals, and `over-budget` handling.

   ```text
   Complexity Budget:
   - Artifact class:
   - Target files / artifacts:
   - Current pressure:
   - Projected post-change pressure:
   - Budget result: within-budget | at-risk | over-budget
   - Planned governance:

   Pre-Edit Complexity Check:
   - Target edit file:
   - Existing pressure signal:
   - Safer edit boundary:
   - Decision: edit-in-place | extract helper | add owner file | split task | pause for plan update

   Pre-Edit Owner-Fit Decision:
   - Edit intent: wiring-only | move-out / extract-first | local-fix-without-new-responsibility | new-responsibility | emergency / compatibility patch
   - Owner fit:
   - Safer edit boundary:
   - Decision: edit-in-place | extract helper | add owner file | split task | pause for plan update
   ```

   If the check contradicts the plan's file boundary, pause and return to plan
   review instead of silently stuffing logic into an overloaded owner. If the
   budget result is `over-budget` and the task does not also govern that
   overrun, stop execution and return to plan review rather than pushing the
   task through as if it were still atomic.
   When the target edit file is over-budget or mixed-purpose,
   `new-responsibility` must not be added in place by default. `wiring-only`,
   `move-out / extract-first`, and `local-fix-without-new-responsibility` may
   proceed only when they do not add a new responsibility and the verification
   boundary is clear. `emergency / compatibility patch` requires residual risk
   and a retirement trigger.
5. Run verifications as specified
6. Update `TodoCheckpointDraft` and `DriftCheckDraft` before marking the task completed.
   When an `Execution Readiness View` exists, the drift check must explicitly
   compare the active slice against the view's intent lock, scope fence,
   baseline lock, compatibility boundary, retirement boundary, test
   obligations, and review gates.
7. Mark as completed

### Step 3: Complete Development

After all tasks complete and verified:
- Announce: "I'm using the finishing-a-development-branch skill to complete this work."
- **REQUIRED SUB-SKILL:** Use aegis:finishing-a-development-branch
- Follow that skill to verify tests, present options, execute choice

## When to Stop and Ask for Help

**STOP executing immediately when:**
- Hit a blocker (missing dependency, test fails, instruction unclear)
- Plan has critical gaps preventing starting
- You don't understand an instruction
- Verification fails repeatedly

**Ask for clarification rather than guessing.**

## When to Revisit Earlier Steps

**Return to Review (Step 1) when:**
- Partner updates the plan based on your feedback
- Fundamental approach needs rethinking

**Don't force through blockers** - stop and ask.

## Remember
- Review plan critically first
- Follow plan steps exactly
- Don't skip verifications
- Reference skills when plan says to
- Stop when blocked, don't guess
- Never start implementation on main/master branch without explicit user consent

## Integration

**Required workflow skills:**
- **aegis:using-git-worktrees** - REQUIRED: Set up isolated workspace before starting
- **aegis:writing-plans** - Creates the plan this skill executes
- **aegis:finishing-a-development-branch** - Complete development after all tasks
