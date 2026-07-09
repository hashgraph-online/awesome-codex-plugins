---
name: competitor-pages
description: "Create competitor comparison pages. Use when: \"X vs Y\" layouts, alternatives pages, feature matrices, roundup pages."
argument-hint: "[URL or generate] [competitor]"
user-invocable: true
---

# /digital-marketing-pro:competitor-pages

## Purpose

Create high-converting competitor comparison and alternatives pages that target competitive intent keywords with accurate, structured content and appropriate schema markup.

## Input Required

The user must provide (or will be prompted for):

- **Page type**: "X vs Y", "alternatives to X", "best tools roundup", or "comparison table"
- **Your product/service**: The product being positioned
- **Competitors**: 1-5 competitor products to compare against
- **Comparison criteria**: Features, pricing, use cases to compare (or auto-detected)
- **Target audience**: Who is making this purchase decision

## Page Types

### 1. "X vs Y" Comparison Pages
- Direct head-to-head comparison between two products/services
- Balanced feature-by-feature analysis
- Clear verdict or recommendation with justification
- Target keyword: `[Product A] vs [Product B]`

### 2. "Alternatives to X" Pages
- List of alternatives to a specific product/service
- Each alternative with brief summary, pros/cons, best-for use case
- Target keyword: `[Product] alternatives`, `best alternatives to [Product]`

### 3. "Best [Category] Tools" Roundup Pages
- Curated list of top tools/services in a category
- Ranking criteria clearly stated
- Target keyword: `best [category] tools [year]`, `top [category] software`

### 4. Comparison Table Pages
- Feature matrix with multiple products in columns
- Sortable/filterable layout recommendations
- Target keyword: `[category] comparison`, `[category] comparison chart`

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice and compliance rules. Check for brand guidelines — especially restrictions on competitor mentions.
2. **Research competitors**: Gather feature data, pricing, positioning from public sources. Verify all claims.
3. **Generate comparison structure**: Feature matrix, content outline, section order
4. **Apply schema markup**: Product, SoftwareApplication, AggregateRating, or ItemList JSON-LD depending on page type
5. **Optimize for conversion**: CTA placement strategy, social proof sections, pricing highlights
6. **Apply fairness guidelines**: Accuracy verification, source citations, affiliation disclosure
7. **Keyword optimization**: Primary and secondary keyword targeting, title tag formulas, H1 patterns
8. **Internal linking strategy**: Cross-link between related comparison pages, feature pages, case studies

## Comparison Table Template

```
| Feature          | Your Product | Competitor A | Competitor B |
|------------------|:------------:|:------------:|:------------:|
| Feature 1        | ✅           | ✅           | ❌           |
| Feature 2        | ✅           | ⚠️ Partial   | ✅           |
| Feature 3        | ✅           | ❌           | ❌           |
| Pricing (from)   | $X/mo        | $Y/mo        | $Z/mo        |
| Free Tier        | ✅           | ❌           | ✅           |
```

### Data Accuracy Requirements
- All feature claims must be verifiable from public sources
- Pricing must be current (include "as of [date]" note)
- Update frequency: review quarterly or when competitors ship major changes
- Link to source for each competitor data point where possible

## Schema Markup Templates

### Product with AggregateRating (for X vs Y pages)
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "[Product Name]",
  "description": "[Product Description]",
  "brand": { "@type": "Brand", "name": "[Brand Name]" },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "[Rating]",
    "reviewCount": "[Count]",
    "bestRating": "5",
    "worstRating": "1"
  }
}
```

### SoftwareApplication (for software comparisons)
```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "[Software Name]",
  "applicationCategory": "[Category]",
  "operatingSystem": "[OS]",
  "offers": { "@type": "Offer", "price": "[Price]", "priceCurrency": "USD" }
}
```

### ItemList (for roundup pages)
```json
{
  "@context": "https://schema.org",
  "@type": "ItemList",
  "name": "Best [Category] Tools [Year]",
  "itemListOrder": "https://schema.org/ItemListOrderDescending",
  "numberOfItems": "[Count]",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "[Product Name]", "url": "[Product URL]" }
  ]
}
```

## Keyword Targeting

### Comparison Intent Patterns
| Pattern | Example | Volume Signal |
|---------|---------|--------------|
| `[A] vs [B]` | "Slack vs Teams" | High |
| `[A] alternative` | "Figma alternatives" | High |
| `[A] alternatives [year]` | "Notion alternatives 2026" | High |
| `best [category] tools` | "best project management tools" | High |
| `[A] vs [B] for [use case]` | "AWS vs Azure for startups" | Medium |
| `[A] vs [B] pricing` | "HubSpot vs Salesforce pricing" | Medium |
| `is [A] better than [B]` | "is Notion better than Confluence" | Medium |

### Title Tag Formulas
- X vs Y: `[A] vs [B]: [Key Differentiator] ([Year])`
- Alternatives: `[N] Best [A] Alternatives in [Year] (Free & Paid)`
- Roundup: `[N] Best [Category] Tools in [Year], Compared & Ranked`

## Conversion-Optimized Layouts

### CTA Placement
- **Above fold**: Brief comparison summary with primary CTA
- **After comparison table**: "Try [Your Product] free" CTA
- **Bottom of page**: Final recommendation with CTA
- Avoid aggressive CTAs in competitor description sections (reduces trust)

### Social Proof Sections
- Customer testimonials relevant to comparison criteria
- G2/Capterra/TrustPilot ratings (with source links)
- Case studies showing migration from competitor
- "Switched from [Competitor]" stories

### Trust Signals
- "Last updated [date]" timestamp
- Author with relevant expertise
- Methodology disclosure
- Disclosure of own product affiliation
- Balanced presentation — acknowledge competitor strengths honestly

## Fairness Guidelines

- **Accuracy**: All competitor information must be verifiable from public sources
- **No defamation**: Never make false or misleading claims about competitors
- **Cite sources**: Link to competitor websites, review sites, or documentation
- **Timely updates**: Review and update when competitors release major changes
- **Disclose affiliation**: Clearly state which product is yours
- **Balanced presentation**: Acknowledge competitor strengths honestly
- **Pricing accuracy**: Include "as of [date]" disclaimers on all pricing data

## Output

A structured competitor comparison page package containing:

- Page content template (minimum 1,500 words) with all sections
- Feature matrix table
- Schema markup (JSON-LD) appropriate to page type
- Primary and secondary keywords with title tag and H1 recommendations
- Internal linking plan (cross-link to related comparisons, feature pages, case studies)
- Conversion optimization recommendations
- Content gap analysis vs existing competitor pages

## Agents Used

- **seo-specialist** — Keyword targeting, schema markup, on-page optimization
- **content-creator** — Comparison content writing, brand voice application
- **competitive-intel** — Competitor feature and pricing research
- **brand-guardian** — Ensure compliance with brand guidelines on competitor mentions

## Scripts Used

- **schema-generator.py** — Generate Product, SoftwareApplication, or ItemList JSON-LD
- **competitor-scraper.py** — Extract competitor page data for comparison
- **content-scorer.py** — Score comparison page quality
