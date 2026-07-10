---
name: narrative-tracker
description: "Track AI engine brand narratives. Use when: detecting narrative drift, misrepresentation, or competitor narrative gains over time."
---

# /digital-marketing-pro:narrative-tracker

## Purpose

Track and analyze the narrative that AI engines construct about the brand. Monitor what ChatGPT, Perplexity, Gemini, and others say when asked about the brand, compare to desired positioning, detect drift or misrepresentation, and identify when competitors are gaining narrative territory in AI responses. Unlike visibility monitoring (which measures whether the brand appears), narrative tracking measures what is said — the qualitative story AI engines tell about the brand, whether it aligns with intended positioning, and how it changes over time. This gives marketers the insight to proactively shape AI perception through targeted content strategy rather than reacting after damage is done.

## Input Required

The user must provide (or will be prompted for):

- **Desired brand positioning statement(s)**: The core positioning the brand wants AI engines to reflect — value proposition, market position, key differentiators, and target audience. If not provided explicitly, these are extracted from the brand profile's positioning and messaging sections
- **Key brand attributes to verify in AI responses**: Specific attributes, claims, or themes that should appear when AI engines describe the brand — e.g., "enterprise-grade security", "founded in 2015", "serving 10,000+ customers", "leader in [category]". These become the checklist for narrative alignment scoring
- **Competitor brands to track narrative for**: One or more competitors whose AI narratives should be monitored alongside the brand — enables detection of narrative territory shifts where a competitor begins owning themes previously associated with the user's brand
- **AI platforms to monitor**: ChatGPT, Perplexity, Gemini, AI Overviews, Copilot — default is all. The user can narrow to platforms most relevant to their audience or where they have observed issues
- **Query types**: Brand queries ("Tell me about [brand]"), comparison queries ("[brand] vs [competitor]"), category queries ("best [category] solutions"), and problem-solution queries ("how to solve [problem brand addresses]"). A balanced mix is recommended for comprehensive narrative coverage

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Extract brand positioning, key messages, differentiators, value propositions, target audience, and competitive claims — these form the reference narrative against which AI responses are evaluated. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load messaging dos/don'ts and positioning guardrails. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with user-provided positioning statements.
2. **Query AI platforms and record narratives**: For each query on each platform, capture the full AI-generated response and extract the narrative — what does the AI say about the brand, how does it position it relative to alternatives, what attributes does it highlight, what does it omit, and what does it get wrong. Record the complete response text, not just scores, because narrative analysis requires the actual language and framing used by the AI engine.
3. **Score narrative alignment**: Compare each AI response against the desired positioning on key dimensions. For each key brand attribute, mark as present (AI includes it accurately), absent (AI omits it), distorted (AI includes it but frames it incorrectly or negatively), or outdated (AI references an old version of this attribute). Flag misrepresentations where the AI states something factually incorrect about the brand. Flag narrative drift where the AI's positioning of the brand has shifted from the previous check — even if not incorrect, the framing or emphasis has changed. Calculate a narrative alignment score per platform and per query type.
4. **Track competitor narratives**: Run the same query types for each competitor brand. Record what AI engines say about competitors — their positioning, highlighted attributes, and claimed differentiators. Identify narrative territory shifts — themes or attributes that were previously associated with the user's brand but now appear in competitor descriptions, or neutral territory that a competitor has begun to claim. Map which brand "owns" which narrative themes in AI responses.
5. **Record all narratives**: Store full narrative data via `python "${CLAUDE_PLUGIN_ROOT}/scripts/geo-tracker.py" --brand {slug} --action track-narrative --platform {platform} --context "{what the AI said}"` (add `--query`/`--url` where available). The payload captures timestamp, platform, query, response text, alignment score, attribute presence/absence/distortion flags, misrepresentation flags, and competitor narrative data.
6. **Compare to previous snapshots**: If previous narrative data exists, diff current narratives against the most recent previous check. Detect new themes the AI has started associating with the brand, lost themes that no longer appear, shifted framing where the same attribute is described differently, resolved issues where previously flagged misrepresentations have been corrected, and new issues that have appeared since the last check.
7. **Generate narrative correction strategy**: Based on all findings, produce a targeted content strategy to influence AI perception — content to create that establishes missing attributes in citable sources, content to update that corrects outdated information AI engines are citing, structured data and entity updates that reinforce correct positioning, citation opportunities on high-authority platforms that AI engines trust, and defensive content for queries where competitors are gaining narrative territory.

## Output

A comprehensive narrative tracking report containing:

- **Narrative alignment report**: Per-platform and per-query-type alignment scores showing how well AI responses match desired brand positioning, with overall narrative health score and trend vs previous check
- **Misrepresentation flags**: Specific factual inaccuracies found in AI responses — what the AI said, what is actually true, which platform, which query triggered it, and severity (minor inaccuracy, significant error, or damaging misrepresentation)
- **Narrative drift indicators**: Changes in how AI engines frame the brand compared to previous checks — shifted emphasis, new associations, lost associations, and tone changes — even when not factually incorrect, drift signals that AI perception is evolving away from desired positioning
- **Competitor narrative comparison**: Side-by-side analysis of how AI engines describe the brand vs each competitor — attribute ownership, positioning differences, and relative narrative strength per platform
- **Narrative territory map**: Visual mapping of which brand "owns" which themes and attributes in AI responses — showing shared territory, contested territory, and unoccupied territory that represents opportunity
- **Content recommendations**: Specific content to create or update to correct narrative issues, strengthen weak attributes, defend contested territory, and claim unoccupied narrative space — with target platform, format, and expected narrative impact
- **Trend over time**: Narrative alignment score history across monitoring periods, with key events annotated (content published, entity updated, competitor launched campaign) to correlate actions with narrative shifts
- **Execution log entry**: Timestamped record with platform count, query count, overall alignment score, misrepresentation count, drift flags, and key narrative changes for audit trail

## Agents Used

- **seo-specialist** — Narrative analysis across AI engine responses, positioning alignment assessment against brand profile, attribute presence and distortion detection, citation strategy for influencing AI perception, content optimization recommendations for narrative correction, structured data and entity update guidance to reinforce accurate brand positioning in knowledge sources
- **competitor-intelligence** — Competitive narrative tracking across AI platforms, narrative territory mapping between the brand and competitors, territory shift detection where competitors gain or lose narrative themes, competitive positioning comparison with attribute-level analysis, and strategic recommendations for defending and expanding narrative territory in AI responses
