---
name: brainstorming
description: "Use when the user wants to brainstorm, choose an approach, design something, or clarify an ambiguous or consequential change."
user-invocable: true
allowed-tools: Glob, Grep, Read, Bash, Task, AskUserQuestion, Skill
---

# Brainstorming

Interview until you and the user share the same understanding.
Walk every branch of the decision tree and resolve dependent decisions in order.
Attach a recommended answer and its trade-off to every question.
Group only independent questions, as the [development loop](../../shared/development-loop.md) Reach agreement section requires.
The number of questions follows the ambiguity: stop when every branch is settled, not at a fixed count.
This rule applies on every path, whether or not the task needs a plan and chronicle.

<HARD-GATE>
Do not write code before the presented design or plan is approved.
Do not write the plan while purpose, scope, solved state, proof, or a contested design remains unresolved.
Once these points are settled, return them to the development loop.
The loop presents the complete design or plan before asking for approval.
Do not ask for separate approval before the plan.

If the user asks for no questions, remove ceremony but keep open decisions.
Present the open decisions with recommendations in one pass instead of choosing silently.
</HARD-GATE>

## Who decides what

- **Facts**: inspect the filesystem, tools, and code. Never ask for discoverable facts.
- **Required outcomes and business trade-offs**: ask the user and apply the answer.
- **Implementation**: recommend and defend an approach with evidence.

The [development loop](../../shared/development-loop.md) Design authority section owns the remaining boundaries.

## Interview for the design

Judge data shape against the [engineering contract](../../shared/engineering.md).
Use concrete cases to expose conflicting meanings and missing boundaries.
Cover errors, edge cases, and assumptions that would invalidate the solution.

Offer genuinely different alternatives and recommend the simplest one that meets the constraints.
Use `best-practices` when current evidence can change the choice.
Persist research only when it remains useful after the task.

If `$ARGUMENTS` is empty, ask what to explore and stop.
Use `AskUserQuestion` for decisions when that tool is available and permitted.
When finished, return to the development loop if you were already there.
