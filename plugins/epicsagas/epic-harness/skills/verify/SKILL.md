---
name: verify
dimension: evaluation_and_reward
description: "Pre-merge verification gate. Build, test, and lint must all pass before marking done or shipping."
---

# Verify — Pre-Completion Check

## Iron Law

NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE. "I tested it" without output is an unverified claim.

## When to Trigger
- Before a `/go` subagent reports "done"
- Before `/ship` creates a PR
- Before telling the user "it's ready"
- After any significant code change

## Process

### 1. Build
```bash
# Detect and run the project's build command
npm run build  # or: go build ./... | cargo build | make
```
Must exit 0. If it fails, fix before proceeding.

### 2. Test
```bash
# Run the project's test suite
npm test  # or: go test ./... | pytest | cargo test
```
Must exit 0. If tests fail, invoke `debug` skill.

### 3. Lint
```bash
# Run linter if configured
npm run lint  # or: golangci-lint run | ruff check | cargo clippy
```
Warnings are OK. Errors must be fixed.

### 4. Type Check (if applicable)
```bash
npx tsc --noEmit  # TypeScript
mypy .            # Python
```

### 5. Final Sanity
- [ ] No `console.log` / `print` debug statements left
- [ ] No `TODO` or `FIXME` introduced without explanation
- [ ] No hardcoded test values or credentials
- [ ] All new files are tracked by git

## Anti-Rationalization

| Excuse | Rebuttal | What to do instead |
|--------|----------|-------------------|
| "Tests pass locally" | Did you actually run them? Trust the output, not your memory. | Run `npm test` right now. Show the output. |
| "I only changed one file" | One file can break the entire build. Imports propagate. | Full build + test. Every time. No exceptions. |
| "Lint warnings aren't errors" | Warnings become errors. Fix them before they multiply. | Zero warnings policy. Fix now or suppress with justification. |
| "CI will catch it" | CI feedback is 5-10 min delayed. Catch it locally in seconds. | Run verify locally before pushing. CI is the safety net, not the test. |

## Evidence Required

Before reporting "ready", show ALL of these:

- [ ] Build output: exit code 0 (show the command + result)
- [ ] Test output: all passing (show summary line)
- [ ] Lint output: zero errors (show summary or "clean")
- [ ] Type check output: no errors (show `tsc --noEmit` or equivalent)
- [ ] Final sanity: no console.log, no unexplained TODO, no hardcoded values

**Each check needs actual command output. "I ran it" without output = not verified.**

## Red Flags
- Reporting success without showing actual command output
- Skipping type check "because JavaScript is dynamic"
- Committing with TODO/FIXME and no explanation
