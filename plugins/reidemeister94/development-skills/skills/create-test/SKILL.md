---
name: create-test
description: "Define or implement regression proof: test strategy, black-box or integration tests, KPIs, thresholds, audits, or missing tests."
argument-hint: "[file-or-directory-or-goal]"
user-invocable: true
allowed-tools: Glob, Grep, Read, Bash, Edit, Write, AskUserQuestion
---

# Create test

Start with the user need or business rule that must always hold, not files, coverage, or internal calls.
Inspect for facts; ask only for business decisions that cannot be discovered.

## Define the regression contract

Establish:

- actors, goals, and externally observable outcomes;
- business rules and invariants that must never change;
- critical paths and relevant rejection, timeout, retry, permission, concurrency, and partial-failure cases;
- the current baseline and every intended behavior change;
- KPIs with window, data set, acceptable variance, and justified pass or fail threshold;
- systems crossed, production-like data needs, and evidence the available environment can provide.

Never invent a metric or threshold; record the gap.
Match the proof's inputs and environment to the context it claims to model.
A subprocess that represents normal runtime must not inherit test-only environment variables.

## Choose the proof

Prefer the highest reliable boundary:

1. black-box tests through the public API, UI, job, event, or CLI;
2. deep integration with the real database, queue, connector, or protocol;
3. contract, replay, property, or characterization tests for narrower risks;
4. unit tests for isolated rules where a wider test adds no confidence.

Mock only beyond the verified boundary.
For database or migration work, read [integration patterns](references/integration-patterns.md).
When proving a process manager, worker, container entrypoint, or deployed artifact, use the real container or operating-system image.
Verify worker replacement, signal handling, and graceful shutdown only when those boundaries apply.

For strategy or audit only, return the contract, prioritized scenarios, proof method, and blind spots.
Judge tests by failures caught, not assertion or coverage counts.
Ask which states the proof covers and whether it includes the most fragile states.

## Prove a refactor differently

A refactor keeps behavior. Capture a characterization baseline and observe it green on the unchanged code and after the refactor.
Never break working behavior to watch a refactor test fail.
If the baseline cannot run, name what is missing instead of lowering the proof standard.

## Prove a performance claim

A performance claim needs a measurement that could contradict it.
Measure unchanged and changed code with the same tool, environment, and data set.
Name the tool and workload. Report the results and run-to-run spread, not one best run.
For a hard maximum, define valid samples and repetitions before measuring, then judge the worst valid sample.
Measure every required process or worker. Report setup separately from the measured interval.
Profile before optimizing. An unmeasured performance claim remains unproven.

## Implement when asked

Follow project layout and the development loop.
Add the smallest important proof, observe it fail, make approved source changes, then observe it pass.
Assert outcomes, state, events, metrics, and error contracts rather than calls.
Run focused and relevant suites. Report what the evidence proves and what it does not cover.
