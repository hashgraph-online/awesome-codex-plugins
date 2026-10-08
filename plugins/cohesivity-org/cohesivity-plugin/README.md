# Cohesivity plugin for Codex

cohesivity.ai offers free agent native backend services. Anonymous account (no-signup) to get started through MCP or API. Hosting, postgres, email, storage, containers, LLMs, voice and third-party APIs. Includes free tiers and 5 USD/mo in AI and Search credits. Top-ups through x402.

This package is generated from
[cohesivity-org/cohesivity-plugin](https://github.com/cohesivity-org/cohesivity-plugin);
do not edit it directly. It contains:

- `skills/cohesivity/SKILL.md`: the Cohesivity agent skill.
- `.mcp.json`: the hosted MCP server at `https://cohesivity.ai/mcp` and the local
  `cohesivity-local` stdio server.
- `mcp/project-bootstrap.mjs`: the dependency-free local MCP server. It needs
  Node 18 or newer and no Cohesivity account.

The hosted MCP needs no account, token, or registration; account sign-in is
optional. Every mutation except feedback requires an explicit `confirmed: true`
from the current user request.

Project credentials live in `.cohesivity`, which must stay out of version
control. Report vulnerabilities through the repository's
[SECURITY.md](https://github.com/cohesivity-org/cohesivity-plugin/blob/main/SECURITY.md).

Documentation: <https://cohesivity.ai/llms.txt>. License: MIT.
