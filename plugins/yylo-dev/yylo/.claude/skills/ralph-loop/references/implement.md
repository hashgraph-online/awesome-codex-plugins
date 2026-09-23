<!-- GENERATED DESTINATIONS: edit this canonical source, then run `npm run generate:implementation-contract`. -->
---
description: Implement exactly one assigned Kanban task in its admitted Bolt product worktree and stop after queueing it.
---

# Bolt implementation worker contract

An implementation worker owns one explicitly assigned task. It does not select
other work, mutate the product target, merge, release, deploy, or clean another
task's workspace.

## Execution boundary

The external agent performs implementation, tests and commits. The CLI owns
workspace preparation, deterministic finish and safe integration, not model
implementation or automatic retry/repair. Task run/resume and implementation
budget recovery are retired. `yy watch status|await|follow RUN_ID` is an optional
read-only observer of existing evidence; it never launches or cancels producers.
A process exit or captured answer does not prove task completion. Continue an
existing admitted workspace only after verifying current ownership; preserve
historical runs and never replay/reset them automatically.

## 1. Resolve and preserve admission

1. Read `AGENTS.md` and the complete assigned task from the canonical controller.
2. Run `yy task start TASK_ID` unless the handoff already contains the matching
   active Bolt task record. Verify the returned worktree, branch, full target ref,
   and exact base SHA before editing; stop on missing or contradictory evidence.
3. Work only in that product worktree. Never edit product files in the controller
   or copy controller ledgers, specs, state, or artifacts into a task worktree.
4. Preserve controller identity and workspace-role checks. Controller checkpoints
   are best-effort local durability warnings after terminal metadata is durable;
   they are not product inputs or lifecycle gates.

## 2. Implement

1. Edit only requested product paths and preserve project sources of truth.
2. Use focused affected tests in the edit loop. Other feature worktrees may run
   concurrently; do not wait for or modify them.
3. Run any project-required tests and semantic reviews explicitly during task
   work. Merge launches zero models, selects no reviewer, and owns no repair or
   validation loop. Never delegate those checks to delivery.
4. If blocked, record bounded truthful state and stop without claiming success.
   Durable diagnostic output belongs in a verified Ledger Artifact Record when
   the installed API supports it; otherwise preserve an external draft and stop,
   never fall back to product documentation or direct controller-store edits.

## 3. Queue and hand off

1. Run focused tests, required dangerous-path checks, parity checks, and
   `git diff --check`.
2. Stage only task-owned paths, commit coherently, and leave the worktree clean.
3. Run `yy task finish TASK_ID` directly after the clean commit; it independently
   enforces admission and validation of the exact committed tip and records
   `QUEUED` with its immutable review-ready closure. Repair any admission,
   generated-output, runtime, or closure refusal while still `WORKING`.
4. Optional read-only `yy task preflight TASK_ID` can diagnose admission before
   finish; it is not a prerequisite or a replacement for finish enforcement.
5. Record the commit and bounded response in Kanban. A lifecycle finalizer may
   attempt a controller checkpoint after terminal metadata is durable; checkpoint
   failure remains a warning and must not change the task or merge outcome.

Stop after queueing. Read-only delivery observation uses `yy merge status
TASK_ID`. One authorized target owner runs `yy merge land TASK_ID` for exactly
that immutable source; land projects the verified Git result to Ledger automatically.
Use `yy merge project TASK_ID` only to recover failed or stale projection. Implementation agents do not land their own work, discard dirty
bytes, reuse a stale candidate after target movement, or claim that Git ancestry
proves tests or requirements. Tests and semantic reviews remain explicit project
checks outside merge; merge launches zero models and owns no repair loop.

Release-version changes use this same ordinary task/merge lifecycle. Package
preparation is maintainer-only and outside `yy`. Never create a tag, push,
publish, deploy, mutate production, restart services, run post-deploy E2E, or
clean worktrees without separate authority.
