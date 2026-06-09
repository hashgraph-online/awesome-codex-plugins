---
name: subagent-execution
description: Delegated step runner over the HOTL execution state machine — delegates eligible steps to fresh subagents while the controller keeps governance, verification, and stop conditions.
---

# HOTL Subagent Execution

## Overview

This is a **delegation profile** over the HOTL execution state machine defined in `skills/loop-execution/SKILL.md`. It follows the same resolve → preflight → lint → execute → verify → loop → gate → summarize flow, but eligible steps are delegated to fresh subagents instead of running inline.

**Core principle:** delegation is allowed; governance is not delegated.

## When to Use

- The workflow file already exists (canonical `docs/plans/YYYY-MM-DD-<slug>-workflow.md` preferred; legacy root `hotl-workflow-<slug>.md` still accepted during migration)
- Steps are independent enough to hand to one worker at a time
- You want the controller to stay in this session and keep ownership of gates and verification

## Execution

Follow the **HOTL Execution State Machine** in `skills/loop-execution/SKILL.md` for the full execution flow (workflow resolution, interrupted run detection, branch/worktree preflight, structural lint, execution state persistence, typed verification, loop rules, gate rules, completion).

The controller owns all `hotl-rt` runtime calls. The controller calls `hotl-rt init`, `hotl-rt step N start/verify/retry/block`, `hotl-rt gate N`, and `hotl-rt finalize` from the resolved `execution_root` and pins every call to the captured `run_id` (`--run-id <run-id>` or `HOTL_RUN_ID=<run-id>`). Subagents never call the runtime directly. The runtime-managed `.hotl/state/<run-id>.json` and `.hotl/reports/<run-id>.md` are the source of truth; delegated workers do implementation only. After execution is finalized, use `hotl:finishing-a-development-branch` to decide what happens to the execution branch/worktree.

The only difference is **how each step body runs:**

1. Announce the step
2. Decide whether to delegate or run inline (see Delegation Rules below)
3. If delegated:
   - Dispatch a fresh subagent with the full step text, the relevant files, and the success condition
   - Do not make the subagent infer the plan from scratch — provide the step directly
   - Require the delegated worker to return one of the statuses defined below
   - Answer clarifying questions before letting the subagent continue
4. If inline: execute the step directly in the controller session
5. Run verification, loop rules, and gate rules as defined in the state machine

## Delegated Worker Prompt Requirements

Every delegated implementation prompt must include:

- Full workflow step text, including `action`, `loop`, `verify`, `gate`, and any relevant frontmatter context
- Exact files or directories the worker may inspect or edit
- The success condition in plain language
- A reminder that the worker is not alone in the codebase and must not revert unrelated changes
- A reminder that the worker must not call `hotl-rt`, mark workflow checkboxes, run gates, or finalize the run
- The required report format:

```
Status: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
Summary:
Files changed:
Tests or checks run:
Concerns or blockers:
```

## Handling Worker Status

Treat the worker's status as an input to controller judgment, not as proof of completion.

**DONE:** Continue with controller-owned verification for the step.

**DONE_WITH_CONCERNS:** Read the concerns before verification. If they raise correctness, scope, safety, or architecture risk, address them before marking the step verified. If they are non-blocking observations, record them in the runtime report and continue to verification.

**NEEDS_CONTEXT:** Provide the missing context and re-dispatch the same step. Do not count this as a failed loop iteration unless the worker had enough context and still could not proceed.

**BLOCKED:** Stop the step and assess the blocker. Options are: provide more context, split the step, run the step inline in the controller, or mark the step blocked through `hotl-rt step ... block`. Do not retry the same prompt unchanged.

Never mark a delegated step complete from the worker report alone. The controller must inspect the changed files as needed, run the configured verification, apply loop rules, and record the result with the pinned `run_id`.

## Critical Invariants

These rules apply regardless of delegation decisions:

1. **Verification always runs in the controller session** — never in the subagent
2. **Gates always stay in the controller session** — `gate: human` pauses the controller, not the subagent
3. **No nested delegation** — subagents cannot spawn other subagents
4. **No parallel write-heavy steps** — do not run multiple implementation subagents in parallel against the same workflow
5. **Controller owns stop conditions** — on repeated verify failure, the controller stops and reports; it does not let the subagent retry silently

## Delegation Rules

**Delegate by default:**
- Test-writing steps
- Implementation steps
- Localized documentation changes
- Contained refactors

**Keep controller-owned by default:**
- Human-gated steps
- Security-sensitive decisions
- Final verification and summaries
- Any step whose failure would require architectural judgment

## Review Checkpoints

Record `git rev-parse HEAD` as the review base before delegating each reviewable batch.

### After Meaningful Delegated Batches

After a meaningful batch of delegated implementation completes and verification passes:
1. Invoke `requesting-code-review` from the controller (not from a subagent)
   - Review type: checkpoint
   - Review base: the recorded pre-batch HEAD
   - Steps reviewed: all steps completed in this batch
2. When findings return, invoke `receiving-code-review` in the controller
   - Follow Verify → Evaluate → Respond → Implement
3. Resolve all BLOCK findings before delegating the next batch

Review is not required after every single delegated step. The controller decides when a batch is "meaningful" based on:
- 3+ completed implementation steps
- Cross-module changes
- High-risk, user-facing, or shared-infra changes

### Before Final Completion

A final review is required unless the most recent review already covers all current changes and no code changed afterward.

1. Invoke `requesting-code-review` with review type: final
   - Review base: branch point or last review base, whichever is more recent
2. When findings return, invoke `receiving-code-review`
3. Resolve all BLOCK findings before finalizing
4. If fixes after the last review changed scope, constraints, or risk_level, request a scoped follow-up review before completing

Review happens after step verification, before `verification-before-completion`, before `hotl-rt finalize`.

## Reporting

Execution report output must conform to `docs/contracts/execution-report-output.md`. This is the canonical reporting contract from `skills/loop-execution/SKILL.md`. Live step visibility follows the same rules as `skills/loop-execution/SKILL.md` — per-step chat logs on all platforms, deterministic renderer for final summary.

## Related Skills

- `hotl:loop-execution` — the canonical execution state machine (this skill builds on it)
- `hotl:verification-before-completion` — required before claiming done
- `hotl:dispatch-agents` — use for generic parallel independent tasks, not governed workflow execution
