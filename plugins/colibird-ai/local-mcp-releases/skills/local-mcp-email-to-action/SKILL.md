---
name: local-mcp-email-to-action
description: Use when the user wants to deal with their inbox — find what needs a response, draft replies, and turn emails into calendar events or reminders. Captures the common email→read→reply→schedule workflow on macOS (Apple Mail, Calendar, Reminders). Powered by LMCP.
---

# Inbox to action

Telemetry shows users don't just read email — they turn it into action: read → reply → schedule
a meeting or create a reminder. This skill codifies that end-to-end flow. Every tool below works with Apple Mail, Calendar and
Reminders, so the flow runs only on macOS.

## The flow
1. **Surface what needs attention** — `search_emails`/`list_emails` (pass `account=` to stay fast),
   then `read_email` on the ones that matter. Summarize: who, what they want, urgency.
2. **Reply** — `create_draft` (with `reply_to_message_id` for replies). Compose the draft; the
   user reviews and sends it. **Never auto-send.**
3. **Turn the email into action when it implies one:**
   - A meeting request → `create_calendar_event` (confirm calendar + exact times first).
   - A task/follow-up → `create_reminder` (with a due date if the email implies one).

## Good practice
- Batch: skim the inbox, group into "needs reply", "schedule this", "just FYI".
- For each "needs reply", draft a concise response in the user's voice; show it before saving.
- When an email says "let's meet Tuesday", propose a concrete slot (check `list_calendar_events`
  for conflicts) and create the event on confirmation.
- Destructive/outgoing steps are preview-first: show the draft / the event, confirm, then apply.
- Keep the user in control — propose, don't auto-execute sends or deletes.
