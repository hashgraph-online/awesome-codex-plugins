---
name: gitlab-ops
user-invocable: false
tags: [reference, vcs, gitlab, github, issues]
model: haiku
model-preference: sonnet
model-preference-codex: gpt-5.4-mini
model-preference-cursor: claude-sonnet-4-6
description: Use this skill when performing VCS operations on GitLab or GitHub repositories — creating, updating, or closing issues and MRs, applying label taxonomy, running `glab`/`gh` CLI commands, or resolving project IDs dynamically. Acts as the single source of truth for CLI command syntax and label conventions; consuming skills reference this rather than duplicating logic. Triggers: "create a GitLab issue", "list open MRs", "apply priority label", "how do I resolve the project ID", "what's the carryover issue template". <example>Context: session-end needs to file a carryover issue for an incomplete task. user: "/close" assistant: "Creating carryover issue via glab with the Carryover Template from gitlab-ops — labels: carryover, priority:high."</example>
---

# VCS Operations Reference

## VCS Auto-Detection

Detect which VCS platform the current repo uses and select the right CLI:

```bash
# Check git remote
REMOTE_URL=$(git remote get-url origin 2>/dev/null)
if echo "$REMOTE_URL" | grep -q "github.com"; then
  VCS=github    # use `gh`
else
  VCS=gitlab    # use `glab`
fi
```

**Session Config overrides:**
- `vcs: github|gitlab` — force a specific platform
- `gitlab-host: <host>` — override auto-detected GitLab host (glab reads host from git remote by default)

## How Other Skills Reference This

**Directive:** Consuming skills MUST NOT duplicate VCS auto-detection logic or CLI command
syntax inline. This skill is the single source of truth for all VCS operations.

When a skill needs VCS operations, include this reference block in its instructions:

> **VCS Reference:** Detect the VCS platform per the "VCS Auto-Detection" section of the gitlab-ops skill.
> Use CLI commands per the "Common CLI Commands" section. For cross-project queries, see "Dynamic Project Resolution."

**Canonical commands:** All `glab` and `gh` command syntax — flags, output formats,
pagination options — is defined in the "Common CLI Commands" section below. Consuming
skills must reference that section rather than redefining commands. If a skill needs a
command variant not listed there, add it to this file first, then reference it.

**What consuming skills should include:**
- The reference block above (copy-paste it verbatim)
- Any skill-specific *parameters* they pass to commands (e.g., label names, issue templates)
- They should NOT include raw `glab`/`gh` invocations or detection snippets

## Dynamic Project Resolution

Never hardcode project IDs. Resolve them at runtime.

### Current project

```bash
# GitLab — get numeric project ID
glab repo view --output json | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])"

# GitHub — get owner/name identifier
gh repo view --json nameWithOwner -q '.nameWithOwner'
```

### Cross-project queries

When a skill needs to reference other projects (e.g., from `cross-repos` in Session Config):

```bash
# GitLab — resolve project ID by name
glab api "projects?search=<project-name>" | python3 -c "import json,sys; [print(p['id'], p['path_with_namespace']) for p in json.load(sys.stdin)]"

# GitHub — resolve repo details
gh api "repos/<owner>/<name>" --jq '.full_name'
```

**Note:** Some API calls require numeric project IDs (GitLab) or `owner/repo` slugs (GitHub). Always resolve dynamically from the project name.

## Label Taxonomy

### Priority Labels
- `priority:critical` — blocking production or users
- `priority:high` — important, schedule this sprint
- `priority:medium` — plan for next sprint
- `priority:low` — backlog, nice-to-have

### Status Labels
- `status:ready` — defined, ready to pick up
- `status:in-progress` — actively being worked on
- `status:review` — MR/PR created, awaiting review
- `status:blocked` — waiting on external dependency

### Area Labels
- `area:frontend` | `area:backend` | `area:database`
- `area:ai` | `area:security` | `area:testing`
- `area:ci` | `area:infrastructure` | `area:compliance`

### Type Labels
- `bug` | `feature` | `enhancement` | `refactor`
- `chore` | `documentation` | `epic` | `discovery` | `carryover`
- `carryover` — auto-created for 2×SPIRAL or FAILED agent tasks; see `scripts/lib/spiral-carryover.mjs`.

## Common CLI Commands

### GitLab (glab)

```bash
# Issues
glab issue list --per-page 50                              # All open issues
glab issue list --label "status:ready" --per-page 10       # Ready to work on
glab issue list --label "priority:high" --per-page 10      # High priority
glab issue list --closed --per-page 10                      # Recently closed
glab issue view <IID>                                       # View issue details
glab issue view <IID> --comments                            # With comments
glab issue create --title "title" --label "priority:high,status:ready"
glab issue update <IID> --label "status:in-progress"
glab issue close <IID>
glab issue note <IID> -m "Comment text"                    # Add comment

# MRs
glab mr list                                                # Open MRs
glab mr create --fill --draft                               # Create draft MR
glab mr merge <MR_IID>                                     # Merge MR

# Pipelines
glab pipeline list --per-page 5                            # Recent pipelines
glab pipeline status <ID>                                  # Pipeline details

# API (reads host from git remote automatically)
glab api "projects/$(glab repo view --output json | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")/issues?state=opened&per_page=50"
glab api "projects/$(glab repo view --output json | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")/milestones?state=active"
```

### GitHub (gh)

```bash
# Issues
gh issue list --limit 50                                   # All open issues
gh issue list --label "status:ready" --limit 10            # Ready to work on
gh issue list --label "priority:high" --limit 10           # High priority
gh issue list --state closed --limit 10                    # Recently closed
gh issue view <NUMBER>                                      # View issue details
gh issue view <NUMBER> --comments                           # With comments
gh issue create --title "title" --label "priority:high,status:ready"
gh issue edit <NUMBER> --add-label "status:in-progress"
gh issue close <NUMBER>
gh issue comment <NUMBER> --body "Comment text"            # Add comment

# PRs
gh pr list --state open                                    # Open PRs
gh pr create --fill --draft                                 # Create draft PR
gh pr merge <NUMBER>                                       # Merge PR

# Workflows (CI equivalent)
gh run list --limit 5                                      # Recent workflow runs
gh run view <RUN_ID>                                       # Run details

# API
gh api "repos/{owner}/{repo}/issues?state=open&per_page=50"
gh api "repos/{owner}/{repo}/milestones?state=open"
```

## Issue Templates

### Bug Template
```
## Description
What happens vs. what should happen.

## Steps to Reproduce
1.
2.

## Root Cause (if known)

## Acceptance Criteria
- [ ]
```

### Feature Template
```
## Goal
What should be achieved and why.

## Tasks
- [ ]

## Acceptance Criteria
- [ ]

## Session Type
[housekeeping|feature|deep]
```

### Carryover Template (from /close)
```
## [Carryover] Original Task Description

### What was completed
- [completed items]

### What remains
- [ ] [remaining task 1]
- [ ] [remaining task 2]

### Context for next session
[relevant context, file paths, decisions made]

### Original Issue
Relates to #ORIGINAL_IID
```

### Discovery Finding

```markdown
## [Discovery] <finding title>

**Probe:** <probe_name>
**Severity:** <priority:critical|high|medium|low>
**Category:** <code|infra|ui|arch|session>

### Finding

<description of the problem>

### Evidence

- **File:** `<file_path>`
- **Line:** <line_number>
- **Code:**
  ```
  <matched_text with surrounding context>
  ```

### Impact

<why this matters — severity rationale>

### Recommended Fix

<concrete fix suggestion>

### Acceptance Criteria

- [ ] <specific, verifiable condition>
- [ ] Quality gates pass after fix
```

Labels: `type:discovery`, `priority:<level>`, `area:<inferred>`, `status:ready`

## Template-First Enforcement (PSA-005 + #519)

Pattern 3 of the gsd Pattern Adoption (Issue #519) registers a PreToolUse hook
`hooks/pre-bash-templates-first.mjs` that **blocks** `gh|glab pr|mr|issue create|new`
Bash calls when the current session contains no prior `Read` on a matching template file.

**When this matters:** before you or a subagent opens an MR, PR, or issue via CLI, a
matching template must have been read in the current session:

- GitHub: `.github/PULL_REQUEST_TEMPLATE.md` / `.github/ISSUE_TEMPLATE*`
- GitLab: `.gitlab/merge_request_templates/Default.md` / `.gitlab/issue_templates/*`

Accepted template paths are configured in `.orchestrator/policy/templates-policy.json`
(versioned, operator-editable). Default behaviour:

- `enforcement: "block"` — hook exits 2 when no prior template Read is found
- Allow-list of host-specific template globs (GitHub + GitLab by default)
- `bypass_patterns` — list of command substrings that skip the hook (e.g. CI/bot calls)

**Bypass options for the current session** (when the hook blocks unexpectedly):

1. **Read the template first** — re-run the `create` call after a `Read` on the template
   path; the hook re-evaluates and sees the Read.
2. **Session acknowledgement** — write `.orchestrator/runtime/templates-acknowledged.json`
   containing `{ sessionId, acknowledgedAt }`; the hook allows all subsequent `create`
   calls in this session.

**What the hook mechanically enforces** (what this skill previously documented as convention only):

- "Template-first" for every new MR/PR/issue
- Prevents convention drift across repos by turning the documentation requirement into
  a hard gate — the same shift from rule to mechanism that PSA-003 made for destructive commands

**If the hook blocks incorrectly**, follow this sequence:

1. Read the template — retry the `create` call.
2. If the hook still blocks, open a bug issue against `hooks/pre-bash-templates-first.mjs`
   with reproduce steps (command, session ID, template path that should have matched).

### Issue/MR Creation Checklist (with template-first gate active)

```bash
# 1. Read the relevant template first (satisfies the hook)
# GitLab MR
Read .gitlab/merge_request_templates/Default.md

# GitHub PR
Read .github/PULL_REQUEST_TEMPLATE.md

# 2. Then create — hook now passes
glab mr create --title "..." --description "..."
gh pr create --title "..." --body "..."
```

### Cross-References

- Hook implementation: `hooks/pre-bash-templates-first.mjs`
- Read-history helper: `hooks/_lib/transcript-history.mjs` (checks session transcript for prior Reads)
- Enforcement policy: `.orchestrator/policy/templates-policy.json`
- Session acknowledgement: `.orchestrator/runtime/templates-acknowledged.json`
- Sister hook (destructive-command model): `hooks/pre-bash-destructive-guard.mjs`
- PRD: `docs/prd/2026-05-22-gsd-pattern-adoption-quickwins.md` § Pattern 3 + § 3 Gherkin Pattern 3
