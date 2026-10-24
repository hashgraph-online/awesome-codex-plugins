# Security policy

This covers the LLMSlim plugin in this folder: the Claude Code plugin, the Codex plugin manifest and the MCP server
they start (`llmslim mcp`). The policy for the whole project is
[SECURITY.md](https://github.com/Thanatos9404/llmslim/blob/main/SECURITY.md) at the repository root.

## Supported versions

| Version | Supported |
| --- | --- |
| 0.11.x | Yes |
| < 0.11.0 | No |

The plugin runs one exact release of the server, pinned in `.mcp.json`. A security fix ships as a new 0.11.x
release, and the pin moves to it.

## Reporting a vulnerability

Please report it privately, not in a public issue:

- **Email:** support@llmslim.app, with the subject `[SECURITY] llmslim plugin`.
- **Private advisory:** [GitHub Security Advisories](https://github.com/Thanatos9404/llmslim/security/advisories/new).

Include what is affected, the impact, steps to reproduce and the version you ran. You will get a reply within 48
hours, and the report stays private until a fix is released.
