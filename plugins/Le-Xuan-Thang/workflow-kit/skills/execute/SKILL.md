---
name: execute
description: Use to start the dispatcher loop — every task is executed by a worker agent then validated by a domain-expert reviewer agent before being marked done. Requires at least one pending task. Also triggers when the user says "start building", "run the dispatcher", "execute the workplan", or "start the dev loop". Pass --stop to stop a running dispatcher.
argument-hint: "[--stop]"
allowed-tools: Read, Bash
---

# Workflow Execute

Start the dispatcher. For every task: worker builds → reviewer validates → PASS marks done, FAIL retries, max retries exceeded escalates to user.

## Reviewer gate

After each worker output passes syntax verification:
1. If `reviewers:` is configured in `workflow.yaml` (or per-task `reviewer:` field in the task JSON), a reviewer agent is called with a domain-appropriate system prompt
2. Domain is auto-detected from task description: `code-reviewer`, `editor`, `researcher`, `designer`, `data-scientist`, or `devops`
3. Reviewer responds with PASS or FAIL on the first line, followed by specific feedback
4. On FAIL: feedback is appended to the retry prompt — worker tries again (up to `max_retries`)
5. After `max_retries` FAILs: task is escalated — user sees reviewer's final feedback and chooses: skip / retry with guidance / redesign
6. On PASS (or no reviewer configured): task is marked completed and committed
7. If reviewer LLM is unreachable: treated as PASS to avoid blocking the pipeline

## Step 1: Check prerequisites

```bash
python3 -c "
from workflow_kit.runtime.state import load_state
from pathlib import Path
s = load_state(Path('.'))
print('phase:', s.phase)
" && \
ls workflow/tasks/pending/*.json 2>/dev/null | wc -l | xargs -I{} echo "pending tasks: {}"
```

- Phase not `plan` or `execute`: warn with correct next skill.
- 0 pending tasks: "Run /workflow-kit:plan first."

## Step 2: Handle --stop

If user passes `--stop` or says "stop":
```bash
python -m workflow_kit stop
```
Done.

## Step 3: Check if already running

```bash
cat workflow/dispatcher.pid 2>/dev/null | xargs -I{} kill -0 {} 2>/dev/null && echo "running" || echo "stopped"
```
If running: "Dispatcher already running. Use /workflow-kit:status."

## Step 4: Advance state to 'execute'

```python
from workflow_kit.runtime.state import load_state, save_state
from pathlib import Path
s = load_state(Path('.'))
if s.phase == "plan":
    s.transition_to("execute")
    save_state(s, Path('.'))
    print("Phase: plan → execute")
```

## Step 5: Start dispatcher

```bash
python -m workflow_kit execute &
echo $! > workflow/dispatcher.pid
```

## Step 6: Report

```
✓ Dispatcher started (PID N)

  Loop: worker builds → reviewer validates → PASS/FAIL
  Max retries: <from workflow.yaml>

  Monitor:
    /workflow-kit:status   — inline progress
    /workflow-kit:monitor  — live dashboard

  When all tasks complete:
    /workflow-kit:synthesize  — package and review deliverables
```

## Reviewer escalation

When a task fails review max_retries times, the dispatcher pauses and prints:

```
⚠ Task <id> failed review N times
  Reviewer (<domain>): <feedback summary>

  A) Skip this task
  B) Retry with your guidance (describe what to fix)
  C) Redesign the task entirely
```

Respond inline — dispatcher waits before continuing.
