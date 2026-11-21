# Artifact Levels

**Purpose**: Pick the smallest prompt artifact level that satisfies the request. **Read when**: choosing or downgrading the artifact level.

## Levels

| Level | Required shape |
|---|---|
| Standalone reusable prompt | Intent, inputs, authority, scope, output, verification, stop |
| Parameterized template | Standalone contract plus typed variables, defaults, missing-input behavior, and examples |
| Prompt pack | Identity, variables, context packet, examples, constraints, output schema, eval cases, source handling when needed, and version note |
| Eval-only artifact | Scenario, oracle, runner, judge, trace, gate, baseline, and result contract |

## Selection Rule

Do not force a full prompt pack onto a user who requested only a reusable prompt or eval fixture. When a downstream parser consumes the result, use stable machine-readable keys and reject malformed required inputs rather than guessing.

## Sources

> No external sources were used. Content checked 2026-11-03.

This file restates the artifact levels this package already applied; it cites no external source.
