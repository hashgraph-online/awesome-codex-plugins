---
name: geo-monitor
description: "Monitor brand AI visibility. Use when: tracking mentions in ChatGPT, Perplexity, Gemini, or AI Overviews."
---

# /digital-marketing-pro:geo-monitor

## Purpose

Monitor and track brand visibility across generative AI engines. Systematically test how AI platforms respond to queries relevant to the brand, score visibility using a structured rubric, track changes over time, and identify opportunities to improve AI presence. This command provides a repeatable, quantitative framework for understanding where and how the brand appears (or fails to appear) in AI-generated responses — giving marketers the data they need to optimize for the emerging generative engine optimization (GEO) channel. Supports baselining, trend tracking, competitive benchmarking, and narrative alignment checks across all major AI platforms.

**This skill is the RECURRING mode of the canonical AI-visibility scoring standard defined in `/digital-marketing-pro:aeo-audit`.** It does not introduce a second scoring model: it applies the same per-platform 1-10 rubric + gates on a schedule and tracks it over time. The 0-100 GEO health score + A-F letter grade produced below is the **trend view** of that same data — a longitudinal roll-up for spotting momentum, not a competing scorecard. The 6 canonical surfaces (Google AI Mode, Google AI Overviews, ChatGPT, Perplexity, Gemini, Copilot) are defined once as the `PLATFORMS` constant in `scripts/geo-tracker.py`.

## Input Required

The user must provide (or will be prompted for):

- **Target queries to test**: Organized by intent type — brand queries ("What is [brand]?"), product queries ("[brand] [product] features"), comparison queries ("[brand] vs [competitor]"), and category queries ("best [category] tools"). Minimum 5 queries recommended for meaningful scoring. If not provided, the command will generate a default query portfolio based on the brand profile
- **AI platforms to monitor**: ChatGPT, Perplexity, Gemini, **Google AI Mode**, AI Overviews, and Copilot — default is all six (AI Mode added May 2026 — it is a distinct surface from AI Overviews and frequently selects different citations for the same query). The user can narrow to specific platforms if they only care about certain engines or have limited testing capacity
- **Monitoring frequency**: `weekly` or `monthly` — determines how often the brand should be re-tested and how trend data is bucketed. Weekly is recommended for active optimization campaigns, monthly for steady-state monitoring
- **Competitor brands to benchmark against (optional)**: One or more competitor brand names to test with the same query portfolio — enables side-by-side visibility scoring to understand relative AI presence. If omitted, the report focuses solely on the user's brand without competitive context

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Extract brand name, product names, category, key differentiators, and desired positioning to inform query portfolio and narrative alignment scoring. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load brand voice and messaging constraints. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Define query portfolio**: Organize target queries by intent type — informational (what is, how does), navigational (brand-specific), transactional (buy, pricing, sign up), and comparison (vs, alternatives, best). If the user provided queries, classify them into these buckets. If not, generate a balanced portfolio of 10-20 queries from the brand profile covering all four intent types. Each query is tagged with its type for segmented scoring.
3. **Test each query on each platform**: For every query-platform combination, record the AI response and score brand visibility using the rubric — cited with link (10 points: brand is mentioned by name and a direct link to the brand's website or content is provided), mentioned by name (7 points: brand is explicitly named in the response but no link), concept referenced without attribution (3 points: brand's product, feature, or approach is described but the brand itself is not named), absent (0 points: brand does not appear in any form), misrepresented (-5 points: brand is mentioned but with incorrect, outdated, or damaging information). Record the full response text for narrative analysis.
4. **Record results**: Store each query-platform-result via geo-tracker (`--result` takes the rubric value: `cited` = cited with link, `mentioned` = named without link, `concept-only` = concept referenced without attribution, `absent`, `misrepresented`):
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/geo-tracker.py" \
       --brand {slug} --action audit-visibility \
       --query "best project management tool for agencies" \
       --platform ai-mode \
       --result cited \
       --context "AI Mode named the brand and linked its comparison page" \
       --url "https://brand.example/compare"
   ```
   Valid `--platform` values are the 6 canonical surfaces: `ai-mode`, `ai-overviews`, `chatgpt`, `perplexity`, `gemini`, `copilot`.
5. **Compare to baseline**: If previous monitoring data exists, diff current scores against the most recent previous check and the original baseline:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/geo-tracker.py" --brand {slug} --action diff
   ```
   Identify per-query and per-platform improvements (score increases), declines (score decreases), new appearances (went from absent to visible), lost appearances (went from visible to absent), and new opportunities (queries where competitors appear but the brand does not).
6. **Calculate visibility scores**: Compute per-platform visibility scores (average of all query scores on that platform, scaled 0-100), per-intent-type scores (how visible is the brand for informational vs transactional queries), and an overall GEO health score (weighted average across all platforms and query types). If competitors were provided, calculate the same scores for each competitor to enable ranking.
7. **Assess narrative alignment**: For queries where the brand appears, compare what the AI says against the desired brand positioning from the brand profile. Flag narrative drift (AI describes the brand differently than intended positioning), outdated information (AI cites old features, pricing, or leadership), missing key attributes (AI omits core differentiators), and misrepresentation (AI states something factually incorrect about the brand).
8. **Generate recommendations**: Based on weak spots, produce a prioritized list of actions to improve AI visibility — content to create or update for better citation, structured data to add, entity consistency to fix (cross-reference with `/digital-marketing-pro:entity-audit`), narrative corrections needed, and platforms where investment in visibility would have the highest impact.

## Output

A comprehensive AI visibility monitoring report containing:

- **AI visibility scorecard**: Per-platform scores (ChatGPT, Perplexity, Gemini, **Google AI Mode**, AI Overviews, Copilot — the 6 canonical surfaces) on the shared 1-10 rubric, plus the overall GEO health score scaled 0-100 with letter grade (A-F) as the **trend view** and a trend indicator vs previous check. The per-platform 1-10 scores are the authoritative assessment; the 0-100 grade exists only to make longitudinal movement legible.
- **Query-level results matrix**: Every query-platform combination with score, response excerpt, and flags — sortable by platform, intent type, or score
- **Trend report**: Score changes vs baseline and vs previous check — per-platform and overall, with sparkline indicators for directional trends and specific queries that improved or declined
- **Narrative alignment assessment**: Per-platform summary of how well AI responses match desired brand positioning, with specific drift flags, outdated information callouts, and missing attribute gaps
- **Competitive benchmark**: If competitors were provided — side-by-side visibility scores, queries where competitors outperform the brand, and narrative territory each brand occupies in AI responses
- **Top opportunities for improvement**: Queries and platforms where the brand is absent or underrepresented but competitors are visible, or where high-intent queries return no brand presence
- **Recommended actions ranked by impact**: Prioritized list of specific actions — content creation, structured data updates, entity fixes, citation building — with estimated impact on visibility scores and effort level
- **Execution log entry**: Timestamped record with query count, platform count, overall score, trend direction, and key flags for audit trail

## Agents Used

- **seo-specialist** — AI visibility analysis across generative engines, query portfolio design by intent type, visibility scoring with the citation-mention-absent-misrepresentation rubric, narrative alignment assessment against brand positioning, citation building recommendations, structured data optimization for AI discoverability, and prioritized action plans for improving GEO health scores
- **performance-monitor-agent** — Trend tracking across monitoring periods with baseline comparison, per-platform and per-query score change detection, threshold alerting for significant visibility drops or gains, competitive score tracking over time, and GEO health score history maintenance for long-term trend analysis
