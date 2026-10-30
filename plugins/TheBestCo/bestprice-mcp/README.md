# BestPrice MCP

[![CI](https://github.com/TheBestCo/bestprice-mcp/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/TheBestCo/bestprice-mcp/actions/workflows/test.yml)
[![Glama score](https://glama.ai/mcp/servers/TheBestCo/bestprice-mcp/badges/score.svg)](https://glama.ai/mcp/servers/TheBestCo/bestprice-mcp)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

The official [Model Context Protocol](https://modelcontextprotocol.io/) server for
[BestPrice.gr](https://www.bestprice.gr/), Greece's price-comparison service. It gives AI
assistants read-only access to shopping decisions, live product search, offer comparison,
and price history. No account or API key is needed.

![BestPrice MCP: products, offers and price history for AI assistants](https://www.bestprice.gr/extra/mcpLanding/assets/bestprice-mcp-share.png)

## Start shopping

- The [ChatGPT plugin](https://chatgpt.com/plugins/plugin_asdk_app_6a8d8ed6e2bc8191b3caaf7214f3c981) is temporarily unavailable while the updated version is under review. Developer integrations can still call the public endpoint below.
- [Connect BestPrice to Claude](https://claude.ai/customize/connectors?modal=add-custom-connector&connectorName=BestPrice&connectorUrl=https%3A%2F%2Fmcp.bestprice.gr%2Fmcp) using the prefilled connector form.
- See the [shopping guide](https://www.bestprice.gr/en/mcp) for examples and other assistants.

For developer integrations, the public endpoint is:

```text
https://mcp.bestprice.gr/mcp
```

- Transport: Streamable HTTP over HTTPS; anonymous shopping, optional OAuth for Events
- Official Registry ID: `gr.bestprice/mcp`
- Server version: `1.8.5`
- Public guide: <https://www.bestprice.gr/mcp>
- Support: <https://www.bestprice.gr/contact>

This repository holds everything that lives outside the hosted service: the install
manifests for each AI client, a local stdio bridge for hosts that cannot speak HTTP, and
the browser-native WebMCP layer. The server itself is not in this repository.

The [current release matrix](submission/current-release-matrix.md) records the
live gateway, UI, OAuth/Events, plugin review and separate ACP qualification.

## Tools

| Tool | What it does | Key arguments |
| --- | --- | --- |
| `get_shopping_decision` | Runs the BestPrice Shopping Brain: an evidence-backed recommendation, need-based comparison, or read-only basket plan with reasons, tradeoffs, and unknowns. | `message` (the need in Greek or English, including any budget), optional `postal_code` (required for a completed basket plan), optional `evidence_detail` (`summary`, the default: only the evidence the answer cites; `full`: every claim and source) |
| `search_products` | Finds canonical products in the catalog. Returns product IDs and the catalog minimum price before shipping. | `query` (2–400 characters: a name, model, category, or a bare GTIN/EAN barcode), optional `price_min`, `price_max`, `required_features`, `sort` (`relevance`, `price_asc`, `price_desc`), `limit` (1–8) |
| `compare_offers` | Compares current merchant offers for one exact product, separating item price, shipping, and delivered total. | `product_id` from a previous result, optional `postal_code` (a Greek postcode, 10000–85999, for delivered totals), `objective`, `in_stock_only`, `minimum_merchant_rating`, `limit` (1–10) |
| `get_price_history` | Summarises how a product's price moved over time, against its 180-day median. | `product_id`, optional `period_days` (30, 90 or 180) |

All four tools are read-only. They never place orders, create alerts, or read account
data. Results link to a BestPrice product page, never directly to a merchant. Unknown
shipping is reported as unknown, not as free. Search covers safe physical products;
digital goods, services, and age-restricted categories are excluded.

## Protocol details

Measured against the live endpoint on 24 September 2026.

- **Versions.** `initialize` negotiates `2025-11-25`, `2025-06-18`, `2025-03-26`, `2024-11-05`
  and `2024-10-07`; a client that asks for any other version is answered with `2025-11-25`.
  The `2026-07-28` per-request revision is also served: send the `MCP-Protocol-Version`,
  `Mcp-Method` (and, for `tools/call`, `Mcp-Name`) headers, and put
  `io.modelcontextprotocol/protocolVersion` and `io.modelcontextprotocol/clientCapabilities` in
  every request's `_meta`. A request that names the revision without that envelope is refused
  with `-32602`.
- **Stateless.** No `MCP-Session-Id` is issued and none is required; `DELETE` answers `405`.
  A `GET` with `Accept: text/event-stream` answers immediately with the SSE comment `: connected`
  and `retry: 300000`, then holds the connection open. It does not send JSON-RPC requests or
  notifications on that stream. Rechecked 29 October 2026. A client loses nothing by not opening it,
  and must not wait for the stream to end.
- **Capabilities.** `tools` and `resources` are available to compatible clients. The
  resource surface contains the optional MCP Apps UI at `ui://bestprice/shopping-results-v1.html`,
  the server card at `mcp://server-card.json`, and the canonical
  `skill://bestprice-shopping/SKILL.md`. On MCP `2026-07-28` the server also declares the
  final `io.modelcontextprotocol/skills` extension: `skills/list` and `skills/get` return the
  one BestPrice Shopping Skill with its SHA-256 digest and byte size, and `resources/read`
  returns the exact markdown bytes. Older clients simply see the Skill as an ordinary resource.
  There are no prompts, completions or logging; those methods answer `-32601`.
- **Responses.** A client that accepts both `application/json` and `text/event-stream` gets a
  one-event SSE response. `Accept: application/json`, `*/*` or no `Accept` header gets a single
  JSON body. Every tool returns `structuredContent` that validates against its `outputSchema`,
  plus the same result as text for clients that do not pass structured content to the model.
- **Errors.** An unknown tool is a JSON-RPC error (`-32602`). Invalid arguments and service
  failures such as an unknown product are tool results with `isError: true`, so the model can
  read and correct them.
- **Limits.** JSON request bodies up to 256 KiB (`413` above that), a 12-second request
  deadline, and per-client rate limits answered with HTTP `429`, JSON-RPC error `-32029` and a
  `Retry-After` header. JSON-RPC batch arrays are refused with `400`.
- **Browsers.** Desktop, CLI and server-side clients send no `Origin` header and are not
  affected. A browser page may call the endpoint from an allowlisted AI-host origin, from
  bestprice.gr, or from `localhost` (so MCP Inspector works in direct mode); any other origin
  gets `403`.
- **Authentication.** The four shopping tools work without an account. Optional account
  linking is scoped to `events:subscribe`; protected-resource metadata is available at
  `/.well-known/oauth-protected-resource` and `/mcp/oauth-protected-resource`.
  Events remains disabled during end-to-end qualification.

## Developer quick start

Every client below connects to the same endpoint. Copy-paste connector setup for Perplexity,
Claude, ChatGPT developer mode, Gemini CLI, Copilot, Grok Bot, and Cursor is in
[`docs/connect.md`](docs/connect.md). Longer provider notes, including OpenAI and Microsoft
Copilot Studio, are in [`docs/provider-setup.md`](docs/provider-setup.md).

### Claude

[Connect BestPrice to Claude](https://claude.ai/customize/connectors?modal=add-custom-connector&connectorName=BestPrice&connectorUrl=https%3A%2F%2Fmcp.bestprice.gr%2Fmcp)
opens the custom-connector flow with the endpoint prefilled. For Claude Code:

```sh
claude mcp add --transport http bestprice-shopping https://mcp.bestprice.gr/mcp
```

The bundled [`.mcp.json`](.mcp.json) is the equivalent project-scoped configuration.

### Cursor

[Add BestPrice to Cursor](https://cursor.com/install-mcp?name=bestprice-shopping&config=eyJ1cmwiOiJodHRwczovL21jcC5iZXN0cHJpY2UuZ3IvbWNwIn0%3D)
shows the decoded configuration before adding it. The [`.cursor-plugin/`](.cursor-plugin/)
directory holds the marketplace plugin and an agent skill.

### VS Code and VS Code Insiders

[Add BestPrice to VS Code](vscode:mcp/install?%7B%22name%22%3A%22bestprice-shopping%22%2C%22type%22%3A%22http%22%2C%22url%22%3A%22https%3A%2F%2Fmcp.bestprice.gr%2Fmcp%22%7D)

[Add BestPrice to VS Code Insiders](vscode-insiders:mcp/install?%7B%22name%22%3A%22bestprice-shopping%22%2C%22type%22%3A%22http%22%2C%22url%22%3A%22https%3A%2F%2Fmcp.bestprice.gr%2Fmcp%22%7D)

### Kiro

[Add BestPrice to Kiro](https://kiro.dev/launch/mcp/add?name=bestprice-shopping&config=%7B%22url%22%3A%22https%3A%2F%2Fmcp.bestprice.gr%2Fmcp%22%2C%22disabled%22%3Afalse%2C%22autoApprove%22%3A%5B%5D%7D)
opens Kiro's confirmation dialog with the remote URL. Kiro shows the configuration before writing it.

### Gemini CLI and Qwen Code

```sh
gemini extensions install https://github.com/TheBestCo/bestprice-mcp
qwen extensions install https://github.com/TheBestCo/bestprice-mcp --consent
```

Both extensions restrict the imported tools to the four listed above.

### Codex, Claude plugins, and Agent Skill hosts

The root [`plugin.json`](plugin.json), [`mcp.json`](mcp.json), and
[`skills/bestprice-shopping/SKILL.md`](skills/bestprice-shopping/SKILL.md) form a portable
Agent Plugins package: the MCP supplies live shopping data and the Skill teaches the host when and
how to route unbranded Greek shopping intent.
Agent-compatible hosts that discover repository-local skills under `.agents/skills/` get the
same canonical workflow at [`.agents/skills/bestprice-shopping/SKILL.md`](.agents/skills/bestprice-shopping/SKILL.md). [`.codex-plugin/`](.codex-plugin/) remains the
Codex compatibility manifest. [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json) plus the
same root Skill and [`.mcp.json`](.mcp.json) also make this repository a Claude plugin package.


### Self-hosted plugin marketplaces

The same repository can be added directly as a plugin marketplace, with no copied tool or Skill logic:

```sh
copilot plugin marketplace add TheBestCo/bestprice-mcp
copilot plugin install bestprice-shopping@bestprice

claude plugin marketplace add TheBestCo/bestprice-mcp
claude plugin install bestprice-shopping@bestprice
```

Copilot reads [`.github/plugin/marketplace.json`](.github/plugin/marketplace.json) and, under
Agent Plugins 1.0, loads the canonical root `plugin.json`, `mcp.json`, and
`skills/bestprice-shopping/SKILL.md`. Claude reads
[`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json) and uses
`.claude-plugin/plugin.json`, `.mcp.json`, and the same root Skill.

### Gemini API, DeepSeek, Z.ai

Runnable examples live in [`examples/`](examples/): the Gemini Interactions API and Genkit,
a DeepSeek Harness plugin entry, and a Z.ai GLM call. Each needs the provider's own API key.
BestPrice needs none.

### Any other MCP client

Add the hosted Streamable HTTP endpoint. That is the install path:

```text
https://mcp.bestprice.gr/mcp
```

Hosts that read an `mcpServers` JSON configuration accept:

```json
{
  "mcpServers": {
    "bestprice-shopping": {
      "url": "https://mcp.bestprice.gr/mcp"
    }
  }
}
```

A checkout of this repository includes `stdio.mjs`, a local forwarder to that same
endpoint for a host that cannot speak HTTP. From a checkout you already have for
development, run `node stdio.mjs`. It accepts two environment variables:
`BESTPRICE_MCP_URL` (default: the public endpoint) and `BESTPRICE_MCP_TIMEOUT_MS`
(default: 60000). A `Dockerfile` builds the same forwarder for
[Glama](https://glama.ai/mcp/servers/TheBestCo/bestprice-mcp) and similar hosts. It is
not an install command and it does not download or execute a remote package.

This package is private. It is not published to npm under `bestprice-mcp` or any scoped name.
There is no registry package to install or to run with npx. A directory that shows an npm
install for version 1.2.7 is repeating a stale crawler inference; that version is not in the
npm registry.

## A safe first conversation

1. Ask for a decision: `Θέλω κινητό έως 500 ευρώ με NFC και 5G υποχρεωτικά.`
   (I want a phone up to 500 euros, NFC and 5G required.)
2. Or search: `Find Sony WH-1000XM5 under 300 euros.`
3. Pass a returned `product_id` to `compare_offers` with postal code `10558`.
4. Pass the same `product_id` to `get_price_history` for 180 days.

Queries work in Greek or English. Result summaries, catalog data and merchant names come back in Greek.

| Search | Compare offers | Price history |
| --- | --- | --- |
| ![search_products in Claude](docs/images/claude-search-products.png) | ![compare_offers in Claude](docs/images/claude-compare-offers.png) | ![get_price_history in Claude](docs/images/claude-price-history.png) |

## Browser-native WebMCP

BestPrice pages register 22 contextual WebMCP tools (contract 2.8) in compatible browsers — each one
reads or acts, never both — covering search with structured results (narrowed by price, stock, deals and
order) and opening the results page a search returned in the tab, the shopper's shopping list and
comparisons (read everywhere, added to and removed from on a product page), a price-drop alert dialog, the visible products and loading more, filters and sorting,
opening any product by id (read before the tab moves), product facts, offers, specifications and price
history (with its chart), one visible-offer action, and the BestPrice Shopping Brain — on every public
page, articles and stores included — while leaving the merchant choice to the shopper. Every tool publishes an input and an output
schema. The contracts, fail-closed runtime, deterministic evaluator, and the 47-case natural-language
dataset are in [`webmcp/`](webmcp/).

## Discovery

- [Official MCP Registry](https://registry.modelcontextprotocol.io/v0.1/servers?search=gr.bestprice%2Fmcp)
- Open agent discovery: [`ard.json`](https://www.bestprice.gr/.well-known/ard.json),
  [`ai-catalog.json`](https://www.bestprice.gr/.well-known/ai-catalog.json),
  [server card](https://mcp.bestprice.gr/mcp/server-card), and the
  provider-neutral [BestPrice Shopping skill](skills/bestprice-shopping/SKILL.md).
  The ARD examples are deliberately unbranded shopper intents so discovery can match
  “what should I buy?”, delivered-price, and price-timing requests before a user knows BestPrice.
- [`webmcp.json`](https://www.bestprice.gr/.well-known/webmcp.json) describes the contextual
  browser tools exposed by BestPrice pages.
- The repository is listed in the [Gemini CLI extension gallery](https://geminicli.com/extensions/?name=TheBestCobestprice-mcp)
  as `bestprice-shopping` (Google crawls tagged public extension repositories), while GitHub Agent Finder
  can ingest the public MCP catalog and ARD resources.
- Copy-ready, CI-pinned external catalog contributions live under [`distribution/`](distribution/):
  a GitHub Agent Finder Skill entry and a Docker MCP Registry remote-server entry. Those catalogs
  require review in their own repositories; the checked-in files are submission payloads, not claims
  that the external listings are already live.
- Community indexes: [Glama](https://glama.ai/mcp/servers/TheBestCo/bestprice-mcp),
  [WebMCP Registry](https://webmcp-registry.dev/domain/www.bestprice.gr),
  [webmcp.com](https://webmcp.com/sites/bestprice.gr),
  [cursor.directory](https://cursor.directory/plugins/bestprice-shopping)

## Development

```sh
npm ci
npm run check   # Biome lint and format
npm test        # node --test: bridge, WebMCP, manifests, dataset
```

Tests need no network: the bridge is exercised against an in-process fake remote. Node 20
or newer is required; `.nvmrc` pins 22.

## Versioning

Two versions appear in this repository on purpose:

- **Package version** in `package.json` and every plugin or extension manifest. It changes
  when this repository's manifests, bridge, or WebMCP layer change, and is tagged `vX.Y.Z`.
- **Server version** in `server.json` and the line near the top of this README. It is the
  version the hosted service reports and is published to the official MCP Registry.

`CHANGELOG.md` tracks the package version.

Timestamped hosted-service checks are recorded separately. The
[7 September Shopping Brain v12 verification](docs/releases/2026-09-07-brain-v12.md)
includes its exact gateway revision, sanitized canary results, and scope limits.

## Security

Report vulnerabilities privately as described in [`SECURITY.md`](SECURITY.md).

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Issues and pull requests are welcome.

## License

Apache License 2.0. Copyright The Best Company S.A. See [`LICENSE`](LICENSE).

Privacy: <https://www.bestprice.gr/policies/privacy> · Terms: <https://www.bestprice.gr/policies/terms>
