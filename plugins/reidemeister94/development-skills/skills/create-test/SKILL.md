---
name: create-test
description: "Use when you must define what done means for a task, design or write acceptance checks, build a regression gate for a refactor or behavior change, or check performance."
argument-hint: "[file-or-directory-or-goal]"
user-invocable: true
allowed-tools: Glob, Grep, Read, Bash, Edit, Write, AskUserQuestion
---

# Create test

An agent stops when its checks pass, so weak checks produce work that only looks done.
Start from what the system must do for its users and what evidence would show it. Build on the existing checks that already give that evidence.

## Definition of done

Agree on these before the work starts, and record them in the plan or the conversation:

- the observable result, as a user or a downstream system sees it;
- a check for every behavior, edge case, and error in the agreed design, so the checks cover the whole result;
- the oracle that decides whether a result is correct: agreed examples, a specification, the previous version, or a property;
- the commands that check it, with their environment, data, and passing result;
- what must stay unchanged, and how that is checked;
- what the checks cannot see.

Ask the user only for what the project cannot settle: business rules, acceptance examples, environments, acceptable differences.
Done means every agreed check passes and the required review has no open CRITICAL or HIGH finding.
Evidence is the command, its exit code, and the relevant output. Report the version, environment, and scenarios you checked.
An agreed check you have not run is an open point: close it as the [development loop](../../shared/development-loop.md#close-every-open-point) says.
For a request about strategy only, return the proposed checks and their limits and change no code.

## Choose the oracle

- **Bug:** reproduce the failure through the entry point where it happened and see it fail, then show the fix resolves it.
- **Refactor:** the previous version is the oracle. Run the checks on the unchanged code first, then keep them passing.
- **New behavior:** agree realistic examples with expected results and failure cases, and see the checks fail before the change.
- **Changed behavior:** the previous version is the oracle for everything else, and each intended difference is declared.

Check each user-visible result through its real entry point (API, UI, job, event, or CLI) with real wiring where it matters. Unit tests alone never show that the system works.
Mock only beyond the boundary the check claims to verify. Test settings must not change the runtime under test.
For database or migration work, read [integration patterns](references/integration-patterns.md). For startup, process management, or deployed code identity, prove it in a production-like run of the real image.

## Regression gate

A regression gate runs the candidate and a trusted reference version through complete real flows and compares what they do.
Use it before you merge a large refactor or a significant behavior change into dev, staging, or main.

The gate is sufficient when:

1. Both versions run on the same inputs and starting state, from real dev or staging data plus edge cases. Compare the inputs first, so data drift does not look like a code difference. Keep every write away from production.
2. It covers every entry point, background job, integration, and supported configuration, and reports the flows it does not reach.
3. It compares everything visible from outside: responses, persisted rows as multisets, messages, external calls, functional logs, errors, and the duration of each flow.
4. It requires exact equality, except for declared differences and for fields that also change when the reference runs against itself, normalized one by one. A duration fails when it exceeds the variation measured on the reference.
5. Each declared difference names the change, its reason, and a real before and after.
6. It fails on an undeclared difference, on a declared difference that does not appear, and on a flow that misses its outcome on either side: matching errors, a success that wrote nothing, or an unreachable side.
7. It runs as one command that exits 0 only when every check passes, and keeps a report.

Prove the gate before you rely on it, and again after you change it:

- Run the reference against itself and record the noise.
- Plant a known fault in a copy of the candidate or of a captured output, and see the gate fail.
- Measure which changed lines the gate runs, and explain each one it does not reach. Coverage finds gaps; it never proves correctness.

When the gate compares incompletely or wrongly, fix the gate first and then rerun it.

## Keep the checks honest

Never weaken, skip, or delete a check, or change an expected value, to make work pass.
A check changes only with a recorded reason that the reviewer sees. In a refactor, a check changes only to follow a renamed internal name.
When a check looks wrong or impossible to pass, stop and report it with the evidence.

## Supervised and autonomous work

In supervised work, the user approves the definition of done with the plan and sees the evidence at the end.
An autonomous run has no one to ask: settle everything above before it starts, and record the proven gate command in the plan.
On its last commit, the gate must exit 0 with only its declared differences. The [unattended-run rules](../../shared/unattended-runs.md) say how it reports `DONE` or `BLOCKED`.

## Performance

Measure the baseline and the candidate with the same workload, environment, and tools, and report the variation across runs.
Take thresholds from the requirement or agree them with the user before you measure. Never invent a target.
For a hard maximum, judge the worst valid sample: an average or median cannot hide an over-limit run.
Measure every required process or worker, and keep setup time out of the measured interval.
