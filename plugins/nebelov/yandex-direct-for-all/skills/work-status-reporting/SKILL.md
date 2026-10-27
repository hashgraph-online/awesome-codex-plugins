---
name: work-status-reporting
description: Use when preparing, reviewing, or correcting weekly, daily, periodic, or client-facing work status reports where finished work, moderation, diagnosis-only progress, unverified repairs, automation/system activity, and in-progress items must not be double-counted or overstated.
---

# Work Status Reporting

Use this skill for weekly or periodic status reports, especially when the user
needs a truthful summary of many operational tasks, campaigns, automations, or
client deliverables.

## Status Separation

Before writing the report, classify each item by evidence-backed state:

- `finished`: the requested user-visible result was completed and verified;
- `waiting_external`: submitted, sent, or in moderation, but not yet accepted or
  live;
- `diagnosis_only`: investigation or root-cause work happened without a verified
  repair;
- `repair_unverified`: a fix was applied but the user-visible path was not
  proven end to end;
- `in_progress`: active work remains inside the requested scope;
- `blocked`: a concrete blocker prevents completion.

Do not call a campaign launched when the evidence shows only draft, moderation,
or another pre-launch state. Do not call a repair complete when only logs,
transport success, code inspection, or a partial internal check exists.

## Counting Rules

- Count deliverables once at the user-facing unit of work, not once per
  automation, reviewer, subtask, retry, or internal artifact.
- Separate automation/system maintenance from client-visible deliverables unless
  the report intentionally has an internal operations section.
- Keep diagnosis, implementation, review, and publication as separate phases
  when they are not all complete.
- If the same event appears in multiple notes, merge it and retain the most
  conservative current status.

## Review Checklist

Before finalizing:

1. Compare the report against source evidence for premature completion claims.
2. Check for duplicated counts caused by automation runs, subagents, review
   passes, dry-runs, or repeated summaries.
3. Preserve reviewer corrections about unfinished states, moderation, missing
   end-to-end proof, or ambiguous metrics.
4. State remaining work plainly instead of hiding it in a positive summary.
