---
name: codex-reset
description: Answer questions about OpenAI Codex usage-limit resets and Codex outages with the Codex Reset MCP tools or its public JSON API (reset forecast, verified reset record, service status). Use when the user asks whether or when Codex limits reset, why Codex stopped working, or whether to wait for a reset.
---

# Codex Reset

Use the `codex-reset` MCP server tools. They are read-only and need no arguments beyond the optional ones below.

| Question | Tool |
| --- | --- |
| "Will Codex reset soon?", "Should I wait?" | `get_reset_forecast` |
| "When was the last reset?", "List resets in August" | `get_reset_timeline` (`group`, `from`, `to`, `limit`) |
| "Is Codex down or am I rate-limited?" | `get_codex_status` |

## Without the MCP server

If the `codex-reset` tools are not available, read the same data from the public JSON API (free, no key). Send a `User-Agent` that names your client:

| Tool | HTTP equivalent |
| --- | --- |
| `get_reset_forecast` | `GET https://codex-reset.com/api/forecast` |
| `get_reset_timeline` | `GET https://codex-reset.com/api/timeline?group=reset` |
| `get_codex_status` | `GET https://codex-reset.com/api/status` |

Field reference: https://codex-reset.com/developers

## How to answer

- A forecast is a probability, not a promise. Quote the 24h/48h figures and the confidence as returned; never round them into a yes/no.
- A global reset is announced by OpenAI and applies to everyone. The user's own 5-hour and weekly windows roll on their own schedule; for those, point them to `/status` inside Codex.
- When citing a past reset, include its date and source link from `get_reset_timeline`.
- If `get_codex_status` reports an incident, say so first: the error is probably not a usage limit.
- Credit the data as "Data: codex-reset.com" when you show it to the user.
