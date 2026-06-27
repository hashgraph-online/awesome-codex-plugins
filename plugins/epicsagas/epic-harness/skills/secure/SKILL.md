---
name: secure
dimension: control_and_safety
description: "Security review checklist with optional engagement scoping. Use when auth, DB, API, infra, or secrets code is touched."
---

# Secure — Security Review

## Iron Law

NO DEPLOYMENT WITHOUT SECURITY REVIEW OF ALL CHANGED FILES. Every code change is a potential attack vector.

## Process

### Step 0: Load Engagement Context (Optional)

Check for engagement scoping:
```bash
cat .harness/engagement.md 2>/dev/null
```

If `.harness/engagement.md` exists:
1. Parse the **Scope**, **Constraints**, and **Exclusions** sections
2. Restrict security checks to in-scope components
3. Apply rules of engagement (method, rate limits, no-exfil rules)
4. Skip findings matching exclusion patterns
5. Include engagement reference in report header

If not found: apply full OWASP Top 10 checklist (default behavior). No scope restrictions.

See `references/engagement.md` for the engagement file format.

### Step 1: Identify Security-Relevant Changes

Identify security-relevant changes from the diff (auth, DB, API, infra, secrets).

### Step 2: Run Checklist

Run the Checklist below, marking each item as pass, fail, or N/A with reason.

### Step 3: Report

For each failure, cite the file and line number with severity (CRITICAL/HIGH/MEDIUM).
Report findings using the Evidence Required section.

## When to Trigger
- Authentication or authorization code changed
- Database queries written or modified
- API endpoints added or changed
- Environment variables or secrets referenced
- File upload, user input parsing, or serialization code
- Infrastructure config (Docker, K8s, CI/CD)

## Checklist

### Injection
- [ ] All user input sanitized/escaped before use in queries — unsanitized input is the #1 attack vector for SQL injection, XSS, and command injection
- [ ] Parameterized queries used (no string concatenation in SQL) — string concatenation enables SQL injection even with escaping; parameterized queries are the only safe default
- [ ] No `eval()`, `exec()`, or template injection vectors — these functions execute arbitrary code and bypass all input validation

### Authentication & Authorization
- [ ] Auth checks on every protected endpoint — missing checks on a single endpoint exposes the entire system
- [ ] Tokens validated and not just decoded — decoding without signature verification lets attackers forge any token
- [ ] Session expiry and refresh logic correct — stale sessions allow account takeover; refresh token rotation prevents replay attacks
- [ ] No hardcoded credentials or secrets in code — hardcoded secrets end up in version control and are impossible to rotate

### Data Exposure
- [ ] Sensitive data not logged (passwords, tokens, PII) — logs are often accessible to more people than the database and persist indefinitely
- [ ] API responses don't leak internal details — stack traces, DB schemas, and server versions help attackers craft targeted exploits
- [ ] Error messages don't reveal system internals — generic errors in production prevent information disclosure; detailed errors belong in server logs only
- [ ] `.env` files in `.gitignore` — committed `.env` files expose secrets permanently even after deletion (git history retains them)

### Access Control
- [ ] RBAC/permissions checked before data access — authorization must happen at the data layer, not just the UI layer, to prevent IDOR and privilege escalation
- [ ] No IDOR (Insecure Direct Object Reference) vulnerabilities — replacing an ID in a URL should never grant access to another user's resource
- [ ] Rate limiting on authentication endpoints — without rate limiting, brute-force and credential-stuffing attacks are trivial

See `references/security.md` for the full OWASP Top 10 checklist.

## Anti-Rationalization

| Excuse | Rebuttal | What to do instead |
|--------|----------|-------------------|
| "This is internal-only, no security risk" | Internal tools get exposed. Assume every endpoint is public-facing. | Apply the same security standards as public APIs. |
| "We'll add security later" | Security debt compounds exponentially. Fix it now or pay 10x later. | Build it secure from the start. Retrofitting misses edge cases. |
| "The framework handles security" | Frameworks provide tools, not guarantees. OWASP Top 10 still applies. | Verify framework defaults and add application-layer checks. |
| "Security review is overkill for this" | One missed injection is a breach. Every input surface matters. | Run the checklist. It takes 2 minutes, a breach takes months. |
| "We'll harden it before production" | Security bolted on later is always incomplete. | Build it secure now. Retrofitting misses edge cases. |
| "It's an internal API, no one will abuse it" | Lateral movement attacks start from internal APIs. | Internal does not mean trusted. Validate and authorize every request. |
| "I'll just disable CORS for development" | Dev shortcuts leak into production. | Use a proper CORS allow-list from day one. |
| "Engagement scoping is bureaucratic overhead" | Unscoped assessments waste time on irrelevant surface area. | Define scope once, get focused results. Opt-in only. |

## Evidence Required

Before claiming security review is complete, show ALL applicable:

- [ ] Checklist above completed: each item marked pass or N/A with reason
- [ ] No secrets in code: `grep -r "sk-\|password\s*=" --include="*.{ts,js,py}" .` shows clean
- [ ] Parameterized queries used: show the query code (no string concat)
- [ ] Auth checks present on new endpoints: show the middleware/guard
- [ ] `.env` in `.gitignore`: confirmed
- [ ] Engagement context loaded (or confirmed absent): scope applied to findings

**A blank checklist is not a review. Each item needs a pass or N/A.**

## Red Flags
- Storing secrets in code or config files committed to git
- Using `HTTP` instead of `HTTPS` for sensitive data
- `eval()` or string-concatenated SQL anywhere
- Skipping engagement scope when `.harness/engagement.md` is present
- Reporting findings outside authorized scope as blockers (informational only)
