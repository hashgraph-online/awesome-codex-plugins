---
name: mnemoverse-docs
description: "Guides a developer adding Mnemoverse long-term memory to their own app, agent or framework: picks the form (hosted MCP server, npm MCP server, REST API, Python SDK, Vercel AI SDK package) and points to the docs page. Use when the user asks how to integrate Mnemoverse or which package, endpoint or authentication to use, or says \"Mnemoverse SDK\", \"Mnemoverse API\" or \"add memory to my agent\"."
---

# Mnemoverse docs for developers

This skill is a map of the Mnemoverse documentation for someone building with it. It needs no memory tools: it answers from the docs pages below.

## Check first: building, or connecting this assistant?

If the user wants memory in the assistant they are talking to right now, this is not an integration question. Use the bundled `setup` skill if it is installed, otherwise https://mnemoverse.com/docs/api/install-by-host, and stop here.

Everything below is for a developer whose own code will read and write memory.

## Pick the form

Every form reaches the same memory in the same account, so a fact written through one is recalled through the others. Pick by where the code runs and how it authenticates.

| The developer is building | Use | Docs |
|---|---|---|
| An MCP client that can open a browser sign-in with a loopback callback (a desktop or CLI app) | The hosted MCP server at `https://mcp.mnemoverse.com/mcp`, OAuth 2.1 with PKCE, no key to paste; a web client served from its own domain cannot register, so it uses the API key row below | https://mnemoverse.com/docs/api/remote-mcp-server#which-clients-can-sign-in-registration-allowlist |
| A server-side app that speaks MCP over HTTP but cannot do a browser sign-in | The same hosted server with a Mnemoverse API key sent as a bearer token | https://mnemoverse.com/docs/api/remote-mcp-server#with-an-api-key-instead-of-the-sign-in |
| An MCP client that starts local servers | The npm package `@mnemoverse/mcp-memory-server`, started with `npx -y @mnemoverse/mcp-memory-server@latest` and the key in `MNEMOVERSE_API_KEY` | https://mnemoverse.com/docs/api/mcp-server |
| Python code | `pip install mnemoverse` (Python 3.10 or newer), sync and async clients | https://mnemoverse.com/docs/api/python-sdk |
| A Vercel AI SDK agent | The `@mnemoverse/ai-sdk` package, or the MCP server through `createMCPClient` | https://mnemoverse.com/docs/api/vercel-ai-sdk |
| Any other language, plain HTTPS | The REST API at `https://core.mnemoverse.com/api/v1` | https://mnemoverse.com/docs/api/reference |
| An agent framework (LangGraph, CrewAI and others) | The framework guide | https://mnemoverse.com/docs/api/use-cases/agent-frameworks |

The REST base and the MCP address are different surfaces: an MCP client pointed at the REST base cannot complete its sign-in. The first table on https://mnemoverse.com/docs/api/agent-setup puts the two addresses side by side.

## First steps to give the developer

1. A free account and API key at https://console.mnemoverse.com, no credit card. Every form in the table above takes this key except the browser sign-in to the hosted server.
2. The first write, read and feedback call in a couple of minutes: https://mnemoverse.com/docs/api/getting-started
3. Per-host install commands (Claude Code, Cursor, VS Code, Codex, Gemini CLI and others): https://mnemoverse.com/docs/api/install-by-host
4. Every published package in one list: https://mnemoverse.com/docs/api/integrations
5. When something fails: https://mnemoverse.com/docs/api/troubleshooting

## What to say about how it works

Keep to what the docs state. Memory is written as self-contained statements, read back by relevance or newest first, and rated after use: tell it a recalled memory helped or misled, and it re-ranks what comes back next. Shared rooms (beta) let several accounts write to one pool: https://mnemoverse.com/docs/api/rooms. Prices and limits: https://mnemoverse.com/docs/api/pricing.

## Rules

- Link the docs page instead of retyping long configs from memory; configs change, the page is kept current.
- Keep the key out of code, chat and memory: an environment variable or the host's secret store.
- If the docs do not answer the question, say so and point to the closest page rather than guessing at behavior.
