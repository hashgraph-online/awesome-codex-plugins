# storyflo Codex Plugin

A Codex plugin that wraps [storyflo](https://www.storyflo.com)'s hosted MCP
server — an **agentic newsroom**. Install it to give Codex narrated news
briefings, the news-versus-prediction-market **Divergence Index**, a
**declassified archive** of released intelligence cases, and vertical (topic-area)
intelligence, all as source-grounded editorial context.

storyflo returns editorial signal and narrated context. It does **not** return
raw prediction-market odds or probabilities — the Divergence Index is a
qualitative signal, not a price feed.

## What storyflo is

storyflo is an agentic newsroom: it aggregates and narrates the news, tracks
where the news narrative is diverging from prediction-market sentiment, and
maintains a searchable archive of declassified intelligence cases. This plugin
exposes that newsroom to Codex over a single remote MCP endpoint.

## What the MCP server exposes

- **Narrated briefings** — daily and per-vertical briefings you can read or
  listen to (`get_daily_briefing`, `get_vertical_briefing`, `digest`,
  `list_podcasts`, `get_audio_url`).
- **Divergence Index** — a qualitative signal of where the news narrative is
  diverging from prediction-market sentiment, with the underlying market-linked
  stories (`get_divergence_index`, `get_market_linked_stories`).
- **Discovery & articles** — trending topics, full-text search, single-article
  fetch, and topic subscriptions (`get_trending_topics`, `search_articles`,
  `get_article`, `subscribe_topic`).
- **Declassified archive** — search, open, and digest released intelligence
  cases (`search_declassified`, `get_declassified_case`, `digest_declassified`).
- **Vertical intelligence** — the landscape of a topic area: entities, threads,
  and momentum (`get_vertical_landscape`).

## Add it to Codex

This plugin connects to storyflo's hosted MCP server over HTTPS
Server-Sent Events. No credentials are bundled in this repo, and none are
needed to install it.

**Two tiers, and it is worth knowing which is which before you call
something.** Measured against the live server on 2026-09-12:

*Callable with no credential at all* — the agent-discovery surface:
`get_trending_topics`, `get_personas`, `get_vertical_landscape`,
`list_podcasts`, `get_divergence_index`, the whole declassified library
(`search_declassified`, `get_declassified_case`, `digest_declassified`,
`subscribe_declassified_topic`), the publisher and fund-manager desk tools
(these carry their own access token in the call arguments), and the
partnership tools (`quote_partnership`, `register_embedder`).

*Require an OAuth bearer token, scope `articles:read`* — `search_articles`,
`get_article`, `get_audio_url`, `digest`, `list_subscriptions`,
`subscribe_topic`, `get_market_linked_stories`, `get_crypto_market_link`,
`get_vertical_briefing`.

A call without a token returns `401` with a `WWW-Authenticate` header
pointing at
`https://api.storyflo.com/.well-known/oauth-protected-resource/mcp/v1`.
Clients that support MCP OAuth complete that flow automatically; the
authorization server supports dynamic client registration, so there is
nothing to request by email and no key to paste.

An earlier version of this file said "No API key is required for the public
tools" without that split, which read as though `search_articles` would just
work. It does not — it 401s — and an agent that is told otherwise fails on
its first useful call.

The server is configured in [`.mcp.json`](./.mcp.json):

```json
{
  "mcpServers": {
    "storyflo": {
      "url": "https://api.storyflo.com/v1/mcp/sse",
      "type": "sse"
    }
  }
}
```

Install this repo as a Codex plugin (via the HOL registry or by pointing a
marketplace source at this repository), and the `storyflo` MCP server plus the
bundled [`storyflo` skill](./skills/storyflo/SKILL.md) become available to your
agent.

## Example prompts

- "Pull today's storyflo daily briefing and summarize the top stories as a
  narrated digest."
- "Read the storyflo Divergence Index and tell me where the news narrative is
  diverging from prediction-market sentiment right now."
- "Search the storyflo declassified archive for recently released intelligence
  cases on this topic and open the most relevant one."

## Contents

```
.codex-plugin/plugin.json   # plugin manifest
.mcp.json                   # remote MCP server (SSE) configuration
skills/storyflo/SKILL.md    # skill teaching agents how/when to use storyflo
assets/icon.png             # composer icon (512x512)
assets/logo.svg             # storyflo mark
SECURITY.md                 # vulnerability disclosure policy
LICENSE                     # MIT
```

## Security

See [`SECURITY.md`](./SECURITY.md). Report vulnerabilities privately to
[story@storyflo.com](mailto:story@storyflo.com).

## Links

- Website: [https://www.storyflo.com](https://www.storyflo.com)
- MCP endpoint: `https://api.storyflo.com/v1/mcp/sse`

## License

[MIT](./LICENSE) © 2026 Storyflo
