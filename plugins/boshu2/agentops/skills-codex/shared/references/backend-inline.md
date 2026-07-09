# Backend: Inline (No Spawn Available)

Degraded single-agent mode when no multi-agent primitives are detected. The current agent performs all work sequentially in its own context.

**When detected:** No `spawn_agent`, no `TeamCreate`, no `Task` tool available — or `--quick` flag was explicitly set.

---

## Council: Single Inline Judge

Instead of spawning parallel judges, the lead evaluates from each perspective sequentially:

```
1. Build the context packet (same as multi-agent mode)
2. For each perspective:
   a. Adopt the perspective mentally
   b. Write findings to .agents/council/YYYY-MM-DD-<target>-<perspective>.md
3. Synthesize into final report
```

Output format is identical — same file paths, same verdict schema. Downstream consumers (consolidation, report) don't know it was inline.

**No debate available** — debate requires messaging between agents.

---

## Swarm: Sequential Execution

Instead of parallel workers, execute each task sequentially:

```
1. TaskList() — find unblocked tasks
2. For each unblocked task (in order):
   a. Execute the task directly
   b. Write result to .agents/swarm/results/<task-id>.json
   c. TaskUpdate(taskId="<id>", status="completed")
3. Check for newly-unblocked tasks
4. Repeat until all tasks complete
```

Same result files, same validation — just sequential.

**Error handling:** If a task fails mid-execution:
1. Write failure result to `.agents/swarm/results/<task-id>.json` with `"status": "blocked"`
2. Check if downstream tasks depend on it (`blockedBy`)
3. Skip blocked downstream tasks, mark as skipped
4. Continue with independent tasks that don't depend on the failed one

---

## Research: Inline Exploration

Instead of spawning an Explore agent, perform the tiered search directly:

```
1. Read docs/code-map/ if present
2. Grep/Glob for relevant files
3. Read key files
4. Write findings to .agents/research/YYYY-MM-DD-<topic>.md
```

---

## Key Rules

1. **Same output format** — inline mode writes the same files as multi-agent mode
2. **Same validation** — all checks still apply
3. **Slower but functional** — no parallelism, but all skill capabilities preserved (except debate)
4. **Inform the user** — log "Running in inline mode (no multi-agent backend detected)"
