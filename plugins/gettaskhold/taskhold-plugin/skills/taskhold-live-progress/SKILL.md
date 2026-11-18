---
name: taskhold-live-progress
description: Report your progress on Taskhold's live board while you work, so the person can see how far along each task is without reading the terminal. Use when the user says "report progress as you go", "let me watch you work", "show me how far along you are", "break this into steps", "keep me posted", or before any task that will take more than a few minutes. Needs the Taskhold MCP tools (taskhold_*); if they are missing, use the taskhold skill to set up.
---

# Taskhold live progress

The person watches https://taskhold.com/dashboard/live: one bar per task, split by step, the step you are on, your latest message, and how long since you last reported. Steps drive the bar.

## Start

1. `taskhold_begin` with `title` (the request, short), `project` (the repo folder name), `agent` (for example "Claude Code in api-server") and `steps`.
2. Plan 3 to 8 steps. Order them so each depends only on earlier ones, and make the first the smallest change that proves the approach.

## While working

- Finish each step with `taskhold_complete` on the step and `start_next: true`. Its summary says what you observed ("tests pass, 14 new"), not only what you did.
- Inside a long step, call `taskhold_progress` on the step at milestones: `current` and `total` when you are counting (files migrated, tests fixed), otherwise `percent`, plus a `message` under 80 characters about what is happening now ("Migrating the invoices table"). Every few minutes at most, never on every tool call.
- If the plan changes, `taskhold_plan` with `replace: true`. Finished steps stay.
- `taskhold_add_note` for findings and decisions a later session would need.

## Finish

`taskhold_complete` on the task with a summary whose first line is the outcome, then what changed and how you checked it. Add `outcome.checks` (tests, builds) and `outcome.links` (PR, commit) when you have them.

## Don't

- Don't report progress you can't count; give a message without a percent instead.
- Don't leave a task in progress when you stop: complete it, or add a note and block it.
