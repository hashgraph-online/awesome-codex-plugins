---
name: scheduled-job-reliability
description: "Use when a periodic, cron, or triggered compute job must run correctly despite missed runs, overlap, retries, or schedule drift"
---

# Scheduled Job Reliability

## Iron Law

```
NO SCHEDULED JOB WITHOUT IDEMPOTENCY, MISSED-RUN DETECTION, OVERLAP CONTROL, AND A COMPLETION SIGNAL
```

"It runs on a timer" is not a reliability design. A timer that silently skips, double-fires, or overlaps is an outage waiting for a quiet weekend.

## Overview

A scheduled job is compute triggered by time or an external event rather than a user request. Its failure modes are distinct from request services and from data pipelines: the trigger can be missed, fire twice, drift across time zones, or overlap a still-running prior instance, and no user is watching when it does.

**Core principle:** make each run idempotent and bounded, detect when a run is missed or stuck, prevent overlap, and emit a completion signal that something alerts on.

## When To Use

- A job runs on a schedule (periodic, cron-style) or on an external trigger and must complete correctly.
- Runs can be missed, delayed, double-fired, or overlap a previous run.
- The job mutates state, sends messages, or produces artifacts other systems depend on.
- Schedule behavior depends on time zones, daylight-saving transitions, or leap handling.

## When Not To Use

- The work is data-pipeline freshness, lineage, or backfill of a dataset; use `data-pipeline-reliability`.
- The work is broker- or queue-driven event consumption; use `event-workflows`.
- The job is a one-shot destructive bulk mutation; use `configuration-and-automation-safety`.
- The concern is the container/runtime lifecycle, drain, or probes; use `container-runtime-and-orchestration`.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Trigger source, schedule, time-zone basis, expected run frequency, and acceptable lateness.
- What the run mutates or emits, and which downstream systems depend on it.
- Run duration distribution, deadline, and behavior when a run exceeds the interval.
- Idempotency/dedup design for repeated or partial runs.
- Missed-run, failed-run, and stuck-run detection and alerting.
- Catch-up policy: backfill missed windows, run once, or skip.
- Concurrency/locking: singleton, leader election, or bounded parallelism.

## Workflow

1. **State the contract.** Write what one successful run guarantees and the acceptable lateness in user or downstream terms.
2. **Make the run idempotent.** Use an idempotency key or dedup record per logical window so a retried or double-fired run does not double-apply effects; checkpoint partial progress so a resumed run continues rather than restarts harmfully.
3. **Prevent overlap.** Choose singleton execution, leader election, or bounded concurrency; decide whether a late run is skipped or queued when the prior run is still active.
4. **Pin the time basis.** State the time zone and how daylight-saving and leap transitions are handled so the job neither double-fires nor skips a window at a transition.
5. **Bound the run.** Set a per-run deadline and behavior on overrun (kill and retry, or let it finish and skip the next window); never let runs pile up unbounded.
6. **Detect missed and stuck runs.** Alert on "expected a run by T and none completed" and on "a run started but did not finish within the deadline," beyond explicit errors; a job that never fires emits no error.
7. **Define catch-up.** Decide whether missed windows are backfilled, collapsed to one run, or skipped, and make backfill idempotent and rate-bounded.
8. **Emit completion evidence.** Record start, end, outcome, and window covered so success is observable and gaps are countable.

## Synthesized Default

Run each job as an idempotent, deadline-bounded, single-writer operation over an explicit time window, with missed-run and stuck-run alerting and a recorded completion signal. Prefer skip-if-overlapping with catch-up over unbounded queuing. Treat a silently missed run as an incident-class defect, not a cosmetic gap.

## Phase Behavior

- Ideation: identify risks, defaults, unknowns, options, and the next decision before code exists.
- Design: shape the target artifact, tradeoffs, checks, and details to gather.
- Development: guide sequencing, code boundaries, checks, and acceptance criteria.
- Testing: define release-blocking tests, evals, fixtures, and failure probes.
- Release: define rollout, observability, abort, rollback, and readiness details.
- Maintenance: define owners, drift checks, cleanup triggers, and refresh cadence.
- Existing artifact: use current code, schedules, logs, or incidents as context for the next engineering decision; do not wait for a finished artifact before guiding design, build, release, or operation.
- Missing details: state assumptions and say what to check next instead of blocking lifecycle guidance.

## Exceptions

- A purely advisory, side-effect-free job may skip overlap control if a double run is provably harmless.
- A job whose missed run is recovered by the next run may use skip-with-no-catch-up if downstream tolerance is explicit.
- Very low-frequency jobs may rely on lighter detection if a missed run is caught by a human cadence that is named.

## Response Quality Bar

- Lead with the run contract, idempotency design, overlap policy, or missed-run detection requested.
- Cover idempotency, overlap, time basis, deadline, missed/stuck detection, catch-up, and completion evidence before optional scheduling breadth.
- Make recommendations actionable with concrete trigger, lock, deadline, alert, and catch-up decisions.
- Name the details to inspect, such as schedule, run durations, lock mechanism, dedup keys, and run history; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside scheduled/triggered compute reliability. Route data-pipeline freshness, broker workflows, one-shot mutations, and runtime lifecycle when those are central.
- Be concise: prefer a run-contract table and failure-mode list over generic cron explanation.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Run contract: what one successful run guarantees and acceptable lateness.
- Idempotency and partial-progress design.
- Overlap/concurrency policy and lock mechanism.
- Time-basis and daylight-saving/leap handling.
- Deadline and overrun behavior.
- Missed-run and stuck-run detection and alerting plan.
- Catch-up/backfill policy.
- Completion-evidence and run-history record.

## Checks Before Moving On

- `idempotent_run`: a repeated or double-fired run does not double-apply effects; partial progress resumes safely.
- `overlap_control`: singleton/leader/bounded concurrency is defined, with skip-or-queue behavior on overlap.
- `time_basis`: time zone and daylight-saving/leap behavior cannot double-fire or skip a window.
- `run_deadline`: a per-run deadline and overrun behavior exist; runs cannot pile up unbounded.
- `missed_run_alert`: missed-run and stuck-run conditions alert without relying on an explicit error.
- `catch_up_policy`: backfill/skip/collapse behavior for missed windows is explicit and idempotent.
- `completion_signal`: each run records start, end, outcome, and window covered.

## Red Flags - Stop And Rework

- The job has retries but no idempotency, so a retry double-applies effects.
- Two runs can overlap with no lock, corrupting shared state.
- A missed run produces no signal because the trigger simply never fired.
- A run can exceed its interval and queue indefinitely behind itself.
- Daylight-saving or time-zone change double-fires or skips a window.
- "Success" is inferred from no error rather than a recorded completion.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Trusting the timer | Detect missed and stuck runs explicitly; a no-fire emits no error. |
| Retry without idempotency | Make each run idempotent before allowing retries. |
| Ignoring overlap | Enforce singleton/leader/bounded concurrency with skip-or-queue rules. |
| Wall-clock naivety | Pin the time zone and handle daylight-saving and leap transitions. |
| Unbounded catch-up | Make backfill idempotent and rate-bounded, or collapse missed windows. |
