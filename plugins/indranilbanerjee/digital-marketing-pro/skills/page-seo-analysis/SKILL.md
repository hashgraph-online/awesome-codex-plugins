---
name: page-seo-analysis
description: "Run a deep SEO audit of one URL across title/meta, headings, content depth, E-E-A-T, schema (with deprecation flags for HowTo, FAQ, SpecialAnnouncement), images, internal links, technical signals, and AI search readiness. Produces a scored /80 report with exact replacement title tags and meta descriptions, ready-to-paste JSON-LD, and optional competitor comparison. Triggers on \"/digital-marketing-pro:page-seo-analysis\", \"analyze the SEO of this page\", \"why isn't this page ranking\", \"audit this URL before publish\", \"compare my page against competitor pages\". Reads the brand profile and guidelines; analysis and recommendations only — nothing is changed on the site. For a site-wide view, pair with /digital-marketing-pro:seo-audit."
argument-hint: "[URL]"
user-invocable: true
---

# /digital-marketing-pro:page-seo-analysis

## Purpose

Deep single-page SEO analysis — examines everything about one URL across all ranking dimensions. More granular than a site-wide audit. Use for landing page optimization, content refresh prioritization, or pre-publish quality checks.

## Input Required

- **URL**: The specific page to analyze
- **Target keyword**: Primary keyword this page should rank for (optional — can be inferred)
- **Competitors**: 1-3 competitor pages targeting the same keyword (optional)

## Process

1. **Load brand context**: Read active brand profile. Load brand guidelines if available.
2. **Fetch and parse page**: Retrieve full HTML, extract all signals.
3. **Title tag analysis**: Character count (50-60 chars ideal), keyword placement, brand inclusion, uniqueness, click-worthiness.
4. **Meta description analysis**: Character count (150-160 chars), keyword inclusion, CTA presence, uniqueness.
5. **Heading hierarchy**: H1 presence and uniqueness, H2-H6 logical structure, keyword distribution across headings.
6. **Content depth analysis**: Word count, reading level, topic coverage completeness, keyword *placement* (primary keyword in title, intro, ≥2 H2s, conclusion, and meta — density is not a target; keyword-density percentages are a discredited metric, not a ranking factor), natural coverage of related/co-occurring terms, content freshness (last modified date).
7. **E-E-A-T signals**: Author byline and bio, credentials, first-hand experience indicators, citations and sources, about page link, contact information.
8. **Schema markup detection**: JSON-LD, Microdata, RDFa — validate against Google's supported types, check for deprecations (HowTo deprecated Sept 2023, FAQ restricted to gov/health Aug 2023, SpecialAnnouncement deprecated July 2025), suggest missing schema opportunities.
9. **Image audit**: Alt text, dimensions, format, lazy loading, fetchpriority on LCP image (see image-seo-audit skill for full methodology).
10. **Internal linking**: Inbound links to this page, outbound links from this page, anchor text quality, orphan page check.
11. **Technical signals**: Canonical tag, robots directives, mobile viewport, HTTPS, page speed indicators, Core Web Vitals.
12. **AI search readiness**: Entity consistency, citation-worthiness, structured answer formatting, concise answer blocks for featured snippets.
13. **Competitor comparison** (if provided): Side-by-side analysis of word count, schema, headings, E-E-A-T signals vs competitor pages.

## Schema Deprecation Tracking

Always check and flag:
- **HowTo**: Deprecated (September 2023) — rich results removed
- **FAQ**: Restricted to government and health authority sites (August 2023)
- **SpecialAnnouncement**: Deprecated (July 2025)
- **EnergyConsumptionDetails**: Replaced by Certification schema (April 2025)

## Output

### Page SEO Score: XX/80

| Dimension | Score | Priority Issues |
|-----------|-------|-----------------|
| Title & Meta | /10 | ... |
| Content Depth | /10 | ... |
| E-E-A-T | /10 | ... |
| Schema Markup | /10 | ... |
| Images | /10 | ... |
| Internal Links | /10 | ... |
| Technical | /10 | ... |
| AI Readiness | /10 | ... |

- Specific, actionable recommendations for each dimension
- Exact replacement title tags and meta descriptions (with character counts)
- Missing schema markup JSON-LD code (ready to implement)
- Content gaps vs competitors
- Quick wins vs strategic improvements

## Agents Used

- **seo-specialist** — All page-level analysis, scoring, recommendations

## Scripts Used

- **tech-seo-auditor.py** — Technical signal extraction
- **content-scorer.py** — Content quality scoring
- **schema-generator.py** — Generate missing schema markup
- **competitor-scraper.py** — Competitor page comparison
