# Structured Reasoning Pattern

**Purpose**: Solve documentation and harness-design problems by decomposing them into structured steps.

## Core Principle

Before starting non-trivial create or refactor work, write an internal structured reasoning note. Do not require any external reasoning MCP or dedicated reasoning tool.

## Reasoning Depth by Complexity

| Complexity | Steps | Typical work |
|------|------|------|
| LOW | 1-2 | Small wording fix, one-file cleanup |
| MEDIUM | 3-5 | Document refactor, rule consolidation |
| HIGH | 5-8+ | Multi-file skill redesign, harness restructuring |

## When to Use

| Situation | Required |
|------|------|
| New documentation skeleton | Yes |
| Refactoring a long or repetitive skill | Yes |
| Reworking provider-sensitive guidance | Yes |
| Adding a small note to an already-stable doc | Optional |

## Local Note Shape

| Field | Description |
|------|------|
| `problem` | The documentation or harness-design problem to solve |
| `steps` | Numbered reasoning steps scaled to complexity |
| `revision` | Any source check or readback that changed the plan |
| `branch` | Alternative structure considered when tradeoffs matter |
| `decision` | Final structure plan and next edit target |

## Example: Refactoring a stale skill

```text
Structured reasoning note:
1. Problem: Refactor the docs mode so its core rules stay provider-neutral and remove mixed implementation concerns.
2. Evidence pass: Read the skill body and rule files, then classify content into core, provider-reference, and local-overlay groups.
3. Plan: Rewrite canonical files to keep only documentation and harness rules; move provider-sensitive details to references.
4. Validation: Run grep checks for stale model literals and review the final wording for consistency and validation coverage.
Decision: Edit the core skill first, then update linked rules and validation notes.
```

## Key Capabilities

### 1. Dynamic adjustment

The step count is not fixed. Increase or reduce it when the document scope changes.

### 2. Revision

Revisit prior reasoning when a source check invalidates an assumption.

### 3. Branching

Use branching when comparing alternative document structures or rule-pack splits.

## Wording Rules for Reasoning Notes

- End each reasoning step with a concrete conclusion or next action.
- Avoid speculative language when the next step requires verification.
- Prefer statements grounded in file reads or source evidence.

## Checklist

- [ ] Determine complexity
- [ ] Set an initial step count
- [ ] Write the first step as a problem definition
- [ ] Revise or branch if the scope changes
- [ ] End with a clear decision and next edit target

## Sources

> No external sources were used. Content checked 2026-09-21.

This file is this package's own procedure text and cites no external source.
