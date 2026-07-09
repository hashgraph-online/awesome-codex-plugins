---
name: sitemap-manager
description: "Manage XML sitemaps. Use when: auditing sitemap health, generating sitemaps, or planning sitemap architecture."
argument-hint: "[URL or generate]"
user-invocable: true
---

# /digital-marketing-pro:sitemap-manager

## Purpose

Analyze existing XML sitemaps for issues and opportunities, or generate new sitemaps with industry-specific templates and best practices.

## Modes

### Mode 1: Analyze Existing Sitemap (`/digital-marketing-pro:sitemap-manager [URL]`)

Provide a sitemap URL (e.g., `https://example.com/sitemap.xml`) to audit:

1. **Fetch and parse**: Download sitemap XML, detect sitemap index vs single sitemap
2. **URL count**: Total URLs, URLs per sitemap file (flag if approaching 50K protocol limit)
3. **lastmod audit**: Check for presence, format (W3C datetime), staleness (>6 months without update), fake lastmod (all same date)
4. **Priority and changefreq**: Check for deprecated/ignored signals (Google ignores both — flag if present, recommend removal to reduce file size)
5. **URL health**: Sample 20-50 URLs and check HTTP status codes — flag 404s, 301s, 302s, 5xx errors
6. **Indexation alignment**: Cross-reference with robots.txt and meta robots — flag noindexed URLs in sitemap, flag sitemap URLs blocked by robots.txt
7. **Missing URLs**: Compare sitemap against site crawl or provided URL list — identify pages missing from sitemap
8. **Image/video/news sitemaps**: Check for specialized sitemap extensions
9. **Compression**: Check if sitemap is gzip compressed (recommended for large sitemaps)
10. **robots.txt registration**: Verify sitemap is declared in robots.txt

### Mode 2: Generate New Sitemap (`/digital-marketing-pro:sitemap-manager generate`)

Generate a sitemap plan or actual XML:

1. **Discover site structure**: Crawl from homepage or use provided URL list
2. **Categorize pages**: Group by type (homepage, category, product, blog, landing, legal)
3. **Apply industry template**: Use appropriate structure based on business model (SaaS, ecommerce, local, publisher, agency)
4. **Set lastmod**: Use actual page modification dates, not generation date
5. **Split strategy**: Plan sitemap index structure if >50K URLs or >50MB uncompressed
6. **Exclude rules**: Noindexed pages, paginated results, faceted URLs, utility pages (login, cart, search results)
7. **Generate XML**: Produce valid XML sitemap following the sitemap protocol (sitemaps.org)

## Industry Templates

### SaaS
- Homepage, features, pricing, integrations, docs, blog, changelog, about, legal
- Integration pages as separate sitemap (if 50+)
- Blog with high update frequency

### eCommerce
- Homepage, categories, products, brands, collections, blog, about, legal
- Product sitemap (largest — split if needed)
- Image sitemap for product photos
- Category pages with canonical handling for filtered views

### Local Business
- Homepage, services, locations, about, contact, blog, reviews, legal
- Location pages as separate sitemap (if multi-location)
- Service area pages

### Publisher/Media
- Homepage, sections, articles, authors, topics, about, legal
- News sitemap (for Google News inclusion)
- Video sitemap (if video content)
- High-frequency article sitemap updates

### Agency
- Homepage, services, case studies, blog, team, about, contact, legal
- Case study sitemap
- Industry/vertical landing pages

## Sitemap Protocol Reference

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/page</loc>
    <lastmod>2026-03-15</lastmod>
  </url>
</urlset>
```

### Sitemap Index (for multiple sitemaps)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>https://example.com/sitemap-pages.xml</loc>
    <lastmod>2026-03-15</lastmod>
  </sitemap>
  <sitemap>
    <loc>https://example.com/sitemap-blog.xml</loc>
    <lastmod>2026-03-28</lastmod>
  </sitemap>
</sitemapindex>
```

### Protocol Limits
- 50,000 URLs per sitemap file
- 50MB uncompressed per sitemap file
- Unlimited sitemap files in a sitemap index
- Must use absolute URLs
- UTF-8 encoding required
- Entity escaping for special characters (&amp; &apos; &quot; &gt; &lt;)

## Output

### Sitemap Analysis Report
- Total URLs indexed, health status breakdown
- Issues found with severity (critical/high/medium/low)
- Missing pages that should be in the sitemap
- Recommendations sorted by impact

### Sitemap Generation Output
- Complete XML sitemap(s) or sitemap plan
- Sitemap index if multiple files needed
- robots.txt sitemap declaration line
- Submission instructions for Google Search Console

## Agents Used

- **seo-specialist** — Sitemap analysis, URL health checks, architecture recommendations

## Scripts Used

- **tech-seo-auditor.py** — URL health checking (status codes, redirects)
