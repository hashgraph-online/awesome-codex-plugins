---
name: getting-started
description: Assess an authenticated Agiflow workspace and recommend the right next project-management workflow. Use when a user is new to Agiflow, asks what to do next, needs orientation, or is unsure whether to plan, refine, groom, triage, or review daily status.
---

# Getting Started with Agiflow

Act as a project-management coach. Diagnose the workspace before recommending action.

## Workflow

1. Call `get_current_scope` to identify the organization and current project context.
2. If the user has not selected a project, call `list_projects` and ask them to choose when more than one plausible project exists.
3. For the selected project, call `get_project_detail`, `list_project_statuses`, `list_work_units`, and `list_tasks`.
4. Call `list_members` only when assignments or team capacity affect the recommendation.
5. Interpret the state instead of only repeating counts.
6. Recommend one primary next workflow and explain why it fits.

## Decision Guide

- Empty project or unstructured requirements: use `project-plan`.
- Vague Planning task or unclear completion criteria: use `refine-task`.
- Ready Planning tasks that need prioritization or grouping: use `backlog-grooming`.
- Stalled, blocked, overloaded, or unhealthy work: use `triage`.
- Quick read-only progress check: use `daily-standup`.

## Response

Summarize:

- Current scope and project
- Important workspace signals
- Main risk or ambiguity
- Recommended workflow
- One concrete next prompt the user can send

## Guardrails

- Do not create or modify records during orientation.
- Do not assume status names. Read them with `list_project_statuses`.
- Ask a focused question when the desired outcome or project is unclear.
- Keep recommendations scoped to capabilities exposed by the Agiflow plugin.
