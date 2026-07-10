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

Never hardcode project IDs. Resolve them at runtime — and re-resolve live each session; never cache a project ID across sessions (a stale ID silently targets the wrong project on rename/fork/mirror-drift, and is the root cause behind the close-verification incident documented below).

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

### Canonical enumeration pattern

To enumerate ALL projects (or issues) in a group, a single page is never the whole result — paginate and guard against silent truncation:

```bash
# GitLab — paginate a group's projects, following x-next-page until empty
page=1
while [ -n "$page" ]; do
  resp=$(glab api "groups/<group-id>/projects?include_subgroups=true&per_page=100&page=$page" --include)
  # parse the response body ($resp) for project ids/paths here, deduping by id.
  # Then advance by reading the `x-next-page` response header — an empty value
  # means this was the last page, so the loop exits (the guard above is what breaks).
  page=$(printf '%s\n' "$resp" | awk -F': *' 'tolower($1)=="x-next-page"{sub(/\r/,"",$2); print $2}')
done
```

- **Follow pagination via the `x-next-page` response header** — loop until it comes back empty. A single-page read on a known-large group is a signal the loop stopped early, not proof the group is small.
- **Dedupe by project id** — subgroup traversal can surface the same project more than once.
- **Silent-zero guard:** `membership=true` can return a misleadingly small subset (e.g. a host that only sees a handful of a group's dozens of projects). If the count looks suspiciously low relative to the known group size, retry WITHOUT `membership` (rely on `include_subgroups=true` alone) before trusting the result. A zero/one-page result on a known-large group is a probable auth/pagination bug — treat it as a bug signal, never as ground truth that "the group is actually empty."

## Label Taxonomy

**Taxonomy convention (decided 2026-07-05, #727):** labels use the SINGLE-COLON form exclusively (`priority:high`, `status:ready`, `area:vcs`, `type:chore`, `from:<agent>`). The `::`-scoped form (`priority::high`, GitLab scoped-labels) is DEPRECATED baseline-scaffold legacy and MUST NOT be introduced — this repo mirrors to GitHub, which has no scoped-label semantics (no mutual-exclusion enforcement), so `::` yields zero benefit on the mirror while a migration would break every existing label reference and issue.

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
- `area:skills` | `area:vcs` | `area:harness`

### Type Labels
- `bug` | `feature` | `enhancement` | `refactor`
- `chore` | `documentation` | `epic` | `discovery` | `carryover` | `broken-window`
- `carryover` — auto-created for 2×SPIRAL or FAILED agent tasks; see `scripts/lib/spiral-carryover.mjs`.
- `broken-window` — knowingly-broken shipment, hard due-date, filed by session-end Phase 2.6 (#730/H5); see `scripts/lib/spiral-carryover.mjs` (`createBrokenWindowIssue`).

### Provenance Labels
- `from:<agent>` — SHOULD be applied to any issue/MR created by an automated agent (e.g. `from:discovery`, `from:reconcile`), so operators can filter agent-authored items from human-authored ones. Single-colon form, per the taxonomy convention above.

## Issue Linking (`blocks` / `is_blocked_by`)

GitLab's native issue-link types `blocks` and `is_blocked_by` (`glab api -X POST projects/:id/issues/:issue_iid/links -f link_type=blocks|is_blocked_by`) are a **Premium/Ultimate license feature**. On a Free/Core-tier GitLab instance this call returns **HTTP 403** — a license-gate signal, not an auth/permission failure. Do not retry with different credentials or escalate as an auth bug.

**Fallback (non-Premium instances):**
1. **Use `relates_to` instead** — `link_type=relates_to` is available on every GitLab tier (no ordering semantics, just an unscoped relation). Same API shape, only the `link_type` value changes:
   ```bash
   glab api -X POST "projects/:id/issues/:issue_iid/links" \
     -f target_project_id=:id -f target_issue_iid=:other_iid -f link_type=relates_to
   ```
2. **Document the blocking semantics in the issue body** — since `relates_to` carries no ordering meaning, add an explicit ordering note to both issues, e.g. `⚠ Ordering: erst #<blocker_iid>, dann dieses Issue — blocks-Link nicht verfügbar (non-Premium)`.
3. **Recognize the 403 as a license signal, not an auth error** — before assuming a token/scope problem, try `relates_to` on the same project pair: if `relates_to` succeeds where `blocks`/`is_blocked_by` 403s, the license gate — not authentication — is the cause.

GitHub has no native issue-blocking relation at all — the body-ordering-note fallback in step 2 above is the standing convention there too, regardless of license tier (see "GitHub (gh)" below).

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
glab issue update <IID> --label "status:in-progress"        # WARNING: --label REPLACES the full set — see caveat below
glab issue close <IID>                                       # then VERIFY: glab issue view <IID> must show state=closed
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

**Label update caveat (PUT-replaces, not additive):** `glab issue update --label` (and the underlying GitLab labels API) PUT-REPLACES the entire label set — it does not add to the existing set. To change a single label you must pass the FULL desired label list, or use the dedicated add/remove operations, which are themselves unreliable across `glab` versions. Preferred safe pattern: use `--label` (adds) together with `--unlabel` (removes) on `glab issue update` when your installed `glab` version supports both; otherwise read the current labels first, compute the full new set, and PUT once. The same PUT-replace semantics apply to `glab mr update --label`.

**Close verification:** after `glab issue close <IID>`, always verify the close actually landed — re-read the issue (`glab issue view <IID>`) and confirm `state: closed` in the output. A stale/wrong project ID or a silent 404 can report local success while closing nothing; a documented incident closed 32 issues into the void this way (project ID pointed at the wrong project — see "Dynamic Project Resolution" above for the re-resolve-each-session rule that prevents it).

**Commit-body close-keyword footgun:** GitLab (and GitHub) auto-close an issue when a commit pushed to the default branch contains a close keyword — `close`/`closes`/`closed`/`fix`/`fixes`/`fixed`/`resolve`/`resolves`/`resolved` — followed by `#N` ANYWHERE in the commit body, not just the subject line. This fires even inside a negation ("does NOT close #N") — the platform pattern-matches the keyword + issue reference; it does not parse English negation, so the negation offers no protection. Rule: when a commit body needs to MENTION an issue without closing intent, always use a non-closing reference — `refs #N`, `part of #N`, `siehe #N` — never a close-keyword verb next to the number, negated or not.

**`-f`/`--raw-field` vs `-F`/`--field` on `glab api`:** `-f` (`--raw-field`) sends a literal string value with no coercion and no `@file` expansion. `-F` (`--field`) interprets a value starting with `@` as a file to read, and coerces bare `true`/`false`/`null`/numeric strings to their typed form. Prefer `-f` for literal values — it avoids an unintended `@`-expansion when a value happens to start with `@` (e.g. an `@mention` in a comment body).

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

### Open Questions
_(optional — include only when unanswered questions remain in STATE.md `## Open Questions` at close; omit this section entirely otherwise)_
- [ ] [unanswered question 1] (source: W<N>/<agent>, prio: high|medium|low)
- [ ] [unanswered question 2] (source: W<N>/<agent>, prio: high|medium|low)

### Original Issue
Relates to #ORIGINAL_IID
```

### Discovery Finding

```markdown
## [Discovery] <finding title>

**Probe:** <probe_name>
**Severity:** <priority:critical|high|medium|low>
**Category:** <code|infra|ui|arch|session|audit|vault|feature>

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
- PRD: "gsd Pattern Adoption Quick-Wins" (#519; archived in the private Meta-Vault) § Pattern 3 + § 3 Gherkin Pattern 3
