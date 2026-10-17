# Creative Intelligence Guide

Reference knowledge for creative fatigue prediction, content decay analysis, refresh prioritization, and creative lifecycle management. Use this to anticipate performance degradation before it erodes campaign results.

---

## 1. Creative Fatigue Modeling

### What Creative Fatigue Is
The point at which ad performance degrades because the target audience has seen the creative too many times. Fatigue is not about the creative being bad — it is about the creative being exhausted. A high-performing ad will fatigue just as surely as a mediocre one; it simply takes longer.

### Decay Curve Types
- **Linear decay**: Gradual, steady performance decline. Typical for broad audiences with high reach and moderate frequency. CTR drops ~2-5% per week after baseline period. Most common pattern
- **Cliff decay**: Stable performance followed by a sudden, sharp drop (>30% in 48 hours). Common with narrow audiences and high frequency caps. The audience collectively hits saturation nearly simultaneously. Hardest to predict but most damaging
- **Plateau-drop**: Extended period of stable performance, then a transition to accelerating decline. Common with well-targeted ads where the most engaged segment converts early, and the remaining audience is progressively less responsive. Often misread as "still working" during the plateau phase
- **S-curve decay**: Slow initial decline, accelerating middle phase, then leveling off at a lower performance floor. Common with evergreen/always-on campaigns. The floor represents a baseline of new audience members seeing the creative for the first time

### Per-Segment Fatigue Thresholds
Fatigue speed depends on audience size relative to impression volume:
- **Narrow audience (<100K)**: Fatigue begins at frequency 4-6. Creative lifespan: 2-3 weeks at moderate budgets
- **Medium audience (100K-1M)**: Fatigue begins at frequency 6-10. Creative lifespan: 3-6 weeks
- **Broad audience (>1M)**: Fatigue begins at frequency 10-15. Creative lifespan: 6-12 weeks
- **Lookalike/prospecting audiences**: Slower fatigue due to continuous audience refresh from the platform. But creative still fatigues — just on a longer timeline
- **Retargeting audiences**: Fastest fatigue due to small, fixed audience pool. Rotate creative every 1-2 weeks

---

## 2. Fatigue Signal Detection

### Primary Signals (Detect Within the Ad Platform)
- **Frequency vs engagement correlation**: When frequency rises but engagement (CTR, engagement rate) stays flat or drops, fatigue is beginning. Plot these on a scatter chart weekly. A negative correlation that was previously positive or flat = fatigue onset
- **CTR velocity**: The rate of change in CTR, not the absolute CTR. A declining CTR velocity (CTR is still okay but declining faster each day) precedes absolute CTR decline by 2-3 days. This is your earliest warning
- **CPM inflation**: When CTR drops, platforms recognize poor engagement and increase CPMs to maintain delivery. Rising CPMs with declining CTR is a lagging but unambiguous fatigue signal
- **Cost-per-result acceleration**: CPA rising while conversion rate holds steady = the platform is spending more to find responsive users in an increasingly fatigued audience

### Secondary Signals (Cross-Platform and Behavioral)
- **Engagement composition shift**: Likes and reactions declining before clicks. Indicates passive rejection — users are no longer stopping to interact, even superficially, but may still click out of habit or curiosity. When clicks also decline, fatigue is advanced
- **Negative feedback increase**: Hide rates, "not interested" clicks, and ad report rates rising. Most platforms surface this in ad-level reporting. Even a small increase in negative feedback significantly reduces delivery
- **Comment sentiment shift**: Early comments are positive or curious. Fatigued comments include "I keep seeing this ad," complaints about frequency, or no comments at all. Monitor comment volume and sentiment as a qualitative signal
- **Video completion rate decline**: For video ads, completion rate drops before CTR. Users stop watching midway through content they have already seen. Particularly acute for non-skippable formats

### Conversion Divergence Signal
When conversion rate drops while CTR holds steady, the problem is NOT creative fatigue — it is landing page fatigue, offer fatigue, or audience quality degradation. Distinguishing creative fatigue from landing page fatigue prevents wasting time rotating creative when the real issue is downstream.
- **Creative fatigue**: CTR drops first, then conversions
- **Landing page fatigue**: CTR holds, conversions drop
- **Offer fatigue**: Both CTR and conversions drop, but CTR recovers when creative changes (audience still interested, just tired of the same offer)
- **Audience exhaustion**: All metrics decline and do not recover with creative rotation (the audience is tapped out, not just fatigued on the creative)

---

## 3. Fatigue Prediction Methodology

### Baseline Capture
The first 72 hours of a creative's performance represent its true baseline, assuming sufficient volume (minimum 1,000 impressions, ideally 5,000+). Record baseline CTR, engagement rate, CPM, and conversion rate during this window. All future comparisons reference this baseline.

### Moving Average Comparison
Compare a 3-day rolling average to the baseline. This smooths daily noise while remaining responsive to real trends. Use 7-day rolling average for lower-volume creatives (fewer than 500 daily impressions).

### Threshold Triggers
Set alerts when any of these thresholds are breached:
| Metric | Warning Threshold | Action Threshold |
|--------|------------------|-----------------|
| CTR | Below 80% of baseline | Below 70% of baseline |
| CPM | Above 115% of baseline | Above 130% of baseline |
| Engagement rate | Below 75% of baseline | Below 60% of baseline |
| Negative feedback rate | Above 150% of baseline | Above 200% of baseline |
| Cost per result | Above 120% of baseline | Above 140% of baseline |

Warning = prepare replacement creative. Action = rotate creative immediately.

### Time-to-Fatigue Estimation
Estimate when a creative will hit action thresholds based on:
- **Audience size**: Smaller audience = faster fatigue
- **Daily impressions**: Higher volume = faster fatigue
- **Frequency cap settings**: Tighter caps extend creative lifespan
- **Historical decay rate**: Use the slope of performance decline from the first 2 weeks to project forward
- **Formula (rough estimate)**: `days_to_fatigue = (audience_size / daily_impressions) * platform_factor`. Platform factors: Meta ~0.8, Google Display ~1.2, LinkedIn ~1.5, TikTok ~0.6 (faster creative consumption culture)

---

## 4. Content Decay Signals (Organic/Owned Content)

### Traffic-Based Signals
- **Month-over-month organic traffic decline >20%**: Decay is underway. Check Search Console for impression and click trends on the target keywords
- **Year-over-year traffic decline >30%**: Significant decay. Content may be losing relevance, authority, or competitive position
- **Seasonal adjustment**: Compare to the same period last year, not just the prior month. Some content is cyclical

### Search Position Signals
- **Primary keyword position drop >5 positions**: Content is losing competitive strength
- **Featured snippet loss**: A competitor has published better content or Google has changed the SERP format
- **Keyword cannibalization**: Another page on your site is now ranking for the same keyword, splitting authority

### Content Quality Signals
- **Outdated statistics**: Data points older than 2 years in content that relies on current data. Readers and search engines both penalize stale data
- **Broken external links**: Link rot, especially for citation links and resource references. Check quarterly with `link-profile-analyzer.py`
- **Outdated screenshots or examples**: UI screenshots of tools that have been redesigned, product examples that have been discontinued
- **Missing current context**: Content about a topic that has evolved significantly since publication (new regulations, new platforms, market shifts)

### Competitive Signals
- **Competitor content freshness**: A competitor publishes a newer, more comprehensive version of content you rank for. Monitor top 5 competitors for content updates on your primary keywords
- **New SERP features**: Google adds a featured snippet, People Also Ask, or AI Overview to a query where you rank — your organic click-through rate will decline even if your position holds
- **AI citation loss**: Content no longer cited by AI search engines (ChatGPT, Perplexity, Google AI Overview) that previously referenced it. Monitor referral traffic from AI sources

---

## 5. Content Refresh Prioritization

### Revenue Impact Scoring
Prioritize content refreshes by business impact, not just traffic:

`Priority Score = (monthly_organic_traffic * conversion_rate * AOV) + (backlink_count * 0.1) + (AI_citation_value * estimated_referral_traffic)`

- **Tier 1 (Immediate refresh)**: High-traffic, high-converting pages showing decay. Revenue at risk. Target: refresh within 2 weeks
- **Tier 2 (Scheduled refresh)**: High-backlink-equity pages losing traffic. SEO authority at risk. Target: refresh within 4 weeks
- **Tier 3 (Planned refresh)**: Pages losing AI visibility or featured snippets. Future traffic at risk. Target: refresh within 6 weeks
- **Tier 4 (Opportunistic)**: Long-tail informational content with low conversion. Refresh when capacity allows

### Effort Estimation
- **Light refresh** (2-4 hours): Update statistics, fix broken links, add recent examples, update screenshots. For content where the core argument is still valid
- **Medium refresh** (4-8 hours): Rewrite sections, add new subsections, update structure, add new media. For content where the topic has evolved moderately
- **Heavy refresh** (8-16 hours): Near-complete rewrite while preserving URL and core topic targeting. For content where the original approach is no longer competitive
- **Retire and redirect**: When the topic is no longer relevant or another page serves the intent better. 301 redirect to the best alternative page

---

## 6. Refresh Brief Methodology

### What to KEEP
Elements that are still performing and should be preserved:
- **URL**: Never change a URL that has backlinks and ranking history
- **Core keyword targeting**: If still relevant to the page's intent
- **Evergreen structural content**: Foundational explanations that remain accurate
- **High-quality original insights**: Proprietary data, unique frameworks, original research
- **Internal links**: Existing internal link structure (update destinations if needed)

### What to CHANGE
Elements showing fatigue or obsolescence:
- **Outdated statistics**: Replace with current data, cite recent sources
- **Stale examples**: Swap in recent, recognizable case studies
- **Dated references**: Remove references to old tools, discontinued products, past events
- **Broken links**: Fix or replace with current, authoritative sources
- **Thin sections**: Expand sections that competitors now cover more thoroughly
- **Meta title and description**: Refresh for current SERP competition and CTR optimization

### What to ADD
New elements that strengthen the content:
- **Updated case studies**: Recent examples with specific metrics
- **New data points**: Current statistics, survey results, industry reports
- **FAQ section**: Address People Also Ask queries and long-tail questions
- **Schema markup**: FAQ schema, HowTo schema, article schema if not already present
- **Visual content**: Updated charts, infographics, embedded videos
- **Expert quotes**: Original insights from subject matter experts

---

## 7. Cross-Channel Fatigue Correlation

### Correlated Channels
- **Paid social and display**: Strongly correlated fatigue patterns. Same audience, similar visual formats. When Meta creative fatigues, expect Google Display creative to fatigue within 1-2 weeks (if targeting the same audience)
- **Social and email**: Moderate correlation. If the same audience sees similar messaging on social and email, email fatigue accelerates. Differentiate creative and messaging between channels
- **Paid and organic brand perception**: Creative fatigue on paid can affect organic brand sentiment. Users who see the same ad 15+ times develop negative brand associations that persist beyond the campaign

### Independent Channels
- **Email**: Fatigue pattern differs from paid. Email fatigue is driven by send frequency and content variety, not impression frequency. Can be addressed by segmentation and content diversification without changing the overall strategy
- **SEO/organic content**: Decays on a completely different timeline (months/years vs days/weeks). Independent of paid creative fatigue

---

## 8. Creative Lifecycle Management

### Phase 1: Creation
Brief (audience, objective, key message, CTA, platform specs) to production to internal review to approval. Include fatigue estimation in the brief: expected lifespan based on audience size and budget.

### Phase 2: Launch
Deploy across channels with full tracking. Capture baseline metrics during the first 72 hours. Set fatigue monitoring alerts based on threshold triggers.

### Phase 3: Monitor
Ongoing performance tracking against baseline. Weekly fatigue assessment using moving averages. Flag when warning thresholds are breached. Begin replacement creative production when warning signals appear.

### Phase 4: Predict
Based on current decay trajectory, estimate days remaining to action threshold. Communicate to creative team with lead time needed for replacement production.

### Phase 5: Refresh or Rotate
For ads: deploy new creative variant, A/B test against fatigued creative to confirm improvement, then replace. For content: execute refresh brief, publish update, monitor recovery. Never hard-swap without testing when possible.

### Phase 6: Archive
Store performance data, creative assets, and learnings. Tag with audience, platform, objective, and lifespan data. Feed into future fatigue predictions — creatives similar to long-lived past winners may also have longer lifespans.
