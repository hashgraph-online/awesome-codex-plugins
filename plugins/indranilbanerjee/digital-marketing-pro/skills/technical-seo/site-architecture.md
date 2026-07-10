# Site Architecture — URL Structure, Internal Linking & Information Architecture

A comprehensive reference for designing and optimizing site architecture for search engines and users. Site architecture determines how link equity flows through a site, how efficiently crawlers discover content, and how easily users find what they need. It is one of the highest-leverage technical SEO levers for large sites.

---

## URL Structure

### Best Practices

**Readability and keywords:**
- URLs should be human-readable and include the primary target keyword: `/blog/technical-seo-guide` not `/blog/post?id=4827`
- Use hyphens (`-`) to separate words, not underscores (`_`) or spaces (`%20`). Google treats hyphens as word separators but underscores as joiners
- Keep URLs concise — under 100 characters when possible (no hard limit, but shorter URLs are easier to share and display in SERPs)
- Use lowercase consistently. URLs are case-sensitive on most servers; mixed case creates duplicate content risk

**Structure patterns:**

| Pattern | Example | Best For |
|---|---|---|
| Flat | `/product-name` | Small sites, individual landing pages |
| Category/page | `/category/page-name` | Blogs, medium sites, content hubs |
| Hierarchical | `/category/subcategory/page-name` | Large sites, ecommerce with clear taxonomy |
| Date-based | `/2025/11/article-name` | News sites (shows freshness), but limits future reorganization |

**What to avoid in URLs:**
- Session IDs: `/page?sessionid=abc123` — use cookies instead
- Excessive parameters: `/page?color=red&size=m&sort=price&page=2&ref=homepage`
- Unnecessary depth: `/store/products/clothing/mens/shirts/casual/blue-shirt` (too deep)
- Stop words in excess: `/the-complete-guide-to-the-best-ways-to-do-seo` — trim to `/complete-seo-guide`
- Changing URLs after publication — every URL change requires a 301 redirect and risks ranking loss

### Trailing Slash Consistency

Choose one format and enforce it sitewide:
- `example.com/page/` (with trailing slash)
- `example.com/page` (without trailing slash)

Google treats these as different URLs. If both resolve with 200 status, it creates duplicate content. Enforce one format with a server-side redirect (301) from the non-canonical format.

Most CMSs have a setting for this. For custom implementations, handle it in the web server config (nginx, Apache) or application router.

---

## Information Architecture

### Principles

1. **Every important page should be reachable within 3 clicks from the homepage.** Pages deeper than 3 levels receive less crawl frequency and less PageRank. This does not mean a flat URL structure — it means internal links create short paths.

2. **Group related content together.** Search engines use content proximity (pages linking to each other, sharing URL path structure, and covering related topics) to understand topical authority.

3. **Build topical authority through content clusters.** A pillar page targeting a broad topic links to cluster pages targeting specific subtopics. All cluster pages link back to the pillar. This creates a self-reinforcing authority signal.

### Topic Cluster Model

```
                    [Pillar Page]
                   "Technical SEO Guide"
                  /    |    |    |    \
                 /     |    |    |     \
    [Cluster]  [Cluster] [Cluster] [Cluster] [Cluster]
   "Core Web   "Crawl   "Site     "Schema   "Mobile-
    Vitals"    Budget"  Migration" Markup"   First"
```

**Pillar page**: Comprehensive overview (2,000-5,000 words) targeting the broad head term. Links to every cluster page.

**Cluster pages**: Deep-dive articles (1,000-3,000 words) targeting specific long-tail subtopics. Each links back to the pillar and cross-links to related cluster pages.

**Result**: Search engines understand the site is an authority on the pillar topic because of the depth and interconnection of coverage.

### Content Siloing

Content siloing organizes site content into distinct thematic sections with controlled linking between them. The goal is to concentrate topical relevance within each silo.

**Hard silo**: URL structure mirrors the silo: `/technical-seo/core-web-vitals`, `/technical-seo/crawlability`. Internal links stay within the silo. Cross-silo links go through the top-level silo pages.

**Soft silo**: URL structure may be flat, but internal linking creates virtual silos. Contextual links connect related content within the same topic area.

**When to silo:**
- Sites covering multiple distinct topics (a marketing agency with SEO, PPC, social, email sections)
- Ecommerce sites with distinct product categories
- Publishers covering multiple beats

**When siloing is unnecessary:**
- Small sites (under 50 pages) where all content is closely related
- Single-topic niche sites where everything is one silo

---

## Internal Linking Strategy

### Why Internal Links Matter

1. **Crawl discovery**: Googlebot follows internal links to discover pages. Pages with more internal links are crawled more frequently
2. **PageRank distribution**: Internal links pass PageRank (link equity) from one page to another. Strategic internal linking concentrates authority on priority pages
3. **Topical relevance signals**: The anchor text and surrounding context of internal links help search engines understand what the linked page is about
4. **User navigation**: Well-placed internal links reduce bounce rate and increase pages per session

### Types of Internal Links

| Type | Description | SEO Value | Example |
|---|---|---|---|
| **Navigation links** | Header, footer, sidebar menus | Medium (sitewide dilution) | Main menu linking to category pages |
| **Contextual links** | In-content links within body copy | High (relevant context + anchor text) | Blog post linking to related article |
| **Breadcrumb links** | Hierarchical path from homepage to current page | Medium-High (reinforces hierarchy) | Home > Category > Subcategory > Page |
| **Related content links** | Algorithmically or manually curated related pages | Medium | "Related articles" section below blog posts |
| **Footer links** | Links in the site footer | Low-Medium (sitewide, often ignored) | Useful for important pages not in main nav |
| **Sidebar links** | Links in sidebar widgets | Low-Medium | Category lists, popular posts, recent posts |

### Anchor Text Optimization

- **Use descriptive, keyword-relevant anchor text**: "technical SEO audit checklist" not "click here" or "read more"
- **Vary anchor text naturally**: Do not use the exact same anchor text for every link to a page. Use variations, partial matches, and natural phrases
- **Avoid over-optimization**: Do not stuff exact-match keywords into every internal link anchor. Google's algorithms detect this pattern
- **Context matters**: The surrounding paragraph provides additional relevance signals beyond just the anchor text
- **Avoid generic anchors** for important links: "Learn more," "Click here," and "Read this" waste an anchor text opportunity

### Internal Link Audit Methodology

1. **Crawl the site** to build a complete link graph (Screaming Frog, Sitebulb, or custom crawler)
2. **Identify pages with low internal link counts**: Important pages (target keyword pages, revenue pages) with fewer than 5 internal links pointing to them need more
3. **Identify pages with excessive internal links**: Pages linking to 200+ URLs dilute PageRank per link. Consolidate or prioritize
4. **Find orphan pages**: Pages with zero internal links (see crawlability.md for detection method)
5. **Analyze link depth**: Map click depth from homepage. Flag critical pages deeper than 3 clicks
6. **Check for broken internal links**: 404s from internal links waste crawl budget and PageRank
7. **Review anchor text distribution**: Ensure important pages receive keyword-relevant anchor text from multiple sources
8. **Visualize link flow**: Use a site architecture visualization to identify PageRank bottlenecks and silos

### Link Equity Distribution Principles

- **Homepage has the most PageRank** (it receives the most external backlinks). Links from the homepage are the most valuable internal links
- **PageRank flows through links and is divided among all links on a page**. A page with 10 outgoing links passes more equity per link than a page with 100 outgoing links
- **Deep pages need intentional linking**: A blog post 5 clicks from the homepage receives minimal PageRank unless linked from higher-authority pages
- **"Link to your money pages"**: Product pages, service pages, and high-converting landing pages should receive internal links from high-authority content (blog posts with backlinks, homepage, category pages)

---

## Pagination Handling

### Current Best Practices (Post rel=prev/next Deprecation)

Google deprecated support for `rel="prev"` and `rel="next"` in 2019. Current approaches:

**Option 1: View-All Page (Preferred for SEO)**
- Create a single page with all content (`/products/shoes?view=all`)
- Set the view-all page as the canonical for all paginated component pages
- Best for: Product listings under 200 items, article lists
- Caveat: Page must load reasonably fast. If 500 products cause a 10-second load time, this is not viable

**Option 2: Self-Canonicalizing Paginated Pages**
- Each paginated page (`/shoes?page=1`, `/shoes?page=2`) has a self-referencing canonical
- Google indexes each page independently
- Best for: Large catalogs where a view-all page is not feasible
- Ensure each page has unique, relevant content (not just the same intro text with different products)

**Option 3: Load More / Infinite Scroll (with SEO Considerations)**
- JavaScript-powered "Load more" button or infinite scroll
- Critical: Implement as progressive enhancement with crawlable paginated URLs underneath
- Google recommends: `<a href="/shoes?page=2">` links in the HTML that JavaScript enhances into "Load more" functionality
- Without crawlable fallback URLs, Googlebot cannot access content beyond the initial load

---

## Faceted Navigation (Ecommerce)

### The Challenge

Ecommerce filtering (color, size, price range, brand, rating) generates enormous URL combinations. A category with 8 filter types and 5 options each creates 5^8 = 390,625 possible URL combinations from a single category.

### Strategy Matrix

| Facet Type | Example | Indexable? | Handling |
|---|---|---|---|
| **High-demand facets** | Color, brand, material for fashion | Yes — if search volume exists for "red running shoes" | Unique title/description, self-referencing canonical, include in sitemap |
| **Sorting parameters** | Sort by price, popularity, newest | No — same products, different order | Canonical to base category; robots.txt block or noindex |
| **Pagination within facets** | Page 2 of red shoes | Depends on depth | Pages 1-3 may be indexable; deeper pages canonical to page 1 |
| **Multi-select facets** | Red + blue + size 10 | No — too specific, no search demand | Canonical to broadest applicable facet; robots.txt block |
| **Price range** | $50-$100 | Rarely | Usually canonical to base category unless "cheap [product]" has volume |
| **Rating filters** | 4 stars and up | No | Canonical to base category |

### Implementation Approaches

1. **AJAX-based filtering (Best)**: Filters update content via JavaScript without generating new URLs. Use History API to update the URL for shareability without creating crawlable parameter URLs. Googlebot sees only the base category URL.

2. **Canonical + robots.txt (Common)**: Allow parameter URLs to exist but canonical low-value combinations to the base URL. Block high-volume parameter patterns in robots.txt to conserve crawl budget.

3. **Noindex, follow (Fallback)**: Apply noindex to parameter pages that should not rank but contain links worth following. Use when canonical signals are insufficient.

---

## Breadcrumb Implementation

### SEO Benefits

- Reinforces site hierarchy for search engines
- Provides keyword-rich internal links to parent pages
- Enables breadcrumb rich results in Google SERPs (increases click-through rate)
- Helps users understand their location within the site

### HTML Implementation

```html
<nav aria-label="Breadcrumb">
  <ol itemscope itemtype="https://schema.org/BreadcrumbList">
    <li itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">
      <a itemprop="item" href="/"><span itemprop="name">Home</span></a>
      <meta itemprop="position" content="1">
    </li>
    <li itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">
      <a itemprop="item" href="/technical-seo"><span itemprop="name">Technical SEO</span></a>
      <meta itemprop="position" content="2">
    </li>
    <li itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">
      <span itemprop="name">Core Web Vitals</span>
      <meta itemprop="position" content="3">
    </li>
  </ol>
</nav>
```

### JSON-LD Alternative (Preferred)

```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://example.com/"},
    {"@type": "ListItem", "position": 2, "name": "Technical SEO", "item": "https://example.com/technical-seo"},
    {"@type": "ListItem", "position": 3, "name": "Core Web Vitals"}
  ]
}
```

### Best Practices

- Always start with "Home" as the first breadcrumb
- The last item (current page) should not be a link
- Use descriptive names (not URL slugs) — "Core Web Vitals Guide" not "core-web-vitals"
- For products in multiple categories, choose the primary category for the breadcrumb path (match canonical)
- Implement BreadcrumbList schema for rich result eligibility

---

## Site Migration Planning

### Pre-Migration Checklist

- [ ] Complete URL mapping: old URL to new URL for every page with organic traffic or backlinks
- [ ] Set up 301 redirects for every mapped URL (test before launch)
- [ ] Verify new site has no robots.txt blocking or noindex tags from development
- [ ] Update all internal links to point to new URLs (avoid relying solely on redirects for internal navigation)
- [ ] Update canonical tags to reference new URLs
- [ ] Update XML sitemaps to reference new URLs
- [ ] Update hreflang tags (if international site)
- [ ] Update structured data (URLs in schema markup)
- [ ] Benchmark current performance: organic traffic by page, indexed page count, crawl stats, rankings for target keywords, Core Web Vitals
- [ ] Notify Google via GSC Change of Address tool (for domain migrations)
- [ ] Set up monitoring: daily organic traffic checks, hourly crawl error monitoring for the first week

### Migration Day

- [ ] Deploy redirects
- [ ] Verify redirects work (test a sample of 50+ URLs across different templates)
- [ ] Submit new sitemap to GSC
- [ ] Request indexing for the most important pages via URL Inspection tool
- [ ] Monitor crawl stats in real-time for the first 24 hours
- [ ] Check for spike in crawl errors in GSC

### Post-Migration Monitoring

| Timeframe | Check | Expected |
|---|---|---|
| Day 1-3 | Crawl errors in GSC | Spike is normal; should decrease rapidly |
| Week 1 | Index coverage | Old URLs transitioning to new URLs |
| Week 1 | Organic traffic | 10-30% dip is normal for well-executed migrations |
| Week 2-4 | Rankings for target keywords | Should begin recovering to pre-migration levels |
| Month 1-2 | Organic traffic recovery | Should reach 90-100% of pre-migration levels |
| Month 3 | Full audit | Comparable or improved performance across all metrics |
| Month 6-12 | Redirect maintenance | Keep old domain and redirects active for at least 12 months |

### When Rankings Do Not Recover

If organic traffic has not recovered to 90% within 8 weeks:
1. Check for redirect errors (broken redirects, redirect chains, loops)
2. Verify no noindex or robots.txt blocks on the new site
3. Check canonical tags are not pointing to old URLs
4. Verify internal links are updated (not just relying on redirect chains)
5. Check for content parity issues (missing content on new pages)
6. Review GSC for manual actions or security issues
7. Audit Core Web Vitals on the new site (performance regression can suppress rankings)
