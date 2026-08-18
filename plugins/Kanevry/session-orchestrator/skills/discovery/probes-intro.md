# Discovery Probes Reference

This document defines all discovery probes used by the discovery skill. It is a reference
document -- not a skill. The main SKILL.md references probes by name and category.

Each probe specifies: activation conditions, exact detection commands, evidence format,
and default severity. All Grep patterns and Bash commands are copy-pasteable.

## Confidence Scoring Reference

Each probe category has typical confidence factors. Use these as guidance when scoring findings:

**Code probes:** Pattern specificity is the primary driver. Hardcoded secrets (API key regex) score high (+20); generic URL matches score low (+0). Findings in test fixtures or example files always get low file context (+0).

**Infra probes:** CI failures and known CVEs score high (objective, verifiable signals). Outdated minor version bumps score low. Deployment health failures score high.

**UI probes:** WCAG Level A violations (img-no-alt, html-no-lang) score high. Responsive heuristics (fixed widths, absolute positioning) score medium — context-dependent.

**Arch probes:** Circular dependencies with short cycles (2-3 files) score high. Deep nesting in generated/vendored files scores low. Complexity hotspots in frequently-changed files score higher.

**Session probes:** Hallucination checks score high (objective, commit-verifiable). Stale issues with no priority label score low. Gap analysis on planned items scores high.

**Feature probes:** Doc claims with exact enforcement-token matches score high (objective, grep-verifiable); heuristic keyword-to-token guesses score low. Flag-name pattern matches in generated/vendored files score low; hits on exported/public routes score higher.

---
