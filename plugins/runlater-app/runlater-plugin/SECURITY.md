# Security policy

## Reporting a vulnerability

Email **hello@greatwork.company** with "Security" in the subject line. Include the affected component (this plugin's files, the MCP server at `https://runlater.app/api/mcp`, or the runlater.app website), steps to reproduce, and any proof of concept. Please don't open a public GitHub issue for security problems.

We will confirm receipt and keep you posted until the issue is fixed. Please give us a reasonable window to fix the problem before disclosing it publicly.

## Scope

- This repository: plugin manifests, the skill and MCP configuration.
- The hosted RunLater service at runlater.app, including OAuth sign-in and the MCP endpoint.

## Notes

- This repository contains no keys or secrets. MCP clients sign in with OAuth 2.1, or use an API key you create in your own RunLater settings.
- The service only calls public URLs; private and local addresses are refused.
