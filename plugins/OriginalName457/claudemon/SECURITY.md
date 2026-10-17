# Security Policy

Claudemon is a local-first Claude Code plugin. It runs a small Node HTTP server on
`localhost` and an MCP server that Claude Code talks to over stdio. It has **no runtime
npm dependencies** and does not send your data anywhere.

## Reporting a vulnerability

If you find a security issue, please **do not open a public issue**. Instead:

- Use GitHub's **[Report a vulnerability](https://github.com/OriginalName457/claudemon/security/advisories/new)**
  (Security → Advisories), or
- Open a minimal private report and we'll follow up.

Please include steps to reproduce, affected version/commit, and impact. We aim to
acknowledge reports within a few days.

## Scope

In scope:
- The MCP server (`src/server.js`) and its tools
- The local web/app server (`src/webserver.js`, `src/standalone.js`)
- Setup / install scripts (`scripts/`)
- State handling (`src/state.js`)

Out of scope:
- Vulnerabilities in Claude Code itself (report to Anthropic)
- Issues requiring a pre-compromised local machine

## Supported versions

The latest release on `main` is supported. Fixes are applied there.
