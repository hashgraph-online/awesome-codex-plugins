# Vibe Pattern Reference

Comprehensive pattern catalog for Talos validation.

## Pattern Categories

| Category | Prefix | Phase | Description |
|----------|--------|-------|-------------|
| Prescan | P1-P10 | Static | Fast, no LLM required |
| Quality | QUAL-xxx | Semantic | Code smells, patterns |
| Security | SEC-xxx | Semantic | OWASP, injection, auth |
| Architecture | ARCH-xxx | Semantic | Boundaries, coupling |
| Accessibility | A11Y-xxx | Semantic | WCAG, keyboard |
| Complexity | CMPLX-xxx | Both | Cyclomatic, cognitive |
| Semantic | SEM-xxx | Semantic | Names, docstrings |
| Performance | PERF-xxx | Semantic | N+1, leaks |
| Slop | SLOP-xxx | Semantic | AI artifacts |

---

## Prescan Patterns (Static Detection)

Fast static analysis - no LLM required.

**Supported Languages:** Python, Go, Bash, TypeScript, JavaScript

### P1: Phantom Modifications (CRITICAL)

**What**: Committed lines that don't exist in current file.

**Why Critical**: Indicates broken git workflow - changes were committed but then removed or lost.

**Detection**: Compare `git show HEAD -- <file>` with actual file content.

**Fix**: Re-commit or investigate git history.

---

### P2: Hardcoded Secrets (CRITICAL)

**What**: API keys, passwords, tokens in source code.

**Why Critical**: Credential exposure leads to immediate compromise.

**Detection**:
- gitleaks scan
- Regex for common patterns (AWS keys, JWT, password=)

**Patterns**:
```regex
(password|secret|api_key|token)\s*[=:]\s*["'][^"']{8,}["']
AKIA[0-9A-Z]{16}
eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+
```

**Fix**: Use environment variables or secrets manager.

---

### P3: SQL Injection Patterns (CRITICAL)

**What**: String concatenation in SQL queries.

**Why Critical**: Direct path to data breach.

**Detection**:
```regex
(execute|query)\s*\(\s*f?["'].*\{.*\}
cursor\.(execute|query)\s*\([^)]*%
```

**Fix**: Use parameterized queries.

---

### P4: TODO/FIXME/Commented Code (HIGH)

**What**: TODO markers, FIXME, commented-out code blocks.

**Why High**: Incomplete work or tech debt markers.

**Detection**:
```bash
grep -E "TODO|FIXME|XXX|HACK|BUG"
grep -E "^\s*#\s*(def |class |if |for |while )"  # Commented code
```

**Fix**: Complete or remove with explanation.

---

### P5: Cyclomatic Complexity (HIGH)

**What**: Functions with CC > 15.

**Why High**: Too complex to maintain safely.

**Detection by Language**:

| Language | Tool | Command |
|----------|------|---------|
| Python | radon | `radon cc <file> -s -n E` |
| Go | gocyclo | `gocyclo -over 15 <file>` |
| TypeScript | escomplex | `escomplex <file>` |

**Thresholds**:
- CC > 10: Warning
- CC > 15: Flag as complex
- CC > 20: Critical

**Fix**: Extract functions, simplify logic.

---

### P6: Long Functions (HIGH)

**What**: Functions exceeding 50 lines.

**Why High**: Long functions are hard to test and maintain.

**Detection**: AST parsing, line counting.

**Thresholds**:
- Lines > 30: Warning
- Lines > 50: Flag
- Lines > 100: Critical

**Fix**: Extract helper functions.

---

### P7: Cargo Cult Error Handling (HIGH)

**What**: Empty except blocks, pass-only handlers, bare except.

**Why High**: Swallowed errors hide bugs.

**Detection by Language**:

| Language | Pattern |
|----------|---------|
| Python | `except: pass`, `except Exception: pass` |
| Go | `if err != nil { }` (empty block) |
| Bash | shellcheck SC2181 |

**Fix**: Handle or propagate errors explicitly.

---

### P8: Unused Imports/Functions (MEDIUM)

**What**: Imported modules or defined functions never used.

**Why Medium**: Dead code clutters codebase.

**Detection**: AST analysis, import tracking.

**Fix**: Remove unused code.

---

### P9: Docstring Mismatches (MEDIUM)

**What**: Docstrings claiming behavior not implemented.

**Why Medium**: False security from lying documentation.

**Detection**: Match docstring claims vs implementation:
- "validates" but no raise/ValueError
- "encrypts" but no crypto imports
- "authenticates" but no token handling

**Fix**: Update docs or implement claimed behavior.

---

### P10: Missing Error Handling (MEDIUM)

**What**: Operations that can fail without error handling.

**Why Medium**: Silent failures cause hard-to-debug issues.

**Detection**:
- File operations without try/except
- Network calls without timeout/retry
- Parsing without validation

**Fix**: Add appropriate error handling.

---

## Semantic Patterns (LLM-Powered)

Deep analysis requiring semantic understanding.

### Quality (QUAL-xxx)

| Code | Pattern | Severity |
|------|---------|----------|
| QUAL-001 | Dead code paths | MEDIUM |
| QUAL-002 | Inconsistent naming | MEDIUM |
| QUAL-003 | Magic numbers/strings | MEDIUM |
| QUAL-004 | Missing tests for complex code | HIGH |
| QUAL-005 | Copy-paste with variations | HIGH |
| QUAL-006 | Feature envy (method uses another class more) | MEDIUM |
| QUAL-007 | Primitive obsession | LOW |
| QUAL-008 | Long parameter lists | MEDIUM |

---

### Security (SEC-xxx)

| Code | Pattern | Severity |
|------|---------|----------|
| SEC-001 | Injection (SQL, command, XSS, template) | CRITICAL |
| SEC-002 | Authentication bypass | CRITICAL |
| SEC-003 | Authorization missing/weak | CRITICAL |
| SEC-004 | Cryptographic weakness | HIGH |
| SEC-005 | Sensitive data exposure | HIGH |
| SEC-006 | Security theater (looks secure, isn't) | HIGH |
| SEC-007 | Insecure deserialization | HIGH |
| SEC-008 | SSRF/path traversal | HIGH |
| SEC-009 | Race conditions | MEDIUM |
| SEC-010 | Debug mode in production | MEDIUM |

---

### Architecture (ARCH-xxx)

| Code | Pattern | Severity |
|------|---------|----------|
| ARCH-001 | Layer boundary violation | HIGH |
| ARCH-002 | Circular dependency | HIGH |
| ARCH-003 | God class/function | HIGH |
| ARCH-004 | Missing abstraction | MEDIUM |
| ARCH-005 | Inappropriate coupling | MEDIUM |
| ARCH-006 | Scalability concern | MEDIUM |
| ARCH-007 | Single point of failure | HIGH |
| ARCH-008 | Hardcoded configuration | MEDIUM |
| ARCH-009 | Missing retry/circuit breaker | MEDIUM |
| ARCH-010 | Synchronous where async needed | MEDIUM |

---

### Accessibility (A11Y-xxx)

| Code | Pattern | Severity |
|------|---------|----------|
| A11Y-001 | Missing ARIA labels | HIGH |
| A11Y-002 | Keyboard navigation broken | CRITICAL |
| A11Y-003 | Color contrast insufficient | HIGH |
| A11Y-004 | Missing alt text | HIGH |
| A11Y-005 | Focus management issues | HIGH |
| A11Y-006 | Missing skip links | MEDIUM |
| A11Y-007 | Form labels missing | HIGH |
| A11Y-008 | Dynamic content not announced | MEDIUM |
| A11Y-009 | Touch target too small | MEDIUM |
| A11Y-010 | Motion without reduced-motion support | LOW |

---

### Complexity (CMPLX-xxx)

| Code | Pattern | Severity | Threshold |
|------|---------|----------|-----------|
| CMPLX-001 | Cyclomatic complexity | HIGH | CC > 10 |
| CMPLX-002 | Cognitive complexity | HIGH | > 15 |
| CMPLX-003 | Nesting depth | MEDIUM | > 4 |
| CMPLX-004 | Parameter count | MEDIUM | > 5 |
| CMPLX-005 | File too long | MEDIUM | > 500 lines |
| CMPLX-006 | Class too large | MEDIUM | > 20 methods |
| CMPLX-007 | Inheritance depth | LOW | > 3 |
| CMPLX-008 | Fan-out too high | MEDIUM | > 10 dependencies |

---

### Semantic (SEM-xxx)

| Code | Pattern | Severity |
|------|---------|----------|
| SEM-001 | Docstring lies | HIGH |
| SEM-002 | Misleading function name | HIGH |
| SEM-003 | Misleading variable name | MEDIUM |
| SEM-004 | Comment rot | MEDIUM |
| SEM-005 | API contract violation | HIGH |
| SEM-006 | Type annotation mismatch | MEDIUM |
| SEM-007 | Inconsistent return types | MEDIUM |
| SEM-008 | Side effects in getter | HIGH |

---

### Performance (PERF-xxx)

| Code | Pattern | Severity |
|------|---------|----------|
| PERF-001 | N+1 query | HIGH |
| PERF-002 | Unbounded loop/recursion | CRITICAL |
| PERF-003 | Missing pagination | HIGH |
| PERF-004 | Resource leak | HIGH |
| PERF-005 | Blocking in async context | HIGH |
| PERF-006 | Inefficient algorithm | MEDIUM |
| PERF-007 | Repeated computation | MEDIUM |
| PERF-008 | Missing caching | LOW |
| PERF-009 | Large object in memory | MEDIUM |
| PERF-010 | Excessive logging | LOW |

---

### Slop (SLOP-xxx)

| Code | Pattern | Severity |
|------|---------|----------|
| SLOP-001 | Hallucinated imports/APIs | CRITICAL |
| SLOP-002 | Cargo cult patterns | HIGH |
| SLOP-003 | Excessive boilerplate | MEDIUM |
| SLOP-004 | AI conversation artifacts | HIGH |
| SLOP-005 | Over-engineering | MEDIUM |
| SLOP-006 | Unnecessary abstractions | MEDIUM |
| SLOP-007 | Copy-paste from tutorials | MEDIUM |
| SLOP-008 | Sycophantic comments | LOW |
| SLOP-009 | Redundant type annotations | LOW |
| SLOP-010 | Verbose where concise works | LOW |

---

## Severity Mapping

| Level | Definition | Action | Exit Code |
|-------|------------|--------|-----------|
| **CRITICAL** | Security vuln, data loss, broken build | Block merge | 2 |
| **HIGH** | Significant quality/security gap | Fix before merge | 3 |
| **MEDIUM** | Technical debt, minor issues | Follow-up issue | 0 |
| **LOW** | Nitpicks, style preferences | Optional | 0 |

---

## Tool Requirements

| Tool | Languages | Install |
|------|-----------|---------|
| radon | Python | `pip install radon` |
| gocyclo | Go | `go install github.com/fzipp/gocyclo/cmd/gocyclo@latest` |
| shellcheck | Bash | `brew install shellcheck` |
| gitleaks | All | `brew install gitleaks` |
| eslint | JS/TS | `npm install eslint` |
