# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this plugin bundle or in the
droplinked MCP server it wraps, please report it privately. Do **not** open a
public issue for security matters.

- **Email:** [support@droplinked.com](mailto:support@droplinked.com)
- **Subject:** `SECURITY: droplinked-codex-plugin`

Please include:

- A description of the issue and its potential impact.
- Steps to reproduce (proof-of-concept if available).
- Any relevant logs, requests, or configuration (with secrets redacted).

## Response SLA

| Stage                | Target                          |
| -------------------- | ------------------------------- |
| Acknowledgement      | Within 3 business days          |
| Initial assessment   | Within 7 business days          |
| Fix or mitigation    | Prioritized by severity         |
| Public disclosure    | Coordinated after a fix ships   |

We will keep you informed throughout the process and credit you in the release
notes if you would like acknowledgement.

## Supported Versions

This bundle is versioned with the plugin manifest
(`.codex-plugin/plugin.json`). Only the latest published minor version receives
security fixes.

| Version | Supported |
| ------- | --------- |
| 0.1.x   | ✅        |
| < 0.1   | ❌        |

## Handling of credentials

This plugin ships **no bundled credentials**. Read-only tools are public and
need no key; the droplinked MCP endpoint requires an `X-MCP-API-Key` only for
write tools, sourced at runtime from the `DROPLINKED_MCP_API_KEY` environment
variable. `.mcp.json` contains only an environment-variable placeholder. Never
commit a real API key to a fork of this repo. If a key is exposed, rotate it via
droplinked and update your environment.

## Scope

This repository is a thin configuration + skill bundle. It ships **no
executable code and no bundled credentials**. It configures a connection to
droplinked's hosted MCP server over an HTTPS streamable-HTTP endpoint
(`https://mcp.droplinked.com/mcp`). Vulnerabilities in the hosted service itself
are handled through the same contact above.
