---
name: osmo-ai-receptionist
description: "AI receptionist, AI phone receptionist and AI answering service for your phone number. Use when the user wants an AI phone receptionist or answering service that picks up their calls, screens spam, takes messages and booking requests, and tells them who called and why. Manage it from the AI app: see missed calls, summaries, transcripts and recordings, pause the AI, choose who is put through, edit VIP and block lists, add rules for specific callers (put through, take a message, block), switch the assistant or its language, check bookings and Facts, and call callers back at a time in their own time zone. Works with the user's existing mobile number through call forwarding. Needs an OsmO app plan."
version: 1.2.1
metadata: {"homepage":"https://getosmo.app","emoji":"☎️"}
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
2. **"Who called?" / "What did I miss?"**: `list_calls` with `callType: "inbound"` (newest first,
   10 per page), then open the ones that matter with `get_call` for the summary, transcript and a
   ▶ Play recording link. Lead with what each caller wanted and anything urgent. To call someone
   back, now or at a time in the user's own time zone, use the `osmo-phone-calls` skill (in apps
   that show MCP Apps cards, such as Claude, the call then shows on a live OsmO call card).
3. **Receptionist settings** (`get_settings` / `update_settings`): who may be put through live
   (`transferMode`: never, contacts or anyone), pausing the AI (`isAiAnsweringPaused`), live-call
   alerts, letting saved contacts skip the AI, Android device screening, and the VIP and block
   lists. `vipList` and `blockList` each replace the whole stored list, so the update must list
   every number to keep plus the change. Show the exact change and apply it only after a yes.
4. **Assistant and language** (`get_assistant` / `update_assistant`): see which assistant answers
   and in which language, and switch to another assistant on offer or to English (`en`) or Hindi
   (`hi`). Preview first, apply on a yes. Names, the greeting and the voice are changed in the
   OsmO app, not here; say so if the user asks.
5. **Rules for callers** (put this person through, take a message from that company, block a
   number): read the current rules (`list_rules`), show the new or changed rule, apply on a yes
   (`add_rule`, `update_rule`, `delete_rule`). A rule about a person needs that person tagged in
   `mentions` with their full number: look them up with `find_contact` (call history), then
   `search_contacts` (phone contacts). To switch a rule off but keep it, set `isActive: false`.
6. **Bookings**: `list_bookings` shows bookings the receptionist took or cancelled for callers;
   `tense: "upcoming"` for slots still ahead, `"past"` for past slots and cancellations.
7. **What the receptionist knows**: `get_facts` shows the business details, website and documents
   it answers callers from. `get_connections` shows whether Google Calendar, Calendly and Google
   Drive are linked. Both are read-only: Facts and connections are changed in the OsmO app.
8. **Not answering yet?** If the account has no recent calls, check the plan and forwarding with
   `get_account_status`, then get the user's carrier forwarding codes from `osmo_support`
   (topic `forwarding`). Do not guess carrier codes.

## Boundaries

- Never ask for card numbers, bank PINs, passwords, one-time codes or government ID numbers.
- Show call details only to the signed-in account owner. Do not read out other people's numbers
  beyond what the tool returns.
- The skill talks only to `https://api.getosmo.app`. It runs no local code and reads no files.
