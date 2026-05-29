---
name: status
description: Use for a quick inline status check — shows current lifecycle phase, dispatcher state, task counts, and recent decisions. No TUI or browser. Also triggers when the user says "what's happening", "workflow progress", "how many tasks are left", or "is the dispatcher running".
allowed-tools: Bash
---

# Workflow Status

Print a compact status snapshot directly in the conversation.

## Step 1: Run

```bash
python -m workflow_kit status
```

## Step 2: Print result inline

```
── Workflow Status ───────────────────────────────────────
  Phase:      execute  (define → plan → [execute] → synthesize → maintain)
  Dispatcher: running (PID 12345)  /  stopped
  Active:     feat-003-dark-mode (started 4 min ago)
  In review:  1 task (reviewer running)
  Pending:    2 tasks
  Completed:  7 tasks  (6 ✓ reviewer passed  ·  1 ✗ failed)
  Workers:    llama3.1:70b → qwen2.5-coder:32b
  Orch:       deepseek/deepseek-chat:free

  Last completed:
    ✓ feat-002: Built CSV export endpoint
    ✗ feat-001: Auth middleware (reviewer: missing tests)
──────────────────────────────────────────────────────────
```

If no `workflow/` directory: "workflow-kit not initialized. Run /workflow-kit:init first."

If dispatcher stopped with pending tasks: append "Run /workflow-kit:execute to resume."

If phase is `synthesize` and all tasks done: append "Run /workflow-kit:synthesize to package deliverables."

## Metrics Summary

Load and display recent task metrics:

```python
from workflow_kit.runtime.metrics import load_metrics, summarize
from pathlib import Path

metrics = load_metrics(Path("."), limit=50)
stats = summarize(metrics)
if stats:
    print(f"""
┌─────────────────────────────────────────┐
│           Task Metrics (last 50)        │
├─────────────────────────────────────────┤
│ Total tasks:      {stats['total']:>4}                  │
│ Completed:        {stats['completed']:>4}  ({stats['pass_rate']}%)          │
│ Failed:           {stats['failed']:>4}                  │
│ Escalated:        {stats['escalated']:>4}                  │
│ Avg duration:     {stats['avg_duration_seconds']:>6.1f}s               │
│ Avg retries:      {stats['avg_retries']:>6.2f}               │""")
    if stats['reviewer_pass_rate'] is not None:
        print(f"│ Reviewer pass:    {stats['reviewer_pass_rate']:>5.1f}%               │")
    print("└─────────────────────────────────────────┘")
else:
    print("No metrics recorded yet. Run /workflow-kit:execute to start.")
```
