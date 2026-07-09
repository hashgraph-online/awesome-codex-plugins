---
name: learn
description: "Save a marketing learning or insight. Use when: capturing knowledge, recording campaign results, building compound intelligence."
---

# /digital-marketing-pro:learn

## Purpose

Save a structured marketing learning to the brand's intelligence graph. Captures what was learned, under what conditions it applies, confidence level, and source agent. Builds compound intelligence that makes every future campaign smarter — turning one-off observations into a persistent knowledge base that compounds across campaigns, channels, and team members over time.

## Input Required

The user must provide (or will be prompted for):

- **Insight or learning**: What was observed or discovered — a concrete marketing observation such as "Subject lines with numbers get 23% higher open rates for our developer audience", a pattern like "Retargeting ads convert best within 48 hours of site visit", or a strategic finding like "Bottom-of-funnel content outperforms top-of-funnel for enterprise accounts in Q4"
- **Context conditions**: The specific circumstances under which this learning applies — channel (email, social, paid search, SEO, etc.), audience segment (developers, marketers, executives, SMB owners, etc.), objective (awareness, conversion, retention, upsell, etc.), campaign type (product launch, seasonal, evergreen, nurture, etc.), and any other qualifying conditions that scope when this insight is relevant
- **Confidence level**: A score from 0 to 1 representing how validated this learning is — 0.3 for early hypothesis based on limited data, 0.5 for new observation with moderate supporting evidence (system default for new learnings), 0.7 for pattern confirmed across multiple campaigns, 0.9+ for statistically validated insight with strong sample size. If not provided, defaults to 0.5
- **Source**: Which agent, analysis, or workflow produced this learning — e.g., "analytics-analyst via Q4 email performance review", "media-buyer from A/B test results", "user observation", or "content-creator from engagement analysis"
- **Supporting evidence (optional)**: Data points, test results, metric snapshots, or campaign references that back the learning — specific numbers, date ranges, sample sizes, or links to reports that substantiate the insight

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, industry context, and known audience segments to validate the learning fits the brand's domain. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Structure the learning**: Assemble the learning record with all required metadata — insight text, context conditions (channel, audience, objective, campaign type), confidence score, source agent or workflow, timestamp, and supporting evidence if provided. Normalize the context conditions to match the brand's established taxonomy for consistent querying later.
3. **Check for related learnings**: Query the intelligence graph via `intelligence-graph.py query-relevant` using the learning's context conditions. Search for existing learnings that overlap in channel, audience, and objective to detect duplicates, supporting evidence, or contradictions.
4. **Handle related learnings**: If a related learning exists and the new insight supports it, increase the existing learning's confidence by +0.1 (capped at 1.0) and append the new evidence. If the new insight contradicts an existing learning, present both to the user with their respective confidence scores and evidence, and ask which to keep, whether to create a conditional split (e.g., "true for SMB but not enterprise"), or whether to flag for further testing.
5. **Save the learning**: If the learning is new or the user confirmed the update, save via `intelligence-graph.py save-learning` with the full structured record. The learning is indexed by all context conditions for multi-dimensional retrieval.
6. **Distribute to relevant agents**: Based on the learning's context conditions, notify relevant specialist agents — email insights route to email-specialist, paid media insights to media-buyer, content insights to content-creator, and cross-channel insights to marketing-strategist. Each agent incorporates the learning into its future recommendations.

## Output

- **Learning saved confirmation**: Learning ID, formatted insight text, and all structured metadata (conditions, confidence, source, timestamp) confirming successful storage in the intelligence graph
- **Initial confidence score**: The assigned confidence level with explanation — whether it was user-specified, system-defaulted, or adjusted from an existing learning's score
- **Related existing learnings**: Any learnings found in the intelligence graph that overlap, support, or contradict the new insight — listed with their confidence scores and how they relate
- **Intelligence base stats update**: Current totals for the brand's intelligence graph — total learnings stored, average confidence across all learnings, learnings added this week, and top contributing agents

## Agents Used

- **intelligence-curator** — Learning structuring with metadata normalization against the brand's taxonomy, deduplication via context-condition matching against the existing intelligence graph, confidence score management with support and contradiction handling, cross-referencing related learnings to surface connections the user may not have noticed, and distribution routing to relevant specialist agents based on channel, audience, and objective tagging
