# gc Pool Dispatch

When `GC_POOL_AVAILABLE=true`, replace `/swarm` invocation with gc pool dispatch:
- Workers are pre-started by gc pool (no spawn overhead)
- Assign work via `gc session nudge <worker> "<issue prompt>"`
- Poll completion via `gc status --json` + `bd show <id>` (check issue closed)
- gc handles crash recovery and session restart automatically

```bash
if [[ "$GC_POOL_AVAILABLE" == "true" ]]; then
    for issue in $READY_ISSUES; do
        ISSUE_DETAIL=$(bd show "$issue" 2>/dev/null)
        WORKER=$(gc status --json 2>/dev/null | jq -r '.pool.agents[] | select(.state == "idle") | .name' | head -1)
        if [[ -n "$WORKER" ]]; then
            gc session nudge "$WORKER" "Implement issue $issue: $ISSUE_DETAIL"
        else
            echo "No idle gc pool workers — waiting for pool auto-scale"
            gc pool wait --min-idle 1 --timeout 300
            WORKER=$(gc status --json 2>/dev/null | jq -r '.pool.agents[] | select(.state == "idle") | .name' | head -1)
            gc session nudge "$WORKER" "Implement issue $issue: $ISSUE_DETAIL"
        fi
    done
    # Poll until all wave issues are closed
    while true; do
        OPEN=$(br ready 2>/dev/null | wc -l)
        [[ "$OPEN" -eq 0 ]] && break
        sleep 30
    done
else
    # Standard /swarm invocation (existing behavior)
    # Invoke /swarm with task creation for each issue in the wave
fi
```

When `GC_POOL_AVAILABLE=false`, the existing `/swarm` path is used unchanged.
