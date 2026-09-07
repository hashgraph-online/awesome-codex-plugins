# Claude Chat (claude.ai / Claude desktop)

Read this file when you are in the **Claude app** — **claude.ai** (web) or **Claude desktop** — with Vibe Prospecting via the **MCP connector**.

**Not Claude Code.** If your system context identifies **Claude Code** (Anthropic CLI, Environment block, shell access), read [`claude-code.md`](claude-code.md) instead.

**Not Claude Cowork.** If you are in a **Cowork** workspace (`.plugin` install), read [`cowork.md`](cowork.md) instead. Connector setup is the same; host identity differs.

**Claude Chat cannot run the vpai CLI.** The **MCP connector** is the only path here.

MCP tools may appear as `mcp__claude_ai_*` or `mcp__*__fetch-entities`. That naming does **not** mean Claude Code.

## How to work

**Follow each MCP tool's description and input schema.** That documentation is authoritative for this path.

Before the first real call for each distinct tool, read its live schema and description. Build each call only from confirmed fields. Use the user's request as `tool_reasoning` where the schema requires it.

**Never** on Claude Chat:

- Run `npx @vibeprospecting/vpai@latest` or any vpai shell command
- Mount `~/.config/vpai` or read `config.json` for CLI auth
- Open OAuth URLs manually or suggest CLI login flows
- Fall back to terminal/CLI when the connector is missing — keep polling until the user connects
- Invent parameters not in the tool schema

## Connector setup (required)

Before doing any work, check whether Vibe Prospecting MCP connector tools are in your tool list (look for `mcp__*__fetch-entities`).

If those tools are present, use them directly — follow each tool's description and input schema. Treat every tool response as JSON.

If those tools are NOT present, always call `search_mcp_registry` first with keywords `["vibe prospecting", "explorium"]` to check current state, then branch on `installState`:

- **`installState: "connected"` (turned off / disabled for this session)** — the connector is installed and authorized but its tools aren't live in this session. Call `suggest_connectors` with UUID `1bdcb159-b6f0-4f13-bc08-fdb40b007828` and tell the user to hit **Use** on the card to start/refresh it. Don't tell them to reinstall — it's already connected.
- **`installState` is anything else (not installed / "off")** — call `suggest_connectors` with the same UUID and tell the user to hit **Connect** on the card to install and authorize it.

Either way: **poll until connected.** On every subsequent turn, re-check your tool list for `mcp__*__fetch-entities`. Do not start prospecting until they appear.

If the suggested card fails in either case, tell the user to open the **connector / integrations UI** directly, connect/install Vibe Prospecting there, and wait while you poll again.

## Troubleshooting

| Problem | Fix |
|---|---|
| No `mcp__*__fetch-entities` in tool list | Run Connector setup above; poll until user connects |
| User asks to use CLI or `npx vpai` | Claude Chat cannot run the CLI; MCP connector is the only path |
| Connector connect fails | Open connector / integrations UI, install Vibe Prospecting, connect again, poll |
| Auth / 401 on connector tools | User must reconnect (Connect on the Vibe Prospecting card) |
| Unsure how to call a tool | Re-read that tool's MCP description and input schema |
| Cowork workspace | Read [`cowork.md`](cowork.md) |
| Claude Code with shell | Read [`claude-code.md`](claude-code.md) |
