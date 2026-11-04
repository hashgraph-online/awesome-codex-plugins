# Platform Notes: How Each Answer Engine Finds Sources

Verified against primary documentation on 2026-10-23 unless marked otherwise.
Answer engines change retrieval, crawlers, and reporting often. Re-check the
linked source before a client deliverable states any of this as current.

Only documented behavior belongs here. Third-party "ranking factor" studies
(domain-authority weights, freshness multipliers, citation shares by site) are
correlational, usually vendor-funded, and rarely reproducible. Do not quote
them as facts.

## Google AI Overviews and AI Mode

- Rooted in core Search ranking and quality systems. "There are no additional
  requirements to appear in AI Overviews or AI Mode, nor other special
  optimizations necessary."
- Eligibility: indexed and eligible to show with a snippet. Indexing and
  serving are not guaranteed.
- Query fan-out: both may issue multiple related searches across subtopics and
  data sources, which can surface a wider set of supporting links than classic
  results. AI Overviews show only when judged additive and often do not trigger.
  AI Mode and AI Overviews can use different models, so links differ.
- Google's optimization guide (last updated 2026-07-10): no special schema,
  AI text files, markup, or Markdown needed; no need to break content into tiny
  pieces; no special writing style; mass-producing pages to manipulate rankings
  or AI responses violates the scaled content abuse policy. It also warns about
  tools claiming access to internal Google metrics.
- Recommended fundamentals: allow crawling (robots.txt and the CDN or host
  layer), internal links, good page experience, important content in text,
  structured data that matches visible text, current Merchant Center and
  Business Profile data for commerce and local.
- Controls: `nosnippet`, `data-nosnippet`, `max-snippet`, `noindex` limit what
  appears. `Google-Extended` controls Gemini training and grounding in Gemini
  Apps and Vertex AI; Google says it does not affect Search inclusion or
  ranking and is not a Search ranking signal.
- Reporting: AI feature traffic is counted in the Performance report under
  search type Web. Google introduced a Search Generative AI performance report
  in June 2026: impressions by page, country, device (Search only), and date;
  no click or query data; hidden for sites below an unpublished impressions
  threshold. Rollout status should be checked in the property itself.
- Agentic experiences: Google names the Universal Commerce Protocol (UCP) as
  emerging, not a current requirement.

Sources:
- https://developers.google.com/search/docs/appearance/ai-features
- https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
- https://developers.google.com/search/blog/2026/06/gen-ai-performance-reports
- https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers

## ChatGPT search (OpenAI)

- `OAI-SearchBot` determines whether a site can appear in ChatGPT search
  answers. Sites opted out "will not be shown in ChatGPT search answers, though
  can still appear as navigational links."
- `GPTBot` is for foundation-model training. Blocking it does not remove a site
  from ChatGPT search.
- `ChatGPT-User` handles user-initiated fetches; robots.txt may not apply and it
  does not decide search inclusion.
- `OAI-AdsBot` validates pages submitted as ChatGPT ads only.
- robots.txt changes take about 24 hours to apply.
- ChatGPT links commonly carry `utm_source=chatgpt.com`; confirm in your own
  GA4 data rather than assuming every click is tagged.

Source: https://developers.openai.com/api/docs/bots

## Claude (Anthropic)

- `ClaudeBot`: collects content that may be used for model training.
- `Claude-SearchBot`: indexes content to improve search result quality;
  blocking it may reduce visibility in Claude's search answers.
- `Claude-User`: fetches pages when a user asks Claude a question; blocking it
  prevents retrieval for user queries.
- All honor robots.txt per Anthropic; IP blocking is not a reliable opt-out.
  Each subdomain needs its own robots.txt. Verify source IPs against Anthropic's
  published list.
- Search index: Anthropic's crawler documentation does not name one. Its
  subprocessor list has named Brave Search for web search since March 2025
  (widely reported at the time; confirm against the current list before a
  client deliverable quotes it). Treat Brave as the practical place to check,
  not as a documented ranking dependency.
- Check whether the site appears at search.brave.com for the brand and key
  terms. If it is missing, request a crawl at search.brave.com/submit-url. That
  page only alerts Brave's crawler: there is no webmaster console and no sitemap
  submission, so confirm the result by watching referrals from
  search.brave.com in analytics.

Sources:
- https://support.claude.com/en/articles/8896518
- Report of the Brave subprocessor entry:
  https://simonwillison.net/2025/Mar/21/anthropic-use-brave/
- https://search.brave.com/submit-url

## Perplexity

- `PerplexityBot` surfaces and links sites in Perplexity results and is not used
  to crawl content for AI foundation models. Perplexity recommends allowing it.
- `Perplexity-User` fetches for user questions and generally ignores robots.txt.
- Changes may take up to 24 hours.

Source: https://docs.perplexity.ai/docs/resources/perplexity-crawlers

## Microsoft Copilot and Bing

- Copilot grounds answers on the Bing index; a page Bing has not indexed cannot
  be cited there. Verify the site in Bing Webmaster Tools, submit sitemaps, and
  allow `Bingbot`.
- Bing Webmaster Tools AI Performance report (public preview, February 2026):
  total citations, unique cited pages, page-level citation counts, and the
  grounding queries that triggered citations, exportable as CSV; no API at
  preview. Grounding queries are Bing's interpretation of the request, not the
  user's typed prompt. No click data, and no mapping from a query to a specific
  citation.
- IndexNow notifies participating engines (including Bing) of changed URLs.
  Google does not participate.

Sources:
- https://www.bing.com/webmasters
- https://www.indexnow.org/
- Secondary report of the AI Performance preview:
  https://www.searchinfluence.com/blog/bing-ai-performance-report-copilot-citations/

## Gemini app

- Grounds on Google Search. `Google-Extended` opts content out of Gemini
  training and Gemini Apps grounding without touching Search.

## What this means for prioritization

1. Google: classic SEO plus original, people-first content. No AI-only tactics.
2. ChatGPT: allow `OAI-SearchBot`; earn corroboration on sites ChatGPT cites.
3. Copilot: Bing indexation and IndexNow; read the AI Performance report.
4. Perplexity and Claude: allow their search and user agents; publish quotable,
   sourced passages. For Claude, confirm the site is in Brave's index.
5. Everywhere: one consistent entity and third-party consensus.
