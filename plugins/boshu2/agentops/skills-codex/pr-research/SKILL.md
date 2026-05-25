---
name: pr-research
description: 'Research an upstream repo.'
---
# PR Research Skill

Systematic exploration of upstream repositories before contributing.

## Overview

Research an external codebase to understand how to contribute effectively.
This is the FIRST step before planning or implementing an open source contribution.

**When to Use**:
- Before contributing to an external repository
- Starting a new open source contribution
- Evaluating whether to contribute to a project

**When NOT to Use**:
- Researching your own codebase (use `$research`)
- Already familiar with the project's guidelines

---

## Workflow

```
-1. Prior Work Check    -> BLOCKING: Check for existing issues/PRs
0.  CONTRIBUTING.md     -> MANDATORY: Find contribution guidelines
1.  Repository Setup    -> Clone/identify upstream repo
2.  Guidelines Analysis -> Templates, CODE_OF_CONDUCT
3.  PR Archaeology      -> Analyze merged PRs, commit patterns
4.  Maintainer Research -> Response patterns, review expectations
5.  Issue Discovery     -> Find contribution opportunities
6.  Output              -> Write research document
```

---

## Phase -1: Prior Work Check (BLOCKING)

**CRITICAL**: Before ANY research, check if someone is already working on this.

```bash
# Search for open issues on this topic
gh issue list -R <owner/repo> --state open --search "<topic keywords>" --limit 20

# Search for open PRs that might address this
gh pr list -R <owner/repo> --state open --search "<topic keywords>" --limit 20

# Check for recently merged PRs (might already be fixed)
gh pr list -R <owner/repo> --state merged --search "<topic keywords>" --limit 10
```

| Finding | Action |
|---------|--------|
| Open issue exists | Link to it, don't create duplicate |
| Open PR exists | Don't duplicate work |
| Recently merged PR | Verify fix, no work needed |
| No prior work found | Proceed to Phase 0 |

---

## Phase 0: CONTRIBUTING.md Discovery (BLOCKING)

**CRITICAL**: Do not proceed without finding contribution guidelines.

```bash
# Check all common locations
cat CONTRIBUTING.md 2>/dev/null
cat .github/CONTRIBUTING.md 2>/dev/null
cat docs/CONTRIBUTING.md 2>/dev/null

# Check README for contribution section
grep -i "contribut" README.md | head -10
```

### Extract Key Requirements

| Requirement | Where to Find |
|-------------|---------------|
| **Commit format** | "Commit messages" section |
| **PR process** | "Pull Requests" section |
| **Testing requirements** | "Testing" section |
| **Code style** | "Style" section |
| **CLA/DCO** | "Legal" or "License" section |

---

## Phase 3: PR Archaeology

**CRITICAL**: Understand what successful PRs look like.

```bash
# List recent merged PRs
gh pr list --state merged --limit 20

# Recent commit style
git log --oneline -30 | head -20

# Check for conventional commits
git log --oneline -30 | grep -E "^[a-f0-9]+ (feat|fix|docs|refactor|test|chore)(\(.*\))?:"
```

### PR Size Analysis

| Size | Files | Lines | Likelihood |
|------|-------|-------|------------|
| **Small** | 1-3 | <100 | High acceptance |
| **Medium** | 4-10 | 100-500 | Moderate |
| **Large** | 10+ | 500+ | Needs discussion first |

---

## Phase 5: Issue Discovery

```bash
# Find beginner-friendly issues
gh issue list --label "good first issue" --state open
gh issue list --label "help wanted" --state open

# Issues with no assignee
gh issue list --state open --json assignees,title,number | \
  jq -r '.[] | select(.assignees | length == 0) | "#\(.number): \(.title)"' | head -10
```

---

## Output

Write to `.agents/research/YYYY-MM-DD-pr-{repo-slug}.md`

```markdown
# PR Research: {repo-name}

## Executive Summary
{2-3 sentences: project health, contribution friendliness}

## Contribution Guidelines
| Document | Status | Key Requirements |
|----------|--------|------------------|
| CONTRIBUTING.md | Present/Missing | {summary} |
| PR Template | Present/Missing | {required sections} |

## PR Patterns
- **Average size**: X files, Y lines
- **Commit style**: {conventional/imperative/etc}
- **Review time**: ~X days

## Contribution Opportunities
| Issue | Type | Difficulty |
|-------|------|------------|
| #N | bug/feat | easy/medium |

## Next Steps
-> `$plan .agents/research/YYYY-MM-DD-pr-{repo}.md`
```

---

## Anti-Patterns

| DON'T | DO INSTEAD |
|-------|------------|
| Skip guidelines check | Always read CONTRIBUTING.md first |
| Ignore PR patterns | Study successful merged PRs |
| Start with large PRs | Begin with small, focused changes |

---

## Workflow Integration

```
$pr-research <repo> -> $plan <research> -> implement -> $pr-prep
```

## Examples

### Research Upstream Before Contributing

**User says:** "Do PR research for `owner/repo` before I propose a fix."

**What happens:**
1. Inspect contribution guidelines and governance files.
2. Analyze merged PR patterns and conventions.
3. Produce a research artifact with opportunities and risks.

### Scope Discovery

**User says:** "Find small starter contribution options in this repo."

**What happens:**
1. Scan issues/labels and prior merged work.
2. Classify candidates by difficulty and scope.
3. Recommend a smallest-safe starting contribution.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| No contribution guide found | Repo lacks standard files | Infer conventions from merged PR history and maintainers' comments |
| Too many possible issues | Scope not constrained | Filter by labels, component paths, and recent maintainer activity |
| Suggested work seems risky | Hidden dependency or broad blast radius | Downscope to narrower file/domain boundary and restate assumptions |
| Output is too generic | Insufficient repository evidence | Add concrete file/PR references and explicit pattern findings |

## Local Resources

### scripts/

- `scripts/validate.sh`


