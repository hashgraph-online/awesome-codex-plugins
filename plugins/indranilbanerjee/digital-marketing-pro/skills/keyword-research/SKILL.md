---
name: keyword-research
description: "Research keyword expansion, intent, and gaps. Use when: mapping search intent, finding content gaps, or long-tail discovery."
argument-hint: "[topic or seed keywords]"
---

# /digital-marketing-pro:keyword-research

## Purpose

Standalone keyword *research* tool — expansion, search-intent classification, and competitor gap analysis. Produces a prioritized, intent-classified keyword list with content recommendations. Volume and keyword-difficulty figures come from the brand's connected keyword MCP (Ahrefs / Semrush / SE Ranking / GSC) — this skill surfaces and interprets them, it does not fabricate them. **Clustering into a pillar+spokes plan is delegated to `/digital-marketing-pro:keyword-cluster`** (the `keyword_cluster.py` engine); this skill produces the seeds that skill consumes.

## Input Required

The user must provide (or will be prompted for):

- **Seed keywords or topic**: Starting keywords, a topic area, or a URL to extract keyword themes from
- **Target audience**: Who the content is intended to reach (demographics, expertise level, pain points)
- **Industry**: The vertical or niche to contextualize volume and difficulty estimates
- **Competitor domains**: Optional -- 1-3 competitor domains to run content gap analysis against
- **Target market/language**: Geographic and language targeting for volume estimates
- **Content goals**: Traffic, leads, thought leadership, product sales, or brand awareness
- **Existing content inventory**: Optional -- URLs or topics already published to avoid duplication

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply voice, compliance, industry context. Check `guidelines/_manifest.json` for restrictions, messaging, channel styles, voice-and-tone rules, and templates. If a template matching this command exists in `~/.claude-marketing/brands/{slug}/templates/`, apply its format. If no brand exists, prompt for `/digital-marketing-pro:brand-setup` or proceed with defaults.
2. **Check campaign history**: Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/campaign-tracker.py" --brand {slug} --action list-campaigns` to identify previous keyword research and content campaigns to build upon rather than duplicate.
3. **Load reference files**: Consult `skills/content-engine/` for content strategy context and `skills/context-engine/industry-profiles.md` for industry-specific keyword benchmarks and search behavior patterns.
4. **Expand the seed set**: Use the brand's connected keyword MCP (Ahrefs `getRelatedKeywords`, Semrush, SE Ranking, or GSC query mining) to expand seeds into a candidate list, pulling provider volume and keyword-difficulty figures where available. Record the provider and pull date — volume/KD are provider estimates, not measurements, and providers disagree by 20-50%. Do **not** claim volume/KD/trend numbers the connected tools didn't return.
5. **Classify search intent**: Categorize every keyword into intent buckets -- informational (how-to, what-is), navigational (brand, product names), commercial (best, reviews, comparison), and transactional (buy, pricing, demo, free trial).
6. **Map keywords to content types**: Assign each cluster a recommended content format -- blog post, landing page, pillar page, comparison page, FAQ, video, tool, or interactive content -- based on intent and SERP feature analysis.
7. **Identify content gaps vs competitors**: If competitor domains were provided, cross-reference their ranking keywords against the brand's current coverage to surface missed opportunities and underserved topics.
8. **Discover long-tail opportunities**: Expand each cluster with long-tail variants, question-based keywords (People Also Ask patterns), and related search modifiers that represent lower-difficulty entry points.
9. **Assess SERP feature opportunities**: For each primary keyword, identify which SERP features are present (featured snippets, People Also Ask, knowledge panels, image packs, video carousels) and note which are attainable.
10. **Identify seasonal and trending opportunities**: Flag keywords with notable seasonal patterns or rising search trends that present time-sensitive content opportunities requiring prioritized scheduling.
11. **Prioritize by impact and difficulty**: Score each keyword cluster on a composite priority metric weighing estimated volume, ranking difficulty, business relevance, conversion potential, and content gap opportunity.
12. **Generate keyword strategy document**: Compile the full analysis into a structured deliverable with clear next-step recommendations for content creation sequencing.

## Output

A structured keyword strategy document containing:

- Keyword clusters organized by topic theme, each with individual keywords listed
- Estimated monthly search volume and keyword difficulty per keyword
- Search intent classification (informational, navigational, commercial, transactional) per keyword
- SERP feature opportunities per cluster (featured snippets, PAA, video, image pack)
- Recommended content type and format for each cluster
- Priority score (high/medium/low) with rationale for sequencing
- Content gap analysis showing competitor-owned keywords the brand is missing
- Long-tail keyword opportunities with lower difficulty and high relevance
- Question-based keyword list for FAQ and People Also Ask targeting
- Recommended content creation roadmap based on priority ranking
- Quick-win keywords (low difficulty, decent volume, high relevance) flagged for immediate action
- Seasonal or trending keyword opportunities with timing recommendations
- Internal linking opportunities between keyword clusters and existing content

## Tips & caveats

- **Search volume from any provider is an estimate.** Ahrefs, Semrush, GSC, SE Ranking all disagree by 20-50% on the same keyword. Use ranges, not point estimates.
- **Keyword difficulty (KD) is a heuristic, not a measurement.** A KD of 60 means "competitive" — not "impossible". A small brand with niche authority can rank for KD-70 keywords against generalist KD-30 sites.
- **Long-tail isn't always lower-volume.** With AI search rewriting queries, the actual click-driving query may differ from the seed. Always check the *resulting* query a user typed via GSC, not the rank-tracker assumption.
- **Hand off to `/digital-marketing-pro:keyword-cluster`** once you have ≥ 20 raw keywords. Clustering before writing is what produces topical authority, not keyword lists.
- **Don't research the same keyword set quarterly.** Re-research only when business model, target market, or competitive landscape changes. Otherwise the deltas are noise.
- **Intent classification beats volume.** A "buy [product]" query at 200/mo is worth more than "what is [product]" at 5000/mo for most commercial brands.

## Agents Used

- **seo-specialist** -- Keyword research, volume and difficulty estimation, SERP analysis, content gap identification, and priority scoring
- **content-creator** -- Content type mapping, content angle recommendations, and editorial planning for keyword-targeted pieces
