---
name: audit
description: "Audit phase. Parallel review: code quality + security + tests. Outputs PASS/WARN/FAIL per dimension. Validates spec coverage."
---

# Audit — Verify Everything

**CRITICAL**: Run `HARNESS_DIR=$(epic path)` first. NEVER use `.harness/` in the project directory.

## Execution Modes

This skill has 3 internal modes that run in parallel:

1. **audit:code** — Code quality, logic, style, test coverage, spec coverage
2. **audit:security** — OWASP Top 10 + performance (N+1, leaks)
3. **audit:test** — Full test suite, AC verification, coverage delta

---

## Process

### Step 0: Prerequisites

Confirm go has run:
```bash
git symbolic-ref --short HEAD  # must NOT be main/master
```

Load the spec to know what was supposed to be built:
```bash
ls -t $HARNESS_DIR/specs/SPEC-*.md | head -1
```
Read the Requirements and Acceptance Criteria sections.

### Step 1: Gather Scope

```bash
git diff --stat $(git merge-base HEAD main)
git diff --name-only $(git merge-base HEAD main)
```

### Step 2: Scope Detection

| Pattern | Scope | Extra checks |
|---------|-------|-------------|
| `*.api.*`, `*route*`, `*controller*`, `*handler*` | API | + Contract testing, request validation |
| `*.tsx`, `*.jsx`, `*.vue`, `*.svelte`, `*.css` | Frontend | + Accessibility, semantic HTML |
| `*.sql`, `*migration*`, `*schema*` | Database | + Migration safety, rollback plan |
| `*.rs`, `Cargo.toml`, `*.go`, `go.mod` | Backend | + Build verification, type safety |
| `*.test.*`, `*.spec.*`, `__tests__/` | Tests | + Coverage delta, flaky test detection |
| `Dockerfile*`, `*.yml`, `*.yaml`, `Makefile` | Infra | + Config validation, secret detection |
| `*.md`, `*.txt` | Docs | + Link checking, freshness |

### Step 3: Run Checks in Parallel

Launch all 3 modes with `run_in_background: true`.

---

## Mode: audit:code (Review)

### Constraints
- Be specific — cite file and line number for every finding
- Suggest fixes, don't just flag problems — every finding needs a one-line fix hint

### Review Dimensions

1. **Correctness**: Does the code do what it claims? Edge cases handled?
2. **Logic**: Race conditions, off-by-one, null pointer risks?
3. **Style**: Consistent with project conventions? Readable?
4. **Tests**: Changes covered by tests? Tests meaningful?
5. **Naming**: Do names clearly convey intent?
6. **Spec coverage**: Each Requirement addressed in the diff?

### Output Format

```
## Code Review: <file or area>
- [BLOCKER] <description> (line X)
- [WARN] <description> (line Y)
- [NIT] <description> (line Z)

## Summary
- Blockers: N
- Warnings: N
- Verdict: APPROVE / REQUEST_CHANGES
```

---

## Mode: audit:security (Security)

### Constraints
- False positives are better than false negatives for security
- Always check `.env` files are in `.gitignore`

### Security Checklist (OWASP Top 10)

1. Injection (SQL, XSS, command)
2. Broken authentication
3. Sensitive data exposure
4. Access control failures
5. Security misconfiguration

### Performance Checklist

1. N+1 queries
2. Unbounded data loading
3. Missing indexes
4. Memory leaks (event listeners, growing caches)
5. Blocking main thread

### Output Format

```
## Security Audit
- [CRITICAL] SQL injection risk in <file>:<line>
- [HIGH] Hardcoded secret in <file>:<line>
- [MEDIUM] Missing rate limit on <endpoint>

## Performance Audit
- [HIGH] N+1 query in <file>:<line>
- [MEDIUM] Unbounded array growth in <file>:<line>

## Summary
- Security: PASS / FAIL (N critical, N high)
- Performance: PASS / WARN (N issues)
```

---

## Mode: audit:test (Test Runner)

1. Run the full test suite
2. Verify each Acceptance Criterion is demonstrably met
3. Report coverage delta
4. Flag any flaky tests

---

### Step 4: Synthesize

Combine all findings into a single report:

```
## Audit Report
- Spec: SPEC-{timestamp} ({goal_slug})
- Branch: {current branch}

### Change Scope
- Scopes detected: [API, Frontend, Backend, Database, Infra, Docs, Tests]
- Scope-specific checks: [list what ran]

### Code Quality: [PASS/WARN/FAIL]
### Security: [PASS/WARN/FAIL]
### Performance: [PASS/WARN/FAIL]
### Tests: [X/Y passing, Z% coverage]

### Spec Coverage
- R1: ✅/❌ addressed in diff
- R2: ✅/❌ addressed in diff
- AC1: ✅/❌ verified by test
- AC2: ✅/❌ verified by test

### Action Items
1. [blocker or warning]
```

### Step 5: Act

- **All PASS + all AC verified**: **"Audit passed. Run `/ship` to create a PR."**
- **WARN**: Show warnings, ask if user wants to fix before shipping
- **FAIL or AC missing**: List each blocker with a one-line fix hint. **"Fix with `/go`, then re-run `/audit`."**

## Anti-Rationalization

| Excuse | Rebuttal | What to do instead |
|--------|----------|-------------------|
| "It's a small change, skip security" | Small changes introduce big vulnerabilities | Always run the security checklist |
| "Tests are passing, that's enough" | Tests don't catch security or performance issues | Run all 3 modes |
| "I'll fix the warnings later" | Later never comes | Fix blockers now, warnings before merge |

## Evidence Required

- [ ] All 3 modes (code, security, test) completed
- [ ] Each Requirement has a coverage verdict
- [ ] Each AC has a test/verification verdict
- [ ] No BLOCKER items remain on PASS

## Red Flags

- Skipping security review for "small changes"
- Approving code with failing tests
- Ignoring performance warnings in hot paths
- Marking audit PASS when any AC is unverified
