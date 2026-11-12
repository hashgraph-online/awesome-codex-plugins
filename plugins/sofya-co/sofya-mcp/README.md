# sofya-mcp

[![Listed on mcpservers.org](https://mcpservers.org/badge.svg)](https://mcpservers.org/servers/sofya-co/sofya-mcp)

MCP server for [Sofya](https://sofya.co) - web **search**, **fetch**, **extract**, and deep **research** for AI agents, exposed over the [Model Context Protocol](https://modelcontextprotocol.io).

Use it either way:

- **Hosted (no install):** connect your client to `https://mcp.sofya.co/mcp` (streamable HTTP). Sign in with OAuth, or send your API key as a Bearer token. This is the server listed in the MCP registry as `co.sofya/sofya`.
- **Local:** build this repo and run it over stdio. It is a thin wrapper around the Sofya REST API with the four core tools.

Eligible GitHub accounts (a year or older) get free monthly credits; everyone else pays as they go.

## Tools

| Tool | What it does | Cost |
|------|--------------|------|
| `search` | Search the web and get extracted page content (not just snippets). Supports `news` topic, domain filters, freshness, and an optional AI-synthesized `answer`. | 1-2 credits (+2 for `include_answer`) |
| `fetch` | Fetch up to 10 URLs as clean markdown. Also handles PDF, DOCX, XLSX, PPTX, EPUB, and more. | 1 credit / URL |
| `extract` | Fetch a page and pull specific information from it using AI. | 10 credits |
| `research` | Decompose a question into sub-queries, read many sources in parallel, and synthesize a cited report. | 50 credits |
| `get_balance` | Show the account's remaining credits. Hosted server only. | free |
| `buy_credits` | Return a payment link for a credit top-up. It does not charge anything. Hosted server only. | free |

`search`, `fetch`, `extract`, `research` and `get_balance` are read-only.

## Hosted server (VS Code / Copilot and others)

Point your client at the hosted endpoint. Clients with OAuth support (Claude, VS Code, Cursor, Cline and others) only need the URL and will ask you to sign in. To use an API key instead, get one at [sofya.co](https://sofya.co) (keys look like `sofya_live_...`) and send it as a Bearer token:

VS Code / GitHub Copilot (`.vscode/mcp.json`):

```json
{
  "servers": {
    "sofya": {
      "type": "http",
      "url": "https://mcp.sofya.co/mcp",
      "headers": { "Authorization": "Bearer sofya_live_..." }
    }
  }
}
```

Claude Code, as a plugin (signs in with OAuth; plugin files in [`plugins/sofya`](plugins/sofya)):

```bash
/plugin install sofya --marketplace sofya-co/sofya-mcp
```

Claude Code, with an API key:

```bash
claude mcp add --transport http sofya https://mcp.sofya.co/mcp --header "Authorization: Bearer sofya_live_..."
```

Cursor (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "sofya": {
      "url": "https://mcp.sofya.co/mcp",
      "headers": { "Authorization": "Bearer sofya_live_..." }
    }
  }
}
```

Cline:

```bash
cline mcp install sofya --transport http https://mcp.sofya.co/mcp
```

Or in `cline_mcp_settings.json`:

```json
{
  "mcpServers": {
    "sofya": {
      "type": "streamableHttp",
      "url": "https://mcp.sofya.co/mcp",
      "headers": { "Authorization": "Bearer sofya_live_..." }
    }
  }
}
```

Then ask your agent things like "search for the latest Node.js LTS release notes", "fetch this PDF and summarize it", or "research how the EU AI Act treats open-weight models". Full API docs: [sofya.co/docs](https://sofya.co/docs).

## Agent skills

Two skills in [`skills`](skills) (the same files ship inside the Claude plugin at `plugins/sofya/skills`) teach an agent when and how to use Sofya: `sofya-search` (search, fetch, extract) and `sofya-research` (cited reports). They use the MCP tools when they are connected, and otherwise call the REST API with `SOFYA_API_KEY`. Install them into Claude Code, Cursor, Codex, Gemini CLI, Copilot and other agents with:

```bash
npx skills add sofya-co/sofya-mcp
```

## Claude Code plugin

The plugin bundles the hosted server and both skills:

```
/plugin marketplace add sofya-co/sofya-mcp
/plugin install sofya@sofya
```

## Codex

The repo root is also a Codex plugin ([`.codex-plugin/plugin.json`](.codex-plugin/plugin.json)) with the hosted server and both skills.

## Kiro

This repo is also a Kiro power ([`plugin.json`](plugin.json), [`mcp.json`](mcp.json) and [`skills`](skills) at the root). In Kiro, open Powers, choose **Add Custom Power**, then **Import power from GitHub** and enter `https://github.com/sofya-co/sofya-mcp`. Kiro opens a Sofya sign-in the first time a tool runs.

## Local server

### Prerequisites

- Node.js 18+
- A Sofya API key - get one at [sofya.co](https://sofya.co) (keys look like `sofya_live_...`)

### Build

```bash
git clone https://github.com/sofya-co/sofya-mcp.git
cd sofya-mcp
npm install          # also builds to build/index.js
```

Check it starts:

```bash
SOFYA_API_KEY=sofya_live_... node build/index.js
```

In the examples below, replace `/path/to/sofya-mcp` with the folder you cloned.

### Configuration

#### Claude Code

```bash
claude mcp add sofya --env SOFYA_API_KEY=sofya_live_... -- node /path/to/sofya-mcp/build/index.js
```

#### Claude Desktop / Cursor / Windsurf / VS Code

Add this to your MCP config (e.g. `claude_desktop_config.json`, or `.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "sofya": {
      "command": "node",
      "args": ["/path/to/sofya-mcp/build/index.js"],
      "env": {
        "SOFYA_API_KEY": "sofya_live_..."
      }
    }
  }
}
```

#### Codex

Add it with the Codex CLI:

```bash
codex mcp add sofya --env SOFYA_API_KEY=sofya_live_... -- node /path/to/sofya-mcp/build/index.js
```

Or edit `~/.codex/config.toml` directly. Note Codex puts environment variables in
a nested `[mcp_servers.<name>.env]` table:

```toml
[mcp_servers.sofya]
command = "node"
args = ["/path/to/sofya-mcp/build/index.js"]

[mcp_servers.sofya.env]
SOFYA_API_KEY = "sofya_live_..."
```

Then run `/mcp` inside Codex to confirm the server is connected.

### Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SOFYA_API_KEY` | yes | - | Your Sofya API key (`sofya_live_...`; older `ay_live_...` keys still work). |
| `SOFYA_BASE_URL` | no | `https://sofya.co` | Override the Sofya API base URL. |

CLI flags `--api-key` and `--base-url` take precedence over the env vars.
Run `node build/index.js --list-tools` to print the tool schemas, or `--help` for options.

## Development

```bash
npm run build        # compile TypeScript to build/
npm run watch        # recompile on change
npm run inspector    # debug with @modelcontextprotocol/inspector
```

The server is a single file, [`src/index.ts`](src/index.ts). Tool definitions
mirror Sofya's hosted MCP server exactly (same names, parameters, and defaults).

## Privacy and support

The hosted server receives the tool arguments (queries, URLs, prompts) to answer each request and keeps them only in server logs, up to 30 days. [Privacy policy](https://sofya.co/privacy) · [Terms](https://sofya.co/terms)

Support: support@sofya.co or [sofya.co/contact](https://sofya.co/contact).

## License

MIT - see [LICENSE](LICENSE).
