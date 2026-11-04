# Profile Templates

Ready-to-use templates for competitor profile sections and the summary document.

## Contents
- Evidence Markers (read first: every template below uses them)
- Deep Profile Template
- Quick Scan Template
- Summary Comparison Table
- Positioning Map
- Competitive SWOT
- Profile Update Changelog

---

## Evidence Markers

Every filled field in every template below carries one of four markers, so a
reader can tell at a glance what is observed and what is reasoned. This is the
mechanism behind "fact, inference, and unknowns kept separate": without it a
profile reads as uniformly authoritative regardless of where each line came from.

| Marker | Use for | Example |
|--------|---------|---------|
| `[fact: url, date]` | Anything read directly off a public page or review source | `$49/mo [fact: acme.com/pricing, 2026-03-04]` |
| `[provider estimate: provider, market, device, date]` | Any third-party metric: traffic, authority, keyword counts | `41k/mo [provider estimate: DataForSEO, US, desktop, 2026-03-04]` |
| `[inference]` | Anything reasoned from evidence rather than stated | `Mid-market ops teams [inference]` |
| `[unknown]` | Looked for, not found | `Team size: [unknown]` |

Two terminal states are legitimate and must not be filled with a guess:
`[unknown]` (searched, not found) and `not collected` (out of scope for this
depth level, or no authorized provider available). Never substitute an estimate
for either.

---

## Deep Profile Template

The full profile for a deep-profile run. One markdown file per competitor at
`competitor-profiles/[competitor-name].md`.

```markdown
# [Competitor Name]: Competitor Profile

**URL**: [website]
**Generated**: [date]
**Depth**: [quick scan / deep profile]
**Evidence markers**: [fact: url, date] · [provider estimate: provider, market, device, date] · [inference] · [unknown]

---

## At a Glance

| Metric | Value |
|--------|-------|
| Tagline | [value] [fact: url, date] |
| Founded | [value] [fact: url, date: or unknown] |
| Headquarters | [value] [fact: url, date: or unknown] |
| Team size | [value] [fact: url, date, or inference, or unknown] |
| Funding | [value] [fact: url, date: or unknown] |
| Provider domain metric | [value] [provider estimate: provider, market, device, date: or not collected] |
| Est. organic traffic | [monthly] [provider estimate: provider, market, device, date: or not collected] |
| Referring domains | [count] [provider estimate: provider, date: or not collected] |
| Organic keywords | [count] [provider estimate: provider, market, date: or not collected] |

---

## Positioning & Messaging

**Primary value proposition**: [headline + subheadline] [fact: homepage url, date]

**Target audience**: [who they're speaking to] [inference: from the copy cited above]

**Positioning angle**: [e.g. "simplicity-first," "enterprise-grade," "all-in-one"] [inference]

**Key messaging themes**:
- [theme 1] [fact: source page url, date]
- [theme 2] [fact: source page url, date]
- [theme 3] [fact: source page url, date]

---

## Product & Features

### Core capabilities
- [capability 1]: [description] [fact: url, date]
- [capability 2]: [description] [fact: url, date]
- ...

### Notable differentiators
- [what they emphasize as unique] [fact: url, date]

### Integrations
- [count] [fact: url, date: or unknown] integrations
- Key: [top 5-10] [fact: url, date]

### Product direction signals
- [read off changelog / recent releases] [inference: cite the changelog url and date]

---

## Pricing

| Tier | Price | Key Inclusions |
|------|-------|---------------|
| [Free/Starter] | [price] [fact: pricing url, date] | [what's included] |
| [Pro/Growth] | [price] [fact: pricing url, date] | [what's included] |
| [Enterprise] | [price] [fact: pricing url, date: or unknown if "contact us"] | [what's included] |

**Billing**: [monthly/annual, annual discount] [fact: pricing url, date]
**Free trial**: [yes/no, duration] [fact: pricing url, date]
**Notable**: [pricing quirks: per-seat, usage-based, hidden costs] [fact or inference]

---

## Customers & Social Proof

**Named customers**: [notable logos] [fact: url, date]
**Industries**: [primary industries served] [inference: from the logos and case studies cited]
**Case study themes**: [what outcomes they highlight] [fact: url, date]
**Review ratings**:
- G2: [rating] ([count] reviews) [fact: g2 url, date: or not collected]
- Capterra: [rating] ([count] reviews) [fact: capterra url, date: or not collected]

---

## SEO & Content Strategy

**Organic strength**:
- Estimated monthly organic traffic: [number] [provider estimate: provider, market, device, date: or not collected]
- Organic keywords (top 10): [count] [provider estimate: provider, market, date: or not collected]
- Organic traffic value: $[estimated] [provider estimate: provider, market, date: or not collected]

**Top organic pages** (by estimated traffic):
1. [page URL], [keyword], [est. traffic] [provider estimate: provider, date]
2. [page URL], [keyword], [est. traffic] [provider estimate: provider, date]
3. [page URL], [keyword], [est. traffic] [provider estimate: provider, date]

**Content strategy signals**:
- Blog post frequency: [estimate] [inference: from the blog index url and date]
- Primary content types: [guides, comparisons, templates, etc.] [fact: blog url, date]
- Content focus areas: [topics they invest in] [inference]

**Backlink profile**:
- Referring domains: [count] [provider estimate: provider, date: or not collected]
- Top referring sites: [list 5] [provider estimate: provider, date: or not collected]
- Link acquisition pattern: [growing/stable/declining] [inference: or not collected]

---

## Strengths & Weaknesses

### Strengths
- [strength 1] [fact: url, date: or inference from a cited capture]
- [strength 2] [fact: url, date: or inference from a cited capture]
- [strength 3] [fact: url, date: or inference from a cited capture]

### Weaknesses
- [weakness 1] [fact: url, date: or inference from a cited capture]
- [weakness 2] [fact: url, date: or inference from a cited capture]
- [weakness 3] [fact: url, date: or inference from a cited capture]

---

## Competitive Implications for [Your Product]

**Where they're strong vs. us**: [areas where this competitor has an advantage] [inference]

**Where we're strong vs. them**: [areas where you have an advantage] [inference]

**Opportunities**: [gaps in their offering or positioning we can exploit] [inference]

**Threats**: [areas where they're improving or gaining ground] [inference]

---

## Raw Data Sources

Built from `competitor-profiles/raw/[competitor-slug]/[YYYY-MM-DD]/`.

- Homepage scraped: [date]
- Pricing page scraped: [date]
- SEO data pulled: [date, provider, market, device]
- Review data pulled: [date, sources]
```

---

## Quick Scan Template

Abbreviated profile for when speed matters more than depth. Same evidence
markers as the deep profile, so the two stay comparable.

```markdown
# [Competitor Name]: Quick Profile

**URL**: [website]
**Generated**: [date]
**Evidence markers**: [fact: url, date] · [provider estimate: provider, market, device, date] · [inference] · [unknown]

## At a Glance

| Metric | Value |
|--------|-------|
| Tagline | [value] [fact: homepage url, date] |
| Target audience | [value] [inference: from the copy cited above] |
| Pricing starts at | [lowest paid tier] [fact: pricing url, date] |
| Free tier/trial | [yes/no + details] [fact: pricing url, date] |
| Provider domain metric | [value] [provider estimate: provider, market, device, date: or not collected] |
| Est. organic traffic | [monthly] [provider estimate: provider, market, device, date: or not collected] |
| Organic keywords (top 10) | [count] [provider estimate: provider, market, date: or not collected] |
| Referring domains | [count] [provider estimate: provider, date: or not collected] |

## Positioning

**Headline**: "[exact homepage headline]" [fact: homepage url, date]
**Subheadline**: "[exact subheadline]" [fact: homepage url, date]
**Positioning angle**: [1-2 sentence summary of how they position] [inference]

## Pricing Summary

| Tier | Price | Notable Inclusions |
|------|-------|-------------------|
| [tier] | [price] [fact: pricing url, date] | [key items] |
| [tier] | [price] [fact: pricing url, date] | [key items] |

## Key Takeaway

[2-3 sentences: what makes this competitor notable, where they're strong, where they're weak]
```

---

## Summary Comparison Table

Use after profiling all competitors to create a side-by-side view.

```markdown
# Competitive Landscape Summary

**Generated**: [date]
**Your product**: [name]
**Competitors profiled**: [count]

## Side-by-Side Comparison

| Dimension | [Your Product] | [Competitor 1] | [Competitor 2] | [Competitor 3] |
|-----------|---------------|----------------|----------------|----------------|
| **Tagline** | [yours] | [theirs] | [theirs] | [theirs] |
| **Target audience** | [yours] | [theirs] | [theirs] | [theirs] |
| **Positioning** | [angle] | [angle] | [angle] | [angle] |
| **Starting price** | $[X]/mo | $[X]/mo | $[X]/mo | $[X]/mo |
| **Free tier** | [yes/no] | [yes/no] | [yes/no] | [yes/no] |
| **Domain rank** | [score] | [score] | [score] | [score] |
| **Est. organic traffic** | [number] | [number] | [number] | [number] |
| **Referring domains** | [count] | [count] | [count] | [count] |
| **G2 rating** | [score] | [score] | [score] | [score] |
| **Key strength** | [one-liner] | [one-liner] | [one-liner] | [one-liner] |
| **Key weakness** | [one-liner] | [one-liner] | [one-liner] | [one-liner] |
```

---

## Positioning Map

Visual representation of where competitors sit along two key dimensions. Choose the two axes most relevant to your market.

### Common Axis Pairs

| Market Type | X-Axis | Y-Axis |
|-------------|--------|--------|
| SaaS tools | Simple → Complex | Cheap → Expensive |
| Developer tools | Low-code → Code-first | Individual → Team |
| B2B platforms | SMB-focused → Enterprise-focused | Point solution → Platform |
| Content tools | Template-driven → Custom | Self-serve → Managed |

### Format

```markdown
## Positioning Map

**Axes**: [X-axis label] vs. [Y-axis label]

                    [Y-axis high label]
                           │
                           │
          [Competitor A]   │    [Competitor B]
                           │
    ───────────────────────┼───────────────────────
    [X-axis low]           │           [X-axis high]
                           │
          [Your Product]   │    [Competitor C]
                           │
                    [Y-axis low label]

### Interpretation
- [1-2 sentences about what the map reveals]
- [where the whitespace / opportunity is]
```

---

## Competitive SWOT

Per-competitor SWOT relative to your product.

```markdown
## SWOT: [Competitor] vs. [Your Product]

### Strengths (theirs vs. ours)
- [Where they genuinely outperform us: be honest]

### Weaknesses (theirs vs. ours)
- [Where they fall short compared to us: with evidence]

### Opportunities (for us)
- [Gaps in their offering we can exploit]
- [Segments they're ignoring]
- [Messaging angles they're missing]

### Threats (from them)
- [Areas where they're improving fast]
- [Features they're building that overlap with us]
- [Market moves that could shift perception]
```

---

## Profile Update Changelog

Append to the bottom of any profile when updating it.

```markdown
---

## Change Log

| Date | What Changed | Source |
|------|-------------|--------|
| [date] | Pricing increased from $X to $Y | Pricing page recapture |
| [date] | Launched [feature] | Changelog recapture |
| [date] | Provider domain metric changed from X to Y | Same-provider refresh with matching market and device |
| [date] | Added [integration] | Integrations page recapture |
```
