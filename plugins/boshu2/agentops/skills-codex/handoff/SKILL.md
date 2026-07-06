---
name: handoff
description: "Write compact continuation handoffs."
---
# Handoff Skill

> **Quick Ref:** Create structured handoff for session continuation. Output: `.agents/handoff/YYYY-MM-DD-<topic>.md` + continuation prompt.

**YOU MUST EXECUTE THIS WORKFLOW. Do not just describe it.**

Create a handoff document that enables seamless session continuation.

## Handoff is the write-side of the self-healing context loop

Handoff is the **write-side of the `handoff → clear → rehydrate` loop** that keeps
a long-running agent (or peer orchestrator) healthy against context bloat. The
natural pre-`/clear` step is to hand off: capture the working state to durable
state *first*, then clear, then rehydrate from the artifact. **Handoff before
clear, always** — clearing without a current handoff loses the thread. The handoff
must be complete enough to rehydrate the lane to exactly where it was (goal,
claimed bead(s), held reservations, peer/comms topology, working-thread pointer).
The structured artifact is `ao session handoff` → `.agents/handoff/` (`--no-kill` writes
without the tmux restart).

## Every handoff is a compounding artifact

A handoff is a first-class node in the compounding artifact graph — it feeds the
llm-wiki / knowledge corpus, gets mined and measured (`consumed`/`consumed_by`
hooks), and each cycle should make the next handoff better. Context, code, and
markdown are all artifacts to be fed back. Write handoffs dense and honest.

## Execution Steps

Given `$handoff [topic]`:

### Step 1: Create Output Directory

```bash
mkdir -p .agents/handoff
```

### Step 2: Identify Session Context

**If topic provided:** Use it as the handoff identifier.

**If no topic:** Derive from recent activity:
```bash
# Recent commits
git log --oneline -5 --format="%s" | head -1

# Check current issue
BEADS_DIR="$(ao beads dir)" br list --status in_progress 2>/dev/null | head -1

# Check ratchet state
ao ratchet status 2>/dev/null | head -3
```

Use the most descriptive source as the topic slug.

**Topic slug format:** 2-4 words, lowercase, hyphen-separated (e.g., `auth-refactor`, `api-validation`).
**Fallback:** If no good topic found, use `session-$(date +%H%M)` (e.g., `session-1430`).

### Step 3: Gather Session Accomplishments

**Review what was done this session:**

```bash
# Recent commits this session (last 2 hours)
git log --oneline --since="2 hours ago" 2>/dev/null

# Recent file changes
git diff --stat HEAD~5 2>/dev/null | head -20

# Research produced
ls -lt .agents/research/*.md 2>/dev/null | head -3

# Plans created
ls -lt .agents/plans/*.md 2>/dev/null | head -3

# Issues closed
br list --status closed --since "2 hours ago" 2>/dev/null | head -5
```

### Step 4: Identify Pause Point

Determine where we stopped:

1. **What was the last thing done?**
2. **What was about to happen next?**
3. **Were we mid-task or between tasks?**
4. **Any blockers or decisions pending?**

Check for in-progress work:
```bash
br list --status in_progress 2>/dev/null | head -5
```

### Step 5: Identify Key Files to Read

List files the next session should read first:
- Recently modified files (core changes)
- Research/plan artifacts (context)
- Any files mentioned in pending issues

```bash
# Recently modified
git diff --name-only HEAD~5 2>/dev/null | head -10

# Key artifacts
ls .agents/research/*.md .agents/plans/*.md 2>/dev/null | tail -5
```

### Step 6: Write Handoff Document

**Write to:** `.agents/handoff/YYYY-MM-DD-<topic-slug>.md` (use `date +%Y-%m-%d`)

```markdown
# Handoff: <Topic>

**Date:** YYYY-MM-DDTHH:MM:SSZ
**Session:** <brief session description>
**Status:** <Paused mid-task | Between tasks | Blocked on X>

---

## What We Accomplished This Session

### 1. <Accomplishment 1>

<Brief description with file:line citations>

**Files changed:**
- `path/to/file.py` - Description

### 2. <Accomplishment 2>

...

---

## Where We Paused

<Clear description of pause point>

**Last action:** <what was just done>
**Next action:** <what should happen next>
**Blockers (if any):** <anything blocking progress>

---

## Context to Gather for Next Session

1. <Context item 1> - <why needed>
2. <Context item 2> - <why needed>

---

## Questions to Answer

1. <Open question needing decision>
2. <Clarification needed>

---

## Files to Read

```
# Priority files (read first)
path/to/critical-file.py
.agents/research/YYYY-MM-DD-topic.md

# Secondary files (for context)
path/to/related-file.py
```

### Step 7: Write Continuation Prompt

**Write to:** `.agents/handoff/YYYY-MM-DD-<topic-slug>-prompt.md` (use `date +%Y-%m-%d`)

```markdown
# Continuation Prompt for New Session

Copy/paste this to start the next session:

---

## Context

<2-3 sentences describing the work and where we paused>

## Read First

1. The handoff doc: `.agents/handoff/YYYY-MM-DD-<topic-slug>.md`
2. <Other critical files>

## What I Need Help With

<Clear statement of what the next session should accomplish>

## Key Files

```
<list of paths to read>
```

## Open Questions

1. <Question 1>
2. <Question 2>

---

<Suggested skill to invoke, e.g., "Use $implement to continue">
```

### Step 8: Extract Learnings (Optional)

If significant learnings occurred this session, also run post-mortem:

```bash
# Check if post-mortem skill should be invoked
# (if >3 commits or major decisions made)
git log --oneline --since="2 hours ago" 2>/dev/null | wc -l
```

**If ≥3 commits:** Suggest running `$post-mortem --quick` to extract learnings.
**If <3 commits:** Handoff alone is sufficient; learnings are likely minimal.

### Step 8.5: Grade Skills Used (ms outcome, optional)

If `ms` is installed (`command -v ms`), grade each skill whose guidance this session **actually used** (genuinely consulted, not merely trigger-matched): `ms outcome <skill> --success` or `ms outcome <skill> --failure`, so ranking is fed by real usage. Honest only — the skills you truly leaned on, not every match. Skip if `ms` is not present.

### Step 9: Report to User

Tell the user:
1. Handoff document location
2. Continuation prompt location
3. Summary of what was captured
4. Suggestion: Copy the continuation prompt for next session
5. If learnings detected, suggest `$post-mortem --quick`

### Step 10: Ensure Codex Closeout

If this handoff is ending a Codex hookless thread, run:

```bash
ao codex ensure-stop --auto-extract 2>/dev/null || true
```

`ao codex ensure-stop` is idempotent for the same Codex thread, so duplicate handoff
invocations are safe. Use `ao codex status` only when you need to confirm
lifecycle health.

**Output completion marker:**
```
<promise>DONE</promise>
```

If no context to capture (no commits, no changes):
```
<promise>EMPTY</promise>
Reason: No session activity found to hand off
```

## Example Output

```
Handoff created:
  .agents/handoff/20260131T143000Z-auth-refactor.md
  .agents/handoff/20260131T143000Z-auth-refactor-prompt.md

Session captured:
- 5 commits, 12 files changed
- Paused: mid-implementation of OAuth flow
- Next: Complete token refresh logic

To continue: Copy the prompt from auth-refactor-prompt.md

<promise>DONE</promise>
```

## Key Rules

- **Capture state, not just summary** - next session needs to pick up exactly where we left off
- **Identify blockers clearly** - don't leave the next session guessing
- **List files explicitly** - paths, not descriptions
- **Write the continuation prompt** - make resumption effortless
- **Cite everything** - file:line for all references

## Integration with $post-mortem

Handoff captures *state* for continuation.
Post-mortem captures *learnings* for the flywheel (full knowledge lifecycle).

For a clean session end:
```bash
$handoff              # Capture state for continuation
$post-mortem --quick  # Extract learnings for future
```

Both should be run when ending a productive session.

## Without ao CLI

If ao CLI not available:
1. Skip the `ao ratchet status` check in Step 2
2. Step 8 retro suggestion still works (uses git commit count)
3. All handoff documents are still written to `.agents/handoff/`
4. Knowledge is captured for future sessions via handoff, just not indexed

---

## Examples

### Paused Mid-Implementation

**User says:** `$handoff` (after working on OAuth flow for 2 hours, need to stop)

**What happens:**
1. Agent detects recent commits (5 commits in last 2 hours, auth-related)
2. Agent checks in-progress work with `br list` (issue #42 still open)
3. Agent identifies pause point: "Completed token generation, about to start refresh logic"
4. Agent lists key files: auth.go, token.go, research doc, plan doc
5. Agent writes handoff document with accomplishments and pause state
6. Agent writes continuation prompt with clear next action
7. Agent checks commits (5) and suggests running `$post-mortem --quick` to extract learnings

**Result:** Handoff captures state, continuation prompt ready, post-mortem suggested.

### Between Tasks, Clean State

**User says:** `$handoff` (just closed issue #40, about to start #41 next session)

**What happens:**
1. Agent detects 1 commit (closed issue #40), no pending changes
2. Agent identifies pause point: "Between tasks. Last: closed #40 (fixed rate limiting). Next: start #41 (add JWT refresh)"
3. Agent lists files from #40 (middleware.go, config.go)
4. Agent writes handoff with accomplishment summary and next-task preview
5. Agent writes continuation prompt with `$implement #41` suggestion
6. Agent skips post-mortem suggestion (<3 commits)

**Result:** Handoff captures clean boundary, continuation is simple.

### Auto-Derived Topic

**User says:** `$handoff` (no topic provided, agent derives from commits)

**What happens:**
1. Agent reads recent commits: "feat: add rate limiting", "fix: token expiry"
2. Agent derives topic slug: "rate-limiting" (from most recent commit)
3. Agent creates handoff files with derived topic in filename
4. Agent reports: "Handoff created: .agents/handoff/20260213T143000Z-rate-limiting.md"

**Result:** Topic auto-derived from git history, no user input needed.

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| "No session activity found to hand off" | No commits, no file changes detected | Expected for idle sessions. Nothing to hand off. Start new work or skip handoff. |
| Handoff files not written | `.agents/handoff/` directory does not exist or not writable | Run `mkdir -p .agents/handoff` or check directory permissions |
| Topic slug is generic "session-1430" | No descriptive commits or issues to derive topic from | Provide explicit topic: `$handoff auth-refactor` for better naming |
| Continuation prompt missing key context | Recent files or artifacts not listed in handoff | Manually add missing files to handoff document or re-run with explicit topic |
| Post-mortem suggested but no learnings | Agent sees ≥3 commits and auto-suggests `$post-mortem --quick` | Run `$post-mortem --quick` or skip if commits are trivial (agent can't judge learning quality, only commit count) |

---

## See Also

- `../post-mortem/SKILL.md` — Full validation + knowledge lifecycle (council + extraction + activation + retirement); `--quick` quick-captures a single learning (folded the retired `$retro`)

## Local Resources

### scripts/

- `scripts/validate.sh`
