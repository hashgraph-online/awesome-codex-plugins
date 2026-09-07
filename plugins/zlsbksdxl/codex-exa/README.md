# Exa Web Search for Codex

Community packaging of the official [Exa MCP server](https://github.com/exa-labs/exa-mcp-server) for Codex.

The plugin provides:

- `web_search_exa` for current web search
- `web_fetch_exa` for full-page retrieval
- the implicitly invoked `exa-web-search` Skill, which prefers Exa for general online research

The plugin connects to Exa's official remote MCP endpoint and requests browser OAuth. Codex opens the account connection flow during installation or first use; no API key is stored in this repository or its plugin configuration.

See the repository [README](../../README.md#connect-exa) for installation and setup.
