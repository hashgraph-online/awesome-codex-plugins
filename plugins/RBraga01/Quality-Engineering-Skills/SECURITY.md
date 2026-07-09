# Security Policy

## Scope

Quality-Engineering-Skills is a **content-only repository** — it contains structured markdown skill files and agent instructions. There is no executable code, no server, no user data collection, and no authentication system.

## What this repository contains

- SKILL.md files: structured methodology instructions for AI agents
- Reference files: quality engineering tables, templates, checklists
- Platform connectors: configuration files for AI platforms (ChatGPT, Claude, Teams, Slack, Gemini)

## Reporting a vulnerability

If you identify a security concern — for example:

- A platform connector that could be misused to exfiltrate data
- A SKILL.md instruction that could cause an AI to produce harmful outputs
- A credential or sensitive value accidentally committed

Please open a GitHub Issue with the label **`security`**. Do not include credentials or sensitive details in the issue body — describe the concern and we will follow up privately.

There is no bug bounty programme for this project.

## API key management

All platform connectors that require API keys (Slack signing secret, Cloudflare Worker tokens) document them as environment variables. No API keys or tokens are committed to this repository.

If you find a token or credential accidentally committed, please report it immediately via a `security`-labelled issue.
