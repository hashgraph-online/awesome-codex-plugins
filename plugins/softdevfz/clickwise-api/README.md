# Clickwise API: products by GTIN, tracked affiliate links, MCP

[![MCP Registry](https://img.shields.io/badge/MCP%20Registry-net.clickwise%2Fmcp-0b7285)](https://registry.modelcontextprotocol.io/v0/servers?search=net.clickwise/mcp)
[![OpenAPI 3.1](https://img.shields.io/badge/OpenAPI-3.1-6ba539)](https://partners.clickwise.net/api/v1/publisher/openapi.json)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

[Clickwise](https://partners.clickwise.net/developers/) is an affiliate network with an API built for developers and AI agents. Search **product feeds with GTINs from the networks**, get product links **tracked to you**, find and join affiliate programs, and pull your conversions. Use it over REST, from an AI agent through **MCP**, or from HasOffers-compatible tools.

This repo gets you from zero to a working call: quickstarts, thin clients, MCP configs and a deployable affiliate store.

## 1. First call, no key

```sh
# How big is the catalog right now?
curl -s https://partners.clickwise.net/api/v1/public/catalog-stats/

# Sample products in one market (DE, ES, GB, PT, SE, FR, US); no links without a key
curl -s "https://partners.clickwise.net/api/v1/public/catalog-sample/?country=DE"

# Ask the MCP server which programs fit your site
curl -s https://partners.clickwise.net/api/v1/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"find_affiliate_programs","arguments":{"topic":"sneakers","country":"ES","channel":"site"}}}'
```

## 2. Get your key

Request a publisher API key at **<https://partners.clickwise.net/developers/>**. Put it in an environment variable and keep it on your server:

```sh
export CLICKWISE_API_KEY=...   # never commit it, never ship it to a browser
```

## 3. First call with your key

```sh
# Who am I, what can this key do, what are my limits?
curl -s https://partners.clickwise.net/api/v1/publisher/me/ -H "X-API-Key: $CLICKWISE_API_KEY"

# Price, stock and YOUR tracked link for up to 100 GTINs
curl -s --get https://partners.clickwise.net/api/v1/publisher/products/lookup/ \
  -H "X-API-Key: $CLICKWISE_API_KEY" \
  --data-urlencode 'gtins=4006381333931,5901234123457' --data-urlencode 'country=DE'

# Search by title in one market
curl -s --get https://partners.clickwise.net/api/v1/publisher/products/ \
  -H "X-API-Key: $CLICKWISE_API_KEY" \
  --data-urlencode 'q=sneaker' --data-urlencode 'country=GB' --data-urlencode 'limit=20'

# Same kind of search in Germany (publisher key or sandbox key)
curl -s --get https://partners.clickwise.net/api/v1/publisher/products/ \
  -H "X-API-Key: $CLICKWISE_API_KEY" \
  --data-urlencode 'q=smartwatch' --data-urlencode 'country=DE' --data-urlencode 'limit=20'
```

Each product comes back as `{"gtin", "title", "price", "currency", "image", "url", "merchant", "availability", ...}`. **`url` is your tracked link**: publish it exactly as returned.

Runnable versions of steps 1 and 3: [`quickstart/curl.sh`](quickstart/curl.sh) · [`quickstart/quickstart.mjs`](quickstart/quickstart.mjs) (Node 18+) · [`quickstart/quickstart.py`](quickstart/quickstart.py) (Python 3.8+). No dependencies.

## 4. Use it from an AI agent (MCP)

Remote MCP server (Streamable HTTP): **`https://partners.clickwise.net/api/v1/mcp`**, listed in the official MCP Registry as `net.clickwise/mcp`. The key is optional: program discovery, deals, catalog stats and provisional tracked links work without it.

```sh
# Claude Code
claude mcp add --transport http clickwise https://partners.clickwise.net/api/v1/mcp --header "X-API-Key: $CLICKWISE_API_KEY"

# OpenAI Codex CLI
codex mcp add clickwise --url https://partners.clickwise.net/api/v1/mcp

# Gemini CLI
gemini mcp add --transport http clickwise https://partners.clickwise.net/api/v1/mcp
```

### Plugins, extensions and skills

- **Claude Code plugin** (MCP server plus the skill below): `/plugin marketplace add softdevfz/clickwise-api`, then `/plugin install clickwise@clickwise`. Set `CLICKWISE_API_KEY` in your environment to use the tools that need a key.
- **Codex plugin** (same MCP server and skill): `codex plugin marketplace add softdevfz/clickwise-api`, then `codex plugin add clickwise@clickwise`. The key, if set, is read from `CLICKWISE_API_KEY`.
- **Antigravity CLI plugin**: `agy plugin install https://github.com/softdevfz/clickwise-api`.
- **Gemini CLI extension**: `gemini extensions install https://github.com/softdevfz/clickwise-api`. It adds the MCP server and [`GEMINI.md`](GEMINI.md) as context.
- **Agent Skill** for any agent that reads `SKILL.md` (Claude, Codex and others): [`skills/clickwise-affiliate-links`](skills/clickwise-affiliate-links/SKILL.md). Copy the folder into your agent's skills directory.

Configs for **Claude Code, Cursor, Claude Desktop, VS Code, ChatGPT, Grok and n8n**, plus the tool list, in [`mcp/`](mcp/README.md).

Earn commission from your AI assistant (product search, sub-IDs and signed postbacks): [`quickstart/monetize-agent.md`](quickstart/monetize-agent.md).

## 5. Ship an affiliate store

[`templates/affiliate-store`](templates/affiliate-store): a Next.js storefront that reads products by GTIN, shows live prices and publishes your tracked links. It deploys without a key in preview mode.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fsoftdevfz%2Fclickwise-api&root-directory=templates%2Faffiliate-store&project-name=my-affiliate-store&repository-name=my-affiliate-store)
[![Deploy to Netlify](https://www.netlify.com/img/deploy/button.svg)](https://app.netlify.com/start/deploy?repository=https://github.com/softdevfz/clickwise-api)

Building with **Lovable, Bolt or v0**? Paste [`templates/affiliate-store/PROMPT.md`](templates/affiliate-store/PROMPT.md).

Running your own app or SaaS? Paste [`templates/merchant-tracking/PROMPT.md`](templates/merchant-tracking/PROMPT.md) into Lovable, Bolt or v0 to add Clickwise sales tracking with Stripe, Lemon Squeezy or the conversions API.

## 6. Clients

Thin, dependency-free clients generated from the OpenAPI, one method per operation:

- **TypeScript**: [`clients/typescript/clickwise.ts`](clients/typescript) (copy one file; Node, Bun, Deno, edge).
- **Python**: [`clients/python`](clients/python) (`pip install "git+https://github.com/softdevfz/clickwise-api#subdirectory=clients/python"`).

```ts
const cw = new Clickwise(); // CLICKWISE_API_KEY
const { products } = await cw.lookupProducts({ gtins: "4006381333931", country: "DE" });
```

## What the API covers

| Area | Endpoints (`/api/v1/publisher/…`) |
|---|---|
| Products | `GET products/` search · `GET products/lookup/` by id or GTIN (1–100) |
| Programs | `GET programs/` · `GET programs/joinable/` · `POST programs/apply/` |
| Links | `GET/POST links/` · `POST links/batch/` (up to 50, each with its own status) |
| Reporting | `GET conversions/` · `GET reports/` (day, week, month, sub-ID, campaign, status) · `GET clicks/` |
| Postbacks | `GET postback/` · `POST postback/test/` · `GET postback/deliveries/` (signed HMAC webhooks) |
| Account | `GET me/`: access and rate limits for your key |

One error shape (`{"error": {"code", "message", "status", "request_id"}}`), `RateLimit-*` headers on every response, `Retry-After` on 429, `Idempotency-Key` on POST, `X-Request-Id` everywhere. Changes inside v1 are additive.

## Reference

- Developer hub: <https://partners.clickwise.net/developers/>
- OpenAPI 3.1: <https://partners.clickwise.net/api/v1/publisher/openapi.json> (snapshot in [`openapi/`](openapi/openapi.json))
- Postman collection: <https://partners.clickwise.net/api/v1/publisher/postman.json>
- For LLMs: <https://partners.clickwise.net/llms.txt>
- Video walkthrough: [Clickwise for developers and AI agents: API, MCP server and sandbox key](https://youtu.be/tyN8JzoA75w) · [Short](https://youtu.be/oU-1Q9BLU1U)
- Guía en español: [Conecta tu asistente de IA a ofertas de productos](https://youtu.be/Bk_g05Mytgc)
- MCP: `https://partners.clickwise.net/api/v1/mcp`
- HasOffers/TUNE-compatible affiliate API: `https://partners.clickwise.net/Apiv3/json`

## Rules of the road

- Keep the key on your server. A key acts only for its own account and never has admin access.
- Publish product and tracking links exactly as returned, and disclose affiliate relationships (`rel="sponsored"` on links plus a visible disclosure).
- Refresh prices at least every 48 hours; hide products a lookup no longer returns.
- Honour rate limits: back off on 429 using `Retry-After`.

## Support

Questions and integration help: **partnerships@clickwise.net**. Bugs in this repo: open an issue.

## License

[MIT](LICENSE). Use of the Clickwise API itself is subject to your Clickwise publisher account terms.
