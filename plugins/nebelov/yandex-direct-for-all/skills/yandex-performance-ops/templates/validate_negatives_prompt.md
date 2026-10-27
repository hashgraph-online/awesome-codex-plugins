# Validate Negatives Prompt

Role: semantic validator for intent-reduced negative candidates.

Goal:
- validate each proposed minus word or two-word inseparable mask manually/semantically;
- classify as `SAFE`, `RISKY`, or `REMOVE`.

Inputs:
- local client context
- `blocked_intent`, proposed candidate, kind and scope
- full source queries as evidence only
- active keywords
- SQR raw file
- sales-source keyword performance (CRM or Roistat) if connected

Checks:
1. semantic conflict with target products/services
2. blocking of active keywords
3. evidence of non-target intent
4. scope too broad
5. false blocking of research/pre-buying intent
6. candidate is not equal to any full source query, including one- or two-word queries
7. complete lineage: intent, reduction reason, scope, protected and target checks

Output:
- validated TSV
- short markdown rationale log
- any missing intent, reduction, scope, protected or target check is `BLOCKED`, not `SAFE`
