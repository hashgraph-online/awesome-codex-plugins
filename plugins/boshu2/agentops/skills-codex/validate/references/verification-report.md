# Structured Verification Report Format

> Inspired by verification-loop patterns. Use with `/vibe --structured` or as pre-PR gate.

## When to Use

- Before any PR submission
- After `/crank` wave completion
- As `/post-mortem` pre-check
- When `--structured` flag is passed to `/vibe`

## Report Template

```
VERIFICATION REPORT — <target>
Date: <YYYY-MM-DD>
Scope: <files or directories reviewed>

Build:     [PASS/FAIL] <details>
Types:     [PASS/FAIL] (<N> errors)
Lint:      [PASS/FAIL] (<N> warnings)
Tests:     [PASS/FAIL] (<N>/<M> passed, <Z>% coverage)
Security:  [PASS/FAIL] (<N> issues)
Diff:      [<N> files changed, +<A>/-<R> lines]

Overall:   [READY/NOT READY] for PR

Issues to Fix:
1. <severity> — <file:line> — <description>
2. ...

Recommendations:
- ...
```

## Phase Execution

### Phase 1: Build Gate (fail-fast)
```bash
# Go
cd cli && go build ./...

# Python
python -m py_compile <changed-files>

# Node
npm run build 2>&1 | tail -20
```
If build fails, STOP. Report failure. Do not proceed.

### Phase 2: Type Check
```bash
# Go
go vet ./...

# Python
mypy <changed-files> --ignore-missing-imports

# TypeScript
npx tsc --noEmit
```

### Phase 3: Lint
```bash
# Go
golangci-lint run ./...

# Python
ruff check <changed-files>

# Shell
shellcheck <changed-scripts>
```

### Phase 4: Tests
```bash
# Go
go test ./... -count=1

# Python
pytest <test-files> -v --tb=short
```
Report coverage if available.

### Phase 5: Security Scan
```bash
# Secrets in changed files
grep -rn 'password\|secret\|api_key\|token' <changed-files> | grep -v test | grep -v '_test'

# Hardcoded values
grep -rn 'http://\|localhost:\|127.0.0.1' <changed-files> | grep -v test

# Console/debug statements
grep -rn 'console\.log\|print(\|fmt\.Print' <changed-files> | grep -v test
```

### Phase 6: Diff Review
```bash
git diff --stat HEAD~1
git diff HEAD~1 -- <changed-files>
```
Review for: unintended changes, leftover debug code, TODO comments, missing error handling.

## Severity Classification

| Severity | Definition | Action |
|----------|-----------|--------|
| CRITICAL | Build breaks, security vuln, data loss risk | Must fix before merge |
| HIGH | Test failure, type error, missing validation | Should fix before merge |
| MEDIUM | Lint warning, missing docs, style violation | Fix or document exception |
| LOW | Suggestion, minor improvement | Optional |

## Integration Points

- `/vibe --structured` triggers this report format
- `/crank` Step 7 can use this as wave-end gate
- `/post-mortem` uses this as pre-check before council
- `/pr-prep` includes this in PR body
