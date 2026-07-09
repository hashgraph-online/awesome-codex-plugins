---
name: dark-funnel
description: "Map invisible buyer journeys. Use when: tracking unattributed discovery, Reddit, AI chatbots, or word-of-mouth."
---

# /digital-marketing-pro:dark-funnel

## Purpose

Map and illuminate the dark funnel — buyer journey activities invisible to traditional attribution. Identify where prospects are encountering the brand outside of trackable channels (Reddit discussions, AI chatbot queries, podcast mentions, community forums, word-of-mouth, dark social sharing) and surface intent signals that reveal the true scope of brand awareness and consideration happening beyond what analytics platforms can measure.

## Input Required

The user must provide (or will be prompted for):

- **Brand name and product names**: The brand and specific products or services to track across dark funnel channels — used to define search terms, mention patterns, and signal queries
- **Known community presence**: Subreddits, Slack communities, Discord servers, industry forums, or niche platforms where the brand has an official or organic presence — these are primary dark funnel listening posts
- **Podcast appearances**: Episodes, shows, or sponsorships the brand has participated in — used to correlate vanity URL visits, promo code redemptions, and branded search spikes with specific air dates
- **AI visibility data (optional)**: Output from `/digital-marketing-pro:geo-monitor` showing how AI chatbots (ChatGPT, Perplexity, Gemini) reference or recommend the brand — a growing dark funnel channel
- **Branded search volume trends**: Google Search Console or third-party keyword data showing branded search volume over time — the strongest proxy signal for offline and untracked brand exposure
- **"How did you hear about us" survey data (optional)**: Self-reported attribution from lead forms, onboarding flows, or post-purchase surveys — direct evidence of dark funnel touchpoints that customers themselves identify

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, industry context, and known competitive landscape. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Aggregate dark funnel signals**: Collect and normalize data from all available dark funnel sources — branded search volume trends over time (the primary proxy for untracked exposure), Reddit and community mention frequency and sentiment, AI chatbot citation data from the geo-tracker, direct traffic anomalies that correlate with offline activities, podcast attribution data (vanity URL visits, promo code usage, post-episode traffic spikes), and self-reported survey response data categorized by source.
3. **Correlate signals with marketing activities**: Cross-reference dark funnel signal spikes against a timeline of known marketing activities — do branded search spikes follow podcast episodes? Do community mentions surge after product launches or PR coverage? Does direct traffic increase after conference appearances? Identify which activities are generating the strongest dark funnel response and which have no measurable dark signal.
4. **Map the invisible buyer journey**: Construct a dark funnel map identifying each untracked touchpoint, its position in the buyer journey (awareness, consideration, decision), estimated audience size, and growth trajectory. Classify touchpoints by channel type — community (Reddit, forums, Discord), media (podcasts, YouTube mentions), AI (chatbot citations), social (dark social sharing via DMs and private groups), and word-of-mouth (survey-reported).
5. **Score dark funnel health per channel**: Rate each dark funnel channel on signal strength (volume and reliability of data), growth trend (expanding, stable, or declining), brand sentiment within the channel, and conversion proximity (how close the channel is to purchase intent). Produce a composite dark funnel health score.
6. **Recommend dark funnel investment opportunities**: Based on scoring and correlation analysis, identify the highest-ROI dark funnel investment opportunities — channels with strong signals but no intentional brand investment, emerging channels showing growth, and underperforming channels that could be amplified with targeted effort.

## Output

A comprehensive dark funnel intelligence report containing:

- **Dark funnel map**: Visual representation of all identified invisible touchpoints, organized by channel type and buyer journey stage, with estimated audience reach per touchpoint
- **Signal strength per dark channel**: Quantified signal volume and reliability for each dark funnel source — branded search volume trends, community mention frequency, AI citation rates, podcast attribution metrics, dark social indicators, and survey-reported sources
- **Correlation analysis**: Timeline overlay showing which marketing activities drive which dark funnel signals, with correlation strength scores and lag time between activity and signal response
- **Dark funnel health score**: Composite score across all channels with per-channel breakdown — signal strength, growth trend, sentiment, and conversion proximity ratings
- **Influence estimation**: Estimated contribution of dark funnel channels to overall pipeline and revenue, based on signal correlation and survey data triangulation
- **Investment recommendations**: Prioritized list of dark funnel investment opportunities with expected impact, effort required, and recommended tactics for each channel
- **Monitoring plan**: Ongoing dark funnel tracking cadence — which signals to monitor weekly, monthly, and quarterly, with alert thresholds for significant changes

## Agents Used

- **market-intelligence** — Dark funnel signal aggregation across community platforms, podcasts, AI chatbots, and dark social channels, cross-referencing signal spikes with marketing activity timelines to identify correlation patterns, trend detection across dark funnel sources to surface emerging channels and declining ones, and competitive dark funnel benchmarking where data is available
- **analytics-analyst** — Branded search volume analysis and trend decomposition, direct traffic anomaly detection and attribution gap identification, correlation scoring between marketing activities and dark funnel signal responses with lag time calculation, and composite dark funnel health scoring across signal strength, growth, sentiment, and conversion proximity dimensions
