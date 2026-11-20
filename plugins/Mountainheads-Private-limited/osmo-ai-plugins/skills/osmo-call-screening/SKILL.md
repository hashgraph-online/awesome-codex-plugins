---
name: osmo-call-screening
description: "Call screening AI for your own phone number: OsmO's AI answers the calls you forward to it, screens spam calls and robocalls, takes the message instead of voicemail, and tells you who called and why. Use when the user wants to screen calls, stop answering spam calls, see missed calls, read a caller's message, or block or let through specific numbers. From the AI app: list missed and screened calls with summaries, transcripts and recordings, edit the block list and VIP list, add rules for a caller (put through, take a message, block), pause the AI, choose who is put through live, and call a caller back. Works with the user's existing mobile number through call forwarding. Needs an OsmO app plan."
version: 1.0.1
metadata: {"homepage":"https://getosmo.app","emoji":"🛡️"}
---

# OsmO Call Screening

OsmO answers calls to the user's own mobile number once the user forwards calls to it (for example
when busy, unanswered or unreachable). Its AI talks to each caller, screens spam, takes the
message, follows the user's rules and sends a summary. This skill lets the user check and control
that screening from their AI app through the hosted OsmO MCP server.

- MCP server: `https://api.getosmo.app/mcp` (Streamable HTTP, OAuth 2.1; no API key)
- Setup: install the OsmO app (https://getosmo.app/app), choose a plan, and turn on call forwarding.
  Calls are screened only once forwarding is on. On Android the OsmO app can also screen calls on
  the device (`deviceScreeningMode`).
- Business owners who want OsmO as a front desk: use the `osmo-ai-receptionist` skill. To place
  outgoing calls: the `osmo-phone-calls` skill.
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
2. **"Who called?" / "Any missed calls?" / "Was that spam?"**: `list_calls` with
   `callType: "inbound"` (newest first, 10 per page; `cursor` for older pages). Show the
   `displayTable` it returns. Open a call with `get_call` for the summary, transcript and the
   ▶ Play recording link. Lead with real callers and anything urgent; group the calls the summary
   marks as spam or sales.
3. **Block or let through numbers** (`get_settings` / `update_settings`): `blockList` and `vipList`
   each replace the whole stored list, so the update must list every number to keep plus the
   change. Show the exact numbers added and removed, and apply only after a yes.
4. **Rules for one caller or company** (always put my doctor through, take a message from the
   delivery company, block this number): read `list_rules`, show the new or changed rule, apply on
   a yes with `add_rule`, `update_rule` or `delete_rule`. A rule about a person needs that person
   in `mentions` with their full number: look them up with `find_contact`, then `search_contacts`.
5. **How screening behaves** (`get_settings` / `update_settings`): who may be put through live
   (`transferMode`: never, contacts or anyone), letting saved contacts skip the AI
   (`skipAllContacts`), live-call alerts, Android device screening, and pausing the AI
   (`isAiAnsweringPaused`). Preview first, apply on a yes.
6. **Call someone back**: hand over to the `osmo-phone-calls` skill (`place_call` with a preview and
   the user's yes first). OsmO can call people who called the user in the last 30 days.
7. **Nothing being screened?** Check the plan and forwarding with `get_account_status`, then get the
   user's carrier forwarding codes from `osmo_support` (topic `forwarding`). Do not guess carrier
   codes.

## Boundaries

- Never ask for card numbers, bank PINs, passwords, one-time codes or government ID numbers.
- OsmO's assistant is an AI. Do not describe it to anyone as a person.
- Show call details only to the signed-in account owner. Do not read out other people's numbers
  beyond what the tool returns.
- The skill talks only to `https://api.getosmo.app`. It runs no local code and reads no files.
