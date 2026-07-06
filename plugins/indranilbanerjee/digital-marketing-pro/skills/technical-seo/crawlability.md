# Crawlability — Robots.txt, Sitemaps, Crawl Budget & Log Analysis

A comprehensive reference for ensuring search engine crawlers can discover, access, render, and efficiently crawl all important pages on a website. Crawlability is the foundation of technical SEO — if search engines cannot crawl a page, it cannot rank.

---

## Robots.txt

### Purpose

The `robots.txt` file tells search engine crawlers which URLs they are allowed or disallowed from requesting. It is a crawl directive, not an indexation directive — pages blocked by robots.txt can still appear in search results if other pages link to them (they will show as "URL is blocked by robots.txt" in GSC).

### Syntax Reference

```
User-agent: *
Disallow: /admin/
Disallow: /api/
Disallow: /internal-search?
Allow: /api/public/

User-agent: Googlebot
Disallow: /staging/
Crawl-delay: 1

Sitemap: https://example.com/sitemap-index.xml
```

**Directives:**
- `User-agent`: Specifies which crawler the rules apply to. `*` means all crawlers
- `Disallow`: Blocks crawling of the specified path. Empty value (`Disallow:`) means allow everything
- `Allow`: Explicitly permits crawling of a path within a broader Disallow. Googlebot supports Allow; some crawlers do not
- `Crawl-delay`: Requests a delay (in seconds) between requests. Google ignores this — use GSC crawl rate settings instead. Bing respects it
- `Sitemap`: Points to the XML sitemap. Can list multiple Sitemap directives

**Pattern matching (Googlebot-specific):**
- `*` matches any sequence of characters: `Disallow: /*.pdf$` blocks all PDF files
- `$` anchors to end of URL: `Disallow: /page$` blocks `/page` but allows `/page/subpage`
- Path matching is case-sensitive

### Common Robots.txt Mistakes

| Mistake | Impact | Fix |
|---|---|---|
| Blocking CSS/JS files | Googlebot cannot render the page; mobile-first indexing fails | Allow all CSS and JS: `Allow: /*.css` and `Allow: /*.js` |
| Blocking entire site accidentally (`Disallow: /`) | No pages crawled; entire site deindexed over time | Audit robots.txt after every deployment |
| Blocking parameterized URLs that have unique content | Valuable pages never crawled | Use noindex instead of Disallow for pages that should not be indexed but can be crawled |
| No Sitemap directive | Crawlers must discover sitemap through other means | Always include `Sitemap:` directive |
| Using robots.txt to prevent indexation | Pages can still be indexed if linked externally | Use meta noindex or X-Robots-Tag for indexation control |
| Different robots.txt on staging vs production | Staging robots.txt (Disallow: /) deployed to production | Add robots.txt validation to deployment checklist |
| Blocking the robots.txt file itself via server config | Crawlers assume everything is allowed | Ensure robots.txt returns 200 status code |

### Testing Robots.txt

- **Google Search Console > Robots.txt Tester**: Validates syntax and tests specific URLs against rules
- **Bing Webmaster Tools**: Similar testing functionality for Bingbot rules
- Robots.txt must be served at the root of the domain: `https://example.com/robots.txt`
- Must return HTTP 200. If it returns 5xx, Google treats it as a temporary allow-all. If 4xx, Google treats it as no restrictions
- Maximum file size: 500KB (Google ignores rules beyond this limit)

---

## XML Sitemaps

### Purpose

XML sitemaps tell search engines which URLs exist and are worth crawling. They supplement natural crawl discovery through links. Sitemaps are especially important for large sites, new sites with few inbound links, sites with deep architecture, and pages with limited internal linking.

### Structure

**Basic sitemap:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/page-1</loc>
    <lastmod>2025-11-15</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
</urlset>
```

**Sitemap index (for large sites):**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>https://example.com/sitemap-products.xml</loc>
    <lastmod>2025-11-15</lastmod>
  </sitemap>
  <sitemap>
    <loc>https://example.com/sitemap-blog.xml</loc>
    <lastmod>2025-11-10</lastmod>
  </sitemap>
</sitemapindex>
```

### Limits and Requirements

| Constraint | Limit |
|---|---|
| URLs per sitemap file | 50,000 |
| Sitemap file size (uncompressed) | 50 MB |
| Sitemaps per sitemap index | 50,000 |
| Maximum total URLs (via index) | 2.5 billion (50K x 50K) |
| Encoding | UTF-8 |
| Compression | gzip supported and recommended for large sitemaps |

### Sitemap Best Practices

1. **Only include canonical, indexable URLs**: Do not include URLs with noindex, non-canonical URLs, redirected URLs, or 4xx/5xx pages
2. **Use accurate `lastmod` dates**: Google uses lastmod to prioritize crawling. Only update the date when content meaningfully changes. Inaccurate dates (auto-updating to today) cause Google to ignore lastmod entirely
3. **Segment sitemaps by content type**: Separate sitemaps for products, blog posts, category pages, and editorial content. This makes GSC reporting more useful and helps diagnose crawl issues by section
4. **Keep sitemaps current**: Dynamically generate sitemaps or update them on content publish/update. Stale sitemaps with dead URLs waste crawl budget
5. **Submit sitemaps in GSC**: Submit via Google Search Console AND reference in robots.txt
6. **Gzip large sitemaps**: Compress sitemaps to reduce server bandwidth and speed up crawler downloads
7. **Monitor sitemap status in GSC**: Check "Sitemaps" report for errors, warnings, and coverage

### Specialized Sitemaps

**Image Sitemap:**
```xml
<url>
  <loc>https://example.com/product-page</loc>
  <image:image>
    <image:loc>https://example.com/images/product.jpg</image:loc>
    <image:title>Product Name</image:title>
    <image:caption>Description of the product image</image:caption>
  </image:image>
</url>
```

**Video Sitemap:**
```xml
<url>
  <loc>https://example.com/video-page</loc>
  <video:video>
    <video:thumbnail_loc>https://example.com/thumb.jpg</video:thumbnail_loc>
    <video:title>Video Title</video:title>
    <video:description>Video description</video:description>
    <video:content_loc>https://example.com/video.mp4</video:content_loc>
    <video:duration>600</video:duration>
  </video:video>
</url>
```

**News Sitemap** (for Google News publishers):
- URLs must be less than 2 days old
- Requires `<news:publication>`, `<news:publication_date>`, and `<news:title>` elements
- Submit only articles, not index pages or category pages

---

## Crawl Budget

### What It Is

Crawl budget is the number of URLs Googlebot will crawl on a site within a given time period. It is determined by two factors:

1. **Crawl rate limit**: The maximum crawling speed Googlebot uses to avoid overloading the server. Determined by server responsiveness and health
2. **Crawl demand**: How much Google wants to crawl based on the site's popularity, freshness signals, and perceived size

### When Crawl Budget Matters

Crawl budget is primarily a concern for:
- Sites with 10,000+ pages
- Sites that generate new URLs rapidly (ecommerce, classified, UGC platforms)
- Sites with slow server response times (< 200ms TTFB is ideal for crawl efficiency)
- Sites where important pages are changing frequently and need quick recrawling

For small sites (under 10,000 pages), crawl budget is rarely a limiting factor.

### What Wastes Crawl Budget

| Waste Source | Description | Fix |
|---|---|---|
| Faceted navigation URLs | Filtering/sorting creates millions of parameter combinations | Block low-value facets in robots.txt; canonicalize to base category |
| Internal search result pages | `/search?q=xyz` indexed and crawled for every query | Block `/search` in robots.txt; add noindex to search results |
| Session ID URLs | Same page with different session parameters | Remove session IDs from URLs; use cookies instead |
| Infinite scroll/pagination traps | Calendar widgets, infinite pagination generating unlimited URLs | Cap pagination depth; use `rel="canonical"` on component pages |
| Soft 404 pages | Pages returning 200 but showing "no results" or empty content | Return proper 404 or 410 status codes |
| Duplicate content from parameters | Sort orders, tracking parameters, currency selectors | Canonicalize to the parameter-free version |
| Orphan pages | Pages with no internal links — only reachable through sitemap | Either add internal links or remove from sitemap if not valuable |
| Redirect chains | Each redirect consumes a crawl, and Google may stop following after 5 hops | Resolve chains to direct 301 redirects |

### Crawl Budget Optimization Strategies

1. **Improve server response time**: TTFB under 200ms allows Googlebot to crawl more URLs per session
2. **Block crawling of low-value URLs** via robots.txt (search results, filtered views, admin pages, API endpoints)
3. **Clean up redirect chains**: Resolve to direct single-hop 301s
4. **Return proper status codes**: 404 for not-found, 410 for permanently removed, 503 for temporary downtime
5. **Keep XML sitemaps clean**: Only canonical, indexable, 200-status URLs
6. **Use internal linking to signal priority**: Pages with more internal links get crawled more frequently
7. **Update `lastmod` accurately**: Helps Googlebot prioritize recently changed URLs
8. **Monitor crawl stats in GSC**: Crawl Stats report shows pages crawled per day, average response time, and crawl response breakdowns

---

## JavaScript Rendering and Crawling

### How Googlebot Handles JavaScript

Googlebot uses a two-phase process:
1. **Crawl phase**: Downloads HTML, discovers links and resources in the raw HTML
2. **Render phase**: Executes JavaScript using a headless Chromium instance, discovers additional content and links in the rendered DOM

The render phase is resource-intensive and happens in a separate queue. During peak load, rendering can be delayed by seconds to days. Content and links that exist only in JavaScript-rendered DOM may be discovered late.

### Rendering Strategies and SEO Impact

| Strategy | Initial HTML | SEO Risk | Best For |
|---|---|---|---|
| **Static HTML** | Complete content | None | Blogs, marketing sites, documentation |
| **Server-Side Rendering (SSR)** | Complete content | None | Dynamic content that changes per request |
| **Static Site Generation (SSG)** | Complete content | None | Content that changes infrequently |
| **Incremental Static Regeneration (ISR)** | Complete content (stale-while-revalidate) | Very low | High-traffic dynamic content |
| **Client-Side Rendering (CSR)** | Empty shell or skeleton | High | Authenticated dashboards (not for SEO pages) |
| **Hybrid (SSR + CSR)** | Critical content server-rendered; interactive parts client-rendered | Low | Modern web apps with SEO requirements |

### JavaScript SEO Checklist

- [ ] Critical content visible in the raw HTML source (View Source, not Inspect Element)
- [ ] Internal links are standard `<a href="...">` tags, not JavaScript-triggered navigation
- [ ] Meta tags (title, description, canonical, robots) are in the initial HTML, not injected by JS
- [ ] Structured data (JSON-LD) is in the initial HTML response
- [ ] URL Inspection tool in GSC shows rendered HTML matches what users see
- [ ] No critical rendering errors in GSC's URL Inspection "More Info" section
- [ ] Client-side routing uses History API (pushState), not hash-based routing (`#/page`)
- [ ] Server returns proper HTTP status codes (404, 301) rather than handling them client-side

---

## Log File Analysis

### What to Analyze

Server logs record every request made to the server, including search engine crawlers. Analyzing these logs reveals how crawlers actually behave on the site, which may differ significantly from what you expect.

### Key Metrics from Log Files

| Metric | What It Tells You | Healthy Range |
|---|---|---|
| **Crawl frequency by URL** | How often Googlebot visits each URL | Important pages: daily; low-value: weekly or less |
| **Crawl frequency by section** | Which site sections get the most crawler attention | Should align with business value of each section |
| **Response code distribution** | Percentage of 200, 301, 404, 5xx responses served to bots | > 90% should be 200; < 1% should be 5xx |
| **Average response time for bots** | Server performance under crawler load | < 200ms ideal; > 500ms is a problem |
| **Crawl of non-indexable URLs** | How much crawl budget is wasted on noindex, blocked, or redirected URLs | < 20% of total bot requests |
| **Crawl of orphan pages** | Pages crawled that have no internal links | Should be near 0 for important content |
| **Bot identification** | Which bots are crawling and their behavior | Verify Googlebot, Bingbot; watch for scraper bots |

### Log Analysis Workflow

1. **Extract bot requests** from access logs (filter by user-agent containing "Googlebot", "bingbot", "Yandex", etc.)
2. **Verify bot identity**: Googlebot IPs resolve to `*.googlebot.com` or `*.google.com` via reverse DNS. Fake Googlebots are common
3. **Segment by URL pattern**: Group crawled URLs by directory/template (product pages, blog posts, category pages, etc.)
4. **Calculate crawl distribution**: What percentage of crawls goes to each section? Does it match the site's priority?
5. **Identify crawl waste**: URLs returning 3xx, 4xx, 5xx to bots; non-indexable URLs being crawled repeatedly
6. **Check response times**: Are any URL patterns consistently slow for bots?
7. **Compare to sitemap**: Are all sitemap URLs being crawled? Are non-sitemap URLs being crawled more than sitemap URLs?
8. **Track over time**: Weekly log analysis to detect crawl behavior changes after site updates

### Tools for Log Analysis

- **Screaming Frog Log File Analyser**: Dedicated tool for SEO log analysis. Parses common log formats, segments by bot, visualizes crawl patterns
- **Custom scripts (Python/pandas)**: For large log files or custom analysis needs. Parse with regex, aggregate in pandas
- **ELK Stack (Elasticsearch, Logstash, Kibana)**: For continuous log monitoring and dashboarding at scale
- **BigQuery or Athena**: For querying very large log files stored in cloud storage
- **Botify, OnCrawl, JetOctopus**: Enterprise SEO platforms with built-in log file analysis

---

## Orphan Page Detection

### What Are Orphan Pages

Orphan pages are URLs that exist on the server and may be indexed but have zero internal links pointing to them. They are only discoverable through:
- XML sitemaps
- External backlinks
- Direct URL entry
- Previously cached crawl data

### Why Orphan Pages Matter

- **Crawl inefficiency**: If the page is valuable, it is being starved of crawl frequency and PageRank
- **Index bloat**: If the page is low-value, it is consuming index space without contributing
- **Missed SEO opportunity**: Pages with no internal links signal low importance to search engines

### Detection Method

1. Crawl the site with a tool like Screaming Frog, Sitebulb, or a custom crawler starting from the homepage
2. Export the list of discovered URLs (reachable through internal links)
3. Compare against: XML sitemap URLs, GSC indexed URLs, server log URLs (pages Googlebot actually crawled)
4. Any URL in the sitemap, GSC, or logs that was NOT found by the internal crawl is an orphan

### Resolution

- **Valuable orphan pages**: Add internal links from relevant parent pages. Include in navigation or related-content sections
- **Low-value orphan pages**: Remove from sitemap, add noindex, or return 410 Gone if truly obsolete
- **Orphan pages with backlinks**: High priority to rescue — add internal links to capture that external link equity

---

## URL Parameter Handling

### The Problem

URL parameters (query strings) create multiple URLs pointing to the same or similar content:
- `example.com/shoes` (base)
- `example.com/shoes?color=red` (filtered)
- `example.com/shoes?sort=price` (sorted)
- `example.com/shoes?color=red&sort=price&page=2` (combined)

For a site with 50 categories, 10 filters, 5 sort options, and 10 pages of pagination, the combinatorial explosion produces 250,000 URL variations from 50 base categories.

### Resolution Strategies

| Strategy | When to Use | Implementation |
|---|---|---|
| **Canonical to base URL** | Parameter does not create unique, valuable content (sort, session, tracking) | `<link rel="canonical" href="base-url">` on parameterized pages |
| **Robots.txt block** | High-volume parameter URLs that waste crawl budget | `Disallow: /*?sort=` in robots.txt |
| **Noindex, follow** | Parameter pages have some link value but should not rank | `<meta name="robots" content="noindex, follow">` |
| **Allow indexation** | Parameter creates genuinely unique, search-valuable content (e.g., `/shoes?color=red` targets "red shoes") | Ensure unique title, description, and content; self-referencing canonical |
| **AJAX-based filtering** | Prevent parameter URLs from being generated at all | Filtering updates content via JavaScript without changing the URL; use History API for shareable state |

Note: Google deprecated its URL Parameters tool in Google Search Console in 2022. Parameter handling must now be managed entirely through on-site signals (canonicals, robots, noindex).
