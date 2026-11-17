---
name: osmo-phone-calls
description: Phone call AI: make phone calls with AI. AI phone call skill: use when the user wants an AI to make a real phone call for them — call a business, shop, clinic, restaurant, helpline or one of their contacts; book, reschedule or cancel an appointment or reservation; reach customer service, get through the phone menu and wait on hold; call up to 5 numbers at once or schedule a call for later in the user's own time zone; follow each call live (a call card in apps that show cards) and bring back the answer with a summary, transcript and recording link, plus an offer to call again or schedule it. Also use to see who called the user's OsmO number, call them back, and run their AI receptionist. 50 free credits (US, Canada, UK, Australia) call businesses and toll-free numbers; calling contacts, call-backs and scheduling need an OsmO app plan. Not for SMS or email.
version: 1.2.0
metadata: {"openclaw":{"homepage":"https://getosmo.app","emoji":"📞"}}
---

# OsmO AI Phone Call

OsmO's AI makes phone calls for the user and answers calls to their own number. This skill uses
the hosted OsmO MCP server. There is no API key: the user signs in once with their phone number.

- MCP server: `https://api.getosmo.app/mcp` (Streamable HTTP, OAuth 2.1 with PKCE and dynamic
  client registration)
- New users get 50 free credits at https://getosmo.app/login (US, Canada, UK, Australia).
  With free credits, OsmO calls businesses and toll-free numbers; calling your contacts and scheduling calls need an OsmO app plan.
- Terms: https://getosmo.app/terms · Privacy: https://getosmo.app/privacy

## Connect (once)

If the `osmo` MCP tools are not available yet, tell the user to add the server and sign in.
Every client below uses the same URL and the same browser sign-in.

**Claude Code**

```sh
claude mcp add --transport http osmo https://api.getosmo.app/mcp
```

then type `/mcp` inside Claude Code and sign in.

**Codex**

```sh
codex mcp add osmo --url https://api.getosmo.app/mcp
codex mcp login osmo
```

**OpenClaw**

```sh
openclaw mcp set osmo '{"url":"https://api.getosmo.app/mcp","transport":"streamable-http","auth":"oauth"}'
openclaw mcp login osmo
```

**Hermes** (`~/.hermes/config.yaml`), then `hermes mcp login osmo`:

```yaml
mcp_servers:
  osmo:
    url: "https://api.getosmo.app/mcp"
    auth: oauth
```

Sign-in opens `https://api.getosmo.app/mcp/oauth/connect` in the browser. The user enters their
phone number and a one-time code there. Never ask for that code in chat, and never store or
repeat it.

## How to use it

1. Read the tool list the server returns and use only those tools. Call `osmo_help` when unsure
   what OsmO can do for this account.
   With free credits, OsmO calls businesses (shops, clinics, restaurants, helplines) and
   toll-free numbers; calling the user's contacts, calling back recent callers and scheduling
   calls need an OsmO app plan. If a tool says something needs the OsmO app, tell the user that
   and do not retry.
2. **Find the number; never guess it.**
   - A shop, clinic, restaurant or other place: `find_business` (what and where, in plain words).
     It returns up to 5 Google Maps listings; `place_call` can call those numbers for 24 hours.
     It does not know current opening hours, so ask on the call.
   - A company's customer care or helpline: `find_customer_care`. Call only numbers marked
     `callable`; if it answers `choose`, ask the user which company they mean.
   - A person (OsmO app plan): `find_contact` searches the call history by name and returns a
     `contactId`; if nobody matches, `search_contacts` searches the phone contacts synced from
     the OsmO app. OsmO can call saved contacts and people who called the user in the last
     30 days ("call back the person who rang this morning": `list_calls` with
     `callType: "inbound"`, then call that number).
3. **Before any call:** state who will be called (name and number) and exactly what OsmO will say
   or ask. Place the call only after the user says yes. A call reaches a real person.
   `place_call` without `confirmed: true` returns that preview and dials nothing; send
   `confirmed: true` with the same arguments only after the yes, plus the `confirmKey` the
   preview returned when it returns one. A confirmed call is placed once, even if the request is
   sent twice (a repeat answers `already_placed` with the same callId). `reason` (what OsmO says the
   call is for) is at most 300 characters; `context` (names, booking numbers, questions it uses
   without reading out) at most 700. Up to 5 numbers go in one request as `recipients`.
4. After placing a call, follow it with `get_call_status` until `resultState` is `ready`, waiting
   about `pollAfterSeconds` between checks, then report the outcome and summary.
   In some apps (Claude, ChatGPT) a status check itself waits for the call to end, so a short
   call's result can come back in the same turn. In apps that show MCP Apps cards (such as
   Claude), `place_call` and `get_call_status` also open a live OsmO call card: Confirm, the call's
   progress (placed, in call, ended), the summary, a recording player, and Call again / Schedule
   buttons; up to 5 calls placed together show as one card with a row per person.
   Do not claim something was done on the call unless the result says so.
   A ready result for a call OsmO made can carry `purposeMet`, a `nextStep` and `callAgain`
   (the same number and words): when the call did not get what was needed, offer to call again
   now or at a set time, and place it with `callAgain`'s values only after a yes.
5. **Calls for later** (OsmO app plan): pass `scheduledAt` to `place_call`, at least 2 minutes
   ahead: either the user's wall-clock time plus their IANA `timeZone` (e.g. `"2026-11-20T09:30"`
   and `"America/New_York"`, safe across daylight-saving changes) or ISO 8601 with an offset. If
   the answer is `time_zone_check`, ask the user which time they meant and send that choice.
   `list_scheduled_calls` shows calls not yet placed, each in the user's own local time;
   `cancel_scheduled_call` calls one off (preview first, then `confirmed: true` on a yes).
6. **Past calls:** `list_calls` (10 per page, newest first; `callType` for inbound or outbound,
   `cursor` for older pages). `get_call` opens one call: summary, transcript and a ▶ Play
   `recordingLink`. Show the `displayTable` or `displayCard` the tool returns as it is.
7. **OsmO app chats:** `list_chats`, then `get_chat` for one chat's messages and the calls it
   placed.
8. **Account:** `get_account_status` gives the plan and renewal or trial end, the OsmO number and
   forwarding status, and calls handled; a web account gets its call credits left instead.
   An answered call uses 3 credits; an unanswered one is free.
9. Changes to settings or screening rules: show the change first, apply only after a yes. For the
   AI receptionist side (settings, rules, bookings), see the `osmo-ai-receptionist` skill.
10. If the account has no credits or no plan, say so and pass on the link the tool result gives
   (`openInOsmoUrl`), or https://getosmo.app/app. Do not retry.

## Boundaries

- Never ask the user, or tell OsmO to ask the callee, for card numbers, bank PINs, passwords,
  one-time codes or government ID numbers.
- No harassment, spam, robocalls or calls the callee would not expect from this user.
- The skill talks only to `https://api.getosmo.app`. It runs no local code and reads no files.
