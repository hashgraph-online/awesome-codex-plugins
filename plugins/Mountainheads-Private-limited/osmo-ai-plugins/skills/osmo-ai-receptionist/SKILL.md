---
name: osmo-ai-receptionist
description: AI receptionist and AI phone receptionist for your phone number. Use when the user wants an AI phone receptionist or answering service that picks up their calls, screens spam, takes messages and booking requests, and tells them who called and why. Manage it from the AI app: see missed calls and summaries, open a call, change the greeting, add rules for specific callers (put through, take a message, block), and check bookings. Works with the user's existing mobile number through call forwarding. Needs an OsmO app plan.
version: 1.0.1
metadata: {"openclaw":{"homepage":"https://getosmo.app","emoji":"☎️"}}
---

# OsmO AI Receptionist

OsmO answers calls to the user's own phone number. Its AI receptionist talks to each caller, screens
spam, takes the message or booking request, follows the user's rules, and sends a summary. This skill
lets the user run that receptionist from their AI app through the hosted OsmO MCP server.

- MCP server: `https://api.getosmo.app/mcp` (Streamable HTTP, OAuth 2.1; no API key)
- Setup: install the OsmO app (https://getosmo.app/app), choose a plan, and turn on call forwarding
  on the user's number. The receptionist only answers calls once forwarding is on.
- To place outgoing calls instead, use the `osmo-phone-calls` skill.
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

1. Read the tool list the server returns and use only those tools. Call `osmo_help` when unsure what
   this account can do.
2. **"Who called?" / "What did I miss?"**: list recent calls, then open the ones that matter with
   `get_call`. Lead with what each caller wanted and anything urgent.
3. **Greeting and receptionist settings**: read them first (`get_assistant`, `get_settings`), show the
   exact change, and apply it only after the user says yes.
4. **Rules for callers** (put this person through, take a message from that company, block a
   number): read the current rules (`list_rules`), show the new or changed rule, apply on a yes.
5. **Bookings**: `list_bookings` shows booking requests callers left.
6. **Not answering yet?** If the account has no recent calls, check the plan with
   `get_account_status`, then get the user's carrier forwarding codes from `osmo_support`
   (topic `forwarding`). Do not guess carrier codes.

## Boundaries

- Never ask for card numbers, bank PINs, passwords, one-time codes or government ID numbers.
- Show call details only to the signed-in account owner. Do not read out other people's numbers
  beyond what the tool returns.
- The skill talks only to `https://api.getosmo.app`. It runs no local code and reads no files.
