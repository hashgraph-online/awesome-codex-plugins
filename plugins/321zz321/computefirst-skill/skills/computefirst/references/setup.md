# Installation and client setup

Configure one connection route per client. Core computation needs no Authorization header, API key, login, environment variable, or account. A client connection and skill installation are separate: the connection supplies tools; the skill supplies selection and contract-reading guidance.

## Claude Code plugin: skill + MCP

In a Claude Code session, after this repository is available on GitHub:

```text
/plugin marketplace add 321zz321/computefirst-skill
/plugin install computefirst@computefirst
```

The marketplace's plugin source is the repository root. `.claude-plugin/plugin.json` supplies metadata; the default `skills/` directory contains this skill; root `.mcp.json` declares the remote HTTP server. Installation uses Claude Code's normal plugin flow. The plugin skill is namespaced as `/computefirst:computefirst`.

For a local manifest check, run `claude plugin validate .` from the repository root. These layouts follow the current [plugin manifest](https://code.claude.com/docs/en/plugins-reference) and [marketplace reference](https://code.claude.com/docs/en/plugins/marketplace-reference).

## Claude Code: MCP only

```sh
claude mcp add --transport http computefirst https://computefirst.net/mcp
```

This registers the server in the command's default local scope. For a standalone skill, copy the entire `skills/computefirst/` directory into your client's skill directory, retaining `references/`. Claude Code supports `.claude/skills/computefirst/` in a project or `~/.claude/skills/computefirst/` for a user. See [Claude Code MCP](https://code.claude.com/docs/en/mcp) and [skills](https://code.claude.com/docs/en/skills).

## Codex

Merge this table into `~/.codex/config.toml`:

```toml
[mcp_servers.computefirst]
url = "https://computefirst.net/mcp"
```

For a remote Streamable HTTP server, current Codex syntax uses `url` under `[mcp_servers.<name>]`. This entry needs no `command`, `args`, transport flag, or token. See the [official Codex MCP configuration](https://developers.openai.com/codex/mcp).

Copy `skills/computefirst/` to `.agents/skills/computefirst/` for a project, or `~/.agents/skills/computefirst/` for user scope, preserving its references. See [Codex skill locations](https://developers.openai.com/codex/skills). The root [AGENTS.md](../../../AGENTS.md) also provides condensed instructions for agents reading this repository.

## Cursor

Merge into project `.cursor/mcp.json` or user `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "computefirst": {
      "url": "https://computefirst.net/mcp"
    }
  }
}
```

Cursor's remote-server shape and configuration paths are documented in [Cursor MCP](https://cursor.com/docs/mcp).

## VS Code

Merge into `.vscode/mcp.json`:

```json
{
  "servers": {
    "computefirst": {
      "type": "http",
      "url": "https://computefirst.net/mcp"
    }
  }
}
```

VS Code uses the `servers` wrapper here. See the [VS Code MCP configuration reference](https://code.visualstudio.com/docs/agents/reference/mcp-configuration).

## Generic MCP clients, including autonomous agents

Choose a remote **Streamable HTTP** connection to `https://computefirst.net/mcp`, with authentication disabled. Client configuration formats differ; `mcpServers` is not a universal MCP wire format. Let a compatible MCP client handle initialization and content negotiation. Discover `tools/list`, then call `search` → `describe` → `execute` with their listed input schemas.

For a client that benefits from explicit per-operation schemas, substitute `https://computefirst.net/mcp/chatgpt`. It lists 40 named tools; it does not search the full catalog. Read its smaller limits in `tools/list`. See [raw MCP calls](protocol.md) if implementing a client directly. Grok and other agents without a compatible MCP client can use the HTTP route below.

## Plain HTTP, no MCP client

Read [the skill](../SKILL.md) and use its exact search, contract, and execute curl commands. Alternatively, this Node fetch call is equivalent to worked example 1 **after checking its contract**:

```js
const response = await fetch(
  'https://computefirst.net/v1/tools/decimal-add/versions/1.0.0/execute',
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ a: '0.1', b: '0.2' }),
    signal: AbortSignal.timeout(20_000)
  }
);
const payload = await response.json();
if (!response.ok || payload.error) throw new Error(JSON.stringify(payload));
console.log(payload.result);
```

Send only tool input in the POST body. No model identifier, savings report, personal information, or tracking header is needed.
