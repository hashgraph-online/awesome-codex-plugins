---
name: media-plan
description: "Create a paid media plan. Use when: building media buy schedules, cross-channel budget allocation, or creative rotation calendars."
argument-hint: "[--budget=amount --channels=list]"
---

# /digital-marketing-pro:media-plan

## Purpose

Generate a holistic paid media plan that coordinates budget, channels, audiences, creative, and timing across all advertising platforms. Balances reach and efficiency objectives with practical execution constraints to produce a ready-to-implement plan with clear pacing targets and contingency protocols.

## Input Required

The user must provide (or will be prompted for):

- **Campaign dates**: Start date, end date, and any blackout periods or mandatory flight windows
- **Total paid media budget**: Aggregate budget for the campaign period with any channel-specific floors or caps
- **Channels available**: Platforms in consideration — Google Ads, Meta Ads, LinkedIn Ads, TikTok Ads, programmatic display, connected TV, native, audio, out-of-home, etc.
- **Campaign objectives**: Primary and secondary objectives — awareness (reach/impressions), consideration (traffic/engagement), conversion (leads/sales/ROAS)
- **Target audiences with segments**: Audience definitions including demographics, interests, behaviors, custom audiences, lookalikes, and retargeting pools
- **Creative assets available**: Existing ad formats and sizes, video lengths, static variants, and any creative production timelines for new assets
- **Geographic targeting**: Markets, regions, DMAs, or countries to target with any geo-specific budget weighting
- **Competitive spending intelligence**: Known or estimated competitor ad spend, share of voice benchmarks, and auction pressure indicators
- **Historical performance by channel**: Past campaign data — CPC, CPM, CPA, ROAS, conversion rates — by channel and audience segment
- **Seasonality factors**: Demand fluctuations, industry events, holidays, promotional periods, or competitive surges that affect costs or performance

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Assess channel-objective fit**: Evaluate each available channel against campaign objectives using reach capability, targeting precision, cost benchmarks, creative format support, and measurement reliability
3. **Allocate budget across channels**: Distribute budget using efficiency-weighted allocation — factor in historical performance, diminishing returns curves, minimum effective spend thresholds, and strategic importance per channel
4. **Design flight schedule**: Structure campaign timing as continuous, pulsing, or flighting based on objectives, seasonality, and budget — define weekly spend levels and heavy-up periods
5. **Build audience targeting matrix**: Map each audience segment to its optimal channel(s) with targeting parameters, expected reach, estimated frequency, and overlap management between platforms
6. **Plan creative rotation**: Schedule creative variants across channels with rotation frequency, fatigue thresholds (impressions or frequency caps), A/B test windows, and refresh dates for new assets
7. **Define measurement framework**: Establish KPIs per channel, tracking requirements (pixels, UTMs, offline conversion imports), attribution model, and reporting cadence
8. **Set contingency holdback**: Reserve 10-15% of budget as contingency for opportunistic scaling, underperformance reallocation, or emerging platform opportunities — define trigger criteria for deployment
9. **Create platform setup checklists**: Build channel-specific setup checklists covering account structure, campaign naming conventions, tracking implementation, audience uploads, and creative specs
10. **Model reach and frequency estimates**: Project total reach, average frequency, and effective frequency per channel and in aggregate — flag oversaturation or underspend risks
11. **Compile unified media plan calendar**: Assemble all components into a single calendar view showing budget pacing, creative rotation, audience activation, and measurement milestones week by week

## Output

A structured paid media plan containing:

- **Channel allocation table**: Budget amount, percentage share, and strategic rationale for each channel with minimum and maximum spend guardrails
- **Flight schedule with weekly budget waves**: Week-by-week spend plan showing ramp-up, steady state, heavy-up, and wind-down phases per channel
- **Audience targeting matrix**: Segment-by-channel-by-creative mapping showing targeting parameters, expected reach, frequency caps, and overlap management
- **Creative rotation calendar**: Asset schedule per channel with rotation dates, fatigue thresholds, A/B test windows, and refresh milestones for new creative
- **Reach and frequency estimates**: Projected reach, average frequency, and effective frequency per channel and in aggregate with confidence ranges
- **Measurement framework**: KPIs per channel, tracking requirements, attribution model, reporting cadence, and data integration points
- **Platform setup checklists**: Channel-specific implementation checklists covering account structure, naming conventions, tracking, audiences, and creative specs
- **Contingency budget plan**: Reserve amount, deployment trigger criteria (over/underperformance thresholds), and reallocation decision framework
- **Competitive spending comparison**: Estimated share of voice, auction overlap indicators, and competitive pressure assessment by channel
- **Daily/weekly pacing targets**: Spend and performance pacing benchmarks for in-flight monitoring with acceptable variance thresholds
- **Cross-channel synergy map**: Retargeting flows between channels, sequential messaging paths, and audience progression logic from awareness to conversion
- **Risk scenarios with budget reallocation triggers**: Defined scenarios (platform outage, CPM spikes, underperformance, budget cuts) with pre-approved reallocation responses

## Agents Used

- **media-buyer** — Channel allocation, budget pacing, auction dynamics, platform setup, reach/frequency modeling, competitive spending analysis, and creative rotation planning
- **marketing-strategist** — Objective-channel alignment, audience strategy, cross-channel synergy design, contingency planning, and measurement framework architecture
