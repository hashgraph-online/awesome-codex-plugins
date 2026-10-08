# SEO audit — dimension checklists, finding tables, follow-ups, and dispatch rules

Read this when you are working an audit dimension, laying out the findings tables and action plan, offering next steps, or fanning the dimensions out in parallel. It supplements `SKILL.md`; the brand-loading step, numbered-output convention, and quality gates there are authoritative.

## Scope options (ask if not given)

- **Full site audit** — end-to-end review across every dimension below (default)
- **Technical only** — crawlability, Core Web Vitals, structured data, infrastructure
- **Content only** — thin content, gaps, freshness, E-E-A-T, keyword opportunities
- **Local SEO** — Google Business Profile, NAP consistency, local schema, reviews
- **Competitor comparison** — head-to-head benchmarking against specific competitors

If no competitors are given and a comparison is needed, identify likely competitors from the keyword space. A topic or keyword can be given instead of a URL when running in keyword-research mode.

## Dimension checklists

### 1. Keyword research
**If an SEO data connector is connected:** pull keyword data, search volume, difficulty scores, and current ranking positions automatically; identify keywords gaining or losing ground.

**If none is connected:** use web search to research the keyword landscape, and note: "For precise volume and difficulty data, connect an SEO data tool via `/digital-marketing-pro:connect`."

For each keyword opportunity assess:
- **Search volume signals** — relative demand (high, medium, low)
- **Keyword difficulty** — how competitive (easy, moderate, hard)
- **Intent classification** — informational, navigational, commercial, or transactional
- **Long-tail opportunities** — specific, lower-competition phrases with clear intent
- **Question-based keywords** — "how to", "what is" queries for People Also Ask

### 2. Technical SEO
- **Page speed** — slow-loading pages, likely causes (large images, render-blocking scripts, redirects)
- **Mobile-friendliness** — responsive design, tap targets, viewport configuration
- **Structured data** — schema markup opportunities (FAQ, HowTo, Product, Article, Organization, Breadcrumb)
- **Crawlability** — robots.txt, XML sitemap, canonical tags, noindex/nofollow usage
- **Broken links** — internal and external 404s, redirect chains
- **HTTPS** — secure connection, mixed content
- **Core Web Vitals** — LCP, INP, CLS indicators
- **Indexation** — pages that should be indexed but aren't, duplicate content risks

### 3. On-page SEO
For each key page (homepage, top landing pages, recent content):
- **Title tags** — present, unique, 50-60 characters, includes the target keyword
- **Meta descriptions** — present, compelling, 150-160 characters, includes a CTA
- **Heading hierarchy** — one H1, logical H2/H3 structure, keywords in subheadings
- **Keyword usage** — primary keyword in the first 100 words, natural distribution, no stuffing
- **Internal linking** — pages link to related content, orphan pages identified, descriptive anchor text
- **Image optimization** — alt text on all images, compressed files, proper sizing
- **URL structure** — clean, readable, keyword-inclusive

### 4. Content quality and E-E-A-T
- **Experience** — first-hand experience signals, original research, case studies
- **Expertise** — author credentials, depth of coverage, technical accuracy
- **Authoritativeness** — citation quality, industry recognition, backlink authority
- **Trustworthiness** — accuracy, transparency, editorial standards, secure site
- **Content freshness** — pages not updated in 12+ months, outdated statistics
- **Thin content** — pages with insufficient depth to rank
- **Content gaps** — topics competitors cover that the site doesn't

### 5. AI answer-engine visibility (AEO/GEO)
- **AI Overview presence** — does the site appear in Google AI Overviews?
- **Citation-worthiness** — are there "citeable moments" (definitions, data, structured answers)?
- **Snippet structuring** — content formatted for direct answer extraction
- **Entity consistency** — brand name, facts, and claims consistent across the web

### 6. Link profile
- **Domain authority signals** — overall site strength based on the backlink profile
- **Backlink quality** — proportion of high-quality vs. low-quality referring domains
- **Anchor text distribution** — natural vs. over-optimized
- **Link velocity** — trend in new links acquired
- **Competitor link gap** — sites linking to competitors but not to this domain (hand off to `/digital-marketing-pro:backlink-gap`)
- **Toxic links** — potentially harmful backlinks to disavow

### 7. Local SEO (if applicable)
- **Google Business Profile** — completeness, accuracy, categories, photos, posts
- **NAP consistency** — name, address, phone matching across directories
- **Local schema markup** — LocalBusiness, opening hours, service area
- **Review profile** — volume, recency, rating, response rate
- **Local content** — city/service pages, local landing pages

## Findings layout

### Executive summary
- Overall SEO health score (1-10 per dimension)
- Top 3 strengths
- Top 3 priorities with estimated impact

### Keyword opportunity table

| Keyword | Volume Signal | Difficulty | Current Rank | Intent | Recommended Action |
|---------|--------------|------------|--------------|--------|--------------------|

Include 15-25 opportunities sorted by opportunity score.

### Issue table

| Page/Area | Issue | Severity | Recommended Fix | Effort |
|-----------|-------|----------|-----------------|--------|

Severity: **Critical** (hurting rankings), **High** (significant impact), **Medium** (best practice), **Low** (minor optimization).

### Content gap recommendations
For each gap: topic, search demand, competitor coverage, recommended content type, priority, and estimated effort.

### Prioritized action plan
**Quick wins (this week)** — actions under 2 hours with immediate impact, e.g. fix title tags, add meta descriptions, fix broken links, add alt text.

**Strategic investments (this quarter)** — higher-effort actions driving long-term growth, e.g. build topic clusters, pillar pages, a link-building campaign, a site structure overhaul.

Each action includes: what to do, expected impact (high/medium/low), effort estimate, and dependencies.

## After the audit

Ask: "Would you like me to:
- Draft content briefs for the top keyword opportunities? (`/digital-marketing-pro:content-brief`)
- Create optimized title tags and meta descriptions? (`/digital-marketing-pro:seo-implement`)
- Run a deeper technical audit? (`/digital-marketing-pro:tech-seo-audit`)
- Set up keyword ranking monitoring? (`/digital-marketing-pro:rank-monitor`)
- Check AI answer engine visibility? (`/digital-marketing-pro:aeo-audit`)
- Compare SEO performance against specific competitors? (`/digital-marketing-pro:competitor-analysis`)"

## Execution discipline — parallel dispatch

An SEO audit covers **6 independent dimensions**: technical infrastructure (Core Web Vitals + crawlability + indexation + redirects + security), on-page optimization, content quality + gaps, E-E-A-T signals, link profile, AI answer engine visibility. None of these depend on the others' findings to produce their own.

Dispatch the independent dimensions concurrently in **one message**, using the real targets:

- **Technical infrastructure** → run the `tech-seo-audit` skill
- **On-page optimization + E-E-A-T signals** → invoke the `seo-specialist` agent (there is no `on-page-audit` or `eeat-evaluator` subagent — `seo-specialist` owns both dimensions)
- **Content quality + gaps** → run `content-engine` in audit mode
- **AI answer engine visibility** → run the `aeo-audit` skill
- **Link profile** → run the link-profile analyzer as a **script** (not an agent): `python "${CLAUDE_PLUGIN_ROOT}/scripts/link-profile-analyzer.py" ...`

Parallel dispatch of these independent dimensions is substantially faster than running them sequentially; actual time varies with model and rate limits.

The **action plan and prioritization step at the end must be sequential** — it consumes the merged output of all six dimensions and produces a single ranked impact-to-effort matrix.
