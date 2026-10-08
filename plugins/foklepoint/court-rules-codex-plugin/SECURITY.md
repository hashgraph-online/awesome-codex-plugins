# Security Policy

## Supported versions

| Version | Supported |
| --- | --- |
| Latest release of this plugin | yes |
| Older tagged releases | no |

## Reporting a vulnerability

Report security issues in this plugin, its skill, or the hosted Court Rules MCP server privately. Do not open a public issue for a vulnerability.

- Email: api@courtrules.app
- Start the subject line with "SECURITY" so it is routed quickly.

Include the affected component (plugin, skill, or hosted server), steps to reproduce, and the impact you saw. We aim to acknowledge a report within 3 business days and to keep you updated while we investigate.

## Scope

This plugin contains no executable code. It ships a skill file and an MCP client configuration that points at `https://mcp.courtrules.app/mcp`. The server is read-only: every tool only reads court rules, court holidays and enforcement data. The plugin stores no credentials. Sign-in runs through the MCP client (OAuth 2.1); an API key, when used, is held by the client's own configuration.

## Disclosure

We follow coordinated disclosure. Please give us a reasonable window to ship a fix before any public write-up, and we credit reporters who want it.
