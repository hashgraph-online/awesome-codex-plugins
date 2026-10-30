---
name: principle-make-operations-idempotent
description: Use when designing commands, setup or install flows, lifecycle steps, or processing loops that might be retried or restarted. Every run, including one following a crash at any step, must end in the same correct state.
disable-model-invocation: true
---

# Make operations idempotent

Build each operation that changes state so that repeating it any number of times, even after a crash at an arbitrary point, lands on one correct final state.

## When it applies

Commands, lifecycle steps, setup and install flows, processing loops, and anything else that may be retried or restarted. Pure reads are exempt.

## What to do

1. For every mutating operation, answer three questions. What does a second consecutive run do? If an earlier run died at any given point, what does the next one do? Does rerunning end in the same state?
2. Base each step on the state present right now, rather than on what a prior run meant to do. Read what is there, compare it with the target, and change only what differs, so a repeated run finds no work left. A script that grants an IAM role should check whether the binding exists before adding it, so a second run is a no-op and not a duplicate or an error.
3. Leave anything a run might abandon (locks, temp files, half-written records, claimed jobs) in a form the following run can identify as stale. Base staleness on evidence that holds wherever the previous run stopped. A lock file holding a PID that is no longer alive is judgeable. A lock file with no owner information turns every crash into manual cleanup.
4. Write to a temporary path, then rename atomically into place, so readers never see a half-written file. Compare artifacts by content (a hash), not by creation order or timestamp.
5. If any answer in step 1 is "it depends on what was left behind", add a reconciliation step that inspects the leftovers and fixes them before proceeding.

Idempotency has a security side. A non-idempotent key-rotation job that crashes between "create new key" and "revoke old key" can leave two valid keys live, and a rerun may create a third. Designing it to converge closes that window.

## The failure it prevents

Restarts that turn into debugging sessions, duplicated side effects (two charges, two notifications, two credentials), and orphaned locks.

## Done when

All three questions in step 1 answer "same end state".

Related: [principle-separate-before-serializing-shared-state](../principle-separate-before-serializing-shared-state/SKILL.md), [principle-build-the-lever](../principle-build-the-lever/SKILL.md).
