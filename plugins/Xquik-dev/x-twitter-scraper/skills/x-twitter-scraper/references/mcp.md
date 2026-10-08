# Xquik MCP server

The remote server lives at `https://xquik.com/mcp` and speaks Streamable HTTP.
Sign in with OAuth from the client. The server exposes 3 tools: `docs` for
guidance, `search` for route contracts, and `execute` for calls. Hosted MCP
adds the `Idempotency-Key` header to writes.

| Client | Setup |
| --- | --- |
| Claude Code | `claude mcp add --transport http xquik https://xquik.com/mcp`, then run `/mcp` and authenticate |
| Claude.ai and Claude Desktop | Settings, Connectors, Add custom connector, enter the URL |
| Cursor | In `~/.cursor/mcp.json` or `.cursor/mcp.json`, add `{"mcpServers": {"xquik": {"url": "https://xquik.com/mcp"}}}`. Cursor opens OAuth when the server answers `401` |
| VS Code | In `.vscode/mcp.json`, add `{"servers": {"xquik": {"type": "http", "url": "https://xquik.com/mcp"}}}`, start it from the MCP view, and follow the OAuth prompt |
| Codex CLI | `codex mcp add xquik --url https://xquik.com/mcp`, then `codex mcp login xquik` |
| ChatGPT | Developer mode, Apps, Create, enter the URL, choose OAuth |

Confirm the connection by listing the client's MCP servers or tools and
checking that `docs`, `search`, and `execute` appear.

Use an API key only when the client cannot run OAuth. Keep it in an
environment variable or the client's secret store, and reference it from the
config. The client sends it as `Authorization: Bearer <key>`, for example
through Codex's `bearer_token_env_var = "XQUIK_API_KEY"`. Never
commit a key to a config file in a repository.
