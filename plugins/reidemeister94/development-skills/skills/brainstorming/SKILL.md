---
name: brainstorming
description: "Use when the user wants to do brainstorming, choose an approach, design something or clarify an ambiguous or consequential change before planning or implementation."
user-invocable: true
allowed-tools: Glob, Grep, Read, Bash, Task, AskUserQuestion, Skill
---

# Brainstorming

Interview the user relentlessly about every aspect of this until we reach a shared understanding. Walk down each branch of the decision tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time with a recommendation and trade-off, waiting for feedback on each question before continuing. Asking multiple questions at once is bewildering.

If a *fact* can be found by exploring the environment (filesystem, tools, etc.), look it up rather than asking the user. The *decisions*, though, are mine — put each one to me and wait for my answer.

Do not act on it until I confirm we have reached a shared understanding, an agree on purpose, scope, solved state, and what evidence would show the proposed answer is wrong.

If `$ARGUMENTS` is empty, ask what to explore and stop.

Use `best-practices` when current evidence can change the choice. Persist research only when it remains useful after the task.

Offer genuinely different alternatives and recommend the simplest that meets the result and constraints.

When finished, return to the full [development loop](../../shared/development-loop.md) if you were already there.

Use `AskUserQuestion` for decisions.
