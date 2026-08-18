---
name: workflow-builder
description: Scaffold an explicit one-shot workflow
---
# Workflow Builder — one-shot adapter authoring

Build a thin adapter only when a caller needs to dispatch an explicit set of
independent operations. A workflow is convenience code, never a correctness or
lifecycle authority.

At-most-once dispatch over explicit inputs is the whole safety argument: a
workflow that cannot retry or select work cannot compound a failure, so the
worst case is one reported error per operation.

Named failure mode — **framework gravity**: a one-shot script growing config
files, plugin hooks, and a state store until it is an unrequested orchestrator.

Anti-pattern: adding retry-on-failure "just for robustness". Corrective:
report the per-operation error and stop; the caller owns whether anything runs
again.

## Contract

- Inputs, executors, write scopes, and outputs are supplied explicitly.
- Each operation is dispatched at most once.
- Parallel operations must have caller-proven disjoint write scopes.
- The workflow reports per-operation output or error and then stops.
- It contains no work selection, retry, budget, queue, tracker, validation, Git,
  integration, closure, release, or delivery logic.
- Optional substrate state cannot be translated into RPI or verdict state.

Prefer the smallest script supported by the target runtime. Include a dry-run or
fixture demonstrating exact dispatch count and failure reporting. Do not create a
new framework or SDK abstraction unless the caller explicitly requests one.
