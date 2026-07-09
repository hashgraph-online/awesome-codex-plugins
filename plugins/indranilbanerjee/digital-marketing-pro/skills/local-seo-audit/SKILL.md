---
name: local-seo-audit
description: "Audit local SEO health. Use when: reviewing GBP optimization, NAP consistency, local citations, or local pack rankings."
---

# /digital-marketing-pro:local-seo-audit

## Purpose

Run a comprehensive local SEO audit that evaluates all factors affecting local search visibility: Google Business Profile completeness, NAP consistency, citation presence, local content, reviews, and local schema. Produces a prioritized action plan to improve local pack rankings and drive foot traffic or service inquiries.

## Input Required

The user must provide (or will be prompted for):

- **Business name and address** (required): Full NAP (Name, Address, Phone)
- **Google Business Profile URL** (helpful): Direct link to GBP listing
- **Number of locations** (required): Single location, or count of locations
- **Service area** (helpful): Geographic area served
- **Industry** (helpful): For industry-specific citation sources and benchmarks
- **Current review count and rating** (optional): Baseline metrics
- **Competitors** (optional): Local competitors to benchmark against
- **Website URL** (required): For location page and schema audit

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Load reference files**: Read `skills/local-seo/gbp-optimization.md`, `skills/local-seo/citation-management.md`, `skills/local-seo/local-content.md`, and `skills/local-seo/multi-location.md` for local SEO frameworks
3. **Run local-seo-checker script** (if Python available): `python "scripts/local-seo-checker.py" --nap '{"name":"...","address":"...","phone":"..."}' --industry {industry}` for NAP consistency and GBP completeness scoring
4. **GBP profile audit**: Evaluate completeness, category selection, attributes, photos, posts, Q&A, services/products, business description, hours accuracy
5. **NAP consistency check**: Assess name, address, and phone consistency across known citation sources for the industry
6. **Citation audit**: Evaluate citation presence on top general and industry-specific directories. Identify missing, inconsistent, or duplicate listings
7. **Local keyword analysis**: Identify geo-modified keyword opportunities, "near me" optimization potential, service+location terms
8. **Location page review**: Assess on-site location pages for unique content, schema markup, internal linking, and conversion elements
9. **Review profile analysis**: Review volume, average rating, response rate, response quality, sentiment trends, competitor comparison
10. **Local schema audit**: Check LocalBusiness schema, GeoCoordinates, OpeningHours, AggregateRating, Review schema implementation
11. **Local link profile**: Evaluate local link opportunities (chambers, sponsorships, community orgs, local media)
12. **Competitor local benchmarking**: Compare GBP completeness, review volume, citation count, and local content against 2-3 local competitors
13. Compile prioritized report: Group by impact, include specific actions, benchmarks, and expected local ranking improvement

## Output

A structured local SEO audit report containing:

- **Audit header**: Brand name, location(s), date, overall local visibility score (0-100)
- **GBP scorecard**: Completeness score with specific optimization actions per section
- **NAP consistency report**: Status across top citation sources, inconsistencies flagged
- **Citation report**: Present, missing, incorrect, duplicate citations with action items
- **Review analysis**: Volume, rating, response rate, sentiment, with targets
- **Location page assessment**: Content quality, schema, optimization recommendations
- **Local keyword opportunities**: Geo-modified terms with estimated volume and competition
- **Competitor benchmarks**: Side-by-side comparison on key local signals
- **Quick wins**: Top 5 highest-impact, fastest actions
- **90-day local SEO action plan**: Week-by-week implementation roadmap

## Agents Used

- **seo-specialist** — Runs the local SEO audit, evaluates GBP optimization opportunities, reviews local schema, benchmarks against competitors, generates prioritized action plan
