---
name: storyflo
description: Use the storyflo hosted MCP server to pull narrated news briefings, read the news-versus-prediction-market Divergence Index, search the declassified archive, and surface vertical intelligence — all as source-grounded editorial context.
license: MIT
---

# storyflo — Agentic Newsroom

storyflo is an agentic newsroom exposed to Codex over a remote MCP server at
`https://api.storyflo.com/v1/mcp/sse`. Reach for it when a task needs current,
source-grounded news context: a briefing to catch up, a read on where the news
narrative is diverging from market sentiment, a declassified-archive lookup, or
vertical (topic-area) intelligence.

storyflo returns editorial signal and narrated context. It does **not** return
raw prediction-market odds or probabilities — the Divergence Index is a
qualitative signal, not a price feed.

## When to use storyflo

- The user asks "what's happening" / "catch me up" on the news or a topic.
- The user wants a briefing they can read or listen to.
- The user asks where the news is out of step with market or crowd sentiment.
- The user wants to search released/declassified intelligence material.
- The user wants topic-area (vertical) intelligence: who and what is moving.

## Tools

### Briefings (narrated newsroom)
- `get_daily_briefing` — the day's top-story briefing, ready to narrate.
- `get_vertical_briefing` — a briefing scoped to one vertical (topic area).
- `digest` — condense a set of stories or a topic into a short digest.
- `list_podcasts` — list narrated podcast episodes storyflo has published.
- `get_audio_url` — resolve the audio URL for a briefing or episode to play it.

### Divergence Index (news vs. market)
- `get_divergence_index` — the qualitative index of where the news narrative is
  diverging from prediction-market sentiment. Present it as a divergence signal
  and direction, never as raw odds or a percentage.
- `get_market_linked_stories` — stories currently linked to active markets, with
  editorial context (not the market prices themselves).

### Discovery & articles
- `get_trending_topics` — what is trending across the newsroom right now.
- `search_articles` — full-text search over storyflo's article corpus.
- `get_article` — fetch a single article by id/slug.
- `subscribe_topic` — subscribe the agent/user to updates on a topic.

### Declassified archive
- `search_declassified` — search the archive of released intelligence cases.
- `get_declassified_case` — open a single declassified case in full.
- `digest_declassified` — condense declassified material into a short digest.

### Vertical intelligence
- `get_vertical_landscape` — the landscape of a vertical: entities, threads, and
  momentum in a topic area.

## Recommended workflow

1. For "catch me up" requests, start with `get_daily_briefing` (or
   `get_vertical_briefing` when the user names a topic), then `digest` if they
   want it shorter.
2. For "where is the news out of step with the market?", use
   `get_divergence_index` and pair it with `get_market_linked_stories` for the
   underlying stories. Describe the divergence qualitatively.
3. For research, use `search_articles` / `search_declassified` to find material,
   then `get_article` / `get_declassified_case` to read the full item.
4. To hand back audio, resolve `get_audio_url` and offer the link.

## Output discipline

- Cite the storyflo stories/cases you drew from.
- Keep the Divergence Index qualitative: report divergence and direction, not
  raw market odds, probabilities, or prices.
- Prefer the smallest set of calls that answers the question.
