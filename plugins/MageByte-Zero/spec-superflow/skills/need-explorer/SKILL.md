---
name: need-explorer
description: Clarify intent, scope, constraints, and success criteria before artifact creation. Invoke when the request is fuzzy, the user is comparing options, or the workflow needs a stable change definition before writing artifacts.
---

# Need Explorer

Turn a rough idea into a stable change definition before writing artifacts.

## Primary Goal

Agree on: problem, scope, non-goals, success criteria, whether to split before specification.

## Process

### 1. Inspect Context First

Before asking questions, understand what exists and what constraints are in place.

### 2. One Question at a Time

Ask a single clear question, wait for the answer, digest, then ask the next. Never ask 3+ questions at once. Each answer informs the next question.

### 3. Prefer Multiple-Choice Questions

Present 2-3 options when reasonable answers are finite. This reduces cognitive load and surfaces unconsidered choices.

### 4. Propose 2-3 Approaches with Trade-Offs

For each approach: what it is, upside, downside, best-for. Then **recommend one** and explain why. Never present a single path — always name at least one alternative.

### 5. Validate Before Concluding

Restate what you heard: "Here's what I'm hearing: [problem, scope, non-goals, success criteria]. Does this match?" Incorporate corrections and re-validate.

### 6. DP-1: Requirement Confirmation Gate

After user confirms the summary:
```bash
npx --yes --package spec-superflow@0.11.0 ssf state set <change-dir> dp_1_result "confirmed: <one-line summary>"
npx --yes --package spec-superflow@0.11.0 ssf state set <change-dir> dp_1_timestamp $(date -u +%Y-%m-%dT%H:%M:%SZ)
```
DP-1 confirms scope, non-goals, and success criteria before artifact creation.

### 7. Hand Off

Once DP-1 is recorded, hand off to `spec-writer`.

## Anti-Patterns

- **Skipping exploration**: "Simple" changes have scope too. Five minutes of exploration prevents two hours of rework.
- **Proposing solutions before clarifying**: If the user says "add caching," first ask what problem caching solves.
- **Exploring indefinitely**: Stop when change name, problem statement, scope, non-goals, success criteria, and decomposition decision are all clear.

## Exploration Standard

You must leave exploration with: a usable change name, a crisp problem statement, scope boundaries, non-goals, success criteria, and a decomposition decision (one change or split).

## Strong Rule

Do not produce implementation code. This skill stabilizes intent, not builds.

## Self-Review Before Handoff

1. **Placeholder scan**: No "probably", "maybe", "TBD", or "we'll figure it out later"
2. **Contradiction check**: No scope items conflicting with non-goals or constraints
3. **Scope check**: Can a developer draw a bright line between in and out?

## Exception Handling

- **Parse failures**: Report the specific file, proceed with available information
- **Missing files**: Note absent essential files as constraints, continue
- **User interruption**: Exploration is stateless — on resume, re-ask the current question
