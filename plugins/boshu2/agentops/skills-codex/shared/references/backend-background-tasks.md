# Backend: Background Tasks (Fallback)

Concrete tool calls for spawning agents using `Task(run_in_background=true)`. This is the **last-resort fallback** when neither Codex sub-agents nor Claude native teams are available.

**When detected:** `Task` tool is available but `TeamCreate` and `spawn_agent` are not.

**Limitations:**
- Fire-and-forget — no messaging, no redirect, no scope adjustment
- No inter-agent communication
- No debate mode (R2 requires messaging)
- No retry (must re-spawn from scratch)
- No graceful shutdown (only `TaskStop`, which is lossy)

---

## Spawn: Background Agents

Spawn agents with `Task(run_in_background=true)`. Each call returns a `task_id` for later polling.

### Council Judges

```
Task(
  subagent_type="general-purpose",
  run_in_background=true,
  prompt="You are judge-1.\n\nYour perspective: Correctness & Completeness\n\n<PACKET>\n...\n</PACKET>\n\nWrite your verdict to .agents/council/2026-02-17-auth-judge-1.md\nThis is your ONLY output channel — there is no messaging.",
  description="Council judge-1"
)
# Returns: task_id="abc-123"

Task(
  subagent_type="general-purpose",
  run_in_background=true,
  prompt="You are judge-error-paths.\n\nYour perspective: Error Paths & Edge Cases\n\n<PACKET>...</PACKET>\n\nWrite your verdict to .agents/council/2026-02-17-auth-judge-error-paths.md",
  description="Council judge-error-paths"
)
# Returns: task_id="def-456"
```

Both `Task` calls go in the **same message** — they run in parallel.

### Swarm Workers

```
Task(
  subagent_type="general-purpose",
  run_in_background=true,
  prompt="You are worker-3.\n\nYour Assignment: Task #3: Add password hashing\n...\n\nWrite result to .agents/swarm/results/3.json\nDo NOT run git add/commit/push.",
  description="Swarm worker-3"
)
```

### Research Explorers

```
Task(
  subagent_type="Explore",
  run_in_background=true,
  prompt="Thoroughly investigate: authentication patterns...\n\nWrite findings to .agents/research/2026-02-17-auth.md",
  description="Research explorer"
)
```

---

## Wait: Poll for Completion

Background tasks have no messaging. Poll with `TaskOutput`.

```
TaskOutput(task_id="abc-123", block=true, timeout=120000)
TaskOutput(task_id="def-456", block=true, timeout=120000)
```

**Or non-blocking check:**

```
TaskOutput(task_id="abc-123", block=false, timeout=5000)
```

**After `TaskOutput` returns**, verify the agent wrote its result file:

```
Read(".agents/council/2026-02-17-auth-judge-1.md")
```

**Timeout behavior:** If `timeout` expires, `TaskOutput` returns with a timeout status — the agent may still be running. **Recovery:**
1. Check result file — agent may have written it but not finished cleanly
2. If result file exists → use it, `TaskStop` the agent
3. If no result file → agent failed silently. For council: proceed with N-1 verdicts, note in report. For swarm: add task back to retry queue, re-spawn a fresh agent.
4. Never assume `TaskOutput` completion means the result file was written — always verify

**Fallback:** If background tasks fail despite detection, fall back to inline mode. See `backend-inline.md`.

---

## No Messaging

Background tasks cannot receive messages. This means:

- **No debate R2** — judges get one round only
- **No retry** — if validation fails, re-spawn a new agent from scratch
- **No scope adjustment** — the prompt is final at spawn time

---

## Cleanup

Background tasks self-terminate when done. For stuck tasks:

```
TaskStop(task_id="abc-123")
```

This is lossy — partial work may be lost.

---

## Key Rules

1. **Filesystem is the only communication channel** — agents write files, lead reads files
2. **No messaging = no debate** — `--debate` is unavailable with this backend
3. **No retry = must re-spawn** — failed agents get a fresh `Task` call, not a message
4. **Always check result files** — `TaskOutput` completion doesn't guarantee the agent wrote its file
5. **Prefer native teams** — this backend is strictly inferior; use it only as last resort
