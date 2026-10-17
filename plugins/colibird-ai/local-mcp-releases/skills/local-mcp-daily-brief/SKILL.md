---
name: local-mcp-daily-brief
description: Use when the user asks "what's on my plate today", "catch me up", "morning brief", or wants a summary of their day across calendar, reminders and email. The single most common multi-step automation. Powered by LMCP on macOS and Windows.
---

# Daily brief / morning catch-up

This is the #1 cross-domain workflow LMCP users run: a quick "what do I need to know today"
across calendar, reminders and email, read from the user's own apps.

> Start here: `daily_brief` exists on **macOS and Windows** and bundles today's calendar, tasks
> and email in one call. Use the steps below to fill gaps or go deeper.

## The flow on macOS (do these, then synthesize one short summary)
1. `get_datetime` — anchor to the user's current date/time (macOS and Windows).
2. `list_calendar_events` for today (and optionally tomorrow) — meetings, with times and gaps.
3. `list_reminders` — what's due/overdue.
4. `list_emails` (pass `account=` when Mail has several accounts) — recent/unread that may need
   attention; skip newsletters and noise.

Steps 2–4 use Apple Calendar, Reminders and Mail, so they exist only on macOS. On Windows, rely
on `daily_brief`.

## Output
Give a tight, scannable brief, not raw dumps:
- **Today:** N meetings (next at HH:MM — title), free blocks.
- **Due:** the 1–3 reminders that matter today.
- **Inbox:** 2–4 emails worth a reply, one line each (who + what they want).
- End with a suggested next action ("Want me to draft a reply to X, or block focus time?").

## Good practice
- Lead with what's time-sensitive (next meeting, overdue items).
- Don't list everything — curate. The value is triage, not a data dump.
- Offer to act (draft a reply, create an event/reminder) — that's usually the user's next step.
