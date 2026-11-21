# AI Crawler Policy

Checked against each operator's documentation on 2026-10-23. Sources are in
`platform-notes.md`. Re-check before shipping a robots.txt change.

## User-agent reference

| Token | Operator | Purpose | Blocking it means | Honors robots.txt |
|---|---|---|---|---|
| `Googlebot` | Google | Search crawling, including AI Overviews and AI Mode | Out of Google Search and its AI features | Yes |
| `Google-Extended` | Google | Product token for Gemini training and Gemini Apps / Vertex AI grounding | No Gemini training or grounding use; Search unaffected | Yes (token, no separate crawler) |
| `OAI-SearchBot` | OpenAI | ChatGPT search index | Not shown in ChatGPT search answers | Yes |
| `GPTBot` | OpenAI | Foundation-model training | Excluded from training; ChatGPT search unaffected | Yes |
| `ChatGPT-User` | OpenAI | User-initiated fetches | Rules may not apply | Not reliably |
| `ClaudeBot` | Anthropic | Training data collection | Future content excluded from training | Yes |
| `Claude-SearchBot` | Anthropic | Search indexing for Claude | Reduced visibility in Claude search answers | Yes |
| `Claude-User` | Anthropic | Fetches for a user's question | Claude cannot retrieve the page for users | Yes |
| `PerplexityBot` | Perplexity | Search index and links; not training | Not surfaced in Perplexity results | Yes |
| `Perplexity-User` | Perplexity | User-initiated fetches | Generally ignores robots.txt | No |
| `Bingbot` | Microsoft | Bing index, which grounds Copilot | Out of Bing and Copilot citations | Yes |
| `CCBot` | Common Crawl | Open web corpus used by many model builders | Excluded from Common Crawl | Yes |

`anthropic-ai` appears in older guides. Anthropic's current article names only
the three Claude agents above; an extra group for it is harmless but optional.

## Default Suede configuration for a brand that wants citations

Allow retrieval, decide training separately. Present the training lines as
the user's licensing decision, not a recommendation either way.

```text
# Search and answer retrieval: allow
User-agent: Googlebot
User-agent: Bingbot
User-agent: OAI-SearchBot
User-agent: Claude-SearchBot
User-agent: Claude-User
User-agent: PerplexityBot
Allow: /

# Model training: the owner's call (shown here opted out)
User-agent: GPTBot
User-agent: ClaudeBot
User-agent: Google-Extended
User-agent: CCBot
Disallow: /

User-agent: *
Allow: /
Disallow: /admin/

Sitemap: https://example.com/sitemap.xml
```

A named group replaces the `*` group for that bot, so repeat any private-path
`Disallow` lines inside named groups if they must apply.

## Checks robots.txt cannot answer

- CDN, WAF, or bot-management rules returning 403 or challenges to these
  agents. Check firewall logs or test with the operator's published IP ranges.
- `noindex`, `nosnippet`, `max-snippet:0`, or `data-nosnippet` on key content.
- Content that only renders after client-side JavaScript. Several AI fetchers
  do not execute JavaScript; compare raw HTML with the rendered DOM.
- Login walls, cookie walls, and geo-blocks on the pages you want cited.

## Verification steps

1. Fetch `/robots.txt` (and each relevant subdomain's) and record status.
2. Classify each token above as allowed, blocked, or unverified.
3. Grep server or CDN logs for each user agent over 30 days; confirm 200s on
   priority pages. Verify IPs against the operator's list before trusting a UA
   string.
4. Re-check 24 to 48 hours after any change.
