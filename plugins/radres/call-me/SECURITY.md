# Security Policy

## Reporting a vulnerability

Please do not open a public issue for a security problem. Email
**serdar@callmemcp.com** with a short description, the affected file or
endpoint, steps to reproduce and the impact you see. You will get a reply.

## What is in scope

- The files in this repository: the Claude Code plugin, the Codex entry, the
  Gemini CLI extension, the Grok Build plugin and the agent skill.
- The hosted MCP server at `https://callmemcp.com/mcp` and the /call-me
  iPhone and Android app that it rings.

## Notes for reviewers

- The plugin and skill ship no secrets. The hosted MCP endpoint takes no
  credentials; the user's own 10-digit /call-me number is a tool argument.
- The local helper keeps its state only under `~/.aiphone/` (owner-only permissions).
- The /call-me app is a paid subscription. This repository is MIT
  licensed.
