---
name: review
description: "Run review."
---

# Review Skill

> **Quick Ref:** `$review <PR>` reviews a PR, `$review --diff` reviews local changes, `$review --agent <path>` reviews agent output with extra scrutiny.

**YOU MUST EXECUTE THIS WORKFLOW. Do not just describe it.**

This skill is for reviewing OTHER people's or agents' changes. For validating your own code quality, use `$validate` instead.

---

## Modes

```bash
$review 42                          # PR mode — review PR #42
$review https://github.com/o/r/pull/42  # PR mode — review by URL
$review --diff                      # Diff mode — review unstaged/staged changes
$review --diff --staged             # Diff mode — staged only
$review --agent .agents/crank/      # Agent mode — review agent-generated output
$review --agent ./output.patch      # Agent mode — review a patch file
$review --deep 42                   # Deep mode — spawns council for second opinion
$review --mocks                     # Find stubs, mocks, placeholders, TODOs
$review --bugs                      # Bug scanner: null derefs, leaks, security holes
$review --audit security            # Domain audit: security, perf, UX, API, CLI
$review --deep-scan                 # Iterative audit-fix-rescan until clean
```

---

## Execution Steps

### Step 0: Detect Review Target and Load Standards

Determine the review mode from arguments:

1. **PR mode** (default): argument is a number or GitHub PR URL.
2. **Diff mode**: `--diff` flag present.
3. **Agent mode**: `--agent <path>` flag present.

Load language-specific conventions from `$standards` based on file extensions in the diff. If `ao` is available, pull prior review context:

```bash
ao lookup --query "code review patterns $(basename "$PWD")" --limit 3 2>/dev/null || true
```

**Apply retrieved knowledge (mandatory when results returned):**

If learnings are returned, do NOT just load them as passive context. For each returned item:
1. Check: does this learning apply to the code under review? (answer yes/no)
2. If yes: include it as a `known_risk` — state the pattern, what to look for, and whether the diff exhibits it
3. Cite the learning by filename in your review output when it influences a finding

After applying, record the citation:
```bash
ao metrics cite "<learning-path>" --type applied 2>/dev/null || true
```

Skip silently if ao is unavailable or returns no results.

### Step 0.5: Apply Behavioral Discipline

Load the behavioral discipline standard from `$standards` before reviewing the diff. Use it to answer four questions:

1. What assumptions does this change make, and were they surfaced or silently chosen?
2. Could the same outcome be achieved with a smaller or more local change?
3. Does every changed line trace back to the stated goal?
4. Does the verification prove the claimed behavior, or only that the code builds?

If any answer is weak, record the problem as a finding. Hidden assumptions, speculative abstractions, drive-by edits, and weak verification are review defects, not style preferences.

---

### Step 1: Fetch the Diff

#### PR Mode

```bash
gh pr view "$PR_REF" --json title,body,author,baseRefName,headRefName,labels,reviewDecision,commits
gh pr diff "$PR_REF"
gh pr diff "$PR_REF" --name-only
```

If the PR has more than 500 changed lines, prioritize: security-sensitive files, high-complexity changes, new files, then test files.

#### Diff Mode

```bash
git diff HEAD                  # unstaged + staged
git diff --cached              # staged only (with --staged flag)
git diff HEAD --name-only      # changed file list
```

#### Agent Mode

```bash
# Directory: find all generated files
find "$AGENT_PATH" -type f \( -name '*.go' -o -name '*.py' -o -name '*.ts' -o -name '*.sh' -o -name '*.md' \)
# Patch file: inspect stats
git apply --stat "$AGENT_PATH"
```

---

### Step 2: Context Gathering

Understand the intent behind the changes before reviewing the code:

- **PR Mode:** Read PR title/body, check linked issues (`fixes #`, `closes #`), read commit messages.
- **Diff Mode:** Check `git log --oneline -5`, branch name, open issues via `br list --status open`.
- **Agent Mode:** Read execution logs in output directory, check `.agents/rpi/` artifacts.

**Output a one-line intent summary before proceeding:**

```
INTENT: <what the change is trying to accomplish>
```

If intent is unclear, flag it: "PR description does not explain the purpose of this change."

---

### Step 3: Systematic Review Pass (SCORED)

Review every changed file against the SCORED checklist. For each category, actively look for problems. Do not skim -- read each changed line.

#### S -- Security

- [ ] No hardcoded secrets, API keys, tokens, or passwords
- [ ] Input validation on all external data (user input, API responses, file reads)
- [ ] SQL/command injection: parameterized queries, no string interpolation in commands
- [ ] Auth/authz checks present where needed (not just authn)
- [ ] Sensitive data not logged or exposed in error messages
- [ ] Dependencies: no known-vulnerable versions added
- [ ] File operations: path traversal prevention, safe temp file handling

For audit-style reviews, generated-code suspicion, mock leakage, or external-review-tool findings, load [references/audit-and-mock-sweeps.md](references/audit-and-mock-sweeps.md) before writing final findings.

#### C -- Correctness

- [ ] Logic errors: off-by-one, wrong operator, inverted condition
- [ ] Edge cases: nil/null handling, empty collections, boundary values
- [ ] Error handling: errors checked, not swallowed, wrapped with context
- [ ] Race conditions: shared mutable state, concurrent access patterns
- [ ] Resource leaks: unclosed files, connections, goroutines, channels
- [ ] Type safety: unchecked casts, implicit conversions, overflow potential
- [ ] Contract compliance: does the change match the stated intent?

#### O -- Observability

- [ ] Errors include enough context for debugging (what failed, with what input)
- [ ] New features have appropriate logging at correct levels
- [ ] Metrics or health indicators added for new failure modes
- [ ] Error messages are actionable (not just "something went wrong")

#### R -- Readability

- [ ] Names are descriptive and consistent with codebase conventions
- [ ] Functions are focused (single responsibility, not doing too much)
- [ ] Complex logic has comments explaining WHY (not WHAT)
- [ ] No dead code, commented-out code, or leftover debug statements
- [ ] Consistent formatting with the rest of the codebase

#### E -- Efficiency

- [ ] No unnecessary allocations in hot paths
- [ ] N+1 query patterns (database calls in loops)
- [ ] Unbounded growth: maps/slices that grow without limits
- [ ] Appropriate use of caching, batching, or pagination
- [ ] No blocking operations in async/concurrent contexts

#### D -- Design

- [ ] Abstraction level is appropriate (not over-engineered, not under-abstracted)
- [ ] API surface is minimal and consistent with existing patterns
- [ ] Changes are cohesive (single concern per PR, not mixing refactoring with features)
- [ ] Ambiguity was surfaced instead of silently assumed away
- [ ] No speculative flexibility or abstractions beyond the stated need
- [ ] Every changed line traces to the requested outcome or required cleanup
- [ ] Dependencies flow in the right direction (no circular imports)
- [ ] Test coverage: new code has tests, tests verify behavior (not just coverage)
- [ ] Breaking changes are documented and intentional

---

### Step 4: Agent-Specific Checks (--agent mode only)

When reviewing agent-generated code, apply additional scrutiny for common agent failure modes:

#### Hallucinated References
- [ ] All imports exist (no invented packages or modules)
- [ ] All called functions exist in the codebase or dependencies
- [ ] Referenced files and paths actually exist
- [ ] API endpoints and URLs are real

#### Over-Engineering
- [ ] No unnecessary abstractions (interfaces with one implementation, factory for one type)
- [ ] No premature generalization (generic solution where specific was asked)
- [ ] No gold-plating (features not requested)
- [ ] Reasonable LOC for the task complexity

#### Missing Fundamentals
- [ ] Error handling is present (agents frequently skip error paths)
- [ ] Edge cases are handled (agents often only handle the happy path)
- [ ] Cleanup/teardown logic exists (defer, finally, context cancellation)
- [ ] Concurrency safety if applicable

#### Test Quality
- [ ] Tests actually assert meaningful behavior (not just `!= nil` or `!= ""`)
- [ ] Test names describe the scenario being tested
- [ ] Tests cover error paths, not just happy paths
- [ ] No `cov*_test.go` naming pattern (coverage-padding anti-pattern)
- [ ] Mocks are realistic (not returning hardcoded success for everything)

#### Codebase Consistency
- [ ] Follows existing naming conventions (check 3+ similar files for patterns)
- [ ] Uses existing helpers/utilities instead of reimplementing
- [ ] Error handling style matches the codebase
- [ ] File organization follows project structure

---

### Step 5: Generate Structured Review Output

Create a review artifact:

```bash
REVIEW_DIR=".agents/review"
mkdir -p "$REVIEW_DIR"
REVIEW_FILE="$REVIEW_DIR/$(date +%Y-%m-%d)-review-$(echo "$PR_REF" | tr '/' '-').md"
```

#### Review Document Structure

```markdown
# Review: <PR title or change description>
**Date:** YYYY-MM-DD  |  **Verdict:** APPROVE | REQUEST_CHANGES | COMMENT
**Target:** PR #N / local diff / agent output at <path>

## Intent
<one-line summary>

## SCORED Assessment
| Category | Rating | Notes |
|----------|--------|-------|
| Security | pass/warn/fail | ... |
| Correctness | pass/warn/fail | ... |
| Observability | pass/warn/fail | ... |
| Readability | pass/warn/fail | ... |
| Efficiency | pass/warn/fail | ... |
| Design | pass/warn/fail | ... |

## Findings
### Critical (must fix)
- **[file:line]** Issue. Suggested fix: ...
### Warning (should fix)
- **[file:line]** Issue. Suggested fix: ...
### Suggestion / Nit
- **[file:line]** Description.

## Missing
<expected but absent: tests, docs, error handling, migration>
```

#### Verdict Rules

- **APPROVE**: No critical or warning findings. All SCORED categories pass.
- **REQUEST_CHANGES**: Any critical finding, OR 3+ warnings, OR any SCORED category rated "fail".
- **COMMENT**: 1-2 warnings with no critical findings. Worth discussing but not blocking.

#### PR Mode: Post Comments

If reviewing a PR and the verdict is REQUEST_CHANGES or COMMENT, offer to post the review:

```bash
# Post review comment on the PR
gh pr review "$PR_REF" --comment --body "$(cat "$REVIEW_FILE")"

# Or for blocking review
gh pr review "$PR_REF" --request-changes --body "$(cat "$REVIEW_FILE")"
```

Only post if the user confirms. Never auto-post a review without explicit approval.

---

## Deep Mode (--deep)

When `--deep` is specified, after the initial SCORED pass, spawn a council for a second opinion:

```bash
$council validate "Review these changes for issues I might have missed: <summary of changes>"
```

Merge council findings into the review document under a "## Council Findings" section.

---

## Integration with Other Skills

| Skill | Relationship |
|-------|-------------|
| `$validate` | Self-review (your own code). `$review` is for others' code. |
| `$council` | Optional second opinion via `--deep` flag. |
| `$standards` | Auto-loaded for language-specific rules. |
| `bug-hunt` | `$review` does a structured pass; `bug-hunt` does deep investigation of suspected bugs. |
| `$validate --mode=pr` | PR-specific validation (isolation, scope creep). Complementary to `$review`. |

---

## Reference Documents

- [references/MOCK_FINDER.md](references/MOCK_FINDER.md) — Find stubs, mocks, placeholders, TODOs
- [references/BUG_SCANNER.md](references/BUG_SCANNER.md) — Bug scanner: null derefs, leaks, security
- [references/DOMAIN_AUDIT.md](references/DOMAIN_AUDIT.md) — Domain-parameterized audit (security, perf, UX, API, CLI)
- [references/DEEP_SCAN.md](references/DEEP_SCAN.md) — Iterative audit-fix-rescan cycle

## See Also

- [validate](../validate/SKILL.md) — Self-review and code quality validation (absorbs vibe)
- [council](../council/SKILL.md) — Multi-model consensus council
- [standards](../standards/SKILL.md) — Language-specific coding conventions
- bug-hunt — Deep bug investigation (absorbed into this skill)
- [validate --mode=pr](../validate/SKILL.md) — PR scope and isolation checks
- [references/audit-and-mock-sweeps.md](references/audit-and-mock-sweeps.md)
