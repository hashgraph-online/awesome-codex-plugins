# Conditional Research Access for Competitor Profiling

This reference maps research needs to capabilities. It does not declare that
Firecrawl, DataForSEO, a browser, a search provider, or any other connector is
installed, connected, authorized, or callable.

## Contents
- Availability and Authorization Gate
- Public-Site Evidence
- Optional SEO and Market Metrics
- Execution Order
- Failure and Fallback Rules

## Availability and Authorization Gate

Before selecting a tool:

1. Inspect the tools actually exposed in the current session.
2. For a relevant connector, confirm the intended account or workspace,
   authorization, current schema, pricing or quota impact, and read-only scope.
3. Use the exact callable name and arguments returned by current tool
   discovery. Do not construct calls from the example names in this file.
4. If no appropriate tool is available, use the browser-neutral/manual
   fallback below or analyze a user-supplied export.
5. Never bypass login, paywalls, bot controls, site terms, privacy controls, or
   rate limits. Platform-specific access requires a connected platform and the
   user's authorization.

## Public-Site Evidence

### Map or discover URLs

**Need:** Find homepage, pricing, product, about, customer, integration, blog,
and changelog URLs.

**Connected-tool route:** Use a currently exposed site-map or crawl capability
after reading its schema. Some Firecrawl connections expose names such as
`firecrawl_map`; treat that as a discovery hint, not a guaranteed command.

**Manual fallback:** Open the public homepage, follow primary navigation,
inspect a public sitemap when accessible, or use ordinary public search. Record
the exact URL and access date for every page selected.

### Capture one page

**Need:** Preserve visible positioning, pricing, proof, and product text.

**Connected-tool route:** Use a currently exposed single-page fetch, scrape, or
extract capability. Some Firecrawl connections expose names such as
`firecrawl_scrape` or `firecrawl_extract`; first confirm that exact tool and its
schema are available.

**Manual fallback:** Open the public page and save the relevant visible text or
notes as markdown. Record omitted dynamic sections and access limitations.

### Find reviews or offsite mentions

**Need:** Locate current review pages, launch discussions, press, and other
public corroboration.

**Connected-tool route:** Use a current authorized search capability if one is
exposed. A name such as `firecrawl_search` may exist in some installations but
must be discovered before use.

**Manual fallback:** Use ordinary public search and open the result directly.
Do not scrape account-only review content without connected, authorized access.

## Optional SEO and Market Metrics

Quantitative SEO data is optional. Provider metrics are estimates, not first-
party traffic truth. Record provider, market, device, database, access date,
date window, and metric definition so competitors remain comparable.

If a DataForSEO or similar connector is currently available and authorized,
discover its exact callable names and schemas at runtime. Common capability
labels in some deployments include:

| Research need | Possible capability label | Capture |
|---------------|---------------------------|---------|
| Domain/backlink overview | `backlinks_summary` | Provider rank, backlinks, referring domains, spam indicator |
| Referring-domain detail | `backlinks_referring_domains` | Referring domain, provider rank, link count |
| Organic domain overview | `dataforseo_labs_google_domain_rank_overview` | Ranked-keyword count, estimated traffic, estimated value |
| Ranked keywords | `dataforseo_labs_google_ranked_keywords` | Keyword, position, volume, ranking URL |
| Site keyword ideas | `dataforseo_labs_google_keywords_for_site` | Keyword, volume, competition, CPC estimate |
| Organic competitors | `dataforseo_labs_google_competitors_domain` | Domain, overlap, position metrics |
| Domain intersection | `dataforseo_labs_google_domain_intersection` | Shared keyword and each domain's position |
| Relevant pages | `dataforseo_labs_google_relevant_pages` | Page and provider-estimated traffic/keywords |
| Technology detection | `domain_analytics_technologies_domain_technologies` | Observed technologies by category |
| Individual backlinks | `backlinks_backlinks` | Source, target, anchor, provider rank |
| Bulk rank comparison | `backlinks_bulk_ranks` | Same provider rank across the submitted domains |

These labels are not an API contract. If the available provider uses different
names or fields, use the current discovered schema. If no provider is
available, accept a current CSV/JSON export from the user or mark the relevant
section `not collected`.

## Execution Order

### Quick scan

1. Discover URLs with an available mapping capability or manual navigation.
2. Capture homepage and pricing evidence with an authorized fetch or manually.
3. If a quantitative provider or user export is available, collect one
   consistent domain overview and backlink summary.
4. Save raw evidence, then synthesize an abbreviated profile.

### Deep profile

1. Capture homepage, pricing, feature, about, customer, integration, and
   changelog evidence.
2. Collect the same available SEO metrics for each competitor; skip the entire
   comparison dimension when consistent inputs are unavailable.
3. Add public reviews and offsite corroboration through an authorized search
   capability or manual browsing.
4. Save every raw response, export, or manual capture with source and date.
5. Synthesize only after separating verified facts, provider estimates,
   inferences, and unknowns.

### Multiple competitors

Parallelize independent reads only when the current tool supports concurrency
and its quota allows it. Use identical sources and parameters across
competitors. Build individual profiles before the cross-competitor summary.

## Failure and Fallback Rules

| Issue | Action |
|-------|--------|
| Named example tool is absent | Do not call it; use another exposed capability or the manual fallback |
| Page is blocked or requires login | Record the limitation; do not bypass access controls |
| JavaScript page does not render in a fetch | Use an available browser when authorized, or capture only verifiable public evidence manually |
| Pricing URL is not obvious | Inspect navigation, public sitemap, and likely public paths; report if still unverified |
| SEO provider returns no data | Record `insufficient provider data`; do not convert absence into zero |
| Providers use incompatible metrics | Do not compare the values directly; choose one consistent provider or mark unavailable |
| Rate or quota limit is reached | Stop additional calls, name the limit, prioritize the smallest useful evidence set |
| Review access is restricted | Use another public source or omit the review dimension with a limitation note |
