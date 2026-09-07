# Claude Cowork

Read this file when you are in **Claude Cowork** — Cowork workspace, `.plugin` install, or Cowork **connector store** workflow.

**Not Claude Code.** If your system context identifies **Claude Code** (Anthropic CLI, Environment block, shell access), read [`claude-code.md`](claude-code.md) instead.

**Not Claude Chat.** If you are in the **Claude app** (claude.ai web or Claude desktop), read [`claude-chat.md`](claude-chat.md) instead.

**Cowork cannot run the vpai CLI.** There is no `npx`, no shell-based `vpai` path, and no CLI auth mount. The **MCP connector store** is the only way to use Vibe Prospecting here.

MCP tools may appear as `mcp__*__fetch-entities`. That does **not** mean Claude Code.

## How to work

**Follow each MCP tool's description and input schema.** That documentation is authoritative for this path.

Before the first real call for each distinct tool, read its live schema and description. Build each call only from confirmed fields. Use the user's request as `tool_reasoning` where the schema requires it.

**Never** in Cowork:

- Run `npx @vibeprospecting/vpai@latest` or any vpai shell command
- Mount `~/.config/vpai` or read `config.json` for CLI auth
- Open OAuth URLs manually or suggest CLI login flows
- Fall back to terminal/CLI when the connector is missing — keep polling the connector store until the user connects
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
| No `mcp__*__fetch-entities` in tool list | Run Connector setup above; poll until user connects via connector store |
| User asks to use CLI or `npx vpai` | Cowork cannot run the CLI; connector store is the only path |
| Connector connect fails | Open connector store, install Vibe Prospecting, connect again, poll |
| Auth / 401 on connector tools | User must reconnect (Connect on the Vibe Prospecting card) |
| Unsure how to call a tool | Re-read that tool's MCP description and input schema |
| claude.ai / Claude desktop | Read [`claude-chat.md`](claude-chat.md) |
| Claude Code with shell | Read [`claude-code.md`](claude-code.md) |
