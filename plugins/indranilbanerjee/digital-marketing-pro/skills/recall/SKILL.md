---
name: recall
description: "Recall marketing learnings. Use when: querying what we know about a channel, audience, objective, or past campaign."
---

# /digital-marketing-pro:recall

## Purpose

Retrieve relevant learnings from the brand's compound intelligence graph. Given a context — channel, audience, objective, or situation — return the most relevant validated insights ranked by confidence and recency. Turns accumulated marketing knowledge into an actionable playbook for any scenario, so past learnings directly inform current decisions without relying on memory or searching through old reports.

## Input Required

The user must provide (or will be prompted for):

- **Query context**: The situation to recall learnings for — specified as one or more of the following dimensions: channel (email, social, paid search, SEO, content, SMS, etc.), audience segment (developers, marketers, executives, SMB owners, enterprise buyers, etc.), objective (awareness, conversion, retention, upsell, win-back, etc.), campaign type (product launch, seasonal, evergreen, nurture, event, etc.), or a freeform situation description that captures the scenario in natural language (e.g., "planning a Black Friday email campaign targeting lapsed customers" or "launching a new product to a developer audience via content marketing")
- **Confidence threshold (optional)**: Minimum confidence score to include — defaults to 0.3 (includes hypotheses and above). Set to 0.7+ for only validated insights, or 0.0 to see everything including early-stage observations
- **Time range (optional)**: Filter learnings by when they were recorded — "last 30 days", "this quarter", "all time" (default). Recent learnings may be more relevant for fast-changing channels like paid social, while evergreen learnings about audience psychology may be valuable regardless of age
- **Max results (optional)**: Number of learnings to return — defaults to 10. Increase for comprehensive research or decrease for quick decision support

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand industry, audience segments, and active channels to contextualize the query and boost relevance of matching learnings. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Query the intelligence graph**: Execute `intelligence-graph.py query-relevant` with the provided context dimensions. The query matches against all indexed conditions — channel, audience, objective, campaign type — and also performs semantic matching for freeform situation descriptions. Apply confidence threshold and time range filters.
3. **Rank results**: Score each returned learning by a composite of relevance (how closely the learning's conditions match the query context), confidence (how validated the insight is based on accumulated evidence), and recency (how recently the learning was recorded or last updated, with a decay curve that weights recent learnings higher for volatile channels). Return the top results by composite score.
4. **Group into actionable themes**: Cluster the ranked learnings into coherent themes — e.g., "Content & Messaging" (what to say), "Timing & Frequency" (when to say it), "Audience Behavior" (how they respond), "Channel Tactics" (platform-specific techniques), and "Things to Avoid" (validated anti-patterns). Each theme gets a summary sentence synthesizing the grouped insights.
5. **Highlight conflicting insights**: Identify any learnings within the results that contradict each other — flag these explicitly with both sides of the conflict, their respective confidence scores, and conditions that may explain the difference (e.g., "true for SMB but not enterprise"). Recommend which to follow based on confidence and recency, or suggest an A/B test to resolve the conflict.
6. **Present as actionable playbook**: Format the output as a decision-ready playbook — themed sections with ranked learnings, a "quick wins" callout for high-confidence actionable insights, a "test these" callout for lower-confidence hypotheses worth validating, and a "watch out" callout for validated anti-patterns and conflicts.

## Output

- **Relevant learnings ranked by confidence**: Each learning displayed with its insight text, confidence score, source, date recorded, and matching context conditions — sorted by composite relevance-confidence-recency score
- **Grouped by theme**: Learnings organized into actionable theme clusters (content, timing, audience, channel tactics, anti-patterns) with a synthesis sentence per theme summarizing the collective insight
- **Conflicting insights flagged**: Any contradictions within the results highlighted with both perspectives, their confidence scores, qualifying conditions, and a recommendation on which to follow or how to test
- **Actionable recommendations**: A synthesized playbook section translating the raw learnings into specific recommendations for the queried situation — what to do, what to avoid, and what to test
- **Intelligence base stats**: Total learnings in the brand's graph, number matching this query, average confidence of matched results, and age distribution of matched learnings

## Agents Used

- **intelligence-curator** — Query execution against the intelligence graph with multi-dimensional context matching and semantic search for freeform queries, relevance-confidence-recency composite ranking, thematic clustering of results into actionable groups, conflict detection across returned learnings with resolution recommendations, and playbook formatting that translates raw intelligence into decision-ready recommendations
