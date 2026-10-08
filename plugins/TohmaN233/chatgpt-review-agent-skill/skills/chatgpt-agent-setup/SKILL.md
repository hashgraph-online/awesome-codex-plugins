---
name: chatgpt-agent-setup
description: >
  Choose ZIP or MCP mode. ZIP needs no setup; configure this workspace's
  Bridge and ChatGPT Connector only when the user explicitly chooses MCP.
---

# ChatGPT Agent Setup

- **ZIP (default):** Codex packages selected local files and sends them to
  ChatGPT. It needs no Bridge or Connector configuration and supports Pro
  models. Continue with `$chatgpt-agent`; do not start MCP.
- **MCP:** ChatGPT can read the selected workspace directly. It requires a
  workspace Bridge and Connector. ZIP and MCP remain available per task.

Let the user choose; do not infer MCP from a generic setup or connection
request. Only after the user explicitly chooses MCP, read and follow the
[MCP setup procedure](references/mcp-setup.md). Do not load that reference for
ZIP work.
