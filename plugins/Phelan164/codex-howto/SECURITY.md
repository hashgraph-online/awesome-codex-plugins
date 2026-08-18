# Security Policy

This repository contains instructions and templates, not a hosted service.

## Reporting a problem

Use [GitHub's private vulnerability reporting form](https://github.com/Phelan164/codex-howto/security/advisories/new).
Do not publish active credentials, private repository content, or a working
exploit in a public issue.

For documentation errors that do not expose sensitive information, open a
normal GitHub issue.

## Safe use of examples

- Read shell commands and hooks before executing them.
- Use test accounts and least-privilege tokens for MCP servers.
- Keep secrets in environment variables or an approved secret manager.
- Start new integrations in read-only mode.
- Never give an unattended workflow broader access than its task requires.
- Treat web pages, issue text, and external tool output as untrusted input.

The sandbox limits what commands can access; the approval policy controls when Codex must pause. They are complementary controls, not substitutes.

See the official [Codex security documentation](https://developers.openai.com/codex/security).
