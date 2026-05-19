---
name: goal-framing
description: Use when the user explicitly sets an Aegis goal with /aegis-goal, Aegis goal:, or asks to define goal, success evidence, stop condition, or task boundaries before work.
---

# Aegis Goal Framing

Use this skill to create a thin goal frame before execution. It is opt-in and
boundary-setting only.

Do not use it for tiny edits, one-command checks, or ordinary fast-path Q&A
unless the user explicitly asks for `/aegis-goal` or `Aegis goal:`.

## Authority Boundary

Current owner:

- Method Pack task framing

Not owned here:

- authoritative `GateDecision`
- final evidence sufficiency
- final completion authority is not owned here
- host daemon / automatic stop enforcement

## Input Forms

Treat these as equivalent:

- `/aegis-goal <task description>`
- `Aegis goal: <task description>`
- "Define the goal / stop condition before we start"

Slash commands are optional host shortcuts. The natural-language form is the
portable fallback.

Example:

```text
Aegis goal: Fix the auth refresh bug without rewriting the auth system.
```

## Output

Produce the smallest useful frame:

```text
TaskIntentDraft:
- Requested outcome:
- Goal:
- Success evidence:
- Stop condition:
- Non-goals:
- Constraints:
- Scope:
- Risk hints:
- Route:
- Next:
```

Stop condition must distinguish:

State set: `done`, `blocked`, `needs-verification`, `scope-exceeded`.

- `done`: success evidence is satisfied
- `blocked`: required dependency, permission, or information is missing
- `needs-verification`: implementation exists but evidence is insufficient
- `scope-exceeded`: continuing would exceed the goal or non-goals

## Routing

After framing:

- Low-risk single-owner work may continue through the normal fast path or TDD
- Ambiguous product / architecture / contract work routes to `brainstorming`
- Approved requirements route to `writing-plans`
- Multi-step, compaction-prone, handoff, or subagent work routes to
  `long-task-continuation`
- Bug diagnosis routes to `systematic-debugging`

### Route Matrix

| Goal signal | Route |
| --- | --- |
| single-owner, low-risk, clear verification | fast path or `test-driven-development` |
| bug, failure, regression, unexpected behavior | `systematic-debugging` |
| ambiguous product, architecture, contract, cross-module behavior | `brainstorming` |
| approved spec, stable requirements, implementation slicing | `writing-plans` |
| multi-step, compaction-prone, handoff, subagent work | `long-task-continuation` |
| completion, release, handoff, "is this done?" | `verification-before-completion` |

Only create `docs/aegis/` records when the routed workflow needs persistent
evidence. Goal framing alone does not create project files.

## Subagent Context Packet

When delegating work, pass a compact packet instead of the full conversation:

```text
SubagentContextPacket:
- Task:
- Goal:
- Stop condition:
- Relevant baseline refs:
- Relevant files:
- Known facts:
- Unknowns:
- Non-goals:
- Expected output:
- Verification expected:
- Must-read excerpts:
- Unsafe assumptions:
```

The packet reduces repeated file reading, but it does not replace evidence.
Subagents should still read the smallest raw file/log/test excerpt needed to
verify critical facts.

Do not paste full chat transcripts, full session history, or unbounded logs into
the packet. If a fact matters, include a file ref, line/window hint, or compact
must-read excerpt.

## Drift Rule

If the goal changes mid-task, do not silently overwrite it. Record old goal,
new goal, changed scope, new risks, and route through `DriftCheckDraft` when a
long-task record exists.
