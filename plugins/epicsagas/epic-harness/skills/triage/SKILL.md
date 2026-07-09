---
name: triage
description: "Adversarial validation of vulnerability findings. Use when triaging security findings, validating vulnerabilities, or prioritizing remediation."
---

# Triage — Adversarial Vulnerability Validation

## Iron Law

A vulnerability finding is not confirmed until an adversary would agree it's exploitable. Unvalidated findings are noise.

## Process

### Step 0: Load Inputs

Required inputs (in order of preference):
1. `VULN-FINDINGS.json` from `/vuln-scan`
2. Raw findings from `/audit --security`
3. User-provided finding list

Optional:
- `THREAT_MODEL.md` for threat scenario context
- `.harness/engagement.md` for scope constraints

If no findings input exists, suggest:
**"Run `/vuln-scan` first to generate findings to triage."**

### Step 1: Adversarial Review

For each finding, challenge it from an attacker's perspective:

#### Exploitability Check
1. **Can input reach the vulnerable code?** Trace the data flow from entry point to vulnerability.
2. **Can the attacker control the input?** Distinguish between user-controlled vs. system-generated data.
3. **Is there a path to impact?** Connecting the vulnerability to a security consequence (data leak, code exec, DoS).
4. **Are there bypasses for existing mitigations?** WAF, input validation, CSP — all have bypass techniques.

#### Severity Validation
| Criteria | Adjust |
|----------|--------|
| Requires authentication | Lower by 1 level |
| Requires specific permissions | Lower by 1 level |
| Chained with another finding | Raise by 1 level |
| Affects all users | Raise by 1 level |
| No mitigation in place | Raise by 1 level |
| Defense-in-depth exists | Lower by 1 level |

#### Classification
| Class | Meaning |
|-------|---------|
| `CONFIRMED` | Exploitable with demonstrated path |
| `LIKELY` | Exploitable with high confidence, minor gaps in proof |
| `POSSIBLE` | Theoretical, needs more investigation |
| `FALSE_POSITIVE` | Not exploitable with justification |
| `ACCEPTED_RISK` | Known, documented, accepted by team |

### Step 2: Dependency Analysis

Check if findings chain together:

1. **Find pairs** where finding A enables finding B (e.g., IDOR → data exposure)
2. **Mark chains** — chained findings are more severe than individual findings
3. **Identify root causes** — multiple findings from the same root cause should be grouped

### Step 3: Produce Output

Write `TRIAGE.json`:

```json
{
  "triage_date": "ISO-8601",
  "source": "VULN-FINDINGS.json | audit | manual",
  "findings": [
    {
      "id": "V1",
      "classification": "CONFIRMED | LIKELY | POSSIBLE | FALSE_POSITIVE | ACCEPTED_RISK",
      "original_severity": "CRITICAL",
      "adjusted_severity": "HIGH",
      "severity_adjustments": ["requires auth (-1)", "no mitigation (+1)"],
      "exploit_path": ["entry point → vulnerable function → impact"],
      "chains_with": ["V3"],
      "root_cause_group": "RC1",
      "remediation": "specific fix instruction",
      "effort": "low | medium | high",
      "validation_notes": "why this classification was chosen"
    }
  ],
  "root_cause_groups": [
    {
      "id": "RC1",
      "description": "shared root cause",
      "findings": ["V1", "V2"],
      "fix_once": "single fix that resolves all findings in group"
    }
  ],
  "chains": [
    {
      "findings": ["V1", "V3"],
      "combined_severity": "CRITICAL",
      "description": "V1 enables V3, creating..."
    }
  ],
  "summary": {
    "total_input": 10,
    "confirmed": 3,
    "likely": 2,
    "possible": 1,
    "false_positive": 2,
    "accepted_risk": 2,
    "root_cause_groups": 3,
    "chains": 1
  },
  "action_items": [
    {
      "priority": 1,
      "severity": "CRITICAL",
      "finding_ids": ["V1"],
      "action": "specific remediation step",
      "effort": "low"
    }
  ]
}
```

### Step 4: Report

Present prioritized remediation plan:

```
## Triage Report

### Summary
- Input: N findings
- Confirmed: X | Likely: Y | False positives: Z
- Root cause groups: K (fix-once opportunities)
- Chained findings: C

### Priority Actions
1. [CRITICAL] V1: {description} — {effort} effort
   Fix: {remediation}
2. [HIGH] V2+V3 (chain): {description} — {effort} effort
   Fix: {remediation}

### Accepted Risks
- V7: {description} — {justification}

### Suggested Next Steps
- Fix priority 1-3 before merge
- Run `/vuln-scan` after fixes to verify
```

## Anti-Rationalization

| Excuse | Rebuttal | What to do instead |
|--------|----------|-------------------|
| "All findings are real, no need to triage" | False positives waste fix time and erode trust in the process. | Validate every finding. Noise reduces signal. |
| "Triaging takes too long" | Fixing false positives takes longer than triaging them. | Triage first, fix only confirmed findings. |
| "It's obviously a vulnerability" | "Obvious" vulnerabilities are often mitigated by context you haven't checked. | Trace the exploit path before confirming. |
| "We can just fix them all" | Not all findings need fixing. Some are accepted risks. | Prioritize by confirmed severity and effort. |
| "Chaining is theoretical" | Real-world breaches use chained vulnerabilities. | Check for chains — they change severity. |

## Evidence Required

- [ ] Every finding classified (CONFIRMED/LIKELY/POSSIBLE/FALSE_POSITIVE/ACCEPTED_RISK)
- [ ] Each CONFIRMED finding has a traced exploit path
- [ ] Each FALSE_POSITIVE has justification for dismissal
- [ ] Severity adjustments documented per finding
- [ ] Root cause groups identified where applicable
- [ ] Chained findings identified and combined severity assessed
- [ ] TRIAGE.json written with action items
- [ ] Priority actions ordered by severity × effort

## Red Flags

- All findings marked CONFIRMED without exploit paths
- All findings marked FALSE_POSITIVE without justification
- No severity adjustments — original severity is almost never perfect
- Ignoring finding chains — individual severity ≠ chain severity
- Skipping dependency analysis between findings
- TRIAGE.json action items not ordered by priority
