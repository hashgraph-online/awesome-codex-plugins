---
name: executing-plans
description: "Use when you have a written implementation plan to execute in a separate session with review checkpoints"
---

# Executing Plans

## Overview

Load plan, review critically, execute all tasks, report when complete.

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

For non-trivial execution, include `Aegis Visibility`: briefly tie the active
slice to its plan, checkpoint, drift or verification boundary. At completion,
pass plan adherence, evidence, complexity and residual risk to
`verification-before-completion` for the unified receipt.

If subagents are available and the plan has genuinely independent tasks,
prefer `subagent-driven-development`; lack of subagent support does not block
inline execution. Same-task agents share one workspace, and the coordinator
remains the only Git mutation owner.

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
5. Run the TDD Route Guard before implementation: confirm `Mode`, `Decision`, `Strict authority`,
   `Test posture`, and verification. Strict steps require recorded explicit
   user/project authority; plan approval or risk labels are not authority. An
   off-mode missing record may be repaired only as `Mode: off / Decision:
   skipped` without loading TDD. Missing/unsupported auto decisions return to
   plan review. Only `Decision: strict` with recorded strict authority may
   authorize steps named `Write failing test`, `Verify RED`, `GREEN`, or
   `REFACTOR`. Do not infer `strict` during execution.
6. If concerns: Raise them with your human partner before starting
7. Before the first write, capture `TaskStartSnapshot`: root, `HEAD`, branch or
   detached state, upstream divergence, staged/unstaged/untracked paths, active
   Git operations, and `git worktree list --porcelain`. Preserve task-preexisting
   state; do not stash, reset, clean, or commit it.
8. Reuse the current branch unless rules require independent history or another
   goal owns it. If justified, switch/create it in the
   current workspace when safe; a worktree still requires
   concurrent checkout or blocking dirty state.
9. If no concerns: Create TodoWrite and proceed

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

Before a verification-driven unplanned edit, read retained `PatchShape`,
`CanonicalOwner`, `UpwardDrillSignal`, outcome, and evidence refs. Route their
comparison with the candidate to `systematic-debugging` before editing; it
decides whether the directions converge. A proven independent canonical-owner
root stays on the normal plan path.

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
6. The coordinator is the Git mutation owner. After the coherent Task passes
   its planned verification, use `verification-before-completion` before a
   default local commit, stage only task-owned paths, and read back `HEAD`, the
   committed file list, and remaining task delta. `no commit`, read-only,
   no-change, and failed-verification tasks create no normal commit.
7. Update `TodoCheckpointDraft` and `DriftCheckDraft` before marking the task completed.
   When an `Execution Readiness View` exists, the drift check must explicitly
   compare the active slice against the view's intent lock, scope fence,
   baseline lock, compatibility boundary, retirement boundary, test
   obligations, and review gates.
8. Mark as completed

### Step 3: Complete Development

After all tasks complete and verified:

- if Aegis created a branch/worktree or the user requests integration handling,
  use `aegis:finishing-a-development-branch`;
- otherwise use `verification-before-completion`, report the local task commit
  and `Task clean` / `Repository clean`, and do not invent merge/PR ceremony.

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
- Do not create a branch merely because the current branch is `main`/`master`
- Do not let task complexity, TDD, planning, or subagents alone trigger a worktree

## Integration

**Required workflow skills:**
- **aegis:writing-plans** - Creates the plan this skill executes
- **aegis:using-git-worktrees** - Only when the approved Git lifecycle says a concurrent checkout is necessary
- **aegis:finishing-a-development-branch** - Only when branch/worktree integration or cleanup is in scope
