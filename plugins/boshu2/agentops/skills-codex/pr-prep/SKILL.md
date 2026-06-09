---
name: pr-prep
description: "Run pr prep."
---
# PR Preparation Skill

Systematic PR preparation that validates tests and generates high-quality PR bodies.

## Overview

Prepares contributions by analyzing the target repo's conventions, git history,
test coverage, and generating properly-formatted PR bodies.

**When to Use**:
- Preparing a PR for an external repository
- Contributing bug fixes or features

**When NOT to Use**:
- Internal commits (use normal git workflow)
- PRs to your own repositories

---

## Workflow

```
-1. Prior Work Check     -> BLOCKING: Final check for competing PRs
0.  Isolation Check      -> BLOCK if PR mixes unrelated changes
1.  Context Discovery    -> Understand target repo conventions
2.  Git Archaeology      -> Analyze commit patterns, PR history
3.  Pre-Flight Checks    -> Run tests, linting, build
4.  Change Analysis      -> Summarize what changed and why
4.5 Commit Split Advisor -> Suggest logical commit groups (manual)
5.  PR Body Generation   -> Create structured PR description
6.  USER REVIEW GATE     -> STOP. User must approve before submission.
7.  Submission           -> Only after explicit user approval
```

---

## Phase 0: Isolation Check (BLOCKING)

**CRITICAL**: Run this FIRST. Do not proceed if PR mixes unrelated changes.

### Commit Type Analysis

```bash
# Extract commit type prefixes from branch
git log --oneline main..HEAD | sed 's/^[^ ]* //' | grep -oE '^[a-z]+(\([^)]+\))?:' | sort -u
```

**Rule**: If more than one commit type prefix exists, the PR is mixing concerns.

### File Theme Analysis

```bash
# List all files changed vs main
git diff --name-only main..HEAD

# Group by directory
git diff --name-only main..HEAD | cut -d'/' -f1-2 | sort -u
```

### Isolation Checklist

| Check | Pass Criteria |
|-------|---------------|
| **Single commit type** | All commits share same prefix |
| **Thematic files** | All changed files relate to PR scope |
| **No main overlap** | Changes not already merged |
| **Atomic scope** | Can explain in one sentence |

**DO NOT PROCEED IF ISOLATION CHECK FAILS.**

---

## CRITICAL: User Review Gate

**NEVER submit a PR without explicit user approval.**

After generating the PR body (Phase 5), ALWAYS:

1. Write the PR body to a file for review
2. Show the user what will be submitted
3. **STOP and ask**: "Ready to submit? Review the PR body above."
4. Wait for explicit approval before running `gh pr create`

```bash
# Write PR body to file
cat > /tmp/pr-body.md << 'EOF'
<generated PR body>
EOF

# Show user
cat /tmp/pr-body.md

# ASK - do not proceed without answer
echo "Review complete. Submit this PR? [y/N]"
```

---

## Phase 3: Pre-Flight Checks

```bash
# Go projects
go build ./...
go vet ./...
go test ./... -v -count=1

# Node projects
npm run build
npm test

# Python projects
pytest -v
```

### Pre-Flight Checklist

- [ ] Code compiles without errors
- [ ] All tests pass
- [ ] No new linting warnings
- [ ] No secrets or credentials in code

---

## Phase 4.5: Commit Split Analysis (Suggestion-Only)

Analyze the branch diff and suggest logical commit groupings.

```bash
# Review the scope of changes
git diff --stat main..HEAD
```

**Output a numbered list** of suggested commits with file groups:

```
Commit 1: [description] -- files: path/a.go, path/a_test.go
Commit 2: [description] -- files: path/b.go, path/c.go
```

**Ordering**: Infrastructure/migrations > Models/services > Controllers/views > Tests > VERSION/CHANGELOG.
Each commit must be independently valid (no broken imports).
If diff is < 50 lines across < 4 files, recommend a single commit.

See [references/commit-split-advisor.md](references/commit-split-advisor.md) for full rules.

> **These are suggestions only. User reads and implements manually.**

---

## Phase 5: PR Body Generation

### Standard Format

```markdown
## Summary

Brief description of WHAT changed and WHY. 1-3 sentences.
Start with action verb (Add, Fix, Update, Refactor).

## Changes

Technical details of what was modified.

## Test plan

- [x] `go build ./...` passes
- [x] `go test ./...` passes
- [x] Manual: <specific scenario tested>

Fixes #NNN
```

**Key conventions:**
- Test plan items are **checked** `[x]` (you ran them before PR)
- `Fixes #NNN` goes at the end

---

## Phase 7: Submission (After Approval Only)

```bash
# Create PR with reviewed body
gh pr create --title "type(scope): brief description" \
  --body "$(cat /tmp/pr-body.md)" \
  --base main
```

**Remember**: This command should ONLY run after user explicitly approves.

---

## Anti-Patterns

| DON'T | DO INSTEAD |
|-------|------------|
| **Submit without approval** | **ALWAYS stop for user review** |
| **Skip isolation check** | **Run Phase 0 FIRST** |
| Bundle lint fixes into feature PRs | Lint fixes get their own PR |
| Giant PRs | Split into logical chunks |
| Vague PR body | Detailed summary with context |
| Skip pre-flight | Always run tests locally |

## Examples

### Prepare External PR Body

**User says:** "Prepare this branch for PR submission."

**What happens:**
1. Run isolation and pre-flight validation.
2. Build structured PR body with summary and test plan.
3. Pause for mandatory user review before submit.

### Evidence-First PR Packaging

**User says:** "Generate a high-quality PR description with clear verification steps."

**What happens:**
1. Gather git archaeology and test evidence.
2. Synthesize concise rationale and change list.
3. Produce submit-ready body pending approval.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| PR body is weak | Missing context from commits/tests | Re-run evidence collection and expand summary |
| Submission blocked | Mandatory review gate not passed | Get explicit user approval before `gh pr create` |
| Test plan incomplete | Commands/results not captured | Add executed checks and outcomes explicitly |
| Title/body mismatch | Scope drift during edits | Regenerate from latest branch diff and constraints |

## Reference Documents

- [references/case-study-historical-context.md](references/case-study-historical-context.md)
- [references/lessons-learned.md](references/lessons-learned.md)
- [references/package-extraction.md](references/package-extraction.md)
- [references/commit-split-advisor.md](references/commit-split-advisor.md)

## Local Resources

### references/

- [references/case-study-historical-context.md](references/case-study-historical-context.md)
- [references/commit-split-advisor.md](references/commit-split-advisor.md)
- [references/lessons-learned.md](references/lessons-learned.md)
- [references/package-extraction.md](references/package-extraction.md)

### scripts/

- `scripts/validate.sh`


