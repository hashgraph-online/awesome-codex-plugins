# Check every owner need

The JSON array in the app's `CODEX.md` fenced `needs` block is the acceptance
source. Keep every owner statement, including AI jobs, reminders, results and
handover. Each need has a unique `id`, `statement`, optional `role` and `steps`,
and nonempty `assertions`. An unavailable capability stays as a need with an
empty assertion list and a prose explanation; check reports it not met.

Run `homie-studio check <app> --url http://localhost:8787 --shots .checks` with
`homie-studio dev` running in the same studio. Headless-only needs require no
Chrome. UI steps and headless steps can be combined in one need and run in order.
Each need starts with its own saved results; records are shared across needs in
the run. The default isolated record scope is shared by browsers, MCP calls and
scheduled effects. `--no-isolate` explicitly uses existing records. Isolation is
for app records, not a sandbox for external email/SMS/payment calls: use the
service's test connection for those jobs.

## Passing assertions and capture evidence

Passing assertions mean **met**, with or without screenshots. A missing capture
never changes that verdict. For every UI surface without a capture, the result
names the surface, why it was unavailable (including the browser's error), and
tells you to rerun with `--shots .checks`. Fix the reported disk/browser error
first. Successful captures are listed in the saved needs report. Inspect them
against the owner's scene: automation proves the assertions, not visual quality.
Headless needs have no screenshots to collect.

Click, fill and select actions re-query their selector for up to ten seconds when
the browser reports a detached/stale element. A permanently unstable control
reports its surface and selector. Other action failures are not replayed: a
navigation error after dispatch does not prove that a purchase did not happen.

## Customer and staff AI calls and returned results

Headless actions require an explicit `role`, inherited from the need or overridden
on a headless step/assertion. Use an app's declared role, or `owner` for owner-only
operations. The dev-only signed identity enforces real MCP audiences and record
capabilities; a customer is not silently promoted to owner. Production OAuth
approval is unchanged. Missing dev credentials, tools or role permissions produce
plain not-met reasons.

```needs
[
  {"id":"ai-book","statement":"A customer's AI books in one call","role":"customer",
   "steps":[{"mcp":{"tool":"book","arguments":{"name":"Ada"}},"save":"booking"}],
   "assertions":[{"result":"booking","contains":{"ok":true}}]},
  {"id":"open-roles","statement":"Staff AI can ask which roles are still open","role":"staff",
   "steps":[{"mcp":{"tool":"open_roles"},"save":"open"}],
   "assertions":[{"result":"open","path":"roles","contains":["cook"]}]}
]
```

Use actual tool names, arguments and returned fields from this studio. `save`
names the returned result; duplicate names fail. `result` reads it. `path` selects
dot-separated object keys or array indexes, such as `records.0.data.name`.
`equals` compares the full selected JSON value; `contains` matches a subset of
object fields, each expected array entry against an actual entry, or a substring.
`text` checks a string for one substring or every string in an array. Use `{"$result":"booking.id"}` anywhere in a subsequent step or assertion
to refer to a saved value, without string interpolation. A missing
result/path, wrong value or malformed assertion stays not met, naming the failed
condition. Standard studio tool envelopes are unwrapped to their `data` value;
other tools retain their structured content or MCP result.

## Schedules, records and results

A `schedule` step invokes a named declared scheduled function through the local
MCP dispatcher, with a simulated timestamp in epoch milliseconds. It runs the
handler headless and reports handler failures. This is a simulated tick, not
proof that a deployed cron fired or an external message reached a person. Assert
the actual resulting record or queue entry; do not just assert the trigger's ID.
The handler still needs a declared role with the relevant record capabilities.

```needs
[
  {"id":"remind","statement":"Daily reminders queue for booked guests","role":"owner",
   "steps":[{"schedule":{"name":"reminders","at":1800000000000}}],
   "assertions":[{"role":"staff","records":{"collection":"reminders"},
                  "contains":{"records":[{"data":{"name":"Ada","state":"queued"}}]}}]},
  {"id":"results","statement":"Staff can read the completed result","role":"staff",
   "assertions":[{"records":{"collection":"results","id":"one"},
                  "contains":{"data":{"status":"complete"}}}]}
]
```

`records` uses the real `app_records` read tool, bound to this app, the named role
and this check's isolation scope. Supply collection and optional ID as accepted by that tool. Use its actual response shape (a single record versus
a list). Create fixtures with steps before asserting them; fresh runs start empty.

## Owner AI events and webhook handoff

Call `studio_events_read` to prove the feed contains the event, or use MCP Events
`events/poll` with an explicit cursor to prove event retrieval. `events/list`
checks discovery. `resources/read` also works and preserves its MCP `contents`
array. These prove the studio exposes an event to the named role; they do not
claim an external AI held a live connection or acted on it.

```needs
[
  {"id":"owner-feed","statement":"The owner's AI can read new bookings","role":"owner",
   "steps":[{"mcp":{"tool":"book","arguments":{"name":"Ada"}},"role":"customer"}],
   "assertions":[{"mcp":{"tool":"studio_events_read","arguments":{"feed":"bookings"}},
                  "contains":{"events":[{"type":"record.changed","data":{"data":{"name":"Ada"}}}]}}]},
  {"id":"mcp-events","statement":"Owner AI retrieves booking events through MCP Events","role":"owner",
   "assertions":[{"mcp":{"method":"events/poll","params":{"name":"bookings","cursor":"v1:bookings:0"}},
                  "contains":{"events":[{"name":"bookings"}]}}]},
  {"id":"webhook","statement":"The declared owner webhook accepts a signed test event","role":"owner",
   "steps":[{"mcp":{"tool":"studio_events_webhook_test","arguments":{"feed":"bookings"}},"save":"delivery"}],
   "assertions":[{"mcp":{"tool":"studio_events_webhook_status","arguments":{"feed":"bookings"}},
                  "waitMs":5000,"contains":{"deliveries":[{"event":{"$result":"delivery.id"},"state":"complete"}]}}]}
]
```

Declare the feed/audience and webhook first using the existing functions guide.
The webhook test sends an explicitly synthetic event to the declared receiver;
match the saved delivery ID to avoid mistaking an older delivery for this test.
Use `studio_events_webhook_status` for subsequent attempts and errors.
A status assertion proves the receiver's acknowledgement, not its downstream
email/SMS or AI work. Read-only MCP/records assertions make one call by default. For asynchronous
effects, set `waitMs` (0–10000) to re-read until the expected value appears.
Tool/permission errors fail immediately. Saved results are immutable and are
never retried. Never put a mutating tool in an assertion; use a step once and
assert its saved result or durable effect. Unknown methods/tools and denied feeds
fail explicitly. Secrets do not belong in the needs block.

## Handover files

```needs
[
  {"id":"handover","statement":"The owner has AI connection and reminder instructions",
   "assertions":[{"file":"HANDOVER.md","text":["/mcp","Reminders run daily"]}]}
]
```

`file` is relative to the studio root. The file must exist and be readable; `text`
checks all requested contents. Without `text` it proves only existence/readability.
Use this for handover instructions and exported text results; use `records` for
live structured results. Missing files and missing text name the exact failure.

## Keep controls connected during delayed refreshes

Never replace a button under a press. A delayed fetch can finish between pointer
down and pointer up; replacing the node cancels its click/navigation and loses
focus. Create interactive nodes once, key repeated items by stable record IDs,
and update text/attributes in place. Keep pending/disabled state deliberate.

```js
const choose = document.createElement('button');
choose.textContent = 'Choose crew';
choose.addEventListener('click', () => selectRole('crew'));
controls.append(choose);
async function refresh() {
  const { open } = await loadRoles();
  choose.textContent = `Choose crew (${open} places)`;
  // Keep this same button connected; do not replace controls.innerHTML here.
}
```

The runner can retry a detected stale handle before dispatch; it cannot infer
that an app silently cancelled a press after dispatch. Both stable DOM updates
and an assertion on the navigation's outcome are necessary.
