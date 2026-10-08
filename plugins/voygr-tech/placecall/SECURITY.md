# Security

## Reporting a vulnerability

Email **support@voygr.tech** with "Security" in the subject. Include what you
found, how to reproduce it, and which file or endpoint it affects. Please do
not open a public issue for anything that could put users, their keys or the
people they call at risk.

## What this repository does on the network

This repository holds instructions and manifests only: a skill (`SKILL.md`),
an `AGENTS.md` reference, plugin and extension manifests, and `install.sh`,
which copies one file and makes no network calls. Nothing here runs on its own.

When an agent follows the skill, it sends HTTPS requests with `curl` to one
host, **`api.voygr.tech`**, and nowhere else. The Cursor plugin and the Gemini
CLI extension also connect to the PlaceCall MCP server on that same host
(`https://api.voygr.tech/mcp`). Your `PLACECALL_API_KEY` is sent only to
`api.voygr.tech`, in the `X-API-Key` header. The README's
[Network access](./README.md#network-access) section lists every endpoint and
what each request carries.

## Handling your key

- Keep the key in an environment variable, your agent's secure settings, or a
  file only you can read. Never paste it into a chat or commit it.
- The skill tells the agent never to print the key and never to search your
  disk for credential files.
- If a key is exposed, email support@voygr.tech. A lost key is replaced at
  <https://api.voygr.tech/recover>.
