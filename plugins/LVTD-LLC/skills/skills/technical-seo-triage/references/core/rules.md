# Technical SEO Triage Rules

Use these rules when diagnosing technical SEO issues.

## Core Rules

### 1. Diagnose The Search Stage First

Classify the issue before recommending fixes.

- Discovery issue: Google does not know the URL exists.
- Crawl issue: Google knows the URL but does not fetch enough.
- Index issue: Google crawls but excludes, canonicalizes, or distrusts the page.
- Ranking/click issue: Google indexes the page but users do not see or click it.
- Conversion issue: search traffic arrives but does not produce value.

### 2. Segment Before Explaining

Do not explain a traffic drop from aggregate charts alone.

- Segment by URL, query, country, device, date, brand/non-brand, and page type.
- Identify winners as well as losers after algorithm updates.
- Compare impressions, clicks, CTR, and conversions separately.

### 3. Treat GSC As The Primary Search Evidence

Use Google Search Console first for search visibility and indexation.

- Inspect URL-level data when a specific page is involved.
- Check whether declared canonicals match Google's selected canonicals.
- Treat many GSC errors as informational, but prioritize robots, crawl, schema, and indexation blockers.

### 4. Fix Internal Link Graphs Before Chasing Links

Large sites often have discovery and authority-flow problems.

- Ensure important pages are reachable from multiple paths.
- Avoid related-content modules that only link popular pages to popular pages.
- Add HTML sitemaps or site directories when they help discovery.
- Mix related, recent, important, and exploratory links where appropriate.

### 5. Reduce Low-Value Crawl Waste

Do not force crawlers through endless low-value URLs.

- Block, noindex, canonicalize, consolidate, or remove pages that waste crawl attention.
- Protect valuable pages from being buried behind weak architecture.
- Keep user value as the deciding principle.

### 6. Do Not Panic About Duplicate Content

Duplicate content is not automatically a penalty.

- Ask whether the duplicate content helps users.
- Use canonicals when a preferred URL exists.
- Avoid manipulative doorway pages or large-scale low-quality duplication.

### 7. Treat Migrations As High-Risk Projects

URL changes require deliberate planning.

- Build a complete old-to-new URL map.
- Use 301 redirects for permanent moves.
- Crawl old URLs before launch to verify redirects.
- Maintain redirects long term.
- Consider staged migrations when business risk is high.

## Red Flags

- A migration has no URL map.
- A traffic drop is explained without URL/query segmentation.
- Robots, noindex, canonicals, or redirects are changed without validation.
- Large sites rely only on homepage/category links for discovery.
- The fix optimizes crawlers while making pages worse for users.
