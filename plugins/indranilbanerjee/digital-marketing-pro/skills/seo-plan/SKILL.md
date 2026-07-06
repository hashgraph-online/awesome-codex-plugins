---
name: seo-plan
description: "Build SEO strategy and roadmap. Use when: planning site architecture, content strategy, or phased implementation."
argument-hint: "[business-type]"
user-invocable: true
---

# /digital-marketing-pro:seo-plan

## Purpose

Generate a comprehensive SEO strategy with industry-specific templates, competitive analysis, content roadmap, and phased implementation plan. Covers both traditional SEO and AI search readiness.

## Dispatcher mode (Confirm-Then-Dispatch)

When invoked on a brand that already has recent specialist outputs in `${CLAUDE_PLUGIN_DATA}/{brand}/seo/`, this skill operates as an **orchestrator** — it reads those outputs as inputs, scores the brand across four pillars, and uses the **weakest pillar to drive the lead theme** of the plan.

### Step D0 — detect fresh outputs (≤ 30 days)

Look under `${CLAUDE_PLUGIN_DATA}/{brand}/seo/` for the latest dated subfolder of each:

| Specialist skill | Output folder |
|---|---|
| `/digital-marketing-pro:tech-seo-audit` | `seo/tech-seo-audit/{YYYY-MM-DD}/PLAN.md` |
| `/digital-marketing-pro:content-decay-scan` | `seo/content-decay-scan/{YYYY-MM-DD}/PLAN.md` |
| `/digital-marketing-pro:aeo-audit` | `seo/aeo-audit/{YYYY-MM-DD}/PLAN.md` |
| `/digital-marketing-pro:backlink-gap` | `seo/backlink-gap/{YYYY-MM-DD}/PLAN.md` |
| `/digital-marketing-pro:gsc-ai-performance` | `seo/gsc-ai-performance/{YYYY-MM-DD}/PLAN.md` |
| `/digital-marketing-pro:keyword-cluster` | `seo/keyword-cluster/{YYYY-MM-DD}/PLAN.md` |
| `/digital-marketing-pro:seo-drift` | `seo/seo-drift/{YYYY-MM-DD}/PLAN.md` |

Any folder dated within the last **30 days** counts as fresh — its `PLAN.md` becomes a primary input.

### Step D1 — confirm before dispatching missing specialists

If some specialists have no fresh output, **do not silently re-run them.** Print exactly:

```
The following specialist outputs are missing or stale (>30 days old):
  - tech-seo-audit (last: 2026-05-12 — 23 days old)
  - backlink-gap (no run found)
  - gsc-ai-performance (no run found)

Running these now will use approximately N MCP credits / API calls.

Run them now in this session? (y / N — default N)
```

- **If `y`** — dispatch in this order:
  - **Parallel batch 1**: `tech-seo-audit`, `backlink-gap`, `aeo-audit`, `gsc-ai-performance` (independent)
  - **Sequential after**: `content-decay-scan` (depends on `tech-seo-audit`'s URL inventory), `keyword-cluster` (depends on `aeo-audit` query set)
  - Each specialist runs its own budget guard; surface aborts back to the user
- **If `N` or default** — fall through; treat missing pieces as Phase 0 ("Discovery") work in the final plan

### Step D2 — pillar scoring (the heart of the dispatcher)

Score each of four pillars 1–10 based on the available specialist outputs:

| Pillar | Sources | What 10 looks like |
|---|---|---|
| **Technical** | tech-seo-audit / gsc-ai-performance / Core Web Vitals data | Clean crawlability, all CWV pass, schema validates, sitemap accurate |
| **Content** | content-decay-scan / seo-audit / content-engine outputs | Topic coverage matches search demand, no cannibalisation, freshness ≥ 80% |
| **Topical** | keyword-cluster / aeo-geo / entity-audit | Clear pillar+spokes structure, entity consistency across Knowledge Graph |
| **AI Search** | aeo-audit / gsc-ai-performance / aeo-geo | Cited in AI Mode + AI Overviews + ChatGPT + Perplexity for target queries |

**The lowest-scoring pillar becomes the LEAD THEME** of the next quarter's plan. Everything else is supporting work. This forces focus.

### Step D3 — dispatcher output

Produce `${CLAUDE_PLUGIN_DATA}/{brand}/seo/seo-plan/{YYYY-MM-DD}/00-pillar-scorecard.md`:

```
Pillar scorecard for {brand} ({date})
=====================================
Technical    : 8 / 10   ✓ healthy
Content      : 6 / 10   ⚠ moderate gaps
Topical      : 4 / 10   ⚠ LEAD THEME — weakest pillar
AI Search    : 7 / 10   ✓ trending up

Lead theme this quarter: Topical authority build-out
(keyword cluster expansion + entity consistency + Knowledge Graph optimisation)
```

The rest of the plan (sections 1-6 below) is then **framed around the lead theme** — supporting work for the other 3 pillars stays in the plan but doesn't drive timeline / budget.

## Numbered output convention

The full dispatcher run produces, under `${CLAUDE_PLUGIN_DATA}/{brand}/seo/seo-plan/{YYYY-MM-DD}/`:

```
00-pillar-scorecard.md      (from Step D2)
01-discovery.md             (business type, audience, competitors — from §1 below)
02-competitive-analysis.md  (competitors + gap synthesis — from §2 + backlink-gap if fresh)
03-architecture.md          (URL hierarchy, internal-link strategy — from §3 + keyword-cluster if fresh)
04-content-strategy.md      (content gaps, calendar, E-E-A-T — from §4 + content-decay-scan if fresh)
05-technical-foundation.md  (hosting, schema, CWV — from §5 + tech-seo-audit if fresh)
06-roadmap.md               (phased 12-month — from §6, framed around lead theme)
07-industry-template.md     (which template applied — from §Industry Templates)
08-kpi-dashboard.md         (metrics + cadence — what gets re-measured next drift)
PLAN.md                     (the deliverable)
```

## Input Required

- **Business type**: SaaS, ecommerce, local service, publisher/media, agency, or general
- **Website URL**: Existing site (if any) to assess
- **Target audience and markets**: Geographic, demographic, and intent profiles
- **Competitors**: 3-5 competitor URLs for gap analysis
- **Budget and timeline**: Resource constraints
- **KPIs**: What success looks like (traffic, rankings, conversions, AI visibility)

## Process

### 1. Discovery
- Business type, target audience, competitors, goals
- Current site assessment (if exists) — crawl health, content inventory, authority signals
- Budget and timeline constraints
- Key performance indicators (KPIs) aligned to business objectives

### 2. Competitive Analysis
- Identify top 5 competitors
- Analyze their content strategy, schema usage, technical setup
- Identify keyword gaps and content opportunities
- Assess their E-E-A-T signals
- Estimate domain authority and link profiles
- AI visibility comparison — which competitors appear in AI overviews

### 3. Architecture Design
- Design URL hierarchy and content pillars based on business model
- Plan internal linking strategy (hub/spoke, topic clusters)
- Sitemap structure with quality gates applied
- Information architecture for user journeys
- Navigation and breadcrumb planning

### 4. Content Strategy
- Content gaps vs competitors
- Page types and estimated counts
- Blog/resource topics and publishing cadence
- E-E-A-T building plan (author bios, credentials, experience signals)
- Content calendar with priorities
- AI-optimized content structure (entity consistency, citation-worthy formatting)

### 5. Technical Foundation
- Hosting and performance requirements
- Schema markup plan per page type
- Core Web Vitals baseline targets (LCP <2.5s, INP <200ms, CLS <0.1)
- AI search readiness requirements
- Mobile-first considerations
- International SEO setup (if applicable)

### 6. Implementation Roadmap (4 phases)

**Phase 1: Foundation (weeks 1-4)**
- Technical setup and infrastructure
- Core pages (home, about, contact, main services/products)
- Essential schema implementation (Organization, LocalBusiness, BreadcrumbList)
- Analytics and tracking setup (GA4, GSC, rank tracking)

**Phase 2: Expansion (weeks 5-12)**
- Content creation for primary pages
- Blog launch with initial posts
- Internal linking structure buildout
- Local SEO setup (if applicable)
- First E-E-A-T improvements (author pages, credentials)

**Phase 3: Scale (weeks 13-24)**
- Advanced content development (pillar pages, topic clusters)
- Link building and digital PR outreach
- GEO/AEO optimization for AI search visibility
- Performance optimization (CWV, page speed)
- Schema expansion (FAQ, Product, VideoObject as applicable)

**Phase 4: Authority (months 7-12)**
- Thought leadership content
- PR and media mentions
- Advanced schema implementation
- Continuous optimization based on data
- Competitive gap monitoring

## Industry Templates

### SaaS
- Primary pages: features, pricing, integrations, use cases, solutions by role
- Content pillars: product education, industry trends, comparison content, technical guides
- Schema focus: SoftwareApplication, Product, FAQPage (if eligible), HowTo (deprecated — use article format instead)
- Link strategy: integration partner pages, guest posts on tech blogs, product directories

### Local Service
- Primary pages: services, service areas, about, contact, testimonials
- Content pillars: service guides, local area content, FAQ content, case studies
- Schema focus: LocalBusiness, Service, Review, BreadcrumbList, GeoCircle
- Link strategy: local directories, chamber of commerce, local press, community involvement

### eCommerce
- Primary pages: categories, products, brands, collections, buying guides
- Content pillars: product education, comparison content, buying guides, trend content
- Schema focus: Product, ProductGroup, Offer, AggregateRating, BreadcrumbList, ItemList
- Link strategy: product reviews, affiliate partnerships, manufacturer relationships

### Publisher/Media
- Primary pages: sections, topic pages, author pages, about, editorial standards
- Content pillars: news coverage, analysis, opinion, investigative, data journalism
- Schema focus: Article, NewsArticle, Person (authors), Organization, VideoObject
- Link strategy: original research citations, expert sourcing, data exclusives

### Agency
- Primary pages: services, industries, case studies, team, methodology
- Content pillars: industry expertise, methodology content, case studies, thought leadership
- Schema focus: Organization, Service, Person (team), Article
- Link strategy: case study features, speaking engagements, industry publications, client co-marketing

## Output

### Deliverables
- **SEO Strategy Document**: Complete strategic plan with business context, competitive landscape, and strategic direction
- **Competitive Analysis**: Keyword gaps, content gaps, authority comparison, AI visibility comparison
- **Content Calendar**: 12-week content roadmap with topics, formats, keywords, and publishing schedule
- **Implementation Roadmap**: Phased action plan with milestones, responsibilities, and measurement checkpoints
- **Site Architecture Plan**: URL hierarchy, content pillar structure, internal linking strategy
- **Schema Markup Plan**: Per-page-type schema recommendations with JSON-LD templates
- **KPI Dashboard Specification**: Metrics to track, tools needed, reporting cadence

## Agents Used

- **seo-specialist** — Strategy, competitive analysis, technical planning
- **content-creator** — Content strategy and calendar planning
- **competitive-intel** — Competitor analysis and gap identification
- **marketing-strategist** — Business alignment and KPI framework

## Scripts Used

- **competitor-scraper.py** — Competitor site analysis
- **tech-seo-auditor.py** — Current site technical assessment
- **keyword_cluster.py** — Keyword clustering with SERP-overlap + quality scorecard (use via `/digital-marketing-pro:keyword-cluster`)
- **content-scorer.py** — Current content quality baseline

## Quality scorecard

Every `PLAN.md` this skill produces must pass these gates before being declared ready:

| Gate | What it checks |
|---|---|
| **lead_theme_named** | `00-pillar-scorecard.md` exists and names exactly one weakest pillar as lead theme |
| **specialist_coverage** | At least 3 of the 7 specialist sources have fresh outputs (≤30 days) |
| **roadmap_phased** | Roadmap has explicit Phase 1/2/3/4 dates with owners |
| **kpi_attached** | `08-kpi-dashboard.md` lists ≥3 lagging + ≥3 leading metrics |
| **drift_re-measure_scheduled** | The KPI dashboard includes a recurring `seo-drift` cadence (default: quarterly) |

If any gate fails, the script that orchestrates the dispatcher must surface the failure in `PLAN.md` rather than silently shipping.

## Chain handoffs

This skill is both a consumer (of specialists) and a producer (of the master plan):

**Upstream (specialists this skill reads from):**
- `/digital-marketing-pro:tech-seo-audit`
- `/digital-marketing-pro:content-decay-scan`
- `/digital-marketing-pro:aeo-audit`
- `/digital-marketing-pro:backlink-gap`
- `/digital-marketing-pro:gsc-ai-performance`
- `/digital-marketing-pro:keyword-cluster`
- `/digital-marketing-pro:seo-drift`

**Downstream (skills that consume this plan):**
- `/digital-marketing-pro:content-engine` — drafts the content scheduled in `04-content-strategy.md`
- `/digital-marketing-pro:campaign-plan` — turns the roadmap into a sprint plan with owners
- `/digital-marketing-pro:performance-report` — re-measures against `08-kpi-dashboard.md` cadence

## Tips & caveats

- **The dispatcher's default is not to dispatch.** If specialists are missing, the default answer is `N` — list them as Phase 0 work. Only auto-dispatch on explicit `y`. This prevents accidental credit / API spend.
- **Pillar scoring is opinionated, not measured.** A `4/10` Topical pillar means "we don't have a clear authority structure", not "Google said so". The numbers are heuristic. Use them to focus the lead theme, not as KPIs.
- **The lead theme should change quarterly.** If the same pillar wins lead theme two quarters in a row, either the work isn't moving the needle (escalate) or the scoring is wrong (recalibrate with current data).
- **Don't run this on Day 1 of an engagement.** Run the specialists first so the dispatcher has fresh inputs. The first `seo-plan` run on a new brand will mostly be Phase 0 (Discovery) work.
- **For YMYL clients,** add E-E-A-T as a 5th pillar manually (the standard 4-pillar scoring doesn't separately weight authority signals).
- **The 30-day freshness window is a default,** not a rule. For high-velocity industries (news, SaaS launches), shorten to 14 days. For slow-moving categories (manufacturing, B2B services), 60 days is fine.

## Context efficiency

This skill's reference docs (`skills/<this-skill>/*.md`) sum to ~30-50KB. Don't load them eagerly — pick targeted sections:

- **Grep before Read.** Find the keyword or section heading first, then Read with `offset` + `limit` to pull just that range.
- **Walk `${CLAUDE_SKILL_DIR}` once.** Use a single directory listing to see what's there, then Read only the files that match your current step.
- **One source at a time.** If the workflow says "consult three reference files," read them sequentially after deciding what you need from each. Bulk-loading all three blows the per-skill 5K-token budget that auto-compaction reserves.
- **Strip noise from CSV inputs.** If the input is a large CSV, grep the header line first to pick columns, then process row-by-row — do not Read the whole file into context.
