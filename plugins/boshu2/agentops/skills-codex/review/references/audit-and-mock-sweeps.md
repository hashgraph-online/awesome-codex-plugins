# Audit And Mock Sweeps

Use this reference when `/review` is acting as a broader audit rather than a normal diff review.

## Sweep Modes

| Mode | Trigger | Primary evidence |
|---|---|---|
| Codebase audit | User asks for risk review across a surface | Findings grouped by severity and domain. |
| Mock sweep | Tests pass but may avoid real behavior | Mock inventory plus risk classification. |
| Generated-code review | Agent output or large mechanical patch | Hallucinated refs, weak tests, broad edits. |
| External-review reconciliation | Tool output exists | Confirmed findings and dismissed false positives. |

## Mock Risk Classification

Classify each mock, stub, fixture, or fake:

- **Safe:** isolates a slow or nondeterministic boundary and still verifies contract.
- **Suspicious:** replaces business logic or hides integration behavior.
- **Blocking:** makes the test pass while the real service path is untested.

For suspicious or blocking mocks, require either a real-service test, a contract harness, or a documented exclusion.

## Finding Rules

- Do not report style-only issues unless they hide behavior risk.
- Every finding needs a file, behavior risk, and concrete fix.
- Dismiss external-tool false positives with a reason so they do not churn.
- Prefer one high-confidence finding over five speculative ones.

---

**Source:** Adapted from an external skill corpus / `codebase-audit`, `mock-code-finder`, and `ubs`. Pattern-only, no verbatim text.
