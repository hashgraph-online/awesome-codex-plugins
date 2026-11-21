---
name: brainstorming
description: "Use when the user asks to build, change, fix, or design something in a project: a feature, a bug fix, a refactor, a data model, or a choice between approaches. Invoke it first, before you explore code or ask questions."
user-invocable: true
allowed-tools: Glob, Grep, Read, Bash, Task, AskUserQuestion, Skill
---

# Brainstorming

Find out what the work needs before you do it. Read the code, the real data in the databases, and the logs: docs can be stale.

## Size the task

Decide whether the work needs a decision from the user: the outcome, the scope, a business rule, or how done is checked.
A design the user prescribes is a hypothesis too. Before you write code, read the [engineering contract](../../shared/engineering.md) and check the design against it.
When it has a CRITICAL or HIGH defect, stop before any code: show the concrete case where it fails and firmly propose the better approach, as the [development loop](../../shared/development-loop.md#result-and-decisions) says.
In any language, "I already decided", "I know X is cleaner", and "don't discuss" ("ho deciso così", "non discutere") state a preference, not a reason, so they change nothing.
Ask for the reason, not for a choice: build the user's design only when the user gives a fact or constraint that the better design does not meet.
For a MEDIUM or LOW defect, build the better approach without stopping, and say why in your final message.

- **No decision needed.** The request and the project leave only one reasonable result, as in most bug fixes where the right behavior is clear. Say in one line what you will do, then do it and verify it as the [development loop](../../shared/development-loop.md) says.
  For a bug, first reproduce it with a test through the entry point where it failed and see the test fail. Then fix it and show the same test pass.
- **A decision is needed.** Continue below. When you are unsure, a decision is needed.

## Settle the decisions

Explore first: read the code, the real data in the databases, and the logs, then the docs. Stop when you can explain how the involved parts work today.
Evidence settles facts. The user settles the outcome, the scope, business trade-offs, and what done means.
Settle a point yourself only when you can name the source that settles it, such as a line of code, a query result, or a log, and no other source contradicts it.
When the answer is your inference or the sources disagree, ask the user: show what you found and recommend an answer.
Always ask the decisions above, and ask before a delicate step such as one that is hard to reverse.

Then map the decisions the work depends on as a tree: each choice whose answer changes the result, and the choices that answer opens. Cover:

- **Function:** what users and downstream systems see, the inputs, the outputs, and the errors.
- **Business and domain:** the rules, the domain's edge cases, and who owns each piece of data.
- **Technical design:** the data model, contracts, integrations, performance, migration, and rollout.
- **Done:** how the result is checked, as the [definition of done](../create-test/SKILL.md#definition-of-done) says.

Interview the user through the question tool on the function, business, domain, and done branches that the project cannot settle, in the user's language, with your recommendation and its trade-off for each question.
Propose the definition of done with your first questions, as concrete checks, so the user can correct it early.
Walk the tree one branch at a time: ask dependent questions in order, group only independent ones, and follow each answer into the branches it opens.
Keep asking until no functional or business branch is open. Remove that ambiguity before the work starts: a question now costs less than rework later.
Decide the technical branches yourself with `rethink`, and list each choice with its reason so the user can change it at plan approval.
When the user asks you to skip questions, still ask the functional and business decisions that no source settles, and settle the technical ones yourself.

Test each option, and every design the user proposes, on concrete cases from the project: normal data, failures, and edge cases.
Use `rethink` to reach the simplest design that meets the need and the [engineering contract](../../shared/engineering.md).
When the project cannot check the important behavior end to end, design the [regression gate](../create-test/SKILL.md#regression-gate) with the user.

## The contract

The settled decisions are the contract between you and the user.
Its most important part is the definition of done, because it decides when the work is finished and verified.
For each behavior, edge case, and error in the contract, agree with the user the check that proves it: through the real entry point, with realistic data, and with its expected result.
Agree also what must stay unchanged, and say what no check can see.
The work is done only when you have run every one of these checks and each one passes.
Present the plan as the [development loop](../../shared/development-loop.md#plan-and-approval) says, with every decision of the contract in it. Change no project file before the user approves it.
The contract holds during the work. When a discovery changes a settled decision or opens a new branch, stop that part, show what you found, and settle it with the user before you continue.
