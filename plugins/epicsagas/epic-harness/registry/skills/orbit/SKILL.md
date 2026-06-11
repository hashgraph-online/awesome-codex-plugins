---
name: orbit
description: "State-persisted autonomous pipeline: spec → go → audit → ship in one command. Auto-detects direct/council/interactive mode. Crash-recoverable via PIPELINE-*.json. Hands-off until PR."
---

# /orbit — Complete Orbit

**CRITICAL**: Run `HARNESS_DIR=$(epic path)` first. NEVER use `.harness/` in the project directory.

You are entering **Orbit** mode — the full autonomous pipeline from spec to PR in one shot.

## Phase Recovery Protocol

At the start of **every response** during an active orbit:

1. Run `ls $HARNESS_DIR/orbit/PIPELINE-*.json 2>/dev/null`
2. Find the file with `"status": "running"`
3. Read it. Verify `phase` matches where you left off
4. **If `phase` is ahead of where you think you are, trust the file** — you may have compacted
5. **Conflict resolution (crash-mid-update)**: If `phase_history` contains an entry for the current `phase` with a completed timestamp, treat that phase as done and advance to the next phase — `phase_history` wins over the `phase` field when they disagree.
6. Resume from the resolved phase. Do NOT re-ask mode selection, re-run spec, or re-discover
7. **Worktree recovery**: If `worktree_name` is set in pipeline state:
   - Check if worktree still exists: `git worktree list | grep "{worktree_name}"`
   - If exists: `cd` into the worktree path to continue work
   - If not found: worktree was cleaned up externally — abort orbit with warning, set `"status": "aborted"`

If no file with `"status": "running"` exists, orbit was not started or has completed. Do not invent one.

**Crash recovery**: If `updated_at` is older than 45 minutes and the pipeline is in `status: running`, assume a crash occurred. Read the state, determine the last completed phase from `phase_history` (rule 5 above applies), and resume from there. Report the recovery to the user.

## Step 0: Preflight

Initialize pipeline state at `$HARNESS_DIR/orbit/PIPELINE-{timestamp}.json`:
```json
{
  "id": "{timestamp}",
  "mode": null,
  "phase": "auto_detect",
  "status": "running",
  "spec_file": null,
  "goal_slug": null,
  "branch": null,
  "worktree_name": null,
  "original_cwd": null,
  "audit_fail_count": 0,
  "max_retries": 3,
  "audit_report": null,
  "deadline": "{ISO-8601, now + 30 minutes}",
  "started_at": "{ISO-8601}",
  "updated_at": "{ISO-8601}",
  "phase_history": []
}
```

## Step 1: Auto-Detect Mode

**DO NOT ask the user for mode selection.** Auto-detect the best path:

### Detection Logic

| Signal | Mode | Reason |
|--------|------|--------|
| PRD / detailed requirements doc exists in project | `council` | Rich input → council synthesizes best approach |
| User request is specific and actionable (clear goal, defined scope) | `direct` | No need for discovery — spec directly |
| User request is vague, unfocused, or "I want to..." without specifics | `council` | Council frames the problem better than guessing |
| User explicitly says "interactive" or "let me discover first" | `interactive` | Respect explicit preference |

### Detection Process

1. Check for PRD/requirements docs: `ls {project}/PRD*.md {project}/docs/PRD*.md {project}/requirements*.md 2>/dev/null`
2. Evaluate user request clarity:
   - **Specific**: contains concrete feature descriptions, acceptance criteria, or technical constraints → `direct`
   - **Vague**: "build X", "improve Y", "add Z" without details → `council`
3. Record detected mode in pipeline state (`"mode": "direct|council|interactive"`)
4. Report mode choice to user as a **notification**, not a question: `"Orbit mode: {mode} (auto-detected)"`
5. Proceed immediately to the matching step below — **do not wait for confirmation**

## Step 2A: Direct Mode (clear request → auto-spec)

**Use when**: Request is specific and actionable.

1. Read the user's request + any existing docs (PRD, README, AGENTS.md)
2. Generate spec directly at `$HARNESS_DIR/specs/SPEC-{timestamp}.md` with `status: approved`
3. Record via `epic mem add --title "Orbit: {mode} mode decision" --type decision --importance 0.9 --body "CONTEXT"`
4. **Proceed immediately to Step 3** — no approval gate

## Step 2B: Council Auto-Spec (complex/vague request → council)

**Use when**: PRD exists or request needs framing.

1. Gather the user's request from conversation context
2. Launch 4 parallel sub-agents (Architect, Skeptic, Pragmatist, Critic) — each receives ONLY the request + codebase context, NOT the full conversation (anti-anchoring)
3. Synthesize: list agreement/disagreement, produce recommended approach
4. Generate spec at `$HARNESS_DIR/specs/SPEC-{timestamp}.md` with `status: approved`
5. Record via `epic mem add --title "Orbit: council decision" --type decision --importance 0.9 --body "CONTEXT"`
6. **Proceed immediately to Step 3** — no approval gate, no "orbit go"

## Step 2C: Interactive Mode (explicit user choice only)

**Use when**: User explicitly requested interactive mode.

1. Tell user to run `/discover` → `/spec`, then say "orbit go". STOP and wait.
2. On resume: load latest `SPEC-*.md` with `status: approved`. Proceed to Step 3.

**This mode is never auto-selected.** It requires explicit user opt-in.

## Step 3: Build (Go)

1. Load spec, extract `goal_slug`
2. **Git preflight**: verify clean working tree and not on detached HEAD:
   ```bash
   [ -z "$(git status --porcelain)" ] || (echo "ERROR: Dirty working tree or untracked files. Commit or stash first." && exit 1)
   git symbolic-ref -q HEAD || (echo "ERROR: Detached HEAD. Checkout a branch first." && exit 1)
   ```
3. **Worktree isolation**: Create an isolated git worktree:
   ```bash
   git worktree add .claude/worktrees/orbit-{goal_slug} -b orbit-{goal_slug} origin/{default-branch}
   cd .claude/worktrees/orbit-{goal_slug}
   ```
   - Record `worktree_name` and `original_cwd` in pipeline state
4. Plan tasks from Requirements (R1, R2...)
5. Execute with sub-agents — TDD, debug on failure, verify before done
6. Handle states: DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED
7. Integrate: full test suite, verify ACs

## Step 4: Audit

1. Gather scope via `git diff --stat`
2. Classify changed files (API, Frontend, DB, Backend, Tests, Infra)
3. Launch parallel sub-agents: Reviewer, Auditor, Test runner (+ scope-specific)
4. Synthesize Audit Report: Quality/Security/Performance PASS/WARN/FAIL + Spec Coverage
5. **PRESERVE audit report** in pipeline state `audit_report` field

## Step 5: Verdict

- **All PASS + all AC verified** → proceed to Ship
- **WARN** → log, auto-proceed
- **FAIL** → increment `audit_fail_count`:
  - `< 3`: plan fixes from action items, execute, return to Step 4
  - `≥ 3`: **PAUSE** — ask user "continue or abort?"

## Step 6: Ship

1. **Gate**: verify PASS audit report exists
2. **Integration verification** — run directly in worktree:
   - Clean build artifacts first: `cargo clean` / `npm run clean` / equivalent
   - Full build from scratch · complete test suite · linter + formatter
   - Fail → STOP. Do NOT create PR.
3. **Git hygiene**: conventional commits, rebase, squash fixups
4. **Create PR** via `gh pr create` with spec + audit report in body
5. **CI watch** via `gh pr checks --watch`, auto-fix failures
6. **Exit worktree**: Return to original directory and keep the worktree

## Step 7: Report

```
## Orbit Complete
- Pipeline: PIPELINE-{id}
- Mode: {direct|council|interactive} (auto-detected)
- Spec: SPEC-{timestamp} ({goal_slug})
- Branch: orbit-{goal_slug}
- Worktree: orbit-{goal_slug} (preserved for PR)
- PR: {URL}
- Audit retries: {count}

### Phase Summary
| Phase | Status | Retries |
|-------|--------|---------|
| Spec | approved | 0 |
| Go | complete | 0 |
| Audit | PASS | {count} |
| Ship | complete | 0 |
```

## Red Flags
- Interactive mode proceeding without spec approval (direct and council modes auto-approve)
- Continuing after 3 audit failures without user consent
- Skipping isolated integration test
- Shipping with FAIL in security audits
- Losing audit report between phases
- Creating branch with dirty working tree
- Losing worktree reference between phases
