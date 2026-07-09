# Team Coordination

## Wave Execution via Swarm

### Beads Mode

1. **Get ready issues from current wave**

```
  subject="<issue-id>: <issue-title>",
  description="Implement beads issue <issue-id>.

Details from beads:
<paste issue details from bd show>

Execute using $implement <issue-id>. Mark complete when done.",
  activeForm="Implementing <issue-id>"
)
```

3. **Add dependencies if issues have beads blockedBy:**
```
```

4. **Invoke swarm to execute the wave:**
```
Tool: Skill
Parameters:
  skill: "agentops:swarm"
```

5. **After swarm completes, verify and close beads with evidence:**
```bash
COMMIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
bd close <issue-id> --reason "crank-sync wave:${wave} commit:${COMMIT_SHA}" 2>/dev/null
```



```
Tool: Skill
Parameters:
  skill: "agentops:swarm"
```


### Both Modes — Swarm Will:

- Spawn workers with fresh context (Ralph pattern)

## Verify and Sync to Beads (MANDATORY)

> Swarm executes per-task validation (see `skills/shared/validation-contract.md`). Crank trusts swarm validation and focuses on beads sync.

**For each issue reported complete by swarm:**

1. **Verify swarm task completed:**
   ```
   ```
   If task is still pending/blocked, swarm validation failed — add to retry queue.

2. **Sync to beads with evidence:**
   ```bash
   COMMIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
   CHANGED_FILES=$(git diff --name-only HEAD~1 2>/dev/null | head -10 | tr '\n' ' ' | sed 's/ $//')
   bd close <issue-id> --reason "commit:${COMMIT_SHA} files:[${CHANGED_FILES}]" 2>/dev/null
   ```

3. **On sync failure** (bd unavailable or error):
   - Log warning but do NOT block the wave
   - Track for manual sync after epic completes

4. **Record ratchet progress (ao integration):**
   ```bash
   if command -v ao &>/dev/null; then
       ao ratchet record implement 2>/dev/null
   fi
   ```

**Note:** Per-issue review is handled by swarm validation. Wave-level semantic review happens in the Wave Acceptance Check.

## Check for More Work

After completing a wave:

### Beads Mode
2. Check if new beads issues are now unblocked: `ao beads exec ready`
4. If no more issues after 3 retry attempts, proceed to final validation

2. If yes, loop back to wave execution
3. If all completed, proceed to final validation

### Both Modes
- **Max retries:** If issues remain blocked after 3 checks, escalate: "Epic blocked - cannot unblock remaining issues"
