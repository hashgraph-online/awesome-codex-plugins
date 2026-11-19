---
name: osmo-customer-service-calls
description: "Customer service calls made for you: OsmO's AI finds a company's customer care or helpline number, calls it, gets through the phone menu, waits on hold in the queue, and asks your question or passes your message, so you skip the hold. Use when the user wants to call customer service or customer care at a bank, airline, mobile carrier, insurer, utility or delivery company — ask about a refund, an order, a bill, a booking or an account question — and get the answer back with a summary, transcript and recording link. Every call is previewed and placed only after the user says yes. 50 free credits (US, Canada, UK, Australia) call businesses and toll-free numbers; scheduling a call for later needs an OsmO app plan."
version: 1.0.0
metadata: {"openclaw":{"homepage":"https://getosmo.app","emoji":"🎧"}}
---

# OsmO Customer Service Calls

OsmO's AI calls a company's customer care line for the user, gets through the phone menu, waits on
hold and asks what the user needs, then reports what it heard. This skill uses the hosted OsmO MCP
server. There is no API key: the user signs in once with their phone number.

- MCP server: `https://api.getosmo.app/mcp` (Streamable HTTP, OAuth 2.1 with PKCE and dynamic
  client registration)
- New users get 50 free credits at https://getosmo.app/login (US, Canada, UK, Australia). An
  answered call uses 3 credits; an unanswered one is free.
- For other calls (shops, contacts, call-backs): the `osmo-phone-calls` skill.
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
2. **Find the number; never guess it.** `find_customer_care` with the company's name. Call only
   numbers marked `callable`. If it answers `choose`, ask the user which company they mean; if
   `not_found`, say so and ask whether the user has the number from the company's own site or app.
3. **Agree on the ask.** Before the call, state the company, the number and exactly what OsmO will
   ask (`reason`, up to 300 characters, e.g. "ask for the status of refund for order 4417"). Put
   details OsmO may need but should not read out (order number, booking reference, the name on
   the account) in `context` (up to 700 characters). Never include card numbers, PINs, passwords,
   one-time codes or government ID numbers, and tell the user OsmO will not give them out on the
   call.
4. **Place the call only after a yes.** `place_call` without `confirmed: true` returns a preview and
   dials nothing; send `confirmed: true` with the same arguments (and the `confirmKey` the preview
   returned, when it returns one) only after the user agrees.
5. **Follow it.** Hold queues can be long. Poll `get_call_status` about every `pollAfterSeconds`
   until `resultState` is `ready`. In apps that show MCP Apps cards (such as Claude) a live OsmO
   call card shows the call's progress. Report only what the result says: the outcome, the
   summary and anything the agent asked for. Do not claim something was done unless the result
   says so.
6. **Not solved?** A ready result can carry `purposeMet`, a `nextStep` and `callAgain`. Offer to call
   again now or at a set time (scheduling needs an OsmO app plan: `scheduledAt` plus the user's
   IANA `timeZone`), and place it with `callAgain`'s values only after a yes.
7. Past calls: `list_calls` with `callType: "outbound"`, then `get_call` for the transcript and the
   ▶ Play recording link.
8. If the account has no credits left, say so and pass on the link the tool gives
   (`openInOsmoUrl`) or https://getosmo.app/app. Do not retry.

## Boundaries

- OsmO's assistant is an AI. Do not tell anyone it is a person.
- Not for emergency services. No harassment, spam or robocalls.
- The skill talks only to `https://api.getosmo.app`. It runs no local code and reads no files.
