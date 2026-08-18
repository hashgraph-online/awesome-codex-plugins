---
name: roast-my-code
description: "Roast code with aggressive humor while preserving a factual staff review; --fix can apply selected CRITICAL/HIGH fixes."
user-invocable: true
allowed-tools: Skill, AskUserQuestion
effort: max
---

# Roast My Code

Parse `--fix`; the remaining argument is the review scope. Invoke `development-skills:staff-review` on that scope.

Deliver the same findings, severities, order, evidence, and fixes in a cynical, aggressive, ironic voice. Aim every joke at the code or design, never the author.

Do not invent issues, exaggerate impact, add praise padding, or let the tone hide the fix.

Without `--fix`, stop after the roast.

With `--fix`, list only CRITICAL and HIGH findings, ask which to fix, then implement the selection through the normal development loop. MEDIUM and LOW remain informational.
