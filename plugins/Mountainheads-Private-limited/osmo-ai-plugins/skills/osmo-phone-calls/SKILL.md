---
name: osmo-phone-calls
description: AI phone call skill. Use when the user wants an AI to make a real phone call for them — call a business, shop, clinic, restaurant, helpline or a person they know; book, reschedule or cancel an appointment or reservation; reach customer service and get through the phone menu; ask a question and bring back the answer with a summary. Also use to see who called the user's OsmO number, what they wanted, and to change OsmO call screening rules. Free to start in the US, Canada, UK and Australia, where free credits call businesses and toll-free numbers; calling contacts and scheduling need an OsmO app plan. Not for SMS or email.
version: 1.0.2
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
   toll-free numbers; calling the user's contacts and scheduling calls need an OsmO app plan. Use
   `find_business` or `find_customer_care` to get a business number; do not guess numbers.
   If a tool says something needs the OsmO app, tell the user that and do not retry.
2. **Before any call:** state who will be called (name and number) and exactly what OsmO will say
   or ask. Place the call only after the user says yes. A call reaches a real person.
3. After placing a call, check its status with the status tool and report the outcome and summary.
   Do not claim something was done on the call unless the result says so.
4. Changes to settings or screening rules: show the change first, apply only after a yes.
5. If the account has no credits or no plan, say so and pass on the link the tool result gives
   (`openInOsmoUrl`), or https://getosmo.app/app. Do not retry.

## Boundaries

- Never ask the user, or tell OsmO to ask the callee, for card numbers, bank PINs, passwords,
  one-time codes or government ID numbers.
- No harassment, spam, robocalls or calls the callee would not expect from this user.
- The skill talks only to `https://api.getosmo.app`. It runs no local code and reads no files.
