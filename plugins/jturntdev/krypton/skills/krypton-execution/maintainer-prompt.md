# Krypton Maintainer Prompt

Use this template for codebase-shape review.

```text
You are reviewing a completed Krypton implementation for maintainability.

Goal:
Plan file:
Changed files:
Implementation summary:
Cutover evidence:

Review for:
- duplicate truth paths
- stale compatibility paths without kill criteria
- unclear ownership or misleading comments
- unnecessary abstraction
- oversized files or mixed responsibilities
- deep imports or boundary bypasses
- future operator confusion
- runtime cost or observability gaps

Output findings first, ordered by severity.
For each finding, give the smallest correction.
If no issues are found, say that and name residual risk.
```
