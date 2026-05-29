---
name: synthesize
description: Use to package all completed work into deliverables appropriate to the product type, then present to the user for final review. User can approve (→ maintain), give feedback (→ sub-tasks → back to execute), or reject specific items. Also triggers when the user says "package the product", "I want to review what was built", "prepare deliverables", or "ship it".
allowed-tools: Read, Write, Bash
---

# Workflow Synthesize

Package completed work, generate a synthesis report, and present to the user for final review.

## Step 1: Check phase and task completion

```bash
python3 -c "
from workflow_kit.runtime.state import load_state
from pathlib import Path
s = load_state(Path('.'))
print('phase:', s.phase, '| product_type:', s.product_type)
for bucket in ('pending', 'active', 'review'):
    d = Path('workflow/tasks') / bucket
    n = len(list(d.glob('*.json'))) if d.exists() else 0
    if n: print(f'  still in {bucket}: {n} tasks')
"
```

If tasks still pending/active/review: "N tasks still running. Wait or stop with /workflow-kit:execute --stop."

## Step 2: Generate synthesis report

```bash
python -m workflow_kit synthesize
```

Writes `workflow/output/report.md` and prints the report.

## Step 3: Show deliverable checklist

Based on product_type:

| product_type | Deliverables |
|---|---|
| webapp | Source code, Deployed URL / run instructions, User guide |
| library | Installable package, API docs, CHANGELOG |
| paper | Document (PDF/Markdown), Bibliography, Abstract |
| article | Formatted text, Assets, Publishing-ready file |
| api | OpenAPI spec, Endpoint URL, Postman collection |
| dataset | Data files, Data card, Methodology doc |

Mark each ✓ (exists in workflow/output/ or project root) or □ (missing).

## Step 4: Present to user

```
╔══════════════════════════════════════════════════════╗
║  Product ready for your review                       ║
╚══════════════════════════════════════════════════════╝

  Type:    <product_type>
  Tasks:   N completed (N ✓ reviewer passed, N ✗ failed)

  Deliverables:
    ✓/□ <deliverable 1>
    ✓/□ <deliverable 2>

  Full report: workflow/output/report.md

  What would you like to do?
  A) Approve → move to maintenance
  B) Give feedback → create sub-tasks and loop back
  C) Reject specific items → targeted rework only
```

## Step 5: Handle response

**A — Approve:**
```python
from workflow_kit.runtime.state import load_state, save_state
from pathlib import Path
s = load_state(Path('.'))
s.transition_to("maintain")
save_state(s, Path('.'))
print("Phase: synthesize → maintain")
```
Tell user: "Run /workflow-kit:maintain to set up ongoing maintenance jobs."

**B — Feedback:**
Parse each piece of feedback into a task JSON in `workflow/tasks/pending/`. Detect task type from content (code issue → "implement", writing issue → "write", etc.). Then:
```python
s.transition_to("execute")
save_state(s, Path('.'))
print("Phase: synthesize → execute (feedback injected as sub-tasks)")
```
Tell user: "Run /workflow-kit:execute to process feedback."

**C — Specific rejection:**
Ask which deliverables to rework. Create targeted tasks for those only. Same execution loop as B.
