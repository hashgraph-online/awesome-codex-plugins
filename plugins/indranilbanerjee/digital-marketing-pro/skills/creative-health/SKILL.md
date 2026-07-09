---
name: creative-health
description: "Assess ad creative fatigue. Use when: ads underperform, need refresh timing, or creative lifecycle review."
---

# /digital-marketing-pro:creative-health

## Purpose

Monitor creative health across all active advertising. Score each creative for fatigue risk, predict when fatigue will impact performance, generate refresh recommendations with specific change suggestions, and create A/B test plans for fatiguing creatives. Creative fatigue is one of the fastest ways to waste ad spend — a high-performing ad that ran too long silently bleeds money as CTR drops, CPM rises, and engagement fades. This command catches fatigue before it costs you, tells you exactly what to change, and gives you a structured test plan to validate the refresh. It covers the full creative lifecycle from launch through maturity to decline, so you always know which creatives are earning their spend and which need attention.

## Input Required

The user must provide (or will be prompted for):

- **Active creatives with performance data**: A list of currently running creatives, each with: creative ID or name, channel (paid social, display, search, email, video), current performance metrics (impressions served, frequency or average times shown per user, current CTR, current CPM or CPC, current engagement rate), baseline metrics from the creative's first 7-14 days (baseline CTR, baseline CPM, baseline engagement rate), days running since launch, audience size the creative is serving, and current daily or weekly spend. Can be provided as exported data or pulled from connected ad platform MCPs
- **Channel context**: Which advertising channels the creatives run on — Meta Ads, Google Ads, TikTok Ads, LinkedIn Ads, display networks, programmatic, or email. Each channel has different fatigue dynamics (social fatigues faster than search, video fatigues differently than static)
- **Refresh constraints (optional)**: Any constraints on creative refreshes — brand guidelines that limit visual changes, approval processes that add lead time, production capacity (how many new creatives can be produced per week), or budget for creative production. These constraints shape the refresh recommendations to be actionable within real-world limits
- **Performance thresholds (optional)**: Brand-specific thresholds for when a creative is considered "fatigued" — e.g., "CTR drops 30% from baseline" or "CPM increases 25% from baseline." If not provided, industry-standard thresholds are applied per channel

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand creative guidelines, historical creative performance benchmarks, known fatigue patterns from past campaigns, and production capacity constraints. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load visual identity restrictions and messaging guardrails that constrain refresh options. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with industry defaults.
2. **Score each creative's health**: Execute `creative-fatigue-predictor.py` with the performance data for each creative. The scoring model evaluates five fatigue signals — CTR ratio (current vs baseline, weighted 30%), CPM ratio (current vs baseline, weighted 25%), engagement ratio (current vs baseline, weighted 20%), frequency or impression saturation (weighted 15%), and time running relative to channel norms (weighted 10%). Each creative receives a health score from 0-100 where 100 is peak health and 0 is fully fatigued, plus a fatigue stage classification: Fresh (80-100), Mature (60-79), Fatiguing (40-59), Fatigued (20-39), or Exhausted (0-19).
3. **Predict fatigue timeline**: For each creative not yet in Fatigued or Exhausted stage, project the estimated days until fatigue based on the current trajectory of decline — rate of CTR decay, CPM acceleration, and engagement erosion. Factor in audience size (smaller audiences fatigue faster), frequency rate (higher frequency accelerates fatigue), channel dynamics (social fatigues 2-3x faster than search), and seasonality effects. Output a "days remaining" estimate with confidence range for each creative.
4. **Generate refresh briefs for fatiguing creatives**: For each creative in Fatiguing, Fatigued, or Exhausted stage, produce a specific refresh brief — what to keep (elements that drove initial performance: hook, value proposition, social proof, CTA that still resonates), what to change (elements contributing to fatigue: visual treatment, headline angle, color scheme, format, opening hook for video), and what to test (new angles or approaches worth experimenting with based on competitor creative trends and brand positioning). Ensure all refresh suggestions comply with brand guidelines.
5. **Create A/B test plan for each creative needing refresh**: For each refresh brief, generate a structured A/B test plan — control (current creative), variant(s) with the recommended changes, hypothesis for why the variant should outperform, primary metric to evaluate (CTR, CPC, conversion rate depending on campaign objective), minimum sample size for statistical significance, expected test duration, and decision criteria for declaring a winner. Include a test naming convention for organized tracking.
6. **Prioritize by spend and impact**: Rank all creatives needing attention by the combination of daily spend (higher spend = more waste if fatigued) and fatigue severity (more fatigued = more urgency). Creatives burning large budgets while deeply fatigued rank highest. Calculate the estimated spend waste — the incremental cost of running a fatigued creative versus a fresh one at baseline performance — to quantify the cost of inaction.

## Output

A creative health report containing:

- **Creative health dashboard**: All active creatives scored and classified — showing creative name or ID, channel, health score (0-100), fatigue stage (Fresh/Mature/Fatiguing/Fatigued/Exhausted), key metrics versus baseline (CTR ratio, CPM ratio, engagement ratio), frequency, days running, and daily spend
- **Fatigue predictions**: For each non-exhausted creative, estimated days remaining before performance drops below acceptable thresholds — with confidence range and the primary driver of projected fatigue (frequency saturation, audience exhaustion, or creative wear-out)
- **Refresh priority list**: Creatives ranked by urgency — combining fatigue severity with spend level to show which refreshes will save the most budget, with estimated daily spend waste for each fatigued creative
- **Refresh briefs per creative**: Specific, actionable refresh recommendations for each fatiguing or fatigued creative — what to keep, what to change, what to test, and why, all within brand guidelines and production constraints
- **A/B test plans**: Structured test plans for each creative refresh — control and variant definitions, hypothesis, primary metric, sample size requirement, test duration estimate, and success criteria with statistical confidence threshold
- **Creative lifecycle timeline**: A timeline view showing when each active creative was launched, its current lifecycle stage, and projected transition dates — enabling proactive production planning so fresh creatives are ready before current ones fatigue out
- **Estimated performance recovery**: Projected improvement in CTR, CPM, and engagement if fatigued creatives are refreshed — quantifying the expected return on creative production investment

## Agents Used

- **content-creator** — Creative refresh ideation including new visual angles, headline variations, hook alternatives, and format experiments grounded in brand voice and positioning, refresh brief generation with specific keep/change/test recommendations, and A/B test variant design with clear hypotheses tied to fatigue diagnosis
- **media-buyer** — Performance analysis across channels with fatigue-adjusted benchmarking, spend waste calculation for fatigued creatives, budget impact prioritization ranking refreshes by cost of inaction, and channel-specific fatigue threshold calibration based on platform dynamics and audience behavior
- **performance-monitor-agent** — Fatigue signal detection from performance metric trends, health score calculation using weighted multi-signal composite model, fatigue timeline projection based on decay rate analysis, and creative lifecycle stage classification with transition monitoring
