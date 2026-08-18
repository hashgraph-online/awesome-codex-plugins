# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 2.2.x   | Yes       |
| < 2.2   | No        |

## Reporting a Vulnerability

Report security issues **privately** — do not open a public GitHub issue for
vulnerabilities.

1. Use [GitHub Security Advisories](https://github.com/GSkuza/BABOK_ANALYST/security/advisories/new)
   for this repository, or
2. Contact the maintainer via the email listed on the [GitHub profile](https://github.com/GSkuza).

Please include:

- A clear description of the issue and affected components (plugin, MCP server, CLI, hooks)
- Steps to reproduce
- Impact assessment (data exposure, privilege escalation, remote code execution, etc.)

## What Not to Include

Do **not** attach secrets in reports or public issues:

- API keys, tokens, passwords, or `.env` contents
- Private keys (`.pem`, `id_rsa`, etc.)
- Customer or project analysis data from `projects/`
- Local keystore or encrypted credential files

## Scope

This repository ships agent instructions, hooks, skills, and the `babok-mcp` MCP
server. Runtime behavior depends on your host agent (Codex, Claude Code, Cursor,
Copilot) and its sandbox settings. Follow your organization's policies for
LLM tooling and data handling.

## Response Expectations

- Initial acknowledgment within **7 business days**
- Status update within **30 days** for confirmed issues
- Coordinated disclosure preferred; we will credit reporters unless anonymity is requested
