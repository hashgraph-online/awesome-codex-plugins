# Security policy

## Reporting a vulnerability

Email support@looot.ai with "security" in the subject. Please do not open a public issue for a
vulnerability.

Include what you found, the steps to reproduce it, and the plugin version (see
`.codex-plugin/plugin.json`). We reply within 3 business days and tell you when a fix ships.

## What this repo contains

This repo holds plugin manifests, an MCP config and one skill (Markdown). It runs no code on your
machine. The MCP config points at the hosted looot server, https://api.looot.ai/mcp, and signs you
in through the browser. No API key or token lives in any file here.

Reports about the hosted looot service (api.looot.ai, looot.ai) go to the same address.

## Supported versions

Only the latest version on the default branch gets fixes.
