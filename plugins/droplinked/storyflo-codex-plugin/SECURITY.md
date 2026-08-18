# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this plugin bundle or in the
storyflo MCP server it wraps, please report it privately. Do **not** open a
public issue for security matters.

- **Email:** [story@storyflo.com](mailto:story@storyflo.com)
- **Subject:** `SECURITY: storyflo-codex-plugin`

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

## Scope

This repository is a thin configuration + skill bundle. It ships **no
executable code and no bundled credentials**. It configures a connection to
storyflo's hosted MCP server over an HTTPS Server-Sent Events endpoint
(`https://api.storyflo.com/v1/mcp/sse`). Vulnerabilities in the hosted service
itself are handled through the same contact above.
