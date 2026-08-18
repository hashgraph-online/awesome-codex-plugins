# Orchestration context budget

Load the sections needed for the current workflow.

## Delegation gate

Delegate only when one or more conditions hold:

- at least two workstreams can finish without waiting for each other;
- exploration or logs would pollute the main decision context;
- independent specialist review adds materially different coverage;
- exclusive subsystem ownership makes parallel implementation safe;
- the task is too large for one coherent context but can be partitioned by a stable boundary.

Prefer one agent when coordination, duplicated reading, or merge conflict is likely to dominate.

## Topology matrix

| Work shape | Topology | Worker posture |
|---|---|---|
| Security, test, and reliability review of one diff | Fan-out/fan-in | Parallel read-only |
| Unknown code path before implementation | Pipeline | Explorer, then implementer |
| Independent services behind stable contracts | Partitioned implementation | Exclusive write ownership |
| Shared schema still changing | Pipeline | Contract first, consumers later |
| Large test or build output | Isolated analysis | One worker returns failing cases |
| Small local fix | Single agent | No delegation |

## Worker context package

Include:

- one objective;
- relevant entry points or artifacts;
- applicable constraints;
- exact permissions;
- evidence requirements;
- output limit;
- stop condition.

Exclude:

- unrelated conversation history;
- raw output from other workers;
- superseded plans;
- broad repository dumps;
- expected conclusions that bias independent review.

## Summary contract

A useful worker summary contains:

1. conclusion;
2. source, file, command, or documentation evidence;
3. uncertainty and checks not run;
4. recommended next action;
5. changed files, when writes were authorized.

For review workers, cap candidate findings and require realistic impact. For test workers, return the command, exit status, failing cases, and concise diagnostic evidence instead of full logs.

## Agent budget

- Begin with one main agent.
- Add the smallest number of workers that matches independent workstreams.
- Start with two workers for a new fan-out pattern.
- Add another worker only when it owns a distinct question or subsystem.
- Stop idle, duplicated, or scope-expanding workers.
- Avoid nested delegation unless the new task is both independent and material.

This is a workflow budget, not a product limit.

## Efficiency measures

Compare:

- total workers and retries;
- elapsed time;
- duplicate reading and duplicate findings;
- main-thread context clarity;
- unique verified findings or completed workstreams;
- conflicts and integration rework;
- tokens, credits, or cost when the surface exposes them;
- defects found after acceptance.

Do not reduce “efficiency” to token count. A smaller run that produces an incorrect change is not efficient.
