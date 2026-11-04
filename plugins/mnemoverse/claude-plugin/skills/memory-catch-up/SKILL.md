---
name: memory-catch-up
description: "Catches up after a break by listing what was added to long-term Mnemoverse memory since a given time, newest first, in personal memory or in a shared room (beta). Use when the user returns to a project and asks \"where were we\", \"what happened since\", \"catch me up\", or \"any new messages in the room\", or at the start of a session that continues earlier work."
---

# Catch up on what changed

## Check first

Look for the tool `memory_list_recent`. If it is missing, memory is not connected: say so in one sentence and use the bundled `setup` skill if it is installed, otherwise https://mnemoverse.com/docs/api/install-by-host.

## Why a list, not a search

A search answers "what do I know about X". Catching up asks "what happened lately", and that needs the newest entries in order, without a query. `memory_list_recent` returns them newest first, and within one scope it skips nothing.

## How to catch up

1. **Choose the scope.** Personal memory needs no `domain`. A shared room (beta) is a separate store: pass its address as `domain`, or a room is never covered. If the room's address is not at hand, `memory_list_rooms` lists the rooms the user owns or has joined, with their addresses.
2. **Set the starting point.** Pass `since` with the time the user last looked, as an ISO 8601 instant. If the user does not know, use the start of the last working day and say so.
3. **Read to the end.** A page can be shorter than `limit` when entries are long, and then it returns a cursor. Follow the cursor until the page says the feed has ended ("end of feed"); a short page that still carries a cursor is not the end, and neither is a page that says more entries exist but shows no cursor: then narrow the window with `since` and `until` and list again. Stopping at the first page reads as "nothing else happened" when it did.
4. **Several scopes.** For personal memory and a room (beta), run one listing per scope. They are not merged.

## How to report

- Lead with what needs the user: questions addressed to them, decisions waiting for them, anything with a date that has passed.
- Then what was decided or changed, one line each, with who wrote it and when if that is recorded.
- Say which scopes and which time window were read, so the user knows what the summary covers.
- If nothing came back, say "nothing new since <time> in <scope>", not just "nothing new".
