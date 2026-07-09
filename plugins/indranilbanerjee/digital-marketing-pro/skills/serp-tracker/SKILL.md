---
name: serp-tracker
description: "Track SERP feature changes. Use when: monitoring AI Overviews, featured snippets, PAA, knowledge panels, local packs."
---

# /digital-marketing-pro:serp-tracker

## Purpose

Track SERP feature presence and changes for target queries. Monitor which SERP features appear for each keyword — AI Overviews, People Also Ask, Featured Snippets, Knowledge Panels, Local Pack, Image Pack, Video Carousel, Shopping — whether the brand owns any of these features, and how features change over time. This command provides strategic visibility into the evolving search landscape beyond traditional blue-link rankings, helping brands identify feature opportunities, defend owned features, and adapt content strategy to Google's increasingly feature-rich results pages.

## Input Required

The user must provide (or will be prompted for):

- **Target queries**: A list of search queries to track SERP features for — can be provided directly, imported from a CSV or Google Sheet, or pulled from the brand's existing keyword list at `~/.claude-marketing/brands/{slug}/seo/keywords.json`. Queries should represent a mix of head terms, long-tail terms, and question-based queries for comprehensive feature coverage
- **SERP features to track**: Which features to monitor — default is `all`. Can be narrowed to specific features: `ai-overview`, `featured-snippet`, `people-also-ask`, `knowledge-panel`, `local-pack`, `image-pack`, `video-carousel`, `shopping`, `sitelinks`, `top-stories`, `twitter-carousel`, `recipes`, `jobs`. Narrowing reduces noise when only specific features matter for the brand's strategy
- **Monitoring frequency**: `daily` or `weekly` — daily for competitive or volatile queries where features change frequently, weekly for stable long-tail queries. Determines snapshot frequency and trend granularity
- **Competitive domains (optional)**: Domains to track for feature ownership — see which competitors own featured snippets, appear in AI Overviews, or dominate image and video carousels. Up to 10 competitor domains for head-to-head SERP feature comparison

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Query current SERP feature landscape**: For each target query, retrieve the current SERP layout via Moz and Google Search Console MCPs. Record every SERP feature present on the results page — feature type, position on page (above or below organic results), the domain that owns the feature (if applicable), and the content displayed within the feature (snippet text, PAA questions, AI Overview summary, local businesses listed, images shown).
3. **Record feature presence per query**: Build a feature presence matrix — rows are target queries, columns are SERP feature types. Each cell contains: feature present (yes/no), owning domain (brand, specific competitor, or other), position on SERP, and content summary. Store this snapshot at `~/.claude-marketing/brands/{slug}/seo/serp-features-{date}.json` and update the cumulative tracker at `~/.claude-marketing/brands/{slug}/seo/serp-feature-history.json`.
4. **Compare to previous snapshot**: Detect changes since the last recorded snapshot — new features appearing for a query (e.g., AI Overview added where there was none before), features disappearing (e.g., featured snippet removed), ownership changes (e.g., competitor took over a featured snippet the brand previously held), content changes within features (e.g., AI Overview now cites a different source), and position changes (e.g., PAA moved above organic results).
5. **Analyze AI Overview presence specifically**: For each target query, assess AI Overview status — is an AI Overview present, is the brand cited as a source, which competitors are cited, what content is being surfaced in the overview, and how has this changed since the last check. AI Overviews represent a significant shift in search visibility, so this analysis is tracked separately with higher priority alerting.
6. **Generate feature opportunity analysis**: Based on current rankings, content quality, and SERP feature patterns, identify which unowned features the brand could realistically target. Rank opportunities by achievability (how close is the brand to winning the feature based on current position and content format) multiplied by traffic impact (estimated click-through impact of owning the feature based on query volume and feature prominence). Include specific content recommendations for each opportunity — FAQ schema for PAA, structured content for featured snippets, video content for video carousels, local optimization for local pack.

## Output

A structured SERP feature report containing:

- **SERP feature matrix**: Query-by-feature grid showing which features appear for each target query, who owns them (brand, competitor name, or other), and position on the results page — providing a complete landscape view of feature presence across the tracked query set
- **Change report**: New features appeared, features disappeared, and ownership changes since the last snapshot — sorted by impact, with the most significant changes (lost features, competitor gains, new AI Overviews) highlighted first
- **AI Overview tracker**: Dedicated section for AI Overview analysis — citation status across all tracked queries, which sources Google is citing, whether the brand is included or excluded, changes since last check, and content optimization recommendations for AI Overview inclusion
- **Feature opportunity list**: Ranked list of unowned SERP features the brand could target — scored by achievability multiplied by traffic impact, with specific content and technical recommendations for each opportunity (schema markup needed, content format changes, structured data additions)
- **Competitive SERP feature comparison**: Side-by-side feature ownership across tracked competitor domains — who dominates featured snippets, who appears most in AI Overviews, who owns the most PAA inclusions, and competitive trend direction over time

## Agents Used

- **seo-specialist** — SERP feature analysis and classification, feature ownership attribution to brand and competitor domains, AI Overview citation analysis and optimization strategy, feature opportunity scoring based on current rankings and content format alignment, and content recommendations for targeting specific SERP features (FAQ schema, structured snippets, video optimization, local SEO signals)
- **performance-monitor-agent** — SERP feature change detection with snapshot comparison, trend tracking across monitoring periods with directional analysis, alert generation for significant feature changes (lost ownership, new AI Overviews, competitor gains), and historical feature presence tracking with cumulative data management
