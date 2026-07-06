---
name: programmatic-seo
description: "Plan programmatic SEO pages. Use when: building template engines, URL patterns, thin content safeguards, or quality gates."
argument-hint: "[URL or plan]"
user-invocable: true
---

# /digital-marketing-pro:programmatic-seo

## Purpose

Plan and audit SEO pages generated at scale from structured data sources (databases, APIs, CSV/JSON files). Enforces quality gates to prevent thin content penalties, index bloat, and Google's Scaled Content Abuse policy.

## Input Required

The user must provide (or will be prompted for):

- **URL or data source**: Existing programmatic pages to audit, or data source details for planning
- **Page type**: What kind of pages are being generated (location, product, integration, glossary, template, tool)
- **Data source**: CSV/JSON files, API endpoints, database queries — or existing pages to analyze
- **Target scale**: How many pages will be generated
- **Current status**: New build or auditing existing programmatic pages

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply industry context and compliance rules. Check for brand guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json`.
2. **Data source assessment**: Evaluate the data powering programmatic pages — row count, column uniqueness, missing values, duplicate detection (>80% field overlap), data freshness
3. **Template engine planning**: Design templates that produce genuinely unique pages — variable injection points, content blocks (static vs dynamic), conditional logic, supplementary content. Validate each page passes the "standalone value test"
4. **URL pattern strategy**: Design URL hierarchy — lowercase hyphenated slugs, logical structure, uniqueness enforcement, under 100 characters, consistent trailing slash
5. **Internal linking automation**: Hub/spoke model, related items (3-5 per page), breadcrumbs with BreadcrumbList schema, cross-linking by shared attributes, varied anchor text
6. **Thin content safeguard check**: Apply quality gates (see below)
7. **Canonical strategy**: Self-referencing canonicals, parameter handling, pagination strategy, manual page priority
8. **Sitemap integration**: Auto-generate entries, split at 50K URLs, `<lastmod>` from actual data timestamps, exclude noindexed pages
9. **Index bloat prevention**: Noindex low-value pages, pagination handling, faceted navigation canonicalization, crawl budget monitoring for 10K+ pages
10. **Score and report**: Score each dimension, produce prioritized action plan

## Quality Gates

### Scale Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| Pages without content review | 100+ | WARNING: require content audit before publishing |
| Pages without justification | 500+ | HARD STOP: require explicit user approval and thin content audit |
| Unique content per page | <40% | Flag as thin content (penalty risk) |
| Unique content per page | <30% | HARD STOP: scaled content abuse risk |
| Word count per page | <300 | Flag for review (may lack sufficient value) |

### Scaled Content Abuse Context (2025-2026)

Google's Scaled Content Abuse policy (introduced March 2024) saw major enforcement escalation:

- **June 2025**: Wave of manual actions targeting AI-generated content at scale
- **August 2025**: SpamBrain update enhanced pattern detection for AI-generated link schemes and content farms
- **Result**: 45% reduction in low-quality, unoriginal content in search results

**Enhanced quality gates for programmatic pages:**

- **Content differentiation**: 30-40%+ of content must be genuinely unique between any two programmatic pages (not just city/keyword string replacement)
- **Human review**: Minimum 5-10% sample review of generated pages before publishing
- **Progressive rollout**: Publish in batches of 50-100 pages. Monitor indexing and rankings for 2-4 weeks before expanding. Never publish 500+ simultaneously without quality review.
- **Standalone value test**: Each page should pass: "Would this page be worth publishing even if no other similar pages existed?"
- **Site reputation abuse**: Publishing programmatic content under a high-authority domain (not your own) may trigger site reputation abuse penalties (enforced aggressively since November 2024)

### Safe vs Risky Programmatic Pages

**Safe at scale:**
- Integration pages (with real setup docs, API details, screenshots)
- Template/tool pages (with downloadable content, usage instructions)
- Glossary pages (200+ word definitions with examples, related terms)
- Product pages (unique specs, reviews, comparison data)
- Data-driven pages (unique statistics, charts, analysis per record)

**Penalty risk at scale:**
- Location pages with only city name swapped in identical text
- "Best [tool] for [industry]" without industry-specific value
- "[Competitor] alternative" without real comparison data
- AI-generated pages without human review and unique value-add
- Pages where >60% of content is shared template boilerplate

### Uniqueness Calculation

Unique content % = (words unique to this page) / (total words on page) x 100

Measured against all other pages in the programmatic set. Shared headers, footers, and navigation excluded. Template boilerplate IS included.

## URL Pattern Library

### Common Patterns
- `/tools/[tool-name]`: Tool/product directory pages
- `/[city]/[service]`: Location + service pages
- `/integrations/[platform]`: Integration landing pages
- `/glossary/[term]`: Definition/reference pages
- `/templates/[template-name]`: Downloadable template pages
- `/compare/[product-a]-vs-[product-b]`: Comparison pages

### URL Rules
- Lowercase, hyphenated slugs derived from data
- Logical hierarchy reflecting site architecture
- No duplicate slugs — enforce uniqueness at generation time
- Keep URLs under 100 characters
- No query parameters for primary content URLs
- Consistent trailing slash usage (match existing site pattern)

## Output

A structured programmatic SEO assessment containing:

### Programmatic SEO Score: XX/100

| Category | Status | Score |
|----------|--------|-------|
| Data Quality | score | /100 |
| Template Uniqueness | score | /100 |
| URL Structure | score | /100 |
| Internal Linking | score | /100 |
| Thin Content Risk | score | /100 |
| Index Management | score | /100 |

- Critical issues (fix immediately)
- High priority (fix within 1 week)
- Medium priority (fix within 1 month)
- Recommendations: data source improvements, template modifications, URL pattern adjustments, quality gate compliance actions
- Progressive rollout plan with batch sizes and monitoring checkpoints

## Agents Used

- **seo-specialist** — Programmatic page analysis, quality gate enforcement, URL strategy, template evaluation
- **content-creator** — Template content design, uniqueness optimization

## Scripts Used

- **tech-seo-auditor.py** — Check technical SEO issues across programmatic page samples
- **content-scorer.py** — Score content quality and uniqueness per template
- **competitor-scraper.py** — Analyze competitor programmatic page patterns
