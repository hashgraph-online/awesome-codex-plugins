# Security Policy

## Scope

This repository contains a Codex plugin: a skill (`SKILL.md`), an MCP server declaration that starts the published npm package [`@wavespeed/mcp`](https://github.com/WaveSpeedAI/mcp-server) with `npx`, and two helper shell scripts that install and check the [`@wavespeed/cli`](https://github.com/WaveSpeedAI/wavespeed-cli). No secrets are stored here. Authentication is handled by the CLI's `wavespeed login` or the `WAVESPEED_API_KEY` environment variable; the skill instructs the agent never to ask a user to paste a key into the chat.

Vulnerabilities in the MCP server or the CLI themselves should be reported against their own repositories, linked above.

## Reporting a vulnerability

Email **security@wavespeed.ai** with a description, reproduction steps, and the affected version. Please do not open a public issue for security reports.

We acknowledge reports within 3 business days and aim to ship a fix, or a mitigation and disclosure timeline, within 14 days for confirmed issues.

## Supported versions

Only the latest tagged release receives security fixes.
