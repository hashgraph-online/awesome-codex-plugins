# Security policy

## Reporting a vulnerability

Please email **security@sofya.co** with a description of the issue and steps to reproduce it. Don't open a public GitHub issue for security problems.

We reply within 3 business days and keep you updated until it is fixed. Please give us a reasonable time to fix the issue before disclosing it.

## Scope

- This repository: the local MCP server (`src/`), the plugin and skill files, and the manifests.
- The hosted MCP server at `https://mcp.sofya.co/mcp` and the Sofya API at `https://sofya.co`.

## What this repository does with credentials

The plugin and the skills contain no API keys. Users sign in with OAuth, or supply their own `SOFYA_API_KEY`, which is sent only to Sofya's own API and MCP server.
