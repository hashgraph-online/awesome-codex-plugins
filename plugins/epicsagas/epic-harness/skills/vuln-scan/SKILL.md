---
name: vuln-scan
description: "Systematic vulnerability scanner across injection, auth, data exposure, and dependencies. Use when scanning for vulnerabilities, reviewing security, or validating threat models."
---

# Vuln Scan — Systematic Vulnerability Scanner

## Iron Law

Code you haven't scanned for vulnerabilities has vulnerabilities you haven't found.

## Process

### Step 0: Load Engagement Context

Check for `.harness/engagement.md`. If present, load scope constraints — only scan in-scope paths and respect exclusions.

Check for `THREAT_MODEL.md` from a previous `/threat-model` run. If present, use its threat scenarios as scan targets. If absent, run full-surface scan.

### Step 1: Scope the Scan

```bash
# Gather changed files (for incremental scans)
git diff --name-only $(git merge-base HEAD main)

# Or scan entire codebase
find . -type f \( -name "*.rs" -o -name "*.ts" -o -name "*.js" -o -name "*.py" -o -name "*.go" \) \
  | grep -v node_modules | grep -v target | grep -v vendor
```

### Step 2: Run Scan Dimensions (Parallel)

Launch all dimensions concurrently:

#### Dimension 1: Injection Scan

Search patterns:
```
eval(              exec(              system(
string concat SQL  format!.*query     raw_query
innerHTML          dangerouslySetInnerHTML
```

For each match:
- File, line number, surrounding context (5 lines)
- Severity: CRITICAL (eval/exec), HIGH (SQL concat), MEDIUM (DOM injection)

#### Dimension 2: Auth & Session Scan

Search patterns:
```
password           secret             api_key
token              credential         private_key
Bearer             Authorization
session            cookie
```

For each match:
- Check: hardcoded value vs. config/env reference
- Check: logged or exposed in error messages
- Severity: CRITICAL (hardcoded secret), HIGH (secret in log), MEDIUM (weak session config)

#### Dimension 3: Data Exposure Scan

Search patterns:
```
console\.log.*token    println!.*secret       log\.info.*password
\.env                  DEBUG.*=.*true         stacktrace
err\.message           error\.response
```

For each match:
- Check: sensitive data in log/output paths
- Check: error messages revealing internals
- Severity: HIGH (PII in logs), MEDIUM (verbose errors in production)

#### Dimension 4: Dependency Scan

```bash
# Rust
cargo audit 2>/dev/null || echo "cargo-audit not installed"

# Node.js
npm audit 2>/dev/null || echo "npm audit not available"
```

For each CVE found:
- Severity from advisory
- Is a fix available?
- Is the vulnerable path actually reachable?

### Step 3: Validate Findings

For each finding, apply adversarial validation:

1. **Is the code path reachable?** Dead code with `eval()` is INFO, not CRITICAL.
2. **Is input actually attacker-controlled?** Internal-only calls with trusted input are lower risk.
3. **Are mitigations already in place?** Parameterized queries behind string concat patterns = false positive.

### Step 4: Produce Output

Write `VULN-FINDINGS.json`:

```json
{
  "scan_date": "ISO-8601",
  "scope": "full | incremental",
  "threat_model_ref": "THREAT_MODEL.md | null",
  "findings": [
    {
      "id": "V1",
      "dimension": "injection | auth | exposure | dependency",
      "severity": "CRITICAL | HIGH | MEDIUM | LOW | INFO",
      "file": "path/to/file",
      "line": 42,
      "pattern": "matched pattern",
      "description": "what was found",
      "validated": true,
      "false_positive": false,
      "reachable": true,
      "mitigated": false,
      "threat_scenario": "T1 | null",
      "remediation": "one-line fix hint"
    }
  ],
  "summary": {
    "total": 10,
    "critical": 1,
    "high": 3,
    "medium": 4,
    "low": 2,
    "false_positives": 0
  }
}
```

### Step 5: Feed into Triage

After producing findings, suggest:
**"Run `/triage` to validate findings with adversarial review."**

## Anti-Rationalization

| Excuse | Rebuttal | What to do instead |
|--------|----------|-------------------|
| "Static scanning has too many false positives" | False positives are filtered in Step 3. Unfiltered findings are better than missed vulnerabilities. | Run the scan, then validate. Skipping scan guarantees missed vulns. |
| "We use a framework that prevents injection" | Frameworks prevent generic injection. Business-logic injection is framework-agnostic. | Scan for application-layer patterns too. |
| "Dependencies are vetted" | Transitive dependencies aren't. `cargo audit` / `npm audit` exist for a reason. | Run dependency scanning every time Cargo.lock or package-lock.json changes. |
| "The code is too new to have vulnerabilities" | New code has the most vulnerabilities. Old code has had time to be tested. | New code is the highest-priority scan target. |

## Evidence Required

- [ ] All 4 scan dimensions completed (injection, auth, exposure, dependency)
- [ ] Each finding validated: reachable, not false positive, severity confirmed
- [ ] VULN-FINDINGS.json written with summary
- [ ] If THREAT_MODEL.md exists: each threat scenario mapped to findings
- [ ] No CRITICAL/HIGH finding dismissed without explicit justification

## Red Flags

- Skipping dependency scanning because "we just updated"
- Marking findings as false positives without validation
- Scanning only changed files when full-surface scan was requested
- Not checking if code paths are reachable
- VULN-FINDINGS.json with zero findings on a non-trivial codebase — scan was likely incomplete
