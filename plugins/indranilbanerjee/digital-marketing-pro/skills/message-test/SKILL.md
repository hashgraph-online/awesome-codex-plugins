---
name: message-test
description: "Test message variants on synthetic audiences. Use when: predicting response rates, sentiment, or objections before live tests."
---

# /digital-marketing-pro:message-test

## Purpose

Test message variants against synthetic audience panels before real-world deployment. Predict which variant will perform best overall and per segment, identify potential objections, and narrow down variants for real A/B testing. This command eliminates wasted ad spend and testing cycles by pre-screening message variants through AI-simulated audience segments grounded in real CRM behavioral data. Instead of testing six variants live and burning budget on underperformers, run them through synthetic panels first to identify the top two or three candidates worth real investment. Each variant is scored on five evaluation criteria — resonance, clarity, credibility, urgency, and differentiation — with per-segment breakdowns that reveal personalization opportunities where different segments prefer different messages.

## Input Required

The user must provide (or will be prompted for):

- **Message variants**: 2-6 variants to test, each containing a headline, body copy, and call-to-action. Variants can be full ad creatives, email subject lines with preview text, landing page hero sections, social media posts, or any message format. Label each variant clearly (Variant A, B, C, etc.). Variants should test meaningfully different approaches — different value propositions, emotional appeals, proof points, or framing — rather than minor word swaps that synthetic testing cannot reliably distinguish
- **Target audience panel**: An existing panel ID from a previous `/digital-marketing-pro:focus-group` or `/digital-marketing-pro:message-test` session, or new segment definitions to build from CRM data. New panels require segment criteria — demographic, behavioral, psychographic, or value-based attributes. Panels with 3-5 segments give the best balance of cross-segment insight and output manageability
- **Evaluation criteria**: The dimensions to score each variant on. Default criteria are resonance (emotional connection and relevance), clarity (ease of understanding the message and desired action), credibility (believability of claims and proof points), urgency (motivation to act now rather than later), and differentiation (distinctiveness from competitor messaging). Custom criteria can be added or defaults can be narrowed to focus the analysis

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, positioning, competitive context, and messaging guidelines. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Load audience panel**: Reference the existing panel by its ID (list available panels with `python "${CLAUDE_PLUGIN_ROOT}/scripts/audience-simulator.py" --brand {slug} --action list-panels`), or create a new panel via `python "${CLAUDE_PLUGIN_ROOT}/scripts/audience-simulator.py" --brand {slug} --action create-panel --panel-name {name} --segments '[...]'` with CRM data grounding if new segment definitions were provided. Verify the panel has sufficient segment diversity for meaningful cross-segment comparison.
3. **Test each variant against each segment**: Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/audience-simulator.py" --brand {slug} --action test-message --panel-id {id} --variants '[...]'` for the variant set. Score each variant on every evaluation criterion (resonance, clarity, credibility, urgency, differentiation) from the perspective of each segment's behavioral profile. Generate predicted response sentiment, key reactions, and specific objections for each combination.
4. **Aggregate scores**: Calculate overall variant rankings by averaging scores across all segments weighted by segment size. Identify the overall winner and per-segment winners. Flag cases where the overall winner is not the per-segment winner — these represent personalization opportunities.
5. **Identify segment preferences**: Map which segments prefer which variant and why. Highlight cases where a single variant wins across all segments (universal appeal) versus cases where different segments strongly prefer different variants (personalization-required). Calculate preference strength to distinguish strong preferences from marginal differences.
6. **Extract objection patterns per variant**: Catalog all objections raised across segments for each variant. Identify recurring objections (cross-segment issues to fix), segment-specific objections (addressable through targeting), and objections unique to the weakest variants (reasons to eliminate them).
7. **Recommend top variants for real A/B testing**: Based on overall ranking, segment preference patterns, and objection severity, recommend the top 2-3 variants worth investing in for real A/B testing. Include specific suggestions for minor improvements that could strengthen each recommended variant based on the objection analysis.

## Output

A structured message test report containing:

- **Variant ranking**: Overall scores for each variant with aggregate ranking across all segments and evaluation criteria, showing the clear winner and relative performance gaps between variants
- **Per-segment breakdown**: Detailed scoring for each variant within each segment — different segments may prefer different variants, and this breakdown reveals which variant wins where and by how much
- **Evaluation criteria scores per variant**: Scores on each criterion (resonance, clarity, credibility, urgency, differentiation) for each variant, identifying specific strengths and weaknesses — a variant may score high on urgency but low on credibility, suggesting specific improvement directions
- **Objection patterns identified**: Recurring objections across segments (fix before any deployment), segment-specific objections (address through targeting or personalization), and variant-specific objections (reasons to eliminate weaker variants)
- **Personalization opportunities**: Where different segments strongly prefer different variants, with recommendations for segment-specific messaging strategies that could outperform a single-variant approach
- **Recommended variants for real A/B test**: The top 2-3 variants recommended for live testing with rationale, suggested improvements based on synthetic feedback, and recommended test parameters (audience, sample size, duration)
- **Confidence level and limitations**: Explicit confidence rating with explanation of what synthetic testing can and cannot predict — directional preference signals are reliable, exact conversion rate predictions are not. Recommendations for what to validate in real-world testing

## Agents Used

- **marketing-strategist** — Variant evaluation framework design, cross-segment insight interpretation and pattern identification, overall ranking methodology with segment-size weighting, personalization opportunity assessment, and A/B test design recommendations for real-world validation of top variants
- **content-creator** — Messaging improvement suggestions based on objection patterns and criterion-level scores, specific copy refinements for recommended variants addressing identified weaknesses, and alternative framing suggestions for variants with high potential but fixable issues
