# Firecrawl Codex plugin

OpenAI [Codex plugin](https://developers.openai.com/codex/plugins/build) that bundles Firecrawl **CLI workflow skills** for search, scrape, crawl, map, interact, agent, and parse workflows.

Canonical skill sources live in [`firecrawl/cli`](https://github.com/firecrawl/cli) (`cli/skills/`). This repo vendors copies for the Codex plugin distribution; refresh when CLI skills change materially.

## Requirements

- [Firecrawl CLI](https://www.npmjs.com/package/firecrawl-cli) installed and authenticated for skill workflows that shell out to `firecrawl`:

  ```bash
  npm install -g firecrawl-cli
  firecrawl login --browser
  ```

  Or set `FIRECRAWL_API_KEY` in your environment.

## Install in Codex (local marketplace)

Until the plugin is listed in the official Codex Plugin Directory, wire a **repo** or **personal** marketplace as described in the OpenAI docs.

### Option A: Git clone next to your project

1. Clone this repository (for example into `plugins/firecrawl-codex-plugin` at the root of the repo where you use Codex).

2. Add `.agents/plugins/marketplace.json` at that repo root (see [`examples/marketplace.json`](examples/marketplace.json)). Point `source.path` at the plugin folder with a `./`-prefixed path relative to the marketplace file’s directory.

3. Restart Codex. Open **Plugins** (Codex app) or run `/plugins` in Codex CLI, pick your marketplace, install **Firecrawl**, and enable the plugin.

### Option B: Codex CLI marketplace add

From the OpenAI docs:

```bash
codex plugin marketplace add ./path-to-marketplace-root
```

Use a marketplace JSON that references this plugin directory (same shape as `examples/marketplace.json`).

## MCP support

This package is intentionally skills-only for the Codex curated catalog. Firecrawl MCP support can be added later through a reviewed ChatGPT app integration and `.app.json`.

## Smoke checks (after install)

In a new Codex thread, try:

1. “Search the web for the latest Firecrawl changelog and summarize.”
2. “Scrape https://docs.firecrawl.dev and list top-level sections.”
3. “Use Firecrawl to crawl the first level of https://docs.firecrawl.dev and summarize the main sections.”

CLI-only checks from a terminal:

```bash
firecrawl --status
firecrawl search "firecrawl web scraping" --limit 3 --json
```

The `_local/` directory is gitignored; use it in your clone for any markdown or notes you do not want committed.

## License

MIT — see [LICENSE](LICENSE).
