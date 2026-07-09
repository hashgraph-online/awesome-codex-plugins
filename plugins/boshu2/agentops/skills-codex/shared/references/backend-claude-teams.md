# Backend: Claude Native Teams

Concrete tool calls for spawning agents using Claude Code native teams (`TeamCreate` + `SendMessage` + shared `TaskList`).

**When detected:** `TeamCreate` tool is available in your tool list.

---

## Pre-Flight: Confirm Modern Claude Features

Before spawning teammates, verify feature readiness:

1. `claude agents` succeeds (custom agents discoverable)
2. Teammate profiles for write tasks declare `isolation: worktree`
3. Long-running teammates prefer `background: true`
4. Hooks include worktree lifecycle coverage (`WorktreeCreate`, `WorktreeRemove`) and config auditing (`ConfigChange`) where policy requires it

For canonical feature details, read:
`skills/shared/references/claude-code-latest-features.md`.

---

## Setup: Create Team

Every spawn session starts by creating a team. One team per wave (fresh context = Ralph Wiggum preserved; see `skills/shared/references/ralph-loop-contract.md`).

```
TeamCreate(team_name="council-20260217-auth", description="Council validation of auth module")
```

```
TeamCreate(team_name="swarm-1739812345-w1", description="Wave 1: parallel implementation")
```

**Naming conventions:**
- Council: `council-YYYYMMDD-<target>`
- Swarm: `swarm-<epoch>-w<wave>`
- Crank: delegates to swarm naming

## Leader Contract (Native Teams)

Claude teams are leader-first orchestration:

1. One lead creates the team and assigns all work.
2. Teammates never self-assign from shared tasks.
3. Teammates report to lead via short `SendMessage` signals.
4. Lead reads result artifacts from disk, validates, and decides retries/escalation.

Recommended signal envelope (single-line JSON, under 100 tokens):

```json
{"type":"completion|blocked|help_request","agent":"worker-3","task":"3","detail":"short status","artifact":".agents/swarm/results/3.json"}
```

`completion`: task finished, artifact written.
`blocked`: cannot proceed safely.
`help_request`: teammate needs coordination or scope clarification.

### Peer Messaging (Allowed, Lead-Controlled)

Native teams support direct teammate-to-teammate messaging. Use this only for coordination handoffs; keep messages thin and always copy the lead in follow-up summaries.

```text
worker-2 -> worker-5: "Need auth schema constant name; please confirm from src/auth/schema.ts"
worker-5 -> lead: "Resolved peer question for worker-2; no scope change."
```

---

## Spawn: Create Workers/Judges

After `TeamCreate`, spawn each agent with `Task(team_name=..., name=...)`. All agents in a wave spawn in parallel (single message, multiple tool calls).

### Council Judges (parallel spawn)

```
Task(
  subagent_type="general-purpose",
  team_name="council-20260217-auth",
  name="judge-1",
  prompt="You are judge-1 on team council-20260217-auth.\n\nYour perspective: Correctness & Completeness\n\n<PACKET>\n...\n</PACKET>\n\nWrite your verdict to .agents/council/2026-02-17-auth-judge-1.md\nThen send a SHORT completion signal to the team lead (under 100 tokens).\nDo NOT include your full analysis in the message — the lead reads your file.",
  description="Council judge-1"
)

Task(
  subagent_type="general-purpose",
  team_name="council-20260217-auth",
  name="judge-error-paths",
  prompt="You are judge-error-paths on team council-20260217-auth.\n\nYour perspective: Error Paths & Edge Cases\n\n<PACKET>\n...\n</PACKET>\n\nWrite your verdict to .agents/council/2026-02-17-auth-judge-error-paths.md\nThen send a SHORT completion signal to the team lead (under 100 tokens).",
  description="Council judge-error-paths"
)
```

Both `Task` calls go in the **same message** — they spawn in parallel.

### Swarm Workers (parallel spawn)

```
Task(
  subagent_type="general-purpose",
  team_name="swarm-1739812345-w1",
  name="worker-3",
  prompt="You are worker-3 on team swarm-1739812345-w1.\n\nYour Assignment: Task #3: Add password hashing\n<description>...</description>\n\nInstructions:\n1. Execute your task — create/edit files as needed\n2. Write result to .agents/swarm/results/3.json\n3. Send a SHORT signal to team lead (under 100 tokens)\n4. Do NOT run git add/commit/push — the lead commits\n\nRESULT FORMAT:\n{\"type\":\"completion\",\"issue_id\":\"3\",\"status\":\"done\",\"detail\":\"one-line summary\",\"artifacts\":[\"path/to/file\"]}",
  description="Swarm worker-3"
)

Task(
  subagent_type="general-purpose",
  team_name="swarm-1739812345-w1",
  name="worker-5",
  prompt="You are worker-5 on team swarm-1739812345-w1.\n\nYour Assignment: Task #5: Create login endpoint\n...",
  description="Swarm worker-5"
)
```

### Research Explorers (read-only)

```
Task(
  subagent_type="Explore",
  team_name="research-20260217-auth",
  name="explorer-1",
  prompt="Thoroughly investigate: authentication patterns in this codebase\n\n...",
  description="Research explorer"
)
```

Use `subagent_type="Explore"` for read-only research agents. Use `"general-purpose"` for agents that need to write files.

---

## Wait: Receive Completion Signals

Workers/judges send completion signals via `SendMessage`. These are **automatically delivered** to the team lead — no polling needed.

When a teammate finishes, their message appears as a new conversation turn. The lead reads result files from disk, NOT from message content.

```
# Teammate message arrives automatically:
# "judge-1: Done. Verdict: WARN, confidence: HIGH. File: .agents/council/2026-02-17-auth-judge-1.md"

# Lead reads the file for full details:
Read(".agents/council/2026-02-17-auth-judge-1.md")
```

**Timeout handling (default: 120s per round, 90s for debate R2):**

If a teammate goes idle without sending a completion signal:
1. Check their result file — they may have written it but failed to message
2. If result file exists → read it and proceed (the message was the only thing missing)
3. If no result file → the agent failed silently. **Recovery:** proceed with N-1 judges/workers and note the failure in the report. For swarm workers, add the task back to the retry queue.
4. Never wait indefinitely — after the timeout, move on

See `skills/council/references/cli-spawning.md` for timeout configuration (`COUNCIL_TIMEOUT`, `COUNCIL_R2_TIMEOUT`).

**Fallback:** If native teams fail at runtime despite passing detection (e.g., `TeamCreate` succeeds but `Task` spawning fails), fall back to background tasks. See `backend-background-tasks.md`.

---

## Message: Debate R2 / Retry

Send messages to specific teammates using `SendMessage`. Teammates wake from idle when messaged.

### Council Debate R2

```
SendMessage(
  type="message",
  recipient="judge-1",
  content="DEBATE ROUND 2\n\nOther judges' verdicts:\n- judge-error-paths: FAIL (HIGH confidence) — file: .agents/council/2026-02-17-auth-judge-error-paths.md\n\nRead the other judge's file. Revise your assessment considering their perspective.\nWrite your R2 verdict to .agents/council/2026-02-17-auth-judge-1-r2.md\nThen send a completion signal.",
  summary="R2 debate instructions for judge-1"
)
```

**R2 timeout (default: 90s):** If a judge doesn't respond to R2 within `COUNCIL_R2_TIMEOUT`, use their R1 verdict for consolidation. See `skills/council/references/debate-protocol.md` for full timeout handling.

### Swarm Worker Retry

```
SendMessage(
  type="message",
  recipient="worker-3",
  content="Validation failed: pytest tests/test_auth.py returned exit code 1.\nFix the failing tests and rewrite your result to .agents/swarm/results/3.json",
  summary="Retry worker-3: test failure"
)
```

---

## Cleanup: Shutdown and Delete

After consolidation/validate, shut down all teammates then delete the team.

```
# Shutdown each teammate
SendMessage(type="shutdown_request", recipient="judge-1", content="Council complete")
SendMessage(type="shutdown_request", recipient="judge-error-paths", content="Council complete")

# After all teammates acknowledge shutdown:
TeamDelete()
```

**Reaper pattern:** If a teammate doesn't respond to shutdown within 30s, proceed with `TeamDelete()` anyway.

**If `TeamDelete` fails** (e.g., stale members): clean up manually with `rm -rf ~/.claude/teams/<team-name>/` then retry `TeamDelete()` to clear in-memory state.

---

## Multi-Wave Pattern

For crank/swarm with multiple waves, create a **new team per wave**:

```
# Wave 1
TeamCreate(team_name="swarm-1739812345-w1", description="Wave 1")
# ... spawn workers, wait, validate, commit ...
# ... shutdown teammates ...
TeamDelete()
# If TeamDelete fails: rm -rf ~/.claude/teams/swarm-1739812345-w1/ then retry

# Wave 2 (fresh context)
TeamCreate(team_name="swarm-1739812345-w2", description="Wave 2")
# ... spawn workers for newly-unblocked tasks ...
TeamDelete()
```

This ensures each wave's workers start with clean context (no leftover state from prior waves).

**If `TeamDelete` fails between waves**, the next `TeamCreate` may conflict. Always verify cleanup succeeded before creating the next wave team.

---

## Key Rules

1. **`TeamCreate` before `Task`** — tasks created before the team are invisible to teammates — **Enforcement: `safety.ValidateTeamLifecycle()` (T9)**
2. **Pre-assign tasks before spawning** — workers do NOT race-claim from TaskList — **Enforcement: documentation only**
3. **Lead-only commits** — workers write files, lead runs `git add` + `git commit` — **Enforcement: `hooks/git-worker-guard.sh` (T4)**
4. **Thin messages** — workers send <100 token signals, full results go to disk — **Enforcement: `safety.ValidateMessageSize()` (T9)**
5. **New team per wave** — fresh context, Ralph Wiggum preserved — **Enforcement: `safety.ValidateTeamLifecycle()` (T9)**
6. **Always cleanup** — `TeamDelete()` after every wave, even on partial failure — **Enforcement: `hooks/stop-team-guard.sh` + `safety.ValidateTeamLifecycle()` (T9)**
