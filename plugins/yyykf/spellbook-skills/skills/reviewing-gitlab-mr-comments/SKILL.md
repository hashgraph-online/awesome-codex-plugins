---
name: reviewing-gitlab-mr-comments
description: Use when reviewing GitLab merge request comments via glab in the current repo, including extracting line ranges and code snippets from inline discussions, then deciding next actions with a checklist or plan before execution
---

# Reviewing GitLab MR Comments

## Overview
Use `glab` to fetch MR comments in the current repository, summarize review feedback, confirm understanding, then propose either a simple action checklist or a full plan before executing changes. Prefer `line_range` for multi-line comments. Default output is comments + line ranges only (no code snippet).

**Core principle:** Read all comments → confirm understanding → choose checklist vs plan → get approval → execute.

**Announce at start:** "I'm using the reviewing-gitlab-mr-comments skill to review GitLab MR feedback."

## Prerequisites

- `glab` installed and authenticated.
- Run from the local repository that owns the MR.

Optional checks:

```bash
glab auth status
```

## Inputs

Accept either:
- MR IID (e.g., `123`)
- MR URL (e.g., `https://gitlab.com/group/project/-/merge_requests/123`)

If not provided, ask for it.

## Workflow

### Step 1: Fetch MR and Comments

Prefer `glab` commands, using IID or URL:

```bash
glab mr view <mr> --comments
```

If you need to see the code under review:

```bash
glab mr diff <mr>
```

If you need to map comments to files/lines (and include multi-line ranges), query discussions:

```bash
project_id=$(glab repo view -F json | python3 - <<'PY'
import json,sys
print(json.load(sys.stdin)["id"])
PY
)
glab api "projects/${project_id}/merge_requests/<mr>/discussions"
```

Then format discussions into a readable list with ranges (comments + line numbers only):

```bash
glab api "projects/${project_id}/merge_requests/<mr>/discussions" | \
  ./scripts/mr_discussions_to_md.py
```

To **include code snippets** (with context lines) and still show comments:

```bash
glab api "projects/${project_id}/merge_requests/<mr>/discussions" | \
  ./scripts/mr_discussions_to_md.py --repo-root "$(pwd)" --context 3 --snippet
```

Notes:
- The formatter prefers `position.line_range.start/end`. It falls back to `new_line/old_line` only when no range exists.
- If files are missing (e.g., deleted or not in the current checkout), the snippet will be marked unavailable.
- Use `--snippet` to enable snippet output; default is no snippet.

### Step 2: Summarize Feedback

Produce a structured summary:
- By thread or file
- Actionable requests vs questions
- Conflicts or ambiguity

### Step 3: Confirm Understanding

Ask the user to confirm the summary or clarify any ambiguous items.

### Step 4: Decide Checklist vs Plan

Use a **simple action checklist** when:
- Changes are localized
- No architectural changes
- 1–2 files, low risk

Use a **plan** when:
- Multiple files/modules
- Conflicting comments or tradeoffs
- Non-trivial refactor or behavior changes

### Step 5: Propose Next Steps

**Checklist output** (simple cases):
- Bullet list of concrete actions
- Verification steps

**Plan output** (complex cases):
- Phased steps with file targets
- Risks and validations

Then ask for approval:
"Do you want me to proceed?"

### Step 6: Execute After Approval

Only implement after the user confirms.

## Quick Reference

| Step | Action |
| --- | --- |
| Identify MR | Accept IID or URL; ask if missing |
| Fetch comments | `glab mr view <mr> --comments` |
| Fetch ranges | `glab api ".../merge_requests/<mr>/discussions"` |
| Format | `./scripts/mr_discussions_to_md.py --repo-root "$(pwd)"` |
| Summarize | Group by thread/file; mark conflicts |
| Choose output | Checklist for simple; plan for complex |
| Execute | Only after approval |

## Common Mistakes

**Skipping understanding confirmation**
- **Problem:** Misinterprets review intent
- **Fix:** Ask for confirmation before planning

**Jumping to code changes**
- **Problem:** Skips the plan/approval gate
- **Fix:** Always ask for approval

**Using the wrong repository context**
- **Problem:** Fetches the wrong MR
- **Fix:** Run in the repo that owns the MR

**Only using single-line fields**
- **Problem:** Inline comments are multi-line in GitLab but appear as a single line
- **Fix:** Prefer `position.line_range.start/end` and only fall back to `new_line/old_line`

## Example

```
MR: 123

Summary:
- fileA.ts: fix null handling
- fileB.ts: add tests

This is small and localized.

Checklist:
1) Fix null handling in fileA.ts
2) Add tests in fileB.ts
3) Run build/compile

Proceed?
```
