---
name: orchestrate
description: "Trigger: active multi-agent run. Manages inbox, dependency resolution, message formatting, and agent handoffs."
modes:
  - auto       # auto-triggered during active orchestration
  - status     # /status — read-only orchestration dashboard
  - intervene  # /intervene — pause/cancel/redirect running agents
---

# Skill: Orchestrate

**CRITICAL**: Run `HARNESS_DIR=$(epic path)` first. NEVER use `.harness/` in the project directory.

## Process

Each mode follows its own step sequence below. In auto mode: check state → read inbox → check control → check deps → execute → hand off. In status mode: check state → read agents → render dashboard. In intervene mode: check state → parse command → write directive → confirm.

## Mode: auto (default)

Triggered automatically when an active multi-agent orchestration is detected.

### Step 1: Check orchestration state
1. Run `HARNESS_DIR=$(epic path)`
2. Read `$HARNESS_DIR/orchestrator/run.json`
3. If no active run, this skill does not apply — return

### Step 2: Read agent inbox
1. Read `$HARNESS_DIR/orchestrator/agents/{my_id}/inbox.jsonl`
2. Process any pending messages from other agents or user interventions
3. Messages from other agents: integrate into current task context
4. Messages from user (via intervene redirect): adjust task accordingly

### Step 3: Check control directives
1. Read `$HARNESS_DIR/orchestrator/control.json`
2. If a directive targets this agent (or "all"), act on it:
   - **pause**: halt work after current tool call, wait for resume
   - **cancel**: stop immediately, set status to "cancelled"
   - **redirect**: adopt the new instruction, discard current task
   - **resume**: resume from paused state
3. After acting on a directive, increment `generation` in control.json to acknowledge

### Step 4: Check dependencies
1. Read `$HARNESS_DIR/orchestrator/run.json` dependency graph
2. Identify which agents this agent depends on
3. Read their `status.json` — if any dependency is not DONE, wait
4. If all dependencies are DONE, proceed with task

### Step 5: Execute with progress reporting
While working on the assigned task:
1. The Rust `orchestrate` hook automatically appends events to `stream.jsonl` on each tool call
2. Status updates happen automatically via the hook
3. No manual progress reporting needed — the hook handles it

### Step 6: Complete and hand off
When task is complete:
1. Report status via structured output format (DONE/DONE_WITH_CONCERNS/BLOCKED/NEEDS_CONTEXT)
2. The `orchestrate` hook will evaluate dependencies and notify downstream agents
3. If results should be shared with specific agents, include in the output summary

---

## Mode: status — Orchestration Dashboard

Read-only view of the current orchestration run. Displayed when user runs `/status` or asks about orchestration state.

### Step 1: Check orchestration state

1. Check if `$HARNESS_DIR/orchestrator/run.json` exists
2. If the file does not exist, output:
   > No active orchestration. Run `/go` or `/orbit` to start.
3. If `status` is not `"running"`, output:
   > Last orchestration ended with status: **{status}**. No active run.
4. If `status` is `"running"`, proceed to Step 2.

### Step 2: Read all agent states

Extract the agent list from `run.json.agents`. For each agent `{id}`:

1. Read agent status from `$HARNESS_DIR/orchestrator/agents/{id}/status.json` (mark `unknown` if missing)
2. Read the last 5 events from `$HARNESS_DIR/orchestrator/agents/{id}/stream.jsonl` (show "no events yet" if missing)
3. Calculate elapsed time:
   - `started_at` set, `completed_at` not set: elapsed = now - `started_at`
   - Both set: elapsed = `completed_at` - `started_at`
   - Format as `Xm Ys` or `Xh Ym`
4. Read the dependency graph from `run.json.dependencies`

### Step 3: Render dashboard

Output a formatted dashboard (keep total under 30 lines):

```
## Orchestration Dashboard

- **Run ID**: {run.id}
- **Status**: {run.status}
- **Elapsed**: {total_elapsed since run.started_at}
- **Agents**: {count where status=running} / {total} active

| Agent | Role | Status | Elapsed | Last Event |
|-------|------|--------|---------|------------|
| {id} | {role} | {status} | {elapsed} | {summary of last event} |

### Dependency Graph
{render with ASCII arrows, e.g.:}
  builder ──→ reviewer ──→ integrator
  builder ──→ tester

### Recent Events (last 5 across all agents)
- [{timestamp}] {agent_id}: {event_summary}

### User Interventions
{read control.json; show directives if any, else "none"}
```

**Dependency graph rendering rules:**
- Read edges from `run.json.dependencies` (format: `{"agent_a": ["agent_b", "agent_c"]}`)
- Render using `──→` arrows
- If no dependencies exist, output: "No inter-agent dependencies."

**Event summary formatting:**
- Each event is one line from `stream.jsonl` with fields: `timestamp`, `type`, `message`
- Summarize `message` to at most 60 characters
- Sort by timestamp descending, take top 5

### Step 4: Optional — file change summary

```bash
git diff --stat
```

If changes exist, append:

```
### File Changes
- {count} files modified ({insertions} insertions, {deletions} deletions)
- Key changes: {list up to 5 file paths}
```

**Note**: This mode is read-only — never modify orchestration state.

---

## Mode: intervene — Agent Intervention

Write control directives that the orchestrate hook reads on the next agent tool call. Triggered when user runs `/intervene`.

### Step 1: Check active orchestration

1. Read `$HARNESS_DIR/orchestrator/run.json`
2. If no active run (status != "running"), output: "No active orchestration to intervene in."
3. Show current agent list with statuses

### Step 2: Parse user command

Invocation format:
- `intervene pause {agent_id}` — pause a specific agent (blocks next tool call)
- `intervene pause all` — pause all agents
- `intervene cancel {agent_id}` — cancel a specific agent
- `intervene cancel all` — cancel entire orchestration
- `intervene redirect {agent_id} {new_instruction}` — change what an agent is doing
- `intervene resume {agent_id}` — resume a paused agent

If the user provides no arguments, ask which action and target they want.

Validate the agent_id against the agent list in run.json. If not found, output: "Agent '{agent_id}' not found in active orchestration. Available agents: {list}" and stop.

### Step 3: Write control directive

Read current generation from `$HARNESS_DIR/orchestrator/control.json` (or 0 if file doesn't exist). Increment by 1.

Write to `$HARNESS_DIR/orchestrator/control.json`:
```json
{
  "action": "pause|cancel|redirect|resume",
  "target": "agent_id or 'all'",
  "message": "optional user message",
  "generation": <current_generation + 1>
}
```

For `redirect`, the message field contains the new instruction.
For `pause`/`cancel`, the message field is optional — use an empty string if none provided.
For `resume`, set action to "resume" and target to the agent_id.

**Additional actions by type:**

- **cancel all**: Also update `$HARNESS_DIR/orchestrator/run.json` status to "aborted"
- **redirect**: Also append the new instruction to the target agent's `$HARNESS_DIR/orchestrator/agents/{agent_id}/inbox.jsonl` as a new line: `{"type": "redirect", "instruction": "{new_instruction}", "at": "{ISO-8601}"}`
- **cancel {agent_id}**: Also update the agent's status in run.json to "cancelled"

### Step 4: Confirm

Output confirmation:
```
Intervention recorded: {action} {target}
The {target} agent will respond on its next tool call.
Use /status to monitor.
```

**Notes:**
- Multiple interventions can be queued (generation number increases each time)
- The orchestrate hook checks `control.json` before every agent tool call, so interventions take effect within one tool call cycle
- "cancel all" is destructive — confirm with the user before executing
- "redirect" requires a new instruction — if none is provided, ask the user

---

## Message Format Convention

When agents need to communicate (via SendMessage or future inbox/outbox):

```json
{
  "from": "agent_id",
  "to": "agent_id",
  "type": "handoff|question|blocked|result",
  "body": "message content",
  "timestamp": "ISO-8601"
}
```

## Anti-Rationalization

| Excuse | Rebuttal | What to do instead |
|--------|----------|-------------------|
| "I'll just work independently" | Orchestration exists to prevent conflicts and duplication | Check dependencies first, report status |
| "Progress reporting slows me down" | The hook does it automatically on every tool call | No manual action needed |
| "I'll read all agents' state" | Only read your own inbox and dependencies | Respect isolation boundaries |
| "I'll intervene directly in agent files" | Direct file edits bypass the generation protocol | Always write to control.json |
| "I'll skip the status check" | Stale state leads to incorrect interventions | Always read run.json first |

## Evidence Required

- [ ] Inbox checked before starting work
- [ ] Control directives checked (auto mode)
- [ ] Dependencies verified (all upstream agents DONE)
- [ ] Structured output format used for completion report
- [ ] Dashboard shows all agent states accurately (status mode)
- [ ] Intervention written to control.json with incremented generation (intervene mode)

## Red Flags

- Starting work before dependencies are met
- Ignoring inbox messages from other agents
- Not reporting BLOCKED state when stuck
- Modifying orchestration state in status mode (read-only)
- Cancelling all agents without user confirmation
- Redirecting an agent without a concrete new instruction
- Writing to control.json when run.json status is "aborted" or "complete"
- Intervening without an active orchestration (check run.json first)
- Showing raw JSON instead of a formatted dashboard (status mode)
