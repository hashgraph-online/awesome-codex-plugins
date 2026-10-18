# Security policy

This repository holds the plugin manifests, MCP configuration and agent skill for the hosted
BulkTranscripts MCP server at `https://bulktranscripts.co/mcp`. It contains no server code and
no credentials. Sign-in is OAuth 2.0 with dynamic client registration, so no API key is stored
in any file here.

## Reporting a vulnerability

Email **hello@bulktranscripts.co** with "Security" in the subject. Include the steps to
reproduce, what you expected and what happened. Please don't open a public issue for a
security problem.

You'll get a reply within 3 working days. Fixes to the hosted service ship as soon as they are
verified, and we'll tell you when yours is live.

## Scope

- The hosted MCP server and REST API at `bulktranscripts.co`
- The manifests and skill files in this repository

Out of scope: denial-of-service tests, spam, and social engineering of staff or users.
