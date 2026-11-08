# SEO Audit Checklist

**Purpose**: Actionable item-by-item checklist for scanning. Use during each audit phase.

## Contents

- Measurement & Confidence Checklist
- Technical SEO Checklist
- Platform Policy Checklist
- On-Page SEO Checklist
- Content SEO Checklist
- AEO (Answer Engine Optimization) Checklist
- GEO (Generative Engine Optimization) Checklist

## Measurement & Confidence Checklist

- [ ] Access level recorded: live URL, local files, Search Console, analytics, field Core Web Vitals, AI citation probe.
- [ ] Each evidence channel labeled as `official`, `live`, `field`, `tool`, `lab`, `synthetic`, or `heuristic`.
- [ ] Missing live/field/probe data is recorded as `unknown` or `not-applicable` with a reason instead of being hidden or scored as zero.
- [ ] Findings include `evidence_grade`, `confidence`, `measurement_method`, and `source_tier`.

## Technical SEO Checklist

### Crawling & Indexing

- [ ] `robots.txt` exists at root and doesn't block important pages
- [ ] `sitemap.xml` exists, is valid, and includes all indexable pages
- [ ] `sitemap.xml` is referenced in `robots.txt`
- [ ] No unintentional `noindex` directives on indexable pages
- [ ] Canonical tags present and pointing to correct URLs
- [ ] No orphan pages (pages not linked from anywhere)

### Crawl, Render & Index Interpretation Boundaries

- [ ] `source HTML` and `rendered DOM` are inspected separately for body text, meta tags, canonical, and links; a JavaScript-rendered page is not treated as a failure by itself
- [ ] `robots.txt` blocking and indexing blocking are reported separately, and robots.txt is not treated as a general index-removal tool
- [ ] `canonical` declared values, Google-selected values, redirects, and sitemap entries are reported separately
- [ ] `internal links` are confirmed as real `<a href>` anchors in the rendered DOM; framework syntax alone is not a failure
- [ ] `filtered URLs` and large sites are checked for URL explosion, zero-result responses, and duplicate paths; this applies conditionally to that site type
- [ ] `sitemap` scope, absolute URLs, and `lastmod` are checked, and submission is not treated as an indexing guarantee

### HTTPS & Security

- [ ] HTTPS enforced site-wide
- [ ] No mixed content (HTTP resources on HTTPS pages)
- [ ] Valid SSL certificate
- [ ] HTTP → HTTPS redirects in place (301)

### Performance & Core Web Vitals

- [ ] LCP target: ≤ 2.5s at p75 when field data is available — check hero image optimization, preloading
- [ ] INP target: ≤ 200ms at p75 when field data is available — check JavaScript execution, event handlers
- [ ] CLS target: ≤ 0.1 at p75 when field data is available — check image dimensions, dynamic content insertion
- [ ] Images optimized (WebP/AVIF, proper sizing, lazy loading for below-fold)
- [ ] Critical CSS inlined or preloaded
- [ ] JavaScript bundle size reasonable, code-split where possible

### Structured Data

- [ ] JSON-LD schema markup present on key pages
- [ ] Schema validates without errors (Schema Markup Validator)
- [ ] Appropriate schema types for visible content (Article, Product, FAQPage/QAPage where eligible, etc.)

### Mobile

- [ ] `<meta name="viewport" content="width=device-width, initial-scale=1">` present
- [ ] Responsive design — no horizontal scroll on mobile
- [ ] Touch targets ≥ 48px
- [ ] Font size ≥ 16px for body text

### URL Structure

- [ ] Clean, descriptive URLs (kebab-case, lowercase)
- [ ] No unnecessary query parameters in indexable URLs
- [ ] Proper 301 redirects for moved/renamed pages
- [ ] No redirect chains (A→B→C, should be A→C)

## Platform Policy Checklist

- [ ] Googlebot indexing/snippet access checked separately from AI training controls.
- [ ] Google-Extended policy checked only where relevant.
- [ ] OAI-SearchBot and GPTBot are evaluated separately for ChatGPT Search vs OpenAI training.
- [ ] `nosnippet`, `data-nosnippet`, `max-snippet`, `noindex`, canonical, and X-Robots-Tag effects checked.
- [ ] Recommendations cite official docs or observed files/headers when marked high confidence.

### Naver (Search Advisor)

- [ ] `Yeti` crawler access to the audited pages is verified separately from Googlebot, and Search Advisor ownership verification is recorded as the prerequisite for feed, console, and collection-request checks (target: naver)
- [ ] Naver's own `robots.txt` response handling is reported as observed: a 4xx response is treated as allow-all, a 5xx response as block-all, and more than five redirects as allow-all; blocking stays a separate finding from index removal (target: naver)
- [ ] `RSS` and `sitemap.xml` submissions are checked against the ownership-verified domain, because every feed URL must belong to the registered site; record the 50,000-URL and 10MB submission limits (target: naver)
- [ ] `og:image` meets the Naver conditions: larger than 150x150, at least 5,000 bytes, an aspect ratio no wider than 3:1, and a page-unique image (target: naver)
- [ ] `nosourceinfo` is reported at its actual scope: it suppresses the AI-generated source description Naver would otherwise show for the site, and it is not a blanket exclusion from AI briefing or model training (target: naver)
- [ ] `soft 404` responses and JavaScript-only navigation are recorded as index-exclusion risks: Naver reads a content-free 200 response as a normal page for collection, and content reachable only through JavaScript can be left out of the index (target: naver)
- [ ] `Google-only directives` are not transferred to Naver: `nosnippet`, `max-snippet`, `data-nosnippet`, `Google-Extended`, FAQPage rich results, and `llms.txt` are Google-side controls with no Naver counterpart, so none of them is reported as a Naver requirement (target: naver)

### Commerce (AI image labeling)

- [ ] AI-generated `image` labeling and metadata requirements that apply to commerce listings are checked only for commerce targets; a non-commerce target is `not-applicable` and unreadable listing data is `unknown` (target: commerce)

### Internationalization (hreflang)

- [ ] `hreflang` is validated as a bidirectional reference: an annotation that is not confirmed by the target URL is not in effect, `x-default` selects a default rather than replacing the other languages, language and region codes must be well formed, and each page includes a self-referencing `hreflang` (target: i18n)

### Bing (IndexNow & Webmaster Tools)

- [ ] `IndexNow` is recorded as a change-notification channel only: an HTTP 200 response means the search engine received the URL and a 202 that key validation is pending, and neither one confirms indexing, ranking, or AI citation (target: bing)
- [ ] `key file` ownership proof is checked before any submission: 8-128 characters of `[A-Za-z0-9-]`, served as UTF-8 at the host root or at the path named by `keyLocation`, and reachable without a login; deploying the key file and submitting URLs happen only when the user asks (target: bing)
- [ ] `urlList` submissions stay within 10,000 URLs per POST, and the response code of each submission is recorded as the finding (target: bing)
- [ ] `429` responses are handled by honoring `Retry-After` and shrinking the batch; the wait is recorded instead of retried in a loop (target: bing)
- [ ] `crawl quota` consumption is reported: every URL submitted through IndexNow counts toward the site's crawl quota, so unchanged URLs are not submitted and a site-wide push stays a sitemap job (target: bing)
- [ ] `backfill submissions` of existing URLs are not recommended: only meaningfully changed URLs, removals, and redirects are notified, and the same URL is not resubmitted within five minutes (target: bing)
- [ ] `changefreq` and `priority` are ignored by Bing sitemap processing; only `lastmod` in ISO 8601 is read, so neither field is reported as a Bing requirement (target: bing)
- [ ] `Bing Webmaster Tools` data that the audit cannot read because no site is verified or no console access exists is recorded as `unknown` rather than a failure; the module is excluded as `not-applicable` only when the target set does not include Bing surfaces (target: bing)

## On-Page SEO Checklist

### Title & Meta

- [ ] `<title>` unique per page; length is reported against a 60-character display heuristic, not a Google limit (heuristic)
- [ ] `<title>` includes primary keyword naturally
- [ ] `<meta name="description">` presence and length reported; 150–160 characters is a snippet display heuristic, not an official requirement (heuristic)
- [ ] Meta description is compelling and includes a call to action or value proposition
- [ ] No duplicate titles or descriptions across pages

### Headings

- [ ] `<h1>` count observed per page; a single `<h1>` is a convention, not a Google requirement (heuristic)
- [ ] `<h1>` includes primary keyword
- [ ] Logical heading hierarchy: h1 → h2 → h3 (no skipped levels)
- [ ] Headings are descriptive, not generic ("Section 1")

### Images

- [ ] All `<img>` have descriptive `alt` attributes
- [ ] Alt text includes relevant keywords where natural
- [ ] Images have explicit `width` and `height` (CLS prevention)
- [ ] Decorative images use `alt=""`

### Social Meta Tags

- [ ] `og:title`, `og:description`, `og:image`, `og:url` present
- [ ] `og:image` dimensions reported; 1200×630px is a platform display heuristic, not a validated requirement (heuristic)
- [ ] `twitter:card` set to `summary_large_image` or `summary`
- [ ] `twitter:title`, `twitter:description` present

### Internal Links

- [ ] Important pages are linked from navigation or content
- [ ] Anchor text is descriptive (not "click here")
- [ ] Internal link counts reported per 1,000 words; 3–5 is an editorial heuristic with no official density target (heuristic)
- [ ] No broken internal links (404s)

## Content SEO Checklist

### Quality & Relevance

- [ ] Content matches search intent for target keyword
- [ ] Content depth judged against search intent; word count is observed and there is no official minimum (heuristic)
- [ ] Original content — no duplicate from other pages or sites
- [ ] Freshness observed against the topic's time sensitivity; 12 months is a heuristic, not an official threshold (heuristic)

### Keyword Usage

- [ ] Primary keyword placement observed in title, H1, and first 100 words (heuristic)
- [ ] Keywords and related entities appear naturally; no fixed-density target or stuffing
- [ ] Semantic variations and related terms used throughout
- [ ] No keyword cannibalization (multiple pages targeting same keyword)

### E-E-A-T Signals

- [ ] Author information visible (bio, credentials)
- [ ] Sources cited for factual claims
- [ ] Contact information accessible
- [ ] Privacy policy and terms of service present
- [ ] Clear disclosure for sponsored/affiliate content

### Readability

- [ ] Short paragraphs (2–4 sentences)
- [ ] Subheading spacing observed; 200–300 words is a readability heuristic, not a requirement (heuristic)
- [ ] Bullet points and lists for scannable content
- [ ] Clear, jargon-free language (unless technical audience)

## AEO (Answer Engine Optimization) Checklist

### Direct Answer Structure

- [ ] Concise visible answer blocks appear near the top of sections for key questions (length rules are heuristic)
- [ ] Question-style H2/H3 headings are used, for example "## What is X?"
- [ ] Definition-style sentences follow the pattern "[Term] is [definition]"
- [ ] List or table content supports Featured Snippet extraction

### FAQ & Schema

- [ ] FAQPage/QAPage markup is checked for visible-content parity and entity clarity; the FAQ rich result is deprecated (effective 2026-05-07, documentation removed 2026-06-15), so rich result eligibility is not claimed
- [ ] FAQ/Q&A answers match visible content and structured data
- [ ] HowTo markup is not applied in expectation of a rich result; Google ended HowTo rich results, so HowTo content is checked for visible-content parity only

### Voice Search

- [ ] Natural-language question-style subheadings are used (Who, What, Where, When, Why, How)
- [ ] Conversational answer structure is present
- [ ] Answers are concise and direct enough for voice assistants to read

## GEO (Generative Engine Optimization) Checklist

### GEO CORE — Context

- [ ] Sufficient context and background are provided for the topic
- [ ] Related concepts and definitions are included
- [ ] The topic scope is clearly defined

### GEO CORE — Organization

- [ ] Clear H2/H3 hierarchy is present
- [ ] Each section starts with a 2-3 sentence key summary
- [ ] Short paragraphs (2-3 sentences), bullets, and tables are used
- [ ] Paragraphs can be extracted independently by AI systems

### GEO CORE — Reliability

- [ ] Verifiable statistics and numeric data are included
- [ ] Explicit source citations are included (author name, organization, date)
- [ ] Expert opinions or case studies are included
- [ ] E-E-A-T signals are strengthened (author information, credentials, contact details)

### GEO CORE — Exclusivity

- [ ] Proprietary data, original research, or benchmarks are included
- [ ] A unique perspective or framework is provided
- [ ] Insights exist that cannot be found elsewhere

### Entity Authority

- [ ] Topic clusters are organized (pillar + cluster)
- [ ] Internal links connect related content
- [ ] Organization/Person schema identifies entities
- [ ] Consistent expertise is expressed across multiple content pieces

### Content Freshness

- [ ] Content freshness matches the topic's time sensitivity, and `dateModified`/source dates are accurate
- [ ] `dateModified` schema markup is included
- [ ] Time-sensitive data includes exact dates

### AI Crawler Access

- [ ] `llms.txt` is checked as an optional content map, and a missing file is not treated as critical by default
- [ ] `robots.txt` is checked for purpose-specific groups: search crawlers (OAI-SearchBot, Claude-SearchBot, PerplexityBot) separately from training crawlers (GPTBot, ClaudeBot, Google-Extended, Applebot-Extended, Meta-ExternalAgent, CCBot) and user-triggered fetchers (ChatGPT-User, Claude-User, Perplexity-User), and CDN or WAF bot rules are checked as a separate layer that can override robots.txt intent
- [ ] Important content is accessible without JavaScript rendering

## Sources

> No external sources; content checked 2026-09-22.

This checklist is this package's own scan order over the criteria stated in `references/seo-fundamentals.md` and `references/aeo-geo-guide.md`, whose source ledgers carry the external references. It adds no external claim of its own.
