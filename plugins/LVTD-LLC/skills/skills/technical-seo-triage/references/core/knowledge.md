# Technical SEO Triage Knowledge

Core concepts for diagnosing technical SEO issues.

## Source References

| Topic | Durable Reference |
|-------|-------------------|
| Discovery, crawling, indexing, ranking | *Product-Led SEO*, how search engines discover, crawl, index, and rank pages |
| Algorithm updates and traffic drops | *Product-Led SEO*, algorithm updates and diagnosing traffic changes |
| Internal linking and link graph | *Product-Led SEO*, internal linking and site architecture |
| Crawl budget | *Product-Led SEO*, crawl budget and crawler attention |
| Google Search Console | *Product-Led SEO*, Google Search Console diagnostics |
| Duplicate content | *Product-Led SEO*, duplicate content and canonicalization |
| Site updates and migrations | *Product-Led SEO*, site updates, redirects, and migration risk |

## Key Concepts

### Search Stages

**Discovery**: Google learns a URL exists from links, sitemaps, submissions, analytics, browser signals, or other sources.

**Crawling**: Google decides whether to spend resources fetching the URL.

**Indexing**: Google decides whether and how to store the page, including duplicate and canonical decisions.

**Ranking**: Google matches indexed pages to queries based on intent, relevance, quality, usability, and context.

Do not diagnose all SEO issues as ranking issues. First identify the stage where the failure happens.

### Google Search Console As Source Of Truth

GSC is the primary source for how Google sees visibility, queries, pages, indexing, canonical choices, and search performance.

Third-party tools are useful, but they estimate. Use them to explore, not to override GSC.

### Internal Link Graph

Internal links distribute authority and help crawlers discover important pages. Large sites often create orphaned or near-orphaned pages when related-content modules only reinforce already popular pages.

### Crawl Budget

Crawl budget is best treated as scarce crawler attention. Low-value URLs, duplicate pages, blocked paths, and weak internal links can waste attention before crawlers reach valuable pages.

### Duplicate Content

Duplicate content is usually a canonicalization and quality-selection issue, not automatically a penalty. The risk rises when duplication exists to manipulate search or makes the site look low quality.

### Migrations And Redirects

URL changes create risk because search engines must accept the new URL as equivalent to the old one. Permanent redirects, complete URL mapping, pre-launch crawls, and long-term redirect maintenance are core safeguards.

## Terminology

| Term | Definition |
|------|------------|
| Canonical | The primary URL Google or the site selects for duplicate/similar content |
| Orphan page | A page with few or no internal links pointing to it |
| Crawl demand | Google's reason to revisit and refresh URLs |
| 301 redirect | Permanent redirect used for moved URLs |
| 302 redirect | Temporary redirect; usually not appropriate for permanent migrations |
| Brand traffic | Queries that include the brand or depend on brand awareness |
| Non-brand traffic | Queries from users who may not know the brand |
