<!-- Generated from shared/connect.md by scripts/sync_shared.py. Edit the shared file, not this copy. -->

# Connecting to sync.

The sync. skills work in one of three modes. Pick one silently at the start of a task, and don't narrate the choice to the user.

1. **sync. MCP tools are available.** You can see tools such as `lipsync_create`, `generations_estimate-cost` and `account_get-context`. Some clients prefix them, for example `mcp__sync__lipsync_create` or `mcp__plugin_sync_sync__lipsync_create`. Use them; this is the preferred mode.
2. **No MCP tools, but `SYNC_API_KEY` is set** and you can run shell commands. Call the REST API at `https://api.sync.so/v2` with the header `x-api-key: $SYNC_API_KEY`. The skill's `references/api.md` has the requests. Never print the key or paste it into chat.
3. **Neither.** Help the user connect, then continue with the original request.

## Connect the hosted MCP server (recommended)

The server is `https://mcp.sync.so/mcp`. Users sign in with their sync. account through OAuth, so there is no key to copy.

| Client | How to connect |
| --- | --- |
| Claude Code | If the sync. plugin is installed, run `/mcp`, select `sync` and sign in. Otherwise run `claude mcp add --transport http sync https://mcp.sync.so/mcp` (add `--scope user` for every project), then `/mcp`. |
| Claude.ai or Claude Desktop | Settings → Connectors → Add custom connector, URL `https://mcp.sync.so/mcp`, then Connect. |
| Codex | `codex mcp add sync --url https://mcp.sync.so/mcp`, then `codex mcp login sync`. |
| Cursor | Add `{"mcpServers": {"sync": {"url": "https://mcp.sync.so/mcp"}}}` to `.cursor/mcp.json` (project) or `~/.cursor/mcp.json` (global). |
| VS Code | Add `{"servers": {"sync": {"type": "http", "url": "https://mcp.sync.so/mcp"}}}` to `.vscode/mcp.json`. |
| Other clients | Any client with remote MCP over Streamable HTTP and OAuth can use the same URL. |

Most clients only load new MCP servers after a restart or reload. Say so, and tell the user to ask again once it's connected.

## Use an API key instead

For scripts, CI, or clients without remote MCP support:

- Create a key at https://sync.so/settings/api-keys and put it in the environment as `SYNC_API_KEY`, in a `.env` file the project already ignores, or in the shell profile. Don't commit it.
- **The same MCP tools, run locally:** sync.'s official MCP server package, `@sync.so/mcp-server` (source: https://github.com/synchronicity-labs/mcp-server), runs on the user's machine with an API key. Give the user the command for their client to run themselves, for example `claude mcp add sync -e SYNC_API_KEY=$SYNC_API_KEY -- npx -y @sync.so/mcp-server@latest`. Other clients take `{"command": "npx", "args": ["-y", "@sync.so/mcp-server@latest"], "env": {"SYNC_API_KEY": "..."}}`. Full steps: https://sync.so/docs/plugins-and-extensions/mcp-server.
- **No MCP at all:** the REST API and the official SDKs read `SYNC_API_KEY`: Python `pip install syncsdk`, TypeScript `npm i @sync.so/sdk`.

## Accounts and plans

Every account starts on the free tier: a few short generations each month, watermarked. Paid plans raise length limits, concurrency and file size, and remove the watermark from Creator up. Don't promote plans. When a limit blocks the request, quote the error's message and point to https://sync.so/billing/subscription.
