---
name: osmo-book-by-phone
description: "Book by phone with AI: OsmO's AI calls restaurants, salons, clinics, dentists, garages and other local businesses to make a reservation or book an appointment for you, or to reschedule or cancel one. Use when the user wants a table booked, an appointment made or moved, or a quick question asked by phone (opening hours, prices, stock, an order). OsmO finds the business's number on Google Maps, previews the call, calls only after the user says yes, and brings back whether it was booked, with a summary, transcript and recording link. Up to 5 places can be called at once to find a free slot. 50 free credits (US, Canada, UK, Australia) call businesses; scheduling a call for later needs an OsmO app plan."
version: 1.0.1
metadata: {"homepage":"https://getosmo.app","emoji":"📅"}
---

# OsmO Book by Phone

OsmO's AI phones a business for the user to book, reschedule or cancel a reservation or
appointment, and reports what the business said. This skill uses the hosted OsmO MCP server.
There is no API key: the user signs in once with their phone number.

- MCP server: `https://api.getosmo.app/mcp` (Streamable HTTP, OAuth 2.1 with PKCE and dynamic
  client registration)
- New users get 50 free credits at https://getosmo.app/login (US, Canada, UK, Australia). An
  answered call uses 3 credits; an unanswered one is free.
- For company helplines: the `osmo-customer-service-calls` skill. For contacts and call-backs: the
  `osmo-phone-calls` skill.
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
2. **Find the place; never guess the number.** `find_business` with what and where in plain words
   ("Italian restaurant near Union Square", "dentist in Austin"). It returns up to 5 Google Maps
   listings; `place_call` can call those numbers for 24 hours. It does not know current opening
   hours or free slots, so OsmO asks on the call.
3. **Agree on the booking.** Before calling, state the business, the number and exactly what OsmO
   will ask: date, time and a fallback window, party size or service, and the name for the booking.
   `reason` (up to 300 characters) is what OsmO says the call is for; `context` (up to 700) holds
   details it uses without reading them out (a booking reference to move, a phone number to leave).
   Never include card numbers or other payment details. If the result says the business wants a
   card or a deposit, tell the user; they arrange that themselves.
4. **Place the call only after a yes.** `place_call` without `confirmed: true` returns a preview and
   dials nothing; send `confirmed: true` with the same arguments (and the `confirmKey` the preview
   returned, when it returns one) only after the user agrees. To find a slot faster, up to 5
   places can go in one request as `recipients`.
5. **Report the outcome.** Poll `get_call_status` about every `pollAfterSeconds` until
   `resultState` is `ready` (in apps that show MCP Apps cards, such as Claude, a live OsmO call card
   follows the call). Say plainly whether it was booked, for when, and under what name, only as the
   result says. Do not add it to a calendar or claim a confirmation the business did not give.
6. **Not booked?** When the result offers `callAgain` or a `nextStep` (call back after 5, try
   another day), offer to call again now or at a set time (scheduling needs an OsmO app plan:
   `scheduledAt` plus the user's IANA `timeZone`), or try the next place from `find_business`,
   only after a yes.
7. If the account has no credits left, say so and pass on the link the tool gives
   (`openInOsmoUrl`) or https://getosmo.app/app. Do not retry.

## Boundaries

- OsmO's assistant is an AI. Do not tell anyone it is a person.
- No spam, robocalls or calls the business would not expect from this user.
- The skill talks only to `https://api.getosmo.app`. It runs no local code and reads no files.
