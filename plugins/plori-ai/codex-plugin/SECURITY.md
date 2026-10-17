# Security Policy

## Reporting a vulnerability

If you find a security issue in this plugin or the plori platform, email **dev@plori.ai**
with the details. We aim to acknowledge reports within three business days and will keep
you posted on remediation. Please do not open a public issue for a security-sensitive
report.

## Scope

This repository contains only plugin metadata: the manifest (`.codex-plugin/plugin.json`),
a pointer to the remote plori MCP server (`https://api.plori.ai/mcp`), and a skill
(documentation text under `skills/`). It runs no local code and installs no third-party
software. Authentication to the plori service is OAuth 2.1 or an API key, handled by the
hosted service; no credentials live in this repository.
