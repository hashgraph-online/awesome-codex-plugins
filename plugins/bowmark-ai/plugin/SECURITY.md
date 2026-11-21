# Security Policy

This repository packages the Bowmark plugin for Claude Code, Codex, Cursor and Gemini CLI.
It holds manifests, MCP configuration and skill files. The plugin connects to the hosted
Bowmark MCP server under `https://api.bowmark.ai/mcp`; no Bowmark service code lives here.

## Supported versions

Only the latest commit on `main` is supported. Plugin hosts install from `main`, so fixes
ship by updating this repository.

## Reporting a vulnerability

Please do not open a public issue for a security problem.

Email **support@bowmark.ai** with the subject line `SECURITY: <short summary>`. Include:

- what you found and where (this repo, the MCP server, the API or bowmark.ai),
- steps to reproduce,
- the impact you expect.

Please give us a reasonable chance to fix the issue before you disclose it publicly.

## Scope

In scope: this repository, the hosted MCP server it points to, `api.bowmark.ai` and
`bowmark.ai`.

Out of scope: third-party websites that Bowmark functions read, and the plugin hosts
themselves (report those to their own maintainers).
