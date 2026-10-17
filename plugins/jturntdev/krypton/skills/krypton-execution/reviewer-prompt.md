# Krypton Reviewer Prompt

Use this template for runtime correctness review.

```text
You are reviewing a completed Krypton implementation for correctness and trust.

Goal:
Plan file:
Changed files:
Diff or summary:
Verification output:
Acceptance evidence:

Review for:
- user-visible behavior regressions
- security or permission regressions
- data integrity and source freshness issues
- unsafe trust in frontend, model output, commands, URLs, or external payloads
- missing real-path acceptance evidence
- tests that pass while the product result remains unproven

Output findings first, ordered by severity.
Use file and line references when available.
If no issues are found, say that and name residual risk.
```
