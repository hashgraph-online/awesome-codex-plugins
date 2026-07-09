# SEO Execution Guide

Reference knowledge for SEO execution via CMS APIs, search console operations, schema deployment, rank monitoring, and technical SEO workflows. Use this when executing SEO tasks programmatically through MCP servers and scripts.

---

## 1. WordPress SEO Field Updates

### Yoast SEO Meta Fields

Update via `POST /wp-json/wp/v2/posts/{id}` with `meta` object:

| Meta Key | Max Length | Purpose |
|---|---|---|
| `_yoast_wpseo_title` | 60 chars | SEO title override. Supports variables: `%%title%%`, `%%sep%%`, `%%sitename%%`, `%%primary_category%%`. |
| `_yoast_wpseo_metadesc` | 160 chars | Meta description for SERP snippet. Include primary keyword naturally. End with CTA or value proposition. |
| `_yoast_wpseo_focuskw` | N/A | Focus keyphrase for Yoast content analysis. Single keyword or phrase. |
| `_yoast_wpseo_canonical` | URL | Canonical URL override. Use when content is syndicated or duplicated. |
| `_yoast_wpseo_opengraph-title` | 60 chars | OG title for social sharing. Falls back to `_yoast_wpseo_title` if empty. |
| `_yoast_wpseo_opengraph-description` | 200 chars | OG description for social sharing. |
| `_yoast_wpseo_opengraph-image` | URL | OG image URL. Recommended: 1200x630 px. |
| `_yoast_wpseo_twitter-title` | 60 chars | Twitter card title override. Falls back to OG title. |
| `_yoast_wpseo_twitter-description` | 200 chars | Twitter card description override. |
| `_yoast_wpseo_schema_article_type` | enum | `Article`, `BlogPosting`, `NewsArticle`, `TechArticle`, `ScholarlyArticle`. |

### RankMath SEO Meta Fields

Update via the same WordPress REST API `meta` object:

| Meta Key | Max Length | Purpose |
|---|---|---|
| `rank_math_title` | 60 chars | SEO title. Supports variables: `%title%`, `%sep%`, `%sitename%`, `%category%`. |
| `rank_math_description` | 160 chars | Meta description. |
| `rank_math_focus_keyword` | N/A | Primary focus keyword. Comma-separated for multiple keywords. |
| `rank_math_canonical_url` | URL | Canonical URL override. |
| `rank_math_robots` | array | Index/noindex directives: `["index", "follow"]` or `["noindex", "nofollow"]`. |
| `rank_math_advanced_robots` | object | `{ "max-snippet": -1, "max-image-preview": "large", "max-video-preview": -1 }` |
| `rank_math_schema_Article` | JSON | Full schema override. Allows custom JSON-LD injection. |

### RankMath Redirect Module

- **API endpoint**: `POST /wp-json/rankmath/v1/redirections`
- **Fields**: `sources` (array of URL patterns), `url_to` (destination), `header_code` (301, 302, 307, 410), `status` (active/inactive)
- **Regex support**: Set `comparison` to `regex` for pattern-based redirects
- **Import**: Bulk import via CSV with columns: source, destination, type, category

---

## 2. Webflow SEO Field Updates

### CMS Item SEO Fields

Update via `PATCH /collections/{collection_id}/items/{item_id}` with `fields` object:

| Field Slug | Purpose | Details |
|---|---|---|
| `name` | Page/item title | Primary display name used in CMS. |
| `slug` | URL slug | Must be unique within collection. Lowercase, hyphens only. |
| `post-body` (or custom) | Rich text content | HTML subset. Supports headings, paragraphs, lists, links, images. |
| Custom SEO title field | SEO title | Map to your collection's custom SEO title field slug. |
| Custom SEO description field | Meta description | Map to your collection's custom meta description field slug. |
| Custom OG image field | Open Graph image | `{ "url": "https://...", "alt": "Description" }`. Must be publicly accessible. |

### Webflow Native SEO Settings

- **Page-level SEO**: Set via `PATCH /pages/{page_id}` with `seo.title`, `seo.description`, `openGraph.title`, `openGraph.description`, `openGraph.titleCopy`, `openGraph.descriptionCopy`
- **OG image**: Upload via `POST /sites/{site_id}/assets` then reference in `openGraph.image`
- **Sitemap**: Auto-generated at `/sitemap.xml`. No API control — managed via Webflow dashboard
- **Redirects**: `POST /sites/{site_id}/redirects` with `{ "path": "/old-path", "target": "/new-path", "statusCode": 301 }`
- **Redirect limits**: Basic plan: 100 redirects. CMS plan: 500. Business plan: 2,000. Enterprise: unlimited
- **Publish after changes**: Changes require `POST /sites/{site_id}/publish` — changes are not live until published

---

## 3. Google Search Console API Operations

### URL Inspection API

- **Endpoint**: `POST https://searchconsole.googleapis.com/v1/urlInspection/index:inspect`
- **Payload**: `{ "inspectionUrl": "https://example.com/page", "siteUrl": "https://example.com/" }`
- **Response fields**: `indexStatusResult.verdict` (PASS, NEUTRAL, FAIL), `indexStatusResult.coverageState` (Submitted and indexed, Crawled - currently not indexed, Discovered - currently not indexed, etc.), `mobileUsabilityResult`, `richResultsResult`
- **Use case**: Check indexing status before and after content updates. Verify new pages are indexed.

### Indexing Request (URL Submission)

- **Endpoint**: `POST https://indexing.googleapis.com/v3/urlNotifications:publish`
- **Payload**: `{ "url": "https://example.com/page", "type": "URL_UPDATED" }` or `"type": "URL_DELETED"`
- **Quota**: 200 publish requests per day per property (not 500 — the API documentation specifies 200 for most properties; high-volume sites may request increases)
- **Scope**: Originally designed for `JobPosting` and `BroadcastEvent` schema pages. Google has expanded support but may not process all URL types equally
- **Best practice**: Use for high-priority pages (new product launches, time-sensitive content). For bulk submissions, use sitemap submission instead

### Sitemap Submission API

- **Endpoint**: `PUT https://www.googleapis.com/webmasters/v3/sites/{siteUrl}/sitemaps/{feedpath}`
- **Parameters**: `siteUrl` (URL-encoded property URL), `feedpath` (URL-encoded sitemap URL)
- **Delete sitemap**: `DELETE /webmasters/v3/sites/{siteUrl}/sitemaps/{feedpath}`
- **List sitemaps**: `GET /webmasters/v3/sites/{siteUrl}/sitemaps`
- **Best practice**: Submit after bulk content updates, new section launches, or site restructuring. Ping Google after sitemap regeneration.

---

## 4. Redirect Implementation Patterns

### WordPress — Redirection Plugin API

- **Plugin REST API base**: `/wp-json/redirection/v1/`
- **Create redirect**: `POST /redirect` with `{ "url": "/old-path", "match_url": "/old-path", "action_data": { "url": "/new-path" }, "action_type": "url", "action_code": 301, "group_id": 1 }`
- **Regex support**: Set `match_type` to `url` (exact) or `regex` (pattern match)
- **Log access**: `GET /log` — redirect hit logs with timestamps, user agents, referrers
- **404 monitoring**: `GET /404s` — unresolved 404 errors for redirect opportunity identification

### Webflow — Native 301 Redirects

- **Create**: `POST /sites/{site_id}/redirects` with `{ "path": "/old-path", "target": "/new-path", "statusCode": 301 }`
- **Bulk create**: Loop through redirect list with 100ms delay between requests (60 req/min rate limit)
- **Validation**: Path must start with `/`. Target can be relative (`/new-path`) or absolute (`https://example.com/new-path`)
- **Plan limits enforced server-side**: API returns 429 or error when redirect limit reached

### Bulk Redirect Safety Protocol

1. **Pre-edit snapshot**: Export current redirect list. Store as `redirects_backup_{timestamp}.json`
2. **Validation pass**: For each redirect, verify source URL returns 200 (exists) and destination URL returns 200 (valid target). Flag redirect chains (A→B where B→C already exists)
3. **Staged deployment**: Deploy in batches of 25. After each batch, spot-check 3 redirects via HTTP HEAD request
4. **Post-deploy verification**: Crawl all source URLs. Confirm 301 status codes. Check for redirect loops. Verify final destination matches intent
5. **Rollback**: If errors detected, restore from pre-edit snapshot. All redirect tools must support rollback within 30 minutes of deployment

---

## 5. Schema Deployment Workflow

### Step-by-Step Execution

1. **Generate JSON-LD** — Build schema markup based on content type:
   - `BlogPosting`: title, author, datePublished, dateModified, image, publisher, description
   - `Product`: name, description, image, offers (price, priceCurrency, availability), aggregateRating, review
   - `FAQ`: mainEntity array with Question/Answer pairs
   - `HowTo`: name, step array with name/text/image, totalTime, estimatedCost
   - `LocalBusiness`: name, address, geo, telephone, openingHours, priceRange
   - `Organization`: name, url, logo, sameAs (social profiles), contactPoint

2. **Validate schema** — Run through Schema.org validator (`https://validator.schema.org/`). Zero errors required. Warnings acceptable but should be minimized.

3. **Deploy to page** — Injection method depends on CMS:
   - **WordPress**: Use `rank_math_schema_Article` meta field, or inject via `wp_head` action in custom plugin, or add to Yoast schema output filter
   - **Webflow**: Inject in page Custom Code section (head or body), or embed in rich text via custom code block
   - **Custom CMS**: Add `<script type="application/ld+json">` to page `<head>`

4. **Verify with Rich Results Test** — `https://search.google.com/test/rich-results` — confirm all schema types detected and eligible for rich results. Screenshot result for documentation.

5. **Monitor in GSC** — Check Enhancements reports: `Unparsable structured data`, `Product`, `FAQ`, `How-to`, `Breadcrumb`. Alert on any new errors within 7 days of deployment.

---

## 6. Rank Monitoring and SERP Feature Tracking

### Rank Monitoring Setup

- **Keyword list definition**: Group by priority tier:
  - **Tier 1** (brand + head terms, 10-30 keywords): Daily tracking. Alert on any position change >3 positions
  - **Tier 2** (high-intent long-tail, 30-100 keywords): 3x/week tracking. Alert on >5 position drop
  - **Tier 3** (informational + discovery, 100-500 keywords): Weekly tracking. Alert on >10 position drop or page 1 exit
- **Baseline capture**: Record initial positions, SERP features present, URL ranking, date
- **Data source**: GSC Performance API (`POST /searchAnalytics/query`) with dimensions `query`, `page`, `date`, `device`, `country`
- **Alerting**: Calculate position delta between current and previous check. Trigger alerts per tier thresholds above

### SERP Feature Tracking Methodology

| Feature | Detection Method | Optimization Signal |
|---|---|---|
| **AI Overview** | Query target keyword in Google, check for AI-generated summary above organic results | Content cited in AI Overview = high authority signal. Track citation presence. |
| **Featured Snippet** | GSC data: filter by `searchAppearance = RICH_RESULT`. Manual: query and check position 0 | Optimize content format: paragraph (40-60 words), list (5-8 items), table (3+ rows) |
| **People Also Ask** | Manual query observation. Track which PAA questions appear for target keywords | Create FAQ content targeting PAA questions. Use exact question as H2/H3 |
| **Knowledge Panel** | Query brand name. Check for right-rail panel | Strengthen entity signals: Wikidata, Google Business Profile, structured data |
| **Local Pack** | Query with local intent modifier. Check for map + 3-pack results | GBP optimization, local schema, citation consistency |
| **Video Carousel** | Query and check for video results | Create video content for keywords showing video intent |
| **Image Pack** | Query and check for image results inline | Optimize image alt text, filenames, surrounding context |

### Content Decay Detection and Refresh

1. **Identify decaying content**: Pull GSC data for last 6 months. Flag pages where clicks dropped >30% or average position worsened >5 positions from peak
2. **Prioritize by impact**: Sort decaying pages by peak traffic (highest former traffic = highest priority)
3. **Refresh checklist**:
   - Update outdated statistics, dates, and references
   - Add new sections covering subtopics competitors now rank for
   - Refresh internal links (add links to/from newer content)
   - Update meta title and description if CTR has declined
   - Add or update schema markup
   - Refresh images and alt text
4. **Re-index**: After refresh, submit URL via Indexing API. Monitor position recovery over 2-4 weeks
5. **Document outcome**: Log pre-refresh metrics, changes made, post-refresh metrics at 2-week and 4-week marks

---

## 7. Technical SEO Execution

### Robots.txt Management

- **WordPress**: Edit via `Settings > Reading` or direct file edit at site root. Use `Disallow` for thin/duplicate content paths, staging directories, internal search results
- **Webflow**: Not directly editable via API. Managed in Project Settings > SEO > Robots.txt
- **Critical rules**: Never block CSS/JS files (Googlebot needs them for rendering). Always include `Sitemap:` directive pointing to XML sitemap URL

### Canonical Tag Management

- **Self-referencing canonicals**: Every indexable page should have a self-referencing canonical. Verify via page source or URL Inspection API
- **Cross-domain canonicals**: Use when syndicating content. Set canonical on syndicated copy pointing to original
- **Pagination**: Use `rel="canonical"` pointing to the paginated page itself (not to page 1). Google deprecated `rel="next/prev"` but canonical per page remains valid
- **Common errors**: Mixed HTTP/HTTPS canonicals, trailing slash inconsistencies, canonical pointing to redirected URL, canonical pointing to non-200 page

### Hreflang Implementation

- **Format**: `<link rel="alternate" hreflang="en-us" href="https://example.com/page" />`
- **Required**: Self-referencing hreflang tag on every page in the set. `x-default` tag for language/region selector or default page
- **Validation**: Every hreflang must have a reciprocal tag on the target page. Non-reciprocal hreflang tags are ignored by Google
- **Deployment options**: HTML `<head>` tags (small sites), HTTP headers (non-HTML files), XML sitemap `<xhtml:link>` elements (large sites, recommended)

### Title Tag A/B Testing Framework

1. **Select test pages**: Choose pages with stable traffic (>100 clicks/week) and consistent ranking
2. **Baseline**: Record current title, CTR, average position, clicks for 4 weeks
3. **Implement change**: Update title tag via CMS API. Document exact change and timestamp
4. **Measurement period**: 4 weeks minimum. Control for position changes (CTR comparison only valid at similar positions)
5. **Decision criteria**: Statistically significant CTR improvement (use chi-squared test, p < 0.05). If CTR improves >10% relative with stable position, keep new title. If negative or inconclusive, revert
6. **Revert protocol**: Restore original title via CMS API within 24 hours of decision. Re-submit URL for indexing
