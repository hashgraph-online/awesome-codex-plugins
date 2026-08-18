# Content Decay — Detection & Refresh Strategy

## Decay Detection Signals

| Signal | Measurement | Threshold |
|--------|------------|-----------|
| Traffic decline | Organic sessions vs 3-month rolling average | >20% decline |
| Ranking drop | Position change for target keyword | Drop 5+ positions |
| CTR decline | Search Console CTR vs historical average | >15% decline |
| Engagement decay | Time on page, scroll depth, bounce rate | Worsening trend for 4+ weeks |
| Backlink loss | Referring domains to the page | >10% loss in 90 days |
| Competitor surpassing | Competitor ranks higher with newer content | Confirmed in SERP review |

---

## Content Audit Spreadsheet Template

| URL | Title | Published | Last Updated | Monthly Traffic | Traffic Trend | Ranking Keyword | Position | Decay Type | Priority | Action |
|-----|-------|-----------|-------------|----------------|--------------|----------------|----------|-----------|----------|--------|

**Fill quarterly. Sort by traffic decline to find biggest opportunities.**

---

## Decay Categories

| Category | Symptoms | Common Causes |
|----------|----------|---------------|
| **Outdated information** | Facts, stats, or dates are wrong | Time passage, industry changes |
| **Ranking decline** | Lost positions for target keywords | Competitor published better content, algorithm update |
| **Broken experience** | Broken links, missing images, broken embeds | Site changes, external link rot |
| **Competitor surpassed** | Competitor content now ranks higher | Their content is more comprehensive, recent, or authoritative |
| **Format outdated** | Content looks old, lacks modern formatting | Design trends changed, mobile expectations evolved |
| **Intent shift** | Search intent for target keyword changed | Google now shows different content type (videos, lists, tools) |

---

## Refresh vs Rewrite vs Retire Decision

| Scenario | Decision | Reasoning |
|----------|----------|-----------|
| Content still accurate, needs minor updates | **Refresh** | Update stats, add sections, improve formatting |
| Content fundamentally outdated or wrong | **Rewrite** | Keep the URL, completely new content |
| Content on a topic no longer relevant | **Retire** | 301 redirect to most relevant page |
| Content cannibalized by another page | **Consolidate** | Merge best parts, redirect the weaker page |
| Content never performed (no traffic ever) | **Evaluate** | Fix if topic is strategic, retire if not |

---

## Content Refresh Checklist

- [ ] Update all statistics and data with current-year sources
- [ ] Fix or remove all broken links
- [ ] Replace outdated screenshots or images
- [ ] Add new sections covering subtopics competitors address
- [ ] Update examples to be current and relevant
- [ ] Improve internal links (link to newer content, update old links)
- [ ] Add FAQ section if one doesn't exist (target featured snippets)
- [ ] Optimize for any new keyword opportunities discovered
- [ ] Improve readability (shorter sentences, better formatting, subheadings)
- [ ] Update schema markup (dateModified, new FAQ schema)
- [ ] Update meta title and description if CTR is declining
- [ ] Add or update table of contents for long content
- [ ] Ensure mobile formatting is optimal
- [ ] Re-submit URL to Google Search Console for re-indexing

---

## Refresh Priority Scoring

Score each piece of decaying content:

| Factor | Weight | Scoring (1-10) |
|--------|--------|----------------|
| **Traffic impact** (current/historical traffic) | 30% | 10 = 1,000+ monthly visits, 1 = <50 |
| **Revenue connection** (converts or assists conversions) | 25% | 10 = direct revenue page, 1 = informational only |
| **Refresh effort** (time/resources to update) | 20% | 10 = quick refresh (1-2 hours), 1 = full rewrite needed |
| **Strategic value** (pillar page, key topic, competitive) | 15% | 10 = core pillar content, 1 = peripheral |
| **Competitive urgency** (competitors gaining) | 10% | 10 = competitor recently published, 1 = no competition |

**Priority Score** = Weighted sum. Address highest scores first.

---

## Update Tracking

For each refresh, document:

| Field | Value |
|-------|-------|
| URL | [page URL] |
| Refresh date | [date] |
| Changes made | [summary of what was updated] |
| Pre-refresh traffic (30-day avg) | [number] |
| Pre-refresh ranking | [position for target keyword] |
| Post-refresh traffic (30-day avg) | [measure 30 days after refresh] |
| Post-refresh ranking | [measure 2-4 weeks after] |
| Traffic change | [% change] |
| Next review date | [schedule next check] |
