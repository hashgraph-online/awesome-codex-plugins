---
name: audit
description: "Audit phase. Parallel review: code quality + security + tests. Semantic dedup of cross-mode findings. Outputs PASS/WARN/FAIL per dimension. Validates spec coverage."
---

# Audit — Verify Everything

**CRITICAL**: Run `HARNESS_DIR=$(epic path)` first. NEVER use `.harness/` in the project directory.

## Execution Modes

This skill has 3 internal modes that run in parallel:

1. **audit:code** — Code quality, logic, style, test coverage, spec coverage
2. **audit:security** — OWASP Top 10 + performance (N+1, leaks)
3. **audit:test** — Full test suite, AC verification, coverage delta

### `--strict` Mode (Trust Boundary Isolation)

When invoked with `--strict` (or when `.harness/engagement.md` has `mode: strict`), the audit enforces independence between verification agents to prevent reward hacking:

- **Artifact-only delivery**: Each mode receives only the code diff and spec — no builder context, no session history, no prior agent conclusions.
- **Cross-check independence**: `audit:code` and `audit:security` run without visibility into each other's findings. Results are combined only during synthesis (Step 4).
- **Blind scoring**: No mode can see another mode's verdict until synthesis. This prevents anchoring bias where a clean code review inflates the security score.
- **No self-review**: If the same agent built the code (via `/go`), a different agent instance must run audit. The builder's session ID is checked and excluded.

Use `--strict` for security-sensitive projects, compliance requirements, or when the build phase had ambiguous outcomes.

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

**`--strict` isolation protocol**: When strict mode is active, each mode agent must be launched with:
- Only the diff output from Step 1 as input (no session context)
- No access to other modes' intermediate or final results
- A fresh context window containing only: spec, diff, and the mode-specific checklist

This ensures each mode forms independent conclusions. Results are combined only in Step 4 synthesis.

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

### Step 3.5: Semantic Deduplication

After all 3 modes complete, merge their findings and deduplicate:

**Collection**: Gather all findings from code, security, and test modes into a single pool.

**Root-Cause Grouping**: For each finding, identify the root cause. Findings sharing the same root cause (same file, same function, same underlying pattern) form a group.

**Classification** (per group):

| Classification | Meaning | Action |
|---------------|---------|--------|
| `NEW` | First finding for this root cause | Include in report |
| `DUP_BETTER` | Duplicate with better evidence or higher severity | Replace original with this |
| `DUP_SKIP` | Duplicate with weaker or equal evidence | Drop; reference the `NEW` finding |

**Severity Reassessment**: The surviving finding in each group takes the highest severity across all modes. For example, if code review says `[WARN]` but security says `[CRITICAL]` for the same root cause, the deduped finding is `[CRITICAL]`.

**Output**: Only deduplicated findings proceed to Step 4 synthesis. The report should note: "N findings deduplicated from M total (K groups collapsed)."

---

### Step 4: Synthesize

Combine deduplicated findings into a single report:

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

### Deduplication
- Total findings: M
- Deduplicated: N (K groups collapsed)

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
| "Dedup is overkill for small audits" | Small audits can still have cross-mode overlap | Always dedup — the cost is trivial |
| "Strict mode is overkill" | Without isolation, the builder can influence reviewers via shared context | Use `--strict` for security-sensitive or compliance-driven projects |
| "The agents are independent enough" | Shared context creates anchoring bias — a clean code review inflates security scores | Strict mode ensures blind scoring until synthesis |

## Evidence Required

- [ ] All 3 modes (code, security, test) completed
- [ ] Each Requirement has a coverage verdict
- [ ] Each AC has a test/verification verdict
- [ ] No BLOCKER items remain on PASS
- [ ] Deduplication applied: total vs. deduplicated count reported

## Red Flags

- Skipping security review for "small changes"
- Approving code with failing tests
- Ignoring performance warnings in hot paths
- Marking audit PASS when any AC is unverified
- Reporting raw findings without deduplication
