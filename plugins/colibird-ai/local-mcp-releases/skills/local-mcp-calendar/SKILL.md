---
name: local-mcp-calendar
description: Use when the user wants to check their calendar, find availability, or create/update/delete events in Apple Calendar on macOS. Powered by LMCP's Calendar tools, which are macOS-only.
---

# Calendar & scheduling via LMCP

LMCP reads and writes the Mac's Calendar app (Calendar.app: local, iCloud and other accounts added
to it). These tools exist only on macOS; for a Microsoft 365 calendar, use `m365_list_events` /
`m365_create_event` (macOS and Windows, require `connect_m365_account`).

## Core tools
- `list_calendar_names` — the user's calendars (Personal, Work, …).
- `list_calendar_events` — events in a date range (defaults to today + 7 days); pass `event_id` to read one event in full.
- `create_calendar_event` — new event (title, start, end, optional location/notes/calendar).
- `update_calendar_event` / `delete_calendar_event` — modify or remove an event by `event_id`; both take `confirm` and require the user's approval before applying.

## Good practice
- For "am I free Tuesday?", list events for that day and report gaps.
- Always confirm the calendar + exact times before creating.
- Use ISO datetimes (e.g. `2026-07-01T10:00:00`).
- Destructive ops (update/delete) are confirm-gated — show the user what will change, get approval, then call with `confirm=true`.
