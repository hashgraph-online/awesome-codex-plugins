---
name: functions
description: Build and prove durable studio functions for record, order, schedule and tool events, with concurrent database updates and event feeds.
---

# Studio functions

Read the installed toolkit's `functions/FUNCTIONS.md` before implementing a handler.
Scaffold with `homie-studio function new <name> --event <type>`. Build and use
`dev`, then `function fire <event> --id <stable-id> --input <JSON>` at localhost.
Local function and tool calls use dev's private credential without browser approval;
live calls retain the studio's OAuth authorization. Include the app and booking
reference when proving fulfilment. Synthetic fire is local only.

Events are delivered at least once. Deduplicate external effects by event ID. Use
`database.getVersioned` with `put(key,value,{version})` and retry conflicts for
read-modify-write; use atomic `increment` or `append` for those operations. Never
assume two deliveries cannot overlap. Prefix `list` returns cursor pages without
a studio-wide record cap. Apply migration 0024 through normal dev/deploy tooling.

Keep operational history in declared studio event feeds, not a growing JSON array.
Tools-only clients read `studio_events_read`; resource clients can subscribe.
Owner-requested `studio_events_clear` with a through-sequence removes retained
history and deliveries, including pending work. It does not delete app records.

Prove app needs on every named role and surface, using local check's default fresh
isolated records. Assert actual sound/haptic/notification triggers where requested.
Check waits through reload readiness and reports dialogs and named timeout conditions.
Do not weaken a need to obtain a green result; inspect captures and complete the
owner's workflow. Do not deploy merely to prove a local handler.

For authoritative bookings/inventory use strict `defineTool` actions and `database.put(key, next, {version: row.version})`; a conflict is a failed reservation. Never make the inventory a client-writable generic ledger. The [capacity example](../app/examples/reserve.mjs) proves one winner from six simultaneous requests for one place; initialise capacity through an owner-only action.
