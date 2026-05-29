---
name: plan
description: Use to generate a structured workplan — objectives and tasks — from workflow/product.md. Requires init to have run first (phase must be 'define' or 'plan'). Also triggers when the user says "generate my workplan", "plan the project", "create tasks from the product definition", or "what should the agent work on".
argument-hint: "[-n <task count>]"
allowed-tools: Read, Bash
---

# Workflow Plan

Read `workflow/product.md` and generate objectives + tasks matched to worker capability. Advances phase to `plan`.

<HARD-GATE>
Do NOT generate tasks if workflow/product.md is missing or phase is past 'plan'. Warn and stop.
</HARD-GATE>

## Step 1: Check prerequisites

```bash
python3 -c "
from workflow_kit.runtime.state import load_state
from pathlib import Path
s = load_state(Path('.'))
print('phase:', s.phase)
print('product_type:', s.product_type)
"
ls workflow/product.md 2>/dev/null && echo "product-ok" || echo "product-missing"
ls workflow/worker_capability.json 2>/dev/null && echo "capability-ok" || echo "no-capability-warning"
```

- Phase `execute` or later: "Already past planning. Use /workflow-kit:execute to continue."
- `workflow/product.md` missing: "Run /workflow-kit:init first."
- No capability file: warn but continue — orchestrator will plan conservatively.

## Step 2: Generate workplan

```bash
python -m workflow_kit workplan
```

Orchestrator (DeepSeek) reads:
- `workflow/product.md` (Vision/Mission/Core)
- `workflow/worker_capability.json` (skill scores)
- `workflow/tasks/completed/` (what's already done)

Creates 3–5 objectives aligned to Vision. Tasks under each objective matched to worker skill scores. Tasks needing a skill < 3.0 are decomposed into smaller sub-tasks.

## Step 3: Write workflow/workplan.md

```markdown
# Workplan — <product name>

Generated: <timestamp>

## Objectives

### <Objective 1>
**Why:** aligned to Vision/Mission
**Success criteria:** measurable outcome

Tasks:
- [ ] <task-id>: <description>
```

## Step 4: Advance state to 'plan'

```python
from workflow_kit.runtime.state import load_state, save_state
from pathlib import Path
s = load_state(Path('.'))
if s.phase == "define":
    s.transition_to("plan")
    save_state(s, Path('.'))
    print("Phase: define → plan")
```

## Step 5: Report

```
Workplan generated:

  Objectives: N
  Tasks:      N pending in workflow/tasks/pending/

  obj-01: <name>  (N tasks)
  obj-02: <name>  (N tasks)

Review workflow/workplan.md, then:
  /workflow-kit:execute  — start the dispatcher with reviewer agents
```
