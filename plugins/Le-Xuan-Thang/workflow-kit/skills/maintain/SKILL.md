---
name: maintain
description: Use to set up and run scheduled maintenance jobs after a product is approved. Suggests jobs based on product type and schedules them via cron. Also triggers when the user says "set up maintenance", "keep the product updated", "schedule recurring checks", or "monitor the product ongoing".
allowed-tools: Read, Write, Bash
---

# Workflow Maintain

Set up scheduled maintenance jobs appropriate to the product type. Jobs run via cron using `python -m workflow_kit schedule`.

## Step 1: Check phase

```bash
python3 -c "
from workflow_kit.runtime.state import load_state
from pathlib import Path
s = load_state(Path('.'))
print('phase:', s.phase, '| product_type:', s.product_type)
"
```

Phase should be `maintain`. If earlier: "Product not yet approved. Run /workflow-kit:synthesize first."

## Step 2: Show suggested jobs by product type

| Product type | Suggested jobs |
|---|---|
| webapp | Weekly dependency audit, Daily uptime check, Monthly perf report |
| library | Monthly compatibility check, Weekly CVE scan |
| paper | Monthly citation freshness check, Quarterly related-work scan |
| article | — (ask user if they want revision reminders) |
| api | Daily endpoint health check, Weekly schema drift detection |
| dataset | Quarterly data quality audit, Monthly license check |

Ask: "Which of these jobs do you want? You can also describe custom jobs."

## Step 3: Write job files

For each enabled job, create `workflow/maintenance/jobs/<job-id>.json`:

```json
{
  "job_id": "<kebab-case-id>",
  "description": "<what this job does>",
  "schedule": "<cron expression, e.g. '0 9 * * 1' = Mon 9am>",
  "agent": "<worker domain: code-reviewer | devops | researcher | editor>",
  "reviewer": "<reviewer domain>",
  "task": "<plain English instructions for the agent>"
}
```

## Step 4: Install cron schedule

```bash
python -m workflow_kit schedule --start 09:00 --stop 10:00 --recurring
```

## Step 5: Report

```
✓ Maintenance configured

  Jobs: N enabled
  Schedule: recurring, 09:00–10:00

  <job-id>: <description> [<cron>]
  ...

  To run manually:   python -m workflow_kit maintain
  To check status:   /workflow-kit:status
  To stop schedule:  python -m workflow_kit schedule --remove
```
