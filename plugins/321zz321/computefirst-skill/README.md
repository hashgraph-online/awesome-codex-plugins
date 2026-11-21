# ComputeFirst agent skill

Instructions for Claude Code, Codex, Grok, and other autonomous agents to use [ComputeFirst](https://computefirst.net) for deterministic computation: search → read the versioned contract → execute. Free, no API key or sign-up. Live-verified catalog: **793 tools** (2026-10-26).

Install the Claude Code skill and MCP connection from this repository's marketplace:

```text
/plugin marketplace add 321zz321/computefirst-skill
/plugin install computefirst@computefirst
```

Or add the MCP connection alone:

```sh
claude mcp add --transport http computefirst https://computefirst.net/mcp
```

Codex `~/.codex/config.toml`:

```toml
[mcp_servers.computefirst]
url = "https://computefirst.net/mcp"
```

For Codex skill discovery, copy `skills/computefirst/` into `.agents/skills/computefirst/` or `~/.agents/skills/computefirst/`, preserving references. [Client setup and sources](skills/computefirst/references/setup.md) cover Claude Code, Cursor, VS Code, generic MCP clients, and plain HTTP.

Read **[the skill](skills/computefirst/SKILL.md)** for selection rules, exact requests, limits, and six actual API results. [AGENTS.md](AGENTS.md) provides condensed guidance. The full MCP route exposes gateway tools; `/mcp/chatgpt` offers 40 named operations with smaller limits.

Verify with Node.js 22+ and network access:

```sh
node scripts/verify-examples.mjs
```

The script reads the documented requests/results directly and fails on drift. It also checks discovery and both MCP routes. No dependencies, credentials, or reporting calls. [MIT license](LICENSE).
