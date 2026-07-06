---
name: technical-seo
description: "Deep technical SEO analysis. Use when: optimizing crawlability, Core Web Vitals, rendering, redirects, or sitemaps."
---

# Technical SEO

## When to Use This Skill

## Context efficiency

Heavy skill. **Grep before Read** any referenced file, then `Read` only matched ranges with `offset` + `limit`. List `${CLAUDE_PLUGIN_DATA}/<brand>/` before opening files. On re-invocation mid-session, skip files already in context.

Activate this module when the user's request involves any of the following:

- **Core Web Vitals**: Optimizing LCP, INP, or CLS scores; diagnosing page speed issues; interpreting CrUX data or PageSpeed Insights reports
- **Crawlability**: Robots.txt configuration, XML sitemap creation or auditing, crawl budget management, or Googlebot access issues
- **Site Architecture**: URL structure planning, information architecture, internal linking strategy, site depth optimization, or content siloing
- **Indexation**: Canonical tag implementation, noindex/nofollow directives, index bloat, duplicate content resolution, or Google Search Console index coverage issues
- **Redirects**: Redirect chain auditing, 301/302 strategy, redirect maps for site migrations, or HTTP-to-HTTPS migration
- **JavaScript SEO**: Client-side rendering issues, SSR vs CSR vs SSG evaluation, dynamic rendering, or JavaScript crawlability problems
- **Mobile-First Indexing**: Mobile rendering issues, mobile parity checks, responsive design auditing, or mobile usability errors
- **Structured Data**: Schema markup implementation (JSON-LD), rich result eligibility, schema validation, or structured data strategy
- **Log File Analysis**: Server log interpretation, crawl frequency analysis, crawl waste identification, or bot behavior auditing
- **International SEO**: Hreflang implementation, ccTLD vs subdomain vs subdirectory decisions, geotargeting, or multilingual site architecture
- **Security**: HTTPS migration, mixed content resolution, HSTS implementation, or security header configuration
- **HTTP Status Codes**: Diagnosing 4xx/5xx errors, soft 404 detection, server error patterns, or status code strategy
- **Page Speed**: Server response time (TTFB), render-blocking resources, image optimization, code splitting, or CDN configuration
- **Site Migrations**: Domain changes, platform migrations, HTTPS transitions, URL restructuring, or merger/acquisition site consolidation

**Trigger phrases**: "technical seo," "core web vitals," "page speed," "crawl budget," "robots.txt," "sitemap," "redirect," "canonical," "indexation," "noindex," "hreflang," "javascript seo," "mobile-first indexing," "log file analysis," "site architecture," "internal linking," "crawl errors," "HTTP status," "schema markup," "structured data," "site migration," "TTFB," "LCP," "INP," "CLS," "render blocking," "crawlability," "index bloat," "redirect chain," "mixed content," "HTTPS"

## Brand Context (Auto-Applied)

Before producing any marketing output from this module:

1. **Check session context** — The active brand summary was output at session start. Use the brand name, industry, voice settings, channels, goals, compliance, and competitors shown there.
2. **If you need the full profile**, read: `~/.claude-marketing/brands/{slug}/profile.json`
3. **Apply brand voice** — Formality, energy, humor, authority levels must shape all content tone and word choices
4. **Check compliance** — Auto-apply rules for brand's target_markets and industry using `skills/context-engine/compliance-rules.md`
5. **Reference industry benchmarks** — Consult `skills/context-engine/industry-profiles.md` for the brand's industry
6. **Use platform specs** — Reference `skills/context-engine/platform-specs.md` for character limits and format requirements
7. **Check campaign history** — Run `python campaign-tracker.py --brand {slug} --action list-campaigns` before planning new work
8. **If no brand exists**, say: "No brand profile found. Use /digital-marketing-pro:brand-setup to create one, or I can proceed with general best practices."
9. **Check brand guidelines** — If `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` exists, load and enforce: `restrictions.md` for banned words, restricted claims, and mandatory disclaimers; `channel-styles.md` for channel-specific tone overrides (may differ from base voice); `messaging.md` for approved key messages, taglines, and positioning language; `voice-and-tone.md` for detailed voice rules beyond the 4 numeric scores. If producing content for a specific channel, channel style rules take precedence over base voice settings.

Do not ask the user for information that already exists in their brand profile.

## Required Context

Before executing technical SEO work, gather:

1. **Website URL**: The domain to audit or optimize
2. **CMS / Platform**: WordPress, Shopify, Webflow, custom, headless, etc. — determines implementation paths
3. **Hosting Environment**: Shared, VPS, dedicated, cloud (AWS/GCP/Azure), CDN provider — affects server-side recommendations
4. **Current Performance Data**: Google Search Console access, PageSpeed Insights scores, CrUX data, or existing audit reports
5. **Site Scale**: Approximate page count (hundreds, thousands, hundreds of thousands) — determines crawl budget relevance
6. **Rendering Method**: Static HTML, server-side rendered, client-side rendered (React/Angular/Vue), hybrid (Next.js/Nuxt) — critical for JavaScript SEO
7. **International Presence**: Target countries and languages, current URL structure for international versions
8. **Known Issues**: Existing problems the user is aware of (crawl errors, indexation drops, speed complaints, ranking losses)
9. **Migration Plans**: Any upcoming domain changes, platform migrations, or URL restructuring
10. **Tech Stack Constraints**: Development team availability, deployment processes, CDN limitations, plugin/extension restrictions

For quick diagnostic requests (e.g., "why is my page slow"), infer reasonable defaults and deliver immediately. For comprehensive audits, gather full context.

## Capabilities

- **Core Web Vitals Optimization**: Diagnose and fix LCP (target < 2.5s), INP (target < 200ms), and CLS (target < 0.1) issues with specific, implementation-ready recommendations; interpret field data (CrUX) vs lab data (Lighthouse) discrepancies; prioritize fixes by user impact
- **Crawlability Audits**: Robots.txt analysis and optimization, XML sitemap structure and validation, crawl budget allocation for large sites, crawl waste identification, orphan page detection, and crawl path optimization
- **Site Architecture Design**: URL structure planning (flat vs hierarchical), information architecture using topic clusters and content silos, internal linking strategy with PageRank flow modeling, click depth optimization (critical pages within 3 clicks), and breadcrumb implementation
- **Internal Linking Optimization**: Link equity distribution analysis, contextual link placement strategy, anchor text optimization, navigation structure auditing, footer and sidebar link strategy, and orphan page rescue
- **Indexation Management**: Canonical tag strategy (self-referencing, cross-domain, parametrized URLs), meta robots directive implementation, X-Robots-Tag HTTP headers, index coverage diagnosis using GSC, index bloat identification and cleanup, and new content indexation acceleration
- **JavaScript SEO**: Client-side rendering assessment, server-side rendering implementation guidance, static site generation recommendations, dynamic rendering as a fallback, Googlebot rendering verification, JavaScript crawl budget impact analysis, and hydration issue diagnosis
- **Mobile-First Indexing**: Mobile rendering parity checks, responsive design validation, mobile usability error resolution, touch target sizing, viewport configuration, and mobile page speed optimization
- **Page Speed Optimization**: TTFB reduction (server tuning, CDN, caching), render-blocking resource elimination, image optimization (format selection, lazy loading, responsive images, preload), CSS/JS minification and code splitting, third-party script auditing, and font loading strategy (font-display, preload, subsetting)
- **Redirect Management**: Redirect chain detection and resolution, 301 vs 302 decision framework, redirect map creation for migrations, redirect loop identification, and redirect performance impact analysis
- **HTTP Status Code Auditing**: 4xx error diagnosis and resolution, 5xx server error pattern analysis, soft 404 detection, 410 Gone implementation for permanently removed content, and status code monitoring strategy
- **Log File Analysis Guidance**: Googlebot crawl frequency and pattern analysis, crawl waste identification (non-indexable URL crawling), response code distribution, crawl budget utilization assessment, and bot vs human traffic ratios
- **Structured Data Implementation**: JSON-LD schema markup for Organization, Product, Article, FAQ, HowTo, BreadcrumbList, LocalBusiness, Event, and Review types; rich result eligibility assessment; schema validation and testing; nested and advanced schema patterns
- **International Technical SEO**: Hreflang implementation (HTML link, HTTP header, XML sitemap methods), ccTLD vs subdomain vs subdirectory decision framework, geotargeting configuration, language and region targeting, and international sitemap strategy
- **Security & HTTPS**: HTTPS migration planning, mixed content detection and resolution, HSTS implementation, security header configuration (CSP, X-Frame-Options, X-Content-Type-Options), and certificate management
- **XML Sitemap Strategy**: Sitemap structure for large sites (sitemap index), image and video sitemaps, news sitemaps, sitemap priority and changefreq guidance, dynamic sitemap generation, and sitemap submission and monitoring
- **URL Structure Optimization**: URL readability and keyword inclusion, parameter handling, trailing slash consistency, URL case sensitivity, and URL length optimization

## Process

**Primary Workflow: Technical SEO Audit & Optimization**

1. **Site Health Snapshot**
   - Pull current Core Web Vitals from CrUX or PageSpeed Insights (LCP, INP, CLS for mobile and desktop)
   - Review Google Search Console index coverage report (valid, excluded, error, warning counts)
   - Check for manual actions or security issues in GSC
   - Note current crawl stats (pages crawled per day, average response time, crawl errors)
   - Baseline: Document current organic traffic, indexed page count, and ranking positions for target keywords

2. **Crawlability Analysis**
   - Review robots.txt for blocking issues (critical resources, CSS/JS, important directories)
   - Validate XML sitemap (well-formed, all important pages included, no non-indexable URLs, within 50K URL / 50MB limit)
   - Assess crawl budget allocation (are crawlers spending time on low-value pages?)
   - Check for crawl traps (infinite calendar pagination, session IDs in URLs, faceted navigation generating millions of URLs)
   - Verify Googlebot can access all critical resources (CSS, JS, images needed for rendering)

3. **Indexation Review**
   - Audit canonical tags across page templates (self-referencing, cross-domain, parameterized URLs)
   - Check for conflicting directives (canonical pointing to page A while noindex is set)
   - Review meta robots directives across templates
   - Identify index bloat (thin content, tag pages, internal search results, parameter variations)
   - Verify pagination handling (paginated series, rel=canonical on component pages)
   - Check for unintended noindex tags (common after staging-to-production migration)

4. **Site Architecture Assessment**
   - Map URL structure and identify depth issues (critical pages beyond 3 clicks from homepage)
   - Analyze internal linking patterns (pages with high/low internal link counts, orphan pages)
   - Evaluate information architecture (logical grouping, topic clusters, content silos)
   - Review navigation structure (header, footer, sidebar, breadcrumbs)
   - Check URL format consistency (trailing slashes, case sensitivity, parameter handling)

5. **Page Speed Deep Dive**
   - **LCP optimization**: Identify the LCP element, check server response time (TTFB < 800ms), audit render-blocking resources, verify image optimization (format, size, lazy loading, preload for above-fold)
   - **INP optimization**: Identify long tasks (> 50ms), audit event handlers, check for main thread blocking, review third-party script impact
   - **CLS optimization**: Check for images/iframes without explicit dimensions, dynamic content injection above the fold, web font loading causing layout shift, ad slot reservations
   - Audit third-party scripts for performance impact (tag managers, analytics, chat widgets, A/B testing tools)
   - Review caching headers (Cache-Control, ETag, Expires) and CDN configuration

6. **Mobile-First Compliance Check**
   - Verify content parity between mobile and desktop rendered versions
   - Check for mobile-specific rendering issues (viewport configuration, touch targets, font sizes)
   - Test mobile page speed separately (mobile networks have higher latency)
   - Review structured data presence on mobile version (must match desktop)
   - Check for lazy-loaded content that Googlebot might miss on mobile

7. **JavaScript SEO Evaluation**
   - Determine rendering strategy (CSR, SSR, SSG, ISR, hybrid)
   - Test Googlebot rendering using URL Inspection tool (rendered HTML vs raw HTML)
   - Check if critical content and links require JavaScript to render
   - Assess JavaScript crawl budget impact (render queue delays)
   - Review client-side routing and its impact on crawlability
   - Verify meta tags and canonicals are in the server-rendered HTML (not injected by JS)

8. **Redirect Chain Audit**
   - Identify redirect chains (more than 1 hop) and redirect loops
   - Check for mixed 301/302 usage (302s that should be 301s)
   - Audit HTTPS redirect implementation (HTTP to HTTPS, www to non-www or vice versa)
   - Verify redirects from old URLs after any past migrations
   - Assess redirect response time impact on crawl efficiency

9. **Structured Data Validation**
   - Audit existing schema markup for errors and warnings (Google Rich Results Test)
   - Identify missing schema opportunities based on content types
   - Validate JSON-LD syntax and nesting
   - Check for rich result eligibility (FAQ, HowTo, Product, Review, Breadcrumb, etc.)
   - Verify schema matches visible on-page content (no hidden/misleading markup)

10. **International SEO Review** (if applicable)
    - Validate hreflang implementation (self-referencing tags, x-default, return links)
    - Check for hreflang conflicts with canonical tags
    - Verify geotargeting settings in Google Search Console
    - Assess URL structure for international versions
    - Review content localization vs translation quality signals

11. **Security Assessment**
    - Verify full HTTPS implementation (no mixed content)
    - Check HSTS header presence and configuration
    - Review security headers (CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy)
    - Verify SSL certificate validity and chain
    - Check for exposed sensitive files (wp-config.php, .env, .git)

12. **Prioritized Recommendation Plan**
    - Score each finding by impact (high/medium/low) and effort (quick win/medium/major project)
    - Create an impact/effort matrix to visualize priority
    - Group recommendations into: Immediate fixes (0-48 hours), Short-term wins (1-2 weeks), Medium-term projects (2-8 weeks), Long-term strategic initiatives (2-6 months)
    - Estimate traffic recovery or growth potential for each fix category
    - Provide implementation specs for the top 5 highest-priority items

## Reference Files

- `core-web-vitals.md` — LCP, INP, and CLS optimization guides with specific thresholds, common causes, fix strategies, measurement methodology, and field vs lab data interpretation
- `crawlability.md` — Robots.txt syntax and best practices, XML sitemap structure and limits, crawl budget management, JavaScript rendering, log file analysis, and orphan page detection
- `site-architecture.md` — URL structure best practices, information architecture frameworks, internal linking strategy, pagination handling, faceted navigation, breadcrumbs, and site migration planning
- `indexation.md` — Canonical tag implementation, meta robots directives, X-Robots-Tag, index coverage diagnosis, duplicate content management, index bloat cleanup, and new content indexation acceleration
- `international-seo.md` — URL structure strategies for international sites, hreflang implementation methods with examples, common hreflang mistakes, geotargeting, content localization, and search engine market share by country

## Output Formats

| Deliverable | Format | Description |
|---|---|---|
| Technical SEO Audit Report | Document | Comprehensive audit across all 12 dimensions with scores, findings, and prioritized recommendations |
| Core Web Vitals Report | Document | CWV-specific analysis with per-metric diagnosis, fix specifications, and expected improvement ranges |
| Redirect Map | Spreadsheet | Source URL to destination URL mapping with status codes and redirect type for migrations |
| XML Sitemap Strategy | Document + Code | Sitemap structure plan with implementation code (sitemap index, per-type sitemaps, generation approach) |
| Site Architecture Plan | Document + Diagram description | URL hierarchy, internal linking strategy, content silo structure, and navigation recommendations |
| Robots.txt Specification | Code | Optimized robots.txt file with directives, sitemap references, and crawl-delay settings |
| Structured Data Spec | Code (JSON-LD) | Ready-to-implement schema markup for all applicable page templates |
| International SEO Plan | Document | Hreflang implementation spec, URL structure recommendation, and geotargeting configuration |
| Migration Checklist | Checklist document | Pre-migration, migration day, and post-migration monitoring checklist with rollback procedures |
| Page Speed Optimization Plan | Document | Prioritized speed fixes with implementation details, expected LCP/INP/CLS improvements, and testing plan |

## Edge Cases

### JavaScript-Heavy Single Page Applications (React, Angular, Vue)
- **Situation**: Site renders all content client-side; Googlebot may see empty or incomplete pages
- **Approach**: Test rendered HTML using Google's URL Inspection tool and compare to source HTML. If critical content or links are missing from server response, recommend SSR (Next.js, Nuxt, Angular Universal) or static site generation. If SSR is not feasible, evaluate dynamic rendering as a stopgap (Rendertron, Puppeteer-based prerendering). Ensure meta tags, canonicals, and hreflang are in the initial HTML response, not injected by JavaScript. Audit JavaScript bundle size and hydration time as they directly impact INP.

### Large Ecommerce Sites (100K+ Pages, Faceted Navigation)
- **Situation**: Faceted navigation generates millions of URL combinations; crawl budget is consumed by low-value parameter pages
- **Approach**: Implement a canonicalization strategy for faceted URLs (canonical to the base category page unless the facet creates genuinely unique, valuable content). Use robots.txt or meta robots to block crawling of low-value parameter combinations. Create a curated internal linking strategy that directs crawlers to high-value pages. Build separate XML sitemaps for product pages, category pages, and editorial content. Monitor crawl stats to verify crawl budget is allocated to revenue-generating pages. Consider AJAX-based filtering that does not generate crawlable URLs for non-valuable combinations.

### Website Migrations (Domain, Platform, HTTPS)
- **Situation**: Business is changing domains, switching CMS platforms, or consolidating multiple sites
- **Approach**: Create a comprehensive URL mapping (old URL to new URL) before migration. Implement 301 redirects for every URL with organic traffic or backlinks. Set up monitoring for crawl errors, index coverage, and organic traffic immediately after migration. Expect a temporary ranking dip (typically 2-8 weeks for well-executed migrations). Keep the old domain/hosting active for at least 12 months to serve redirects. Verify all internal links, canonical tags, sitemaps, and hreflang tags reference the new URL structure. Run a full technical audit 1 week, 1 month, and 3 months post-migration.

### Multilingual Sites with Complex Hreflang Requirements
- **Situation**: Site serves content in 10+ languages with regional variations (e.g., en-US, en-GB, en-AU, es-ES, es-MX)
- **Approach**: Use XML sitemap method for hreflang at scale (HTML link tags become unmanageable above 20+ versions). Ensure every page has self-referencing hreflang and an x-default fallback. Verify bidirectional return links (if page A points to page B with hreflang, page B must point back to page A). Watch for canonical conflicts (canonical and hreflang must reference the same URL). Automate hreflang generation through CMS or build system to prevent manual errors. Test with Google's hreflang testing tools and monitor international targeting in GSC.

### Sites with Legacy Technical Debt
- **Situation**: Years of accumulated issues — mixed HTTP/HTTPS, orphan pages, redirect chains 5+ hops deep, duplicate content across subdomains, abandoned staging environments indexed by Google
- **Approach**: Prioritize by damage — index bloat and crawl waste first (they affect the entire site), then redirect chains (they bleed PageRank), then mixed content (security and trust signals), then orphan pages (wasted content investment). Do not try to fix everything at once. Create a phased remediation plan: Phase 1 (crawl and index cleanup), Phase 2 (redirect consolidation), Phase 3 (architecture optimization). Monitor organic traffic after each phase to measure impact and catch regressions.

## Related Skills

- **Content Engine** — Page speed and crawlability directly affect content discoverability; structured data enhances content appearance in SERPs; site architecture determines how content authority flows through internal links
- **Paid Advertising** — Core Web Vitals and landing page speed impact Google Ads Quality Score; technical health of landing pages affects conversion rates and ad spend efficiency
- **AEO/GEO Intelligence** — Structured data implementation strengthens AI platform comprehension and citation likelihood; site architecture affects how AI crawlers discover and interpret content
- **Analytics & Insights** — Technical SEO changes require measurement through organic traffic, crawl stats, index coverage, and Core Web Vitals dashboards; analytics data drives technical SEO prioritization
- **CRO** — Page speed directly correlates with conversion rates (every 100ms of LCP improvement can increase conversions by up to 1%); mobile usability affects conversion paths; site architecture determines user flow efficiency
