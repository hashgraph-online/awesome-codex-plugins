# New Site Setup Guide

**Purpose**: Setup-mode reference for planning and launching a new site or homepage so search engines and AI answer engines can crawl, index, and cite it.
**Last verified**: 2026-11-03 from Google Search Central and Search Console Help, Next.js documentation, OpenAI, Anthropic, and Perplexity crawler documentation, Bing Webmaster blog, IndexNow, NAVER Search Advisor, and RFC 9309.

## Contents

- Scope And Evidence Rules
- Phase 1: Plan Before Build
- Phase 2: Build Checks Before Launch
- Phase 3: Launch Day Registration
- Phase 4: First 30 Days
- Crawler Policy Template
- Framework Notes
- What Not To Set Up
- Setup Completion Criteria
- Source Ledger

## Scope And Evidence Rules

- Setup mode produces a plan and launch checklist for a site that does not exist yet or is being rebuilt. It edits code only when `allowed_action` is `edit-code`.
- Every item keeps an evidence class. Official requirements cite the platform document; practitioner habits stay `heuristic`.
- Registration and submission are notification and diagnostics channels. None of them guarantees indexing, ranking, rich results, or AI citation.
- Account actions (console registration, DNS records, key files, IndexNow submissions) need the site owner's credentials. Prepare the steps and values; do not perform them without explicit permission.

## Phase 1: Plan Before Build

| Item | What to decide | Evidence class |
|---|---|---|
| Keyword and intent map | One primary intent per page; build pages from the questions people search, not menus first | `heuristic` |
| Intent research | Search the target keyword and record the result formats on top, related searches and questions, comparison targets, and the next question people ask; turn them into the page outline | `heuristic` |
| Information architecture | Hierarchy, navigation, breadcrumb trail, internal links between related pages | `official` (breadcrumbs, links) + `heuristic` (depth) |
| URL rules | Lowercase, hyphen-separated, stable, one URL per piece of content; parameter variants consolidated by canonical unless the variant has unique value | `official` |
| Page templates | Home, category, detail, article, contact; each with its own title, description, heading, and structured-data plan | `official` |
| Entity facts | One consistent site name, organization name, address, and contact data across the site and profiles | `official` (site names, Organization) |
| Locales | Whether hreflang is needed; every locale lists itself and the others | `official` |
| Indexing scope | Which pages are `noindex` (search results, thin utility pages) and which paths are disallowed only to save crawling | `official` |

## Phase 2: Build Checks Before Launch

- **Server-rendered HTML** — primary content, title, description, canonical, and links are in the initial HTML response. Several AI crawlers and Common Crawl do not execute JavaScript, and Naver ownership verification reads raw HTML. Dynamic rendering is a deprecated workaround.
- **Canonical** — self-referential, absolute, one per page, set in HTML rather than by client JavaScript. Do not use `robots.txt` or `noindex` to choose a canonical.
- **Sitemap** — only canonical, indexable, 200-status URLs; at most 50,000 URLs or 50 MB per file; `lastmod` only when it is accurate. Google ignores `priority` and `changefreq`.
- **robots.txt** — served as `text/plain` with 200; disallow only real private or crawl-wasting paths; include the `Sitemap:` line. Robots rules are not access control. A 5xx response on Naver blocks crawling.
- **Structured data** — JSON-LD for supported types only: `WebSite` (site name, on the home page) and `Organization` on the home page, `BreadcrumbList` on inner pages, `Article` on posts, `Product` on product pages. Markup matches visible content. FAQ and HowTo rich results are no longer shown.
- **Metadata** — unique title and description per page, Open Graph tags (`og:title`, `og:type`, `og:image`, `og:url`), and a page-specific `og:image` that meets the Naver conditions when Naver is in scope.
- **Core Web Vitals budget** — LCP 2.5 s, INP 200 ms, CLS 0.1 at the 75th percentile as targets, not a ranking switch.
- **Status codes** — real 404 for missing pages, 301 for permanent moves, no soft 404.
- **Crawler policy** — decide search versus training access per vendor and mirror it at the CDN or WAF; see the template below.

## Phase 3: Launch Day Registration

| Step | Action | Caveat |
|---|---|---|
| Google Search Console | Add a Domain property verified by DNS; add URL-prefix properties for subdomains or sections that need separate data | A Domain property mixes all subdomains and protocols, and the disavow tool does not support Domain properties |
| Sitemap submission | Submit the sitemap in Search Console | Discovery hint, not an index guarantee |
| Search generative AI setting | Confirm the property is included (default) unless the owner decides otherwise | Required for Google generative AI features; not a ranking signal |
| Bing Webmaster Tools | Import from Search Console or verify; submit the sitemap | Bing data also feeds Copilot citation reporting |
| IndexNow | Generate a key, serve the key file at the host root, ping on publish, update, or delete | Notification only; one ping is shared with participating engines, including Naver |
| NAVER Search Advisor (target: naver) | Verify ownership with the meta tag in server-rendered `<head>` or the HTML file; submit the sitemap | There is no Naver registration step that grants exposure; verification unlocks diagnostics and submission |
| Daum webmaster tool (target: naver) | Optional diagnostics registration | Registration does not affect inclusion |
| Analytics | GA4 with an "AI assistants" custom channel group above Referrals | AI app traffic often arrives as direct; the channel undercounts |

## Phase 4: First 30 Days

- Read the Search Console Pages report for "Crawled - currently not indexed" and "Discovered" clusters, and the Sitemaps report for read errors.
- Read the generative AI performance report separately from the web search report; it shows impressions, not citations.
- Read Bing AI Performance (citations, grounding queries) and, when available, Citation Share.
- Notify new or changed URLs through the sitemap and IndexNow. Request indexing manually only for a few important URLs; repeated requests for one URL do not speed crawling, and neither Google nor Naver guarantees exposure from a request.
- Measure AI visibility as a frequency over a fixed prompt set and window (for example share of days cited over 7-30 days), never from one observation.

## Crawler Policy Template

Use explicit groups per token; `User-agent: *` alone does not express a per-vendor decision. Adjust each group to the owner's decision.

```text
# Search and answer surfaces (citations)
User-agent: Googlebot
User-agent: Bingbot
User-agent: OAI-SearchBot
User-agent: Claude-SearchBot
User-agent: PerplexityBot
User-agent: Applebot
User-agent: Meta-WebIndexer
User-agent: Yeti
Allow: /

# Model training (allow or disallow by owner decision)
User-agent: GPTBot
User-agent: ClaudeBot
User-agent: Google-Extended
User-agent: Applebot-Extended
User-agent: Meta-ExternalAgent
User-agent: CCBot
Disallow: /

Sitemap: https://example.com/sitemap.xml
```

- Blocking a training token does not remove the site from that vendor's search answers; blocking the search token does.
- User-triggered fetchers (`ChatGPT-User`, `Perplexity-User`) may not follow robots.txt; enforcement needs the CDN or WAF.
- A CDN default that blocks AI crawlers can override an allow rule; check the edge configuration separately.

## Framework Notes

- **Next.js App Router** — set `metadataBase` in the root layout (relative metadata URLs fail the build without it); use `generateMetadata` with `alternates.canonical` and `alternates.languages`; `app/sitemap.ts` and `app/robots.ts`; render JSON-LD in a `<script>` in the layout or page and escape `<`; `opengraph-image` with a declared size and alt.
- **Other frameworks** — use the framework's head and sitemap facilities, then verify the served HTML with view-source or `curl`, not developer tools.

## What Not To Set Up

- `llms.txt` as a visibility lever. Google ignores it and most published files are never fetched; publish it only for developer documentation consumed by coding agents.
- AI-only schema, "chunked" content, or FAQ blocks added for AI visibility. Google states they are not needed, and within-site evidence shows no robust citation effect.
- Large sets of near-duplicate pages per keyword or satellite sites; they compete with each other and can fall under scaled content abuse.

## Setup Completion Criteria

- Every phase item is `done`, `planned` with an owner, `not-applicable`, or `unknown` with the missing access named.
- The served HTML of each page template was checked for content, title, canonical, and structured data.
- The crawler policy records an explicit decision for each search and training token in scope.
- Registration steps that need credentials are listed with their exact values and left to the owner unless permission was given.
- No item promises indexing, ranking, rich results, or AI citation.

## Source Ledger

| Source | Accessed | Supports | Caveat |
|---|---|---|---|
| https://developers.google.com/search/docs/fundamentals/ai-optimization-guide | 2026-11-03 | Generative AI search optimization is still SEO; llms.txt and chunking unnecessary; generative AI inclusion setting required | Google surfaces only |
| https://developers.google.com/search/docs/appearance/ai-features | 2026-11-03 | No extra files or markup for AI Overviews and AI Mode | Living document |
| https://support.google.com/webmasters/answer/16908024 | 2026-11-03 | Search generative AI include, exclude, inherit setting | Not a ranking or training control |
| https://support.google.com/webmasters/answer/34592 | 2026-11-03 | Domain versus URL-prefix property scope and DNS verification | Console UI wording can change |
| https://support.google.com/webmasters/answer/2648487 | 2026-11-03 | Disavow tool does not support Domain properties | Disavow is rarely needed |
| https://developers.google.com/search/docs/crawling-indexing/ask-google-to-recrawl | 2026-11-03 | Crawl requests do not guarantee inclusion; quota; repeats do not help | Google only |
| https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls | 2026-11-03 | Self-referential canonical; no robots.txt canonicalization | Canonical is a signal, not a directive |
| https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap | 2026-11-03 | Sitemap limits; accurate lastmod; priority and changefreq ignored | Google behavior |
| https://developers.google.com/search/docs/crawling-indexing/javascript/dynamic-rendering | 2026-11-03 | Dynamic rendering is a workaround, not a long-term solution | Google renders JavaScript; other crawlers may not |
| https://developers.google.com/search/docs/appearance/site-names | 2026-11-03 | WebSite structured data on the home page for site names | Domain or subdomain level only |
| https://nextjs.org/docs/app/api-reference/functions/generate-metadata | 2026-11-03 | metadataBase, alternates.canonical, alternates.languages | Next.js App Router only |
| https://www.rfc-editor.org/rfc/rfc9309 | 2026-11-03 | Robots rules are not access authorization; group matching | Standard published 2022 |
| https://platform.openai.com/docs/bots | 2026-11-03 | OAI-SearchBot, GPTBot, ChatGPT-User purposes | Bot strings can change |
| https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler | 2026-11-03 | ClaudeBot, Claude-SearchBot, Claude-User purposes | Bot strings can change |
| https://docs.perplexity.ai/guides/bots | 2026-11-03 | PerplexityBot is not used for model training; Perplexity-User generally ignores robots.txt | Vendor statement |
| https://commoncrawl.org/faq | 2026-11-03 | CCBot does not execute JavaScript | Not an answer engine |
| https://blogs.bing.com/webmaster/2026/2/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview/ | 2026-11-03 | Bing AI Performance citation reporting | Public preview |
| https://www.indexnow.org/documentation | 2026-11-03 | IndexNow submissions shared with participating engines | Notification only |
| https://searchadvisor.naver.com/guide/faq-start-register | 2026-11-03 | No Naver registration step; verification meta in server-rendered head | Naver pages are undated |
| https://searchadvisor.naver.com/guide/indexnow-about | 2026-11-03 | Naver supports IndexNow without an indexing guarantee | Naver pages are undated |
| https://searchadvisor.naver.com/guide/request-crawl | 2026-11-03 | Crawl requests do not guarantee Naver exposure | Naver pages are undated |
| https://www.threads.com/@avcd.eee/post/DfMnpWEj3ij | 2026-11-03 | Practitioner planning, launch, intent-research, and content workflow | Single practitioner; used only as `heuristic` and cross-checked against the rows above |

## Sources

> Checked 2026-11-03.

Every external claim in this file is listed in the source ledger above with the date it was read. The full research journal for this revision is outside the package.
