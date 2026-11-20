# Security policy

This repository holds the client setup files for the hosted Wavegrain MCP server at `https://wavegrain.com/api/mcp`.
It contains no server code and no secrets.

## Reporting a vulnerability

Email support@wavegrain.com with the subject "Security".
Describe the issue and how to reproduce it.
Please do not open a public issue for a vulnerability.

## Scope

- The files in this repository (`plugin.json`, `mcp.json`, `.mcp.json`, `server.json`, `gemini-extension.json`, `skills/`).
- The hosted MCP server and its OAuth endpoints on `wavegrain.com`.

Access keys (`wg_pat_`) are shown once and stored only as a fingerprint.
If you think a key leaked, revoke it in Wavegrain Settings and tell us.
