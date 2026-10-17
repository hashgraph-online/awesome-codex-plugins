---
name: orchestrate-engineering
description: Coordinate complex engineering work across bounded subagents while protecting the main context, preventing edit conflicts, and measuring whether delegation was worthwhile. Use when the user asks to delegate, parallelize, orchestrate, use subagents, fan out a review, or handle a large task with independent workstreams; do not use for small, tightly coupled, or inherently sequential tasks.
---

# Orchestrate Engineering

## Start with the delegation decision

1. Read applicable `AGENTS.md` files and the task’s acceptance criteria.
2. Map dependencies before creating workers.
3. Use one agent when the task is small, tightly coupled, or dominated by shared-file edits.
4. Delegate only when at least two workstreams are genuinely independent, noisy investigation should be isolated, or specialized review materially improves coverage.
5. Explain the chosen topology briefly before starting workers.

Subagents normally consume more total tokens than a comparable single-agent run. Optimize for fewer failed loops, cleaner context, better coverage, or lower elapsed time—not the highest agent count.

## Choose a topology

- Use **fan-out/fan-in** for independent read-only research, review, triage, or log analysis.
- Use a **pipeline** when exploration, planning, implementation, testing, and review depend on prior outputs.
- Use **partitioned implementation** only after shared interfaces are stable and each worker owns exclusive files or subsystems.

Read [references/context-budget.md](references/context-budget.md) when selecting a topology, preparing worker context, defining summaries, or evaluating efficiency.

## Prepare every worker

Give each worker:

```text
Objective:
Bounded scope:
Required context:
Allowed actions and permissions:
Required evidence:
Output format:
Stop condition:
```

Provide the minimum task-local context. Do not copy the entire main-thread history into every worker.

## Coordinate

1. Start with the smallest useful number of workers.
2. Keep research, review, and test-analysis workers read-only when possible.
3. Assign exclusive ownership before parallel writes.
4. Keep cross-cutting decisions, requirements, and interface changes in the main thread.
5. Require concise evidence summaries instead of raw logs.
6. Stop or steer workers that expand scope, duplicate another worker, or lose their evidence path.
7. Wait at explicit dependency or integration gates.

## Integrate and verify

1. Validate worker claims against source files, commands, or authoritative documentation.
2. Deduplicate findings and resolve contradictions.
3. Integrate write results in dependency order.
4. Run focused checks, cross-module checks, and a final combined-diff review.
5. Report verified outcomes, unverified areas, residual risks, and worker failures.
6. Compare the orchestration against the single-agent alternative using available evidence.

## Guardrails

- Do not claim token savings without measurement.
- Do not delegate merely because subagents are available.
- Do not let parallel workers edit the same file.
- Do not allow a worker’s unverified assumption to become another worker’s requirement.
- Do not broaden sandbox, network, or external-system permissions for convenience.
- Do not continue spawning workers recursively without a new independent need.
- Preserve user authority for destructive, production, credential, and external write actions.

## Acceptance criteria

- The topology matches the dependency graph.
- Every worker has bounded scope and a stop condition.
- Parallel write ownership is exclusive.
- Worker summaries are smaller and cleaner than their working context.
- The main agent validates and integrates rather than forwarding claims blindly.
- System-level verification covers cross-worker behavior.
- The final report states whether delegation improved quality, elapsed time, or context clarity enough to justify its cost.
