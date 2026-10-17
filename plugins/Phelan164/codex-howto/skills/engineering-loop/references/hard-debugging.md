# Hard debugging loop

Use this reference only after the normal engineering loop fails to isolate the
cause, or when the defect is intermittent, timing-sensitive, or
performance-related.

## Build a red-capable feedback loop

Define one agent-runnable command that can fail for the suspected behavior.
Prefer the narrowest deterministic test. If that is impossible, create a
bounded reproducer that records inputs, environment, and timing without
touching production.

Reduce the reproducer before expanding investigation:

- remove unrelated setup and data;
- pin variable inputs such as time, randomness, concurrency, and network
  responses where practical;
- preserve the smallest case that still fails;
- record the failure signature that distinguishes the bug from noise.

## Test ranked hypotheses

Write three to five falsifiable hypotheses. Rank them by evidence and cost to
test. For each hypothesis, state:

- the mechanism that could cause the failure;
- the observable prediction if it is true;
- one probe that can disprove it.

Change one variable per probe. Prefer targeted assertions, traces, counters, or
tagged logs over broad logging. Give temporary instrumentation a distinctive
tag so it can be found and removed.

Update the ranking after every probe. Discard disproven hypotheses instead of
retrofitting them to new evidence.

## Close the loop

After isolating the cause:

1. add a regression test at the closest stable seam;
2. implement the smallest causal fix;
3. rerun the original red-capable command;
4. run affected repository checks;
5. remove temporary instrumentation and experimental code;
6. confirm the failure signature no longer appears.

If no hypothesis survives, report the reproducer, probes, and missing evidence.
Do not claim a root cause from correlation alone.
