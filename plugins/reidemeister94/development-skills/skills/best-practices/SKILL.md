---
name: best-practices
description: "Research current best practices and turn the evidence into a clear recommendation. Use for state-of-the-art, evidence-based, optimal-approach, comparison, or pros-and-cons questions in any field."
argument-hint: "<topic>"
user-invocable: true
allowed-tools: WebSearch, WebFetch, Read, Glob, Grep, Skill
---

# Best Practices

Match research depth to the decision: quick lookup for a narrow fact; multiple primary sources for costly, risky, disputed, or fast-changing choices.

Use `/deep-research` on Claude when available; on Codex, browse iteratively.

Prefer primary sources, cite material claims inline, and separate evidence from inference. Explain consensus, disagreement, uncertainty, and where each recommendation applies. Recommend for the user's goals and constraints, not for an imaginary average user.

If missing context changes the answer, ask for it or give clearly conditional recommendations. Do not pad the report with source quotas, evidence labels, or weak secondary material.
