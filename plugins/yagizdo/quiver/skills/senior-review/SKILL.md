---
name: senior-review
description: "Pragmatic senior developer code review -- evaluates code quality, risks, and conventions through a team lead lens. Standalone or integrated into /review pipeline."
argument-hint: "[--quick] [#PR_NUMBER | PR_URL]"
when-to-use: "user wants a quick targeted single-pass senior developer review -- '/senior-review', 'senior review', 'quick review', 'fast review', 'single-pass review'"
---

# Gather Context

```
!`git rev-parse --is-inside-work-tree 2>/dev/null || echo "NO_GIT"`
```

```
!`git branch --show-current 2>/dev/null || echo "NO_GIT"`
```

```
!`git log --oneline -10 2>/dev/null || echo "NO_GIT"`
```

---

# Senior Review

Run a pragmatic senior developer code review -- evaluating structural decisions, code quality, risk areas, and language conventions through a team lead lens.

**Announce:** "Using the senior-review skill for a pragmatic code review."

---

## Step 0 -- Git Availability

If any gather-context block above returned `NO_GIT`, this directory is not a git repository.
Print: `> No git repository detected. /senior-review requires a git repo.`
**Stop here.**

## Step 0.5 -- Input Validation

If `$ARGUMENTS` is empty AND there is no conversation context about what to review (no prior diff discussion, no files mentioned), print:

> Usage: `/senior-review [--quick] [#PR_NUMBER | PR_URL]`
>
> Options:
> - `--quick` -- Single-pass review (faster, same quality bar)
> - `#123` or PR URL -- Review a specific pull request
> - No arguments -- Prompted to select diff source

**Stop here.**

If `$ARGUMENTS` is empty but conversation context exists (e.g., user was just discussing a diff), proceed -- use the contextual diff.

---

## Step 1 -- Argument Parsing

Parse `$ARGUMENTS`:

- Contains `--quick` --> set mode to `quick`, remove flag from remaining arguments
- Contains `#NNN` (hash + digits) --> set source to `pr`, extract PR number
- Contains a URL matching a PR/MR pattern (github.com/.../pull/NNN, gitlab.com/.../-/merge_requests/NNN) --> set source to `pr`, extract URL
- Otherwise --> source is unset (will prompt in Step 2)

---

## Step 2 -- Diff Source Selection

If source was set from Step 1 (PR number or URL), skip to Step 3.

If source is unset, infer from context: "this"/"my changes"/"just made" --> `uncommitted`; "branch"/"vs main" --> `branch`. If clear, skip prompt.

Only if intent cannot be inferred, use `AskUserQuestion`:

> What would you like me to review?

Buttons:
- **"Uncommitted changes"** --> source = `uncommitted`
- **"Branch diff (vs main/master)"** --> source = `branch`
- **"Pull Request"** --> source = `pr` (will prompt for PR number)

If user selects "Pull Request" and no PR number was provided, ask:
> Enter the PR number or URL:

---

## Step 3 -- Diff Gathering

| Source | Command | Notes |
|--------|---------|-------|
| `uncommitted` | `git diff` + `git diff --staged` | Combine both; stop if both empty: "No uncommitted changes found." |
| `branch` | `git rev-parse --verify main` then `git diff main...HEAD` | Fall back to `master` if `main` missing; stop if empty: "No changes found between current branch and base branch." |
| `pr` | `gh pr diff <pr_number_or_url>` via Bash tool (not `!` block) | Stop if `gh` fails: "Could not fetch PR diff. Ensure `gh` CLI is installed and authenticated." |

Also gather the file list: `git diff --name-only main...HEAD` (for PR source, use `gh pr diff --name-only` or parse diff headers).

---

## Step 4 -- Language Detection

Language detection is handled by the senior-reviewer agent.

---

## Step 5 -- Context7 Lookup (Full Mode Only)

If mode is `quick`, skip this step entirely.

For the detected primary language, query context7 for current conventions. One query, primary language only. Skip if quick mode or context7 unavailable.

---

## Step 6 -- Agent Dispatch

Dispatch `quiver:senior-reviewer` with the following context (in this order):

1. **Full diff** from Step 3.
2. **Changed file list** with detected language(s) from Step 4.
3. **Mode:** `full` or `quick`.
4. **Context7 results** (if available from Step 5, omit if quick mode or unavailable).
5. **Scope reminder:** "Your findings MUST be scoped to code CHANGED in this diff. Reading surrounding code for context is expected; flagging pre-existing issues is not."
6. **Citation accuracy:** "Every file:line reference in your findings must be verified by reading the file. Do not cite line numbers from memory or inference -- use the Read tool to confirm the content at the cited line before including it in a finding."

Do NOT pass pipeline context. This is standalone mode -- Phase 5 (meta-review) must not activate.

---

## Step 7 -- Output

Present the agent's findings in the terminal.

After presenting findings, use `AskUserQuestion`:

> Review complete. What would you like to do?

Buttons:
- **"Save report"** --> Write to `.claude/reports/senior-review-{timestamp}.md` (use `date '+%Y-%m-%d_%H-%M-%S'` format). Confirm with: `> Report saved to {path}`
- **"Done"** --> Stop.
