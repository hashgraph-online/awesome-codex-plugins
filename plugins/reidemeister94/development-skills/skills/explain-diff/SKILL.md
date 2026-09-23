---
name: explain-diff
description: Explain a code change, its reasons, effects, trade-offs, and verification limits.
argument-hint: "[--visual] [scope]"
user-invocable: true
allowed-tools: Glob, Grep, Read, Bash, Write, AskUserQuestion
---

# Explain diff

Explain the change so the user can understand its behavior and maintain it.
Manual mode is repository-read-only; `--visual` may write only to system temp.

Use the requested worktree, branch, range, pull request, patch, or packet. Default to the current worktree.
Inspect the implementation, request, relevant decisions, verification, review verdict, and evidence limits.
Use runtime data and logs when they settle a material claim. Label absent or stale evidence **Unverified change**.
For `--visual`, read [visual mode](references/visual-mode.md).

Explain the result, prior behavior, reasons, important failure cases, operational effects, and trade-offs.
The explanation must stand alone without requiring the user to open the repository.
Explain public or operational names before using them. Include implementation detail only when it helps the user's purpose.
Use a diagram or concrete example when it makes the behavior clearer.

## Optional dialogue

When the user wants an interactive explanation, ask applied questions one at a time.
Ask the user to predict behavior, make a decision, or diagnose an observable result.
Test useful reasoning, not remembered syntax or file layout. The user can skip questions or request another explanation.
Do not delay task completion for a mandatory quiz or record personal comprehension scores.

When an answer exposes conflicting requirements or behavior, inspect the evidence before treating the answer as wrong.
Persist only confirmed, useful decisions in the document that owns them. Manual mode proposes edits without writing.

If evidence disproves the implementation, return to the affected workflow step.
Changed code repeats verification and review before the final explanation.
