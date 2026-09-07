# Bounded autonomous loop policy

Use this reference when a task is expected to need several autonomous
iterations or when retry, elapsed-time, token, or cost limits are part of the
task. Do not add this ceremony to a small change with an obvious check.

## Define the judge before building

```text
Judge command or observation:
Success predicate:
Known failure signature:
Maximum build-judge iterations:
Maximum no-new-evidence retries:
Time, token, or cost budget when surfaced:
Human-gate triggers:
```

Prefer a machine-decidable success predicate such as a test, evaluator, build,
or observable behavior. Keep subjective product, design, security, and risk
decisions human-gated rather than converting them into a weak automated proxy.

## Plan, build, judge

For each iteration:

1. **Plan:** choose one bounded change and state what new evidence it should
   produce.
2. **Build:** implement only that change.
3. **Judge:** run the predefined judge and compare the result with the success
   predicate.
4. Record the result and choose `pass`, `continue`, `blocked`, or `partial`.

Start another iteration only when the judge result or a new observation changes
the next technical decision. Repeating an unchanged command against unchanged
code is not an iteration; it is a retry.

Baseline reproduction happens before the build-judge budget starts. Count an
iteration whenever a repository change, including temporary diagnostic
instrumentation, is followed by the judge. Remove temporary instrumentation
before the final accepted judge unless the task explicitly requires it.

## Damping and stop-loss rules

- Change one causal variable per iteration when practical.
- After two identical failures, classify the failure before another attempt.
- Do not spend a new iteration on a hypothesis already disproved by the same
  repository state and evidence.
- Do not weaken tests, acceptance criteria, safety boundaries, or review gates
  to fit the remaining budget.
- Stop when an explicit iteration, retry, time, token, or cost budget is
  exhausted. Report the last judge result and the smallest evidence-producing
  next action.
- Pause at a human gate before expanding scope, changing a public contract,
  accessing an external system, or taking an irreversible action.

## Resumable checkpoint

At a phase boundary or before stopping, replace the previous checkpoint with:

```text
Confirmed facts:
Failed hypotheses — do not retry without new evidence:
Last judge command and result:
Current diff or checkpoint:
Budget used and remaining:
Next evidence-producing action:
```

This checkpoint is working memory, not a transcript. Keep commands and
diagnostics only when they affect the next decision.
