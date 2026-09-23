# Zero-friction policy

Codex Quota Optimizer exists to improve the Codex experience, so the optimizer itself must not become the overhead.

## Invariants

CQO should add:

- **0 additional model calls** just to classify or budget a task.
- **0 network requests** for task classification, journaling, or auditing.
- **0 blocking budget gates** in the Codex execution path.
- **0 forced user confirmations** when a soft budget is exceeded.
- **0 automatic subagents** created by CQO itself.

The Skill should remain useful even if the optional CLI is never installed or run.

## Soft budgets, not hard limits

Task budgets are guidance. If evidence shows that another file, test, or reasoning step is required for correctness, continue without interrupting the user.

Do not pause execution just because:

- a suggested discovery range was exceeded,
- another dependency must be inspected,
- a broader verification step becomes necessary,
- the task was initially classified too small.

Reclassify internally when needed and keep moving.

## Classifier behavior

Task classification should happen inside the existing reasoning turn or through the optional local heuristic CLI.

Do not make a second LLM call solely to classify a task.

The local classifier may use:

- task text,
- current Git change-surface size,
- risk terms,
- complexity/debugging terms.

Its output is advisory, not authoritative.

## Optional local journal

The CLI stores task-level state under:

```text
~/.cqo/
```

or the directory provided by `CQO_HOME`.

It stores only local task metadata and does not contact OpenAI, inspect private account pages, or estimate hidden account quota.

The journal should prefer task-level observations over tool-level tracing. Do not hook every Codex tool call merely to collect analytics.

## Audit honesty

CQO must not invent token savings, quota savings, or precise avoided-cost percentages.

An audit may report:

- the task classification,
- the selected soft budget,
- the current local Git change surface,
- CQO policy decisions it did not force (for example, no automatic full-suite run),
- explicit notes supplied by the user.

Do not report actions as "avoided" unless there is direct evidence they would otherwise have occurred.

## CLI placement

The `cqo` CLI is an inspection and journaling layer, not a runtime dependency.

Normal Codex execution must continue to work when:

- the CLI is absent,
- no CQO session was started,
- the journal directory was deleted,
- the user never asks for an audit.

The default experience should feel like Codex with better discipline, not Codex behind another approval system.
