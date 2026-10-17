# Competitor analysis — dimension checklists, report tables, follow-ups, and dispatch rules

Read this when you are working each dimension of the teardown, laying out the report tables, offering next steps, or fanning the dimensions out in parallel. It supplements `SKILL.md`; the brand-loading step there is authoritative.

## Scope options (ask if not given)

- **Full analysis** — all dimensions below (default)
- **SEO comparison** — keyword overlap, domain authority, content depth, link gaps
- **Content analysis** — publishing strategy, content types, topics, quality, frequency
- **Paid advertising** — ad copy, creative themes, platforms, estimated spend
- **Social media** — platform presence, engagement, content mix, posting cadence
- **Pricing and positioning** — pricing models, value props, messaging frameworks

## Dimension checklists

### 1. Content strategy
- Content types produced (blog, video, podcast, newsletter, reports, tools)
- Publishing frequency and consistency
- Top-performing content (shares, backlinks, estimated traffic)
- Content themes and topic clusters
- Content gaps — topics you cover that they don't, and vice versa
- Quality assessment (depth, originality, E-E-A-T signals)

### 2. SEO competitive landscape
**If an SEO data connector is connected:** pull domain metrics, keyword rankings, and backlink profiles automatically; identify exact keyword overlap and gaps.

**If none is connected:** use web search to research the SEO landscape, and note: "For detailed ranking data, connect an SEO data tool via `/digital-marketing-pro:connect`."

Assess:
- Domain authority comparison
- Keyword overlap — terms both sites rank for, and who ranks higher
- Keyword gaps — terms competitors rank for that you don't
- Backlink profile comparison (referring domains, link quality)
- Content depth — average word count, topic breadth
- SERP feature ownership (featured snippets, People Also Ask, knowledge panels)

### 3. Paid advertising intelligence
- Platforms in use (search, social, programmatic)
- Ad copy themes and messaging patterns
- Landing page strategies
- Estimated ad spend (if data available)
- Creative approaches (image, video, carousel, text)
- Targeting signals (audiences they appear to target)

### 4. Social media benchmarking
- Platform presence (which platforms, follower counts)
- Engagement rates by platform
- Content mix (text, image, video, stories, live)
- Posting frequency and consistency
- Community engagement (response rate, comment quality)
- Viral or standout content

### 5. AI answer-engine visibility
- How competitors appear in Google AI Overviews
- Presence in other AI answer engines
- Citation patterns — which competitor sites are cited most for key topics
- Structured content that makes competitors more "citeable"

### 6. Pricing and positioning
- Pricing models (subscription, per-unit, freemium, enterprise)
- Price points relative to market
- Value proposition and messaging pillars
- Market positioning (premium, mid-market, budget, niche)
- Differentiation claims

## Report layout

### Competitive Overview Matrix

| Dimension | Your Brand | Competitor A | Competitor B | Competitor C |
|-----------|-----------|--------------|--------------|--------------|

Include rows for: content volume, SEO strength, social following, ad presence, pricing tier, AI visibility.

### Content Strategy Comparison

| Metric | Your Brand | Comp A | Comp B | Winner |
|--------|-----------|--------|--------|--------|

### SEO Landscape

| Keyword | Your Rank | Comp A | Comp B | Gap/Opportunity |
|---------|-----------|--------|--------|-----------------|

### SWOT per Competitor
For each competitor: Strengths, Weaknesses, Opportunities (for your brand), Threats.

### Strategic Recommendations
- **Quick Wins** — competitive gaps you can exploit immediately
- **Strategic Opportunities** — larger market positioning or content strategy moves
- **Defensive Priorities** — areas where competitors are gaining ground that need protection

## After the analysis

Ask: "Would you like me to:
- Set up ongoing competitor monitoring? (`/digital-marketing-pro:competitor-monitor`)
- Create a counter-narrative strategy? (`/digital-marketing-pro:counter-narrative`)
- Draft content to fill the competitive gaps identified? (`/digital-marketing-pro:content-brief`)
- Build a share-of-voice tracking dashboard? (`/digital-marketing-pro:share-of-voice`)
- Analyze competitor ad creative in detail? (`/digital-marketing-pro:paid-advertising`)
- Map the full narrative landscape? (`/digital-marketing-pro:narrative-landscape`)"

## Execution discipline — parallel dispatch

A full competitor analysis covers **7 independent dimensions** per competitor: content, SEO, paid ads, social, AI visibility, pricing, positioning. These have no cross-dependencies — they read different data sources and produce different sections of the final report.

Dispatch them via **one message with seven parallel `Task` tool calls** rather than seven sequential calls. Parallel dispatch of these independent dimensions is substantially faster than running them one after another; actual time varies with model and rate limits. Keep concurrency to a handful — past roughly 8 concurrent subagents you queue against API rate limits and the wall-clock win drops.

For multi-competitor analyses (the common case), parallelize per-dimension within each competitor, but **sequence the competitors** — running 3 competitors × 7 dimensions = 21 parallel subagents at once hits API concurrency ceilings on most tiers.
