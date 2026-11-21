# --threat-verify Mode

Verify that threat mitigations declared in a threat model (ADR threat table, PLAN.md risk section, or an architecture review's threat table) are actually implemented in the codebase.

**Trigger:** pass `--threat-verify` or say "verify threat mitigations" / "check threat model compliance"

**Input:** threat model source: file path or pasted content. Accepted formats: ADR threat table, PLAN.md risk section, free-form "Threat: X / Mitigation: Y" pairs.

**Process:**
1. Parse the threat model into: { threat_id, description, declared_mitigation, expected_location }
2. For each threat: grep the codebase for the declared mitigation at ALL relevant entry points (routes, handlers, middleware, auth layers)
3. Classify each threat:
   - **CLOSED**: mitigation confirmed at all relevant entry points
   - **OPEN**: mitigation partially implemented (found in some but not all entry points)
   - **UNREGISTERED**: no evidence of declared mitigation in codebase
4. Output THREAT-REVIEW.md:

```
| Threat ID | Description | Declared Mitigation | Status | Evidence | Gaps |
| --- | --- | --- | --- | --- | --- |
```

**Blockers:** OPEN and UNREGISTERED items are reported as blockers: the recommendation is to close them before shipping; the user makes the final call.

**What this is NOT:** This mode does not scan for new vulnerabilities (that is what the OWASP lane does). It only verifies previously declared mitigations exist.
