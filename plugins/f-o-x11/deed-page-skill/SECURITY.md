# Security

## Reporting a vulnerability

Email ops@avatar33.com with a description, steps to reproduce, and the affected URL or file. Please do not open a public issue for a security report.

Report abusive or phishing sites hosted on deed.page at https://deed.page/abuse.

## What this plugin does

This repository contains instructions and configuration only. It ships no executable code, install scripts, or hooks.

- `skills/deed-page/SKILL.md` tells the agent to run `curl` (and `tar` for folders) against `https://deed.page/v1/sites` when the user asks to publish something.
- `mcp.json` and `.mcp.json` point to the hosted deed.page MCP server at `https://deed.page/mcp`.

## Network endpoints

| Endpoint | Used for |
| --- | --- |
| `https://deed.page/v1/sites` | Publish, update, and delete sites (skill) |
| `https://deed.page/mcp` | Hosted MCP server (Streamable HTTP) |
| `https://<slug>.deed.page/` | The published site |

No other hosts are contacted.

## Credentials

- No account or API key is needed to publish.
- The first publish without a token returns a site token (`deed_tok_...`) once. The skill saves it to `~/.config/deed-page/token` (file mode 600, directory mode 700), writes that file only when a response contains a non-empty token, and loads it from `DEEDPAGE_TOKEN` or that file before every publish. It sends the token only to `https://deed.page` as `Authorization: Bearer`, to keep all sites under one owner and to update or delete them. It is never written to a published page, a commit, or a log.
- deed.page stores only a SHA-256 hash of the token.

## Data

Published sites are public. Do not publish secrets or private data. See the privacy policy at https://deed.page/privacy.
