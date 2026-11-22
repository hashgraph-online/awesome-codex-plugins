# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest release | Yes |
| Earlier releases | No |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

This plugin connects Codex and ChatGPT to Graphify's hosted MCP server at `https://api.graphify.com/mcp`. Report security issues the same way [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify/blob/main/SECURITY.md) does:

- Use GitHub's private vulnerability reporting on [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify/security/advisories/new) (and on this repository once it is published).
- Or email the maintainer directly.

The Graphify-Labs/graphify `SECURITY.md` (verified 21 Nov 2026) does not list a specific security email address, so this file does not invent one.

Please include:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will acknowledge receipt as soon as possible and work with you to release a coordinated fix.

## Secrets

This repository contains no API keys, tokens or OAuth client secrets. Authentication is OAuth in the browser. Do not paste credentials into issues, pull requests or plugin files.
