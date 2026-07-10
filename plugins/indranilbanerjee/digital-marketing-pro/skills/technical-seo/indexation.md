# Indexation — Canonicals, Meta Robots, Duplicate Content & Index Management

A comprehensive reference for controlling which pages search engines index, resolving duplicate content, managing index coverage, and accelerating indexation of new content. Indexation management ensures that search engine indexes contain only the pages you want to rank, with no duplication, no bloat, and no wasted authority.

---

## Canonical Tags

### Purpose

The `rel="canonical"` link element tells search engines which URL is the preferred (canonical) version of a page when multiple URLs serve the same or substantially similar content. It consolidates ranking signals (backlinks, PageRank) onto the canonical URL.

### Implementation

**HTML link element (most common):**
```html
<link rel="canonical" href="https://example.com/preferred-page">
```

**HTTP header (for non-HTML resources like PDFs):**
```
Link: <https://example.com/preferred-page>; rel="canonical"
```

### Canonical Tag Rules

1. **Self-referencing canonicals**: Every indexable page should have a canonical tag pointing to itself. This prevents issues from URL parameters, tracking codes, or session IDs creating duplicate URLs that Google discovers through external links
2. **Canonical must be an absolute URL**: `href="https://example.com/page"` not `href="/page"`
3. **Canonical must point to a 200-status page**: Do not canonical to a 301, 404, or 5xx page
4. **Canonical must match the protocol**: HTTPS pages should canonical to HTTPS URLs
5. **Canonical is a hint, not a directive**: Google may choose to ignore the canonical if other signals contradict it (e.g., internal links primarily point to a different URL)
6. **One canonical per page**: Multiple canonical tags on the same page cause Google to ignore all of them

### Common Canonical Mistakes

| Mistake | Impact | Fix |
|---|---|---|
| Canonical points to a noindex page | Conflicting signals — Google may ignore both | Remove noindex from the canonical target, or change the canonical to an indexable page |
| Canonical points to a 404/410 page | Canonical signal is ignored; page may be indexed independently | Update canonical to a live, relevant page |
| Canonical to a redirected URL | Google may follow the redirect and use the final destination, but this adds unnecessary ambiguity | Point canonical directly to the final destination URL |
| Canonical chain (A canonicals to B, B canonicals to C) | Google may resolve correctly but processing delays occur; long chains may be abandoned | Point A directly to C |
| Relative URLs in canonical | Parsed relative to current URL — may resolve incorrectly across templates | Always use absolute URLs |
| Canonical between very different pages | Google ignores the canonical because content does not match | Only canonical between pages with substantially similar content |
| Missing self-referencing canonical | Parameter variations and tracking URLs may be indexed as duplicates | Add self-referencing canonical to every indexable page template |
| Canonical in the `<body>` instead of `<head>` | Google may not process it | Ensure canonical tag is within the `<head>` element |

### Cross-Domain Canonicals

Used when the same content exists on multiple domains (syndication, multi-brand, regional sites):

```html
<!-- On syndication-partner.com -->
<link rel="canonical" href="https://original-publisher.com/article">
```

Cross-domain canonicals are a stronger hint than same-domain, and Google generally respects them when the content is truly identical. The canonicalized domain passes ranking signals to the canonical domain.

---

## Meta Robots Directives

### Available Directives

| Directive | Meaning |
|---|---|
| `index` | Allow this page to be indexed (default behavior; rarely needs to be explicit) |
| `noindex` | Do not show this page in search results. Strongest indexation control |
| `follow` | Follow links on this page (default behavior) |
| `nofollow` | Do not follow any links on this page for ranking purposes |
| `noarchive` | Do not show a cached copy of this page in search results |
| `nosnippet` | Do not show a text snippet or video preview in search results |
| `max-snippet:[n]` | Limit text snippet to n characters |
| `max-image-preview:[size]` | Limit image preview size: `none`, `standard`, `large` |
| `max-video-preview:[n]` | Limit video preview to n seconds |
| `notranslate` | Do not offer translation of this page in search results |
| `noimageindex` | Do not index images on this page |
| `unavailable_after:[date]` | Do not show this page after the specified date |

### Implementation

**HTML meta tag:**
```html
<meta name="robots" content="noindex, follow">
```

**Specific crawler:**
```html
<meta name="googlebot" content="noindex">
<meta name="bingbot" content="noindex">
```

**X-Robots-Tag HTTP header** (works for all file types, not just HTML):
```
X-Robots-Tag: noindex, follow
```

### When to Use noindex vs robots.txt vs canonical

| Goal | Use | Reason |
|---|---|---|
| Page should never appear in search results | `noindex` | Definitive removal from index once crawled |
| Page should not be crawled at all (save crawl budget) | `robots.txt Disallow` | Prevents crawling, but page can still be indexed if linked externally |
| Multiple URLs for same content — pick one winner | `canonical` | Consolidates signals to preferred URL |
| Temporarily remove a page from search | GSC URL Removal Tool + noindex | Removal tool is fast (hours) but temporary (6 months); noindex is permanent |
| Permanently removed content | `410 Gone` status code | Tells Google the page is permanently gone; faster than noindex for deindexation |

**Critical distinction**: robots.txt blocks crawling but not indexing. If a page blocked by robots.txt has external backlinks, Google may index it based on anchor text alone (appearing as "No information is available for this page" in search results). To prevent indexation, use noindex — but the page must be crawlable for Google to see the noindex tag.

---

## Index Coverage in Google Search Console

### Status Categories

| Status | Meaning | Action |
|---|---|---|
| **Valid** | Page is indexed and can appear in search results | Monitor for changes. Verify these are pages you want indexed |
| **Valid with warnings** | Page is indexed but has issues that may affect visibility | Review warnings (e.g., indexed but blocked by robots.txt) |
| **Excluded** | Page is not indexed — could be intentional or problematic | Review exclusion reasons below |
| **Error** | Page has issues preventing proper indexing | Fix server errors, redirect errors, or crawl anomalies |

### Common Exclusion Reasons and Fixes

| Exclusion Reason | What It Means | Action |
|---|---|---|
| **Excluded by noindex tag** | Page has meta noindex — intentional if you set it | Verify this is intentional. If not, remove the noindex tag |
| **Blocked by robots.txt** | Robots.txt prevents crawling | If intentional, fine. If the page should be indexed, update robots.txt |
| **Crawled — currently not indexed** | Google crawled but chose not to index (quality/relevance issue) | Improve content quality, add internal links, build backlinks. This is Google saying "I saw it but it is not good enough" |
| **Discovered — currently not indexed** | Google knows the URL exists but has not crawled it yet | Common for new/low-authority pages. Improve internal linking, submit in sitemap, request indexing via URL Inspection |
| **Alternate page with proper canonical** | Page canonicals to another URL — expected behavior | Verify the canonical target is correct and indexed |
| **Duplicate without user-selected canonical** | Google found duplicate content and chose its own canonical | Check if Google's choice matches your intent. If not, strengthen canonical signals (internal links, sitemap, explicit canonical tag) |
| **Duplicate, Google chose different canonical** | You set a canonical but Google disagreed | Review why — content may not be similar enough, or the canonical target may have issues. Strengthen signals on your preferred canonical |
| **Page with redirect** | URL redirects to another page | Expected for redirected URLs. Verify redirect targets are correct |
| **Soft 404** | Page returns 200 but Google thinks it is a 404 (empty or near-empty content) | Either return a proper 404/410 status code, or add substantial content to the page |
| **Not found (404)** | Page returns 404 status | If intentional, the 404 will eventually drop out. If the page should exist, fix the URL or implement a redirect |

---

## Duplicate Content Management

### Types of Duplicate Content

**Exact duplicates**: Identical content accessible at multiple URLs
- `http://` vs `https://`
- `www.` vs non-www
- Trailing slash vs no trailing slash
- URL parameters (tracking, session, sorting)
- `index.html` vs `/`
- Uppercase vs lowercase URLs

**Near duplicates**: Substantially similar content with minor variations
- Product pages differing only by color/size selection
- Location pages with boilerplate content and only city name changed
- Paginated content where intro text repeats across pages
- Print-friendly versions of pages
- Mobile-specific URLs (m.example.com)

**Syndicated duplicates**: Same content on different domains
- Content republished on partner sites
- Press releases on wire services
- Product descriptions provided by manufacturers

### Resolution Strategies

| Duplicate Type | Strategy | Implementation |
|---|---|---|
| Protocol/www/slash variations | 301 redirect to canonical version | Server config (nginx/Apache redirect rules) |
| Parameter variations | Self-referencing canonical on clean URL | Canonical tag on every page template |
| Print-friendly versions | Canonical to main page or noindex | Canonical tag on print pages |
| Near-duplicate location pages | Unique content per page (minimum 60-70% unique) | Invest in location-specific content |
| Syndicated content | Cross-domain canonical to original publisher | Canonical tag on syndication partner pages |
| Paginated content | Self-referencing canonical per page OR view-all canonical | Depends on page count (see site-architecture.md) |
| Translated content (same language) | Choose one version; canonical to it | Canonical tag; do not use hreflang for same-language duplicates |

---

## Index Bloat

### What It Is

Index bloat occurs when a search engine indexes significantly more pages than the site has valuable, unique content. Common symptoms:
- Indexed page count in GSC is 2x+ the number of pages in the sitemap
- Large numbers of thin or duplicate pages appearing in the index
- Important pages competing with low-value pages for rankings

### Common Sources of Index Bloat

| Source | Example | Scale Risk |
|---|---|---|
| Faceted navigation | Every filter combination generates an indexable URL | Extreme (hundreds of thousands to millions) |
| Internal search results | `/search?q=*` pages indexed for every query | High |
| Tag/archive pages | WordPress tag pages with 1-2 posts each | Medium |
| Pagination | Deep paginated pages (page 50+) with no unique value | Medium |
| Calendar/date archives | Empty or near-empty date archive pages | Medium |
| User profile pages | Thin public profile pages on UGC platforms | High |
| Parameter variations | Tracking, session, currency, language parameters | High |
| Staging/development environments | Staging.example.com indexed by Google | Medium |
| PDF and file duplicates | Same content as HTML pages but in PDF format | Low-Medium |

### Index Bloat Cleanup Process

1. **Audit the index**: Compare GSC indexed page count to your sitemap URL count. A ratio above 1.5:1 suggests bloat
2. **Identify bloat sources**: Use GSC index coverage report, site: search operator, and crawl data to categorize indexed URLs by template type
3. **Prioritize by volume**: Address the largest bloat sources first (faceted navigation before tag pages)
4. **Apply controls**:
   - `noindex, follow` on pages that have link value but should not rank
   - `robots.txt Disallow` on URL patterns that should never be crawled
   - `canonical` to consolidate duplicate/near-duplicate pages
   - `410 Gone` for pages that should be permanently removed
   - `rel="canonical"` to view-all or primary page for paginated series
5. **Clean up sitemaps**: Remove all non-indexable URLs from XML sitemaps
6. **Monitor**: Track indexed page count weekly. Expect a gradual decrease over 4-8 weeks as Google recrawls and deindexes pages

---

## New Content Indexation

### How to Speed Up Indexation of New Pages

**Tier 1: High-impact (do immediately)**
- Add internal links from high-authority, frequently crawled pages (homepage, category pages, popular blog posts)
- Include the new URL in the XML sitemap with an accurate `lastmod` date
- Use Google Search Console URL Inspection tool > "Request Indexing" (limited to ~10-20 requests per day)

**Tier 2: Supplementary (do within 24 hours)**
- Share the URL on social media (Google discovers URLs through social platforms)
- Ping the sitemap: `https://www.google.com/ping?sitemap=https://example.com/sitemap.xml`
- If the site uses Google's Indexing API (eligible for job postings and live streaming content), submit through the API (much faster than standard crawling)

**Tier 3: Long-term (ongoing)**
- Maintain a healthy crawl rate by keeping the site fast and error-free
- Build external backlinks to new content
- Publish content consistently (sites with regular publishing schedules get crawled more frequently)
- Keep XML sitemaps accurate (no broken URLs, accurate lastmod dates)

### Indexation Timeline Expectations

| Site Authority | New Page Indexation | Factors |
|---|---|---|
| High (established domain, strong backlink profile) | Minutes to hours | Google crawls frequently; new content discovered quickly through internal links |
| Medium (growing domain, moderate authority) | Hours to days | Regular crawling schedule; sitemap and internal links help |
| Low (new domain, few backlinks) | Days to weeks | Infrequent crawling; URL Inspection and sitemap submission are critical |
| Very low (brand new domain, no backlinks) | Weeks to months | Google may need multiple crawl cycles before indexing; focus on building authority |

### Google Indexing API

The Indexing API provides near-instant indexation (minutes) but is officially supported only for:
- `JobPosting` structured data pages
- `BroadcastEvent` (live streaming) structured data pages

Some SEOs use it for broader content types with mixed results. Google has stated it is only intended for the supported types. For most sites, the URL Inspection tool's "Request Indexing" is the recommended manual indexation method.

---

## URL Removal Tools and Processes

### Temporary Removal (Google Search Console)

- **URL Removal Tool**: Temporarily hides a URL from Google Search results for approximately 6 months
- Use for: Emergency removal of sensitive content, outdated pages that need time to fix
- Does NOT permanently remove the page from the index — the page must also have noindex or return 404/410 for permanent removal

### Permanent Removal Methods

| Method | Speed | Permanence | Use Case |
|---|---|---|---|
| `noindex` meta tag | Days to weeks (next crawl) | Permanent while tag is present | Pages that should exist but not rank |
| `410 Gone` status code | Days to weeks | Permanent (Google drops from index) | Content permanently removed with no replacement |
| `404 Not Found` | Weeks to months | Eventually drops from index | Content no longer exists |
| `301 Redirect` | Days to weeks | Old URL replaced by new URL in index | Content moved to a new URL |
| URL Removal Tool + noindex | Hours (removal) + permanent (noindex) | Permanent | Urgent removal of sensitive/harmful content |

### Outdated Content Removal

Google provides a separate "Remove Outdated Content" tool for requesting removal of cached content that no longer reflects the live page. This is used when:
- A page's snippet in search results shows outdated information
- A page has been updated but Google's cache has not refreshed
- A removed page still appears in search results for other users to request removal

This tool is available to anyone, not just site owners: `https://search.google.com/search-console/remove-outdated-content`
