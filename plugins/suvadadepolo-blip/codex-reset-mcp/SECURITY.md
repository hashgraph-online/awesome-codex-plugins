# Security policy

## What this repository contains

Client configuration and directory metadata for the hosted Codex Reset MCP server at `https://codex-reset.com/mcp`. It holds no executable code, no dependencies, no secrets and no install scripts. The plugin points a client at a read-only HTTPS endpoint and nothing else.

The server exposes three read-only tools. They take no credentials, write nothing, and read the same public data as `https://codex-reset.com/api/*`.

## Reporting a vulnerability

Email **hello@codex-reset.com** with the subject `security:` and a description of the problem and how to reproduce it. Please do not open a public issue for a security report.

We aim to acknowledge reports within 3 business days. Fixes to the hosted server ship without any client update.

## Supported versions

Only the latest release of this repository and the live endpoint are supported.
