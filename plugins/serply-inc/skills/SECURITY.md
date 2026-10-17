# Security Policy

## Reporting a vulnerability

Email security issues to team@serply.io with "Security" in the subject line, or open a private GitHub security advisory on this repository. Please do not file public issues for vulnerabilities. We aim to acknowledge reports within three business days.

## Credentials

This repository never contains API keys. The Codex MCP configuration (`codex.mcp.json`) reads the key from the `SERPLY_API_KEY` environment variable at runtime and sends it only in the `X-Api-Key` header to `https://api.serply.io/mcp`. Never commit a key, a local Codex or Claude Code config file, or request logs that contain one.

## Scope

This repository ships instructions (`SKILL.md`), plugin manifests and an MCP endpoint reference. It runs no code of its own. Issues in the hosted Serply API or MCP server are in scope and go to the same address.
