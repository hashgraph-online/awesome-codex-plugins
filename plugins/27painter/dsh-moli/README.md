# Moli Browser for Codex

A local Codex MCP plugin that exposes the installed Moli headless browser.

## Tools

- `moli_search` searches through configurable public result pages and returns
  structured titles, URLs, and snippets.
- `moli_fetch` returns rendered Markdown, HTML, semantic trees, selector text,
  or a JavaScript evaluation result.
- `moli_capture` writes PNG screenshots or PDFs to an explicit path, creating
  missing parent directories.
- `moli_probe` inspects or explicitly installs the Moli executable, and reports
  the configured search providers and proxy state.

## Install

```powershell
codex plugin marketplace add 27painter/dsh-moli --ref main
codex plugin add moli@27painter-codex
```

Start a new Codex conversation after installation so the MCP tool catalog is
loaded.

## Configuration

The MCP server supports `MOLI_BIN`, `MOLI_PROXY`, `MOLI_SEARCH_URL`,
`MOLI_SEARCH_URLS`, `MOLI_TIMEOUT_MS`, `MOLI_MAX_CHARS`, and
`MOLI_INSECURE_TLS`. Search providers default to DuckDuckGo HTML → Baidu → Bing →
Brave, and the proxy applies to every tool call: search, fetch, capture, and
probe. See the repository README for details.

## Security

See [SECURITY.md](./SECURITY.md). This plugin is independent of OpenAI and
Moli/Lexmount.
