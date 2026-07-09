# Media Planning Framework

## Media Planning Fundamentals

Media planning is the strategic process of selecting channels, timing, and budget allocation to deliver advertising messages to a target audience with maximum efficiency.

### Core Metrics

| Metric | Definition | Formula | Use Case |
|--------|-----------|---------|----------|
| Reach | Unique individuals exposed to an ad at least once | Unique impressions / Target population | Campaign breadth measurement |
| Frequency | Average number of times each person sees the ad | Total impressions / Reach | Message reinforcement tracking |
| GRP (Gross Rating Points) | Total weight of a media schedule | Reach (%) x Frequency | TV/radio/OOH planning currency |
| TRP (Target Rating Points) | GRP filtered to target demographic | Target Reach (%) x Frequency | Demographic-focused planning |
| CPM (Cost Per Thousand) | Cost to reach 1,000 impressions | (Cost / Impressions) x 1,000 | Cross-channel cost comparison |
| SOV (Share of Voice) | Brand's ad presence vs. total category | Brand spend / Category spend | Competitive positioning |

### Effective Frequency

The minimum number of exposures needed before an ad drives measurable response:

1. **1-2 exposures** — Awareness registration only; message unlikely to stick
2. **3-5 exposures** — Generally accepted effective frequency range for most campaigns
3. **6-10 exposures** — Required for complex messages, new categories, or low-involvement decisions
4. **10+ exposures** — Diminishing returns begin; risk of ad fatigue and negative sentiment
5. **Recency model** — For established brands, a single exposure close to the purchase decision can be most effective

The diminishing returns curve follows a logarithmic pattern: the first three exposures deliver roughly 70% of total campaign impact. Every subsequent exposure yields progressively smaller lifts. Monitor frequency caps at the platform level to avoid waste.

### Media Weight

Media weight refers to the total volume of advertising pressure applied to a market. It is measured through GRPs, impressions, or spend. Higher weight does not always equal better results — the relationship between weight and outcome is S-curved, with a minimum threshold below which spend is wasted and a ceiling above which additional spend yields negligible returns.

---

## Channel Selection Methodology

### Four Approaches

| Approach | Method | When to Use |
|----------|--------|-------------|
| Historical Performance | Allocate based on past channel ROAS/CPA data | Mature accounts with 6+ months of data |
| Incremental Testing | Run controlled lift tests to measure true incrementality | When historical data may overcount due to attribution issues |
| Competitive Parity | Match or exceed competitor spend in key channels | Defending market share in saturated categories |
| Share-of-Voice (SOV) | Set SOV above share-of-market (SOM) to grow | Growth phase; brand building campaigns |

### Channel-Objective Fit Matrix

| Objective | Search | Social | Display | Video | Audio | Native | OOH |
|-----------|--------|--------|---------|-------|-------|--------|-----|
| Brand Awareness | Low | High | Medium | High | High | Medium | High |
| Consideration | High | High | Medium | High | Medium | High | Low |
| Lead Generation | High | High | Low | Medium | Low | Medium | Low |
| Direct Sales | High | High | Low | Medium | Low | Medium | Low |
| Retention | Medium | High | Medium | Medium | Medium | Medium | Low |
| Local Reach | High | Medium | Medium | Low | High | Low | High |

Selection priority: Start with channels that align to the primary objective, then layer in supporting channels for sequential messaging.

---

## Budget Allocation Models

| Model | Description | Pros | Cons | Best For |
|-------|-------------|------|------|----------|
| Top-Down (% of Revenue) | Allocate a fixed percentage of actual or projected revenue to advertising | Simple, predictable, scales with business | Ignores market conditions, self-reinforcing (low revenue = low spend) | Stable businesses with consistent revenue |
| Bottom-Up (Objective-Based) | Calculate spend required to achieve specific goals (CPL x target leads) | Directly tied to outcomes, defensible | Requires accurate benchmarks, can exceed budget capacity | Performance-driven campaigns with clear KPIs |
| Competitive Parity | Match or proportionally exceed competitor spend levels | Maintains market position, easy to benchmark | Assumes competitors are spending efficiently, reactive | Mature markets with transparent competitor data |
| Optimization-Based | Use algorithmic models (MMM, MTA) to allocate based on marginal returns | Data-driven, maximizes efficiency | Requires significant data infrastructure, model lag | Large budgets with robust measurement systems |
| Hybrid | Combine top-down budget ceiling with bottom-up allocation within it | Balances fiscal discipline with performance optimization | More complex to manage, requires alignment across teams | Most mid-to-large advertisers |

### Rule-of-Thumb Splits by Funnel

- **Brand building (awareness/consideration):** 40-60% of total budget
- **Performance (conversion/acquisition):** 30-50% of total budget
- **Retention/loyalty:** 10-20% of total budget

Adjust ratios based on brand maturity: new brands skew 60/30/10 toward awareness; established brands can run 30/50/20 toward performance and retention.

---

## Flighting Strategies

| Strategy | Pattern | Decision Criteria |
|----------|---------|-------------------|
| Continuous | Steady, even spend across all weeks | Evergreen products, always-on lead gen, consistent demand |
| Pulsing | Baseline spend with periodic bursts | Seasonal products with year-round relevance (e.g., fitness) |
| Flighting | Alternating on/off periods with zero spend gaps | Highly seasonal products, limited budgets, event-driven |
| Front-Loading | Heavy spend in early weeks, tapering off | Product launches, time-sensitive offers, building early momentum |
| Back-Loading | Light spend initially, ramping to peak at end | Events with fixed dates (conferences, holidays), building anticipation |

### Decision Framework

1. Is demand seasonal or consistent? Seasonal leads to pulsing or flighting; consistent leads to continuous.
2. Is there a fixed event date? Yes leads to back-loading or front-loading depending on whether pre-event awareness or last-minute urgency matters more.
3. Is budget constrained relative to competitive noise? Constrained budgets benefit from flighting (concentrated impact) over continuous (diluted presence).
4. Does the product require sustained consideration? Long sales cycles favor continuous; impulse products can handle flighting.

---

## Budget Waves & Contingency

### Holdback Reserves

Maintain 10-15% of total budget as uncommitted reserve. This holdback serves three purposes:

1. **Opportunity capture** — Respond to unexpected viral moments, competitor missteps, or trending topics
2. **Performance scaling** — Double down on campaigns that exceed targets mid-flight
3. **Risk mitigation** — Cover cost increases from auction pressure or platform changes

### Seasonal Multipliers

Apply multipliers to baseline weekly spend based on demand patterns:

| Period | Multiplier | Rationale |
|--------|-----------|-----------|
| Peak season | 1.5-2.0x | Highest demand, competitive pressure |
| Shoulder season | 1.0-1.2x | Moderate demand, cost-efficient |
| Off-season | 0.5-0.8x | Lower demand, brand building opportunity |
| Tentpole events (Black Friday, etc.) | 2.0-3.0x | Concentrated demand, high CPMs |

### Trigger-Based Reallocation Rules

Define rules in advance so mid-flight decisions are fast:

- If CPA exceeds target by 30% for 5+ consecutive days, reduce spend by 25% and reallocate to top performer
- If ROAS exceeds target by 50% for 3+ days, increase spend by 20% from reserve
- If a channel exhausts its audience (frequency > 8), pause and shift budget to next-best channel
- If a competitor launches a major campaign, activate reserve for defensive SOV push

### Pacing Targets

- **Daily pacing:** Actual spend within +/-10% of daily target
- **Weekly pacing:** Cumulative spend within +/-5% of weekly target
- **Monthly reconciliation:** Adjust remaining weeks to hit monthly target

---

## Creative Rotation Cadence

### Fatigue Indicators by Platform

| Platform | Fatigue Signal | Threshold | Action |
|----------|---------------|-----------|--------|
| Meta (Facebook/Instagram) | CTR decline | >20% drop from baseline over 7 days | Refresh creative |
| Meta | Frequency | >4.0 for conversion, >6.0 for awareness | Rotate or expand audience |
| Google Display | CTR decline | >30% drop from baseline | Swap creative variants |
| YouTube | View-through rate decline | >15% drop from baseline | Test new hooks |
| LinkedIn | CTR decline | >25% drop from baseline | Refresh copy and imagery |
| TikTok | Engagement rate decline | >20% drop over 5 days | Replace with new concept |

### Refresh Cycles

- **Social (Meta, TikTok, LinkedIn):** Every 2-4 weeks, or sooner if fatigue signals appear
- **Display:** Every 4-8 weeks for standard banners; 2-4 weeks for remarketing
- **Video (YouTube, CTV):** Every 6-8 weeks for full production; 3-4 weeks for UGC-style
- **Search ads:** Quarterly copy refresh; ongoing RSA asset rotation

### A/B Structure Within Rotation

Maintain at least 3 active creatives per ad set at all times. Structure as: 1 proven performer (control) + 1 iterative variant (evolution) + 1 bold test (exploration). Promote winners to control, retire losers, and introduce new tests in a continuous cycle.

---

## Cross-Channel Synergy

### Sequential Messaging

1. **Awareness layer** — Broad reach channels (video, display, social) introduce the brand or product
2. **Consideration layer** — Retarget engaged users with deeper content (case studies, demos, comparisons)
3. **Conversion layer** — Capture intent with search, remarketing, and direct-response social
4. **Retention layer** — Re-engage customers with email, social, and loyalty-focused messaging

### Channel Role Assignment

| Role | Channels | KPIs |
|------|----------|------|
| Acquisition (new audiences) | Prospecting social, broad search, video, programmatic | CPM, reach, new visitor rate |
| Retargeting (warm audiences) | Remarketing display, social retargeting, email | CTR, conversion rate, CPA |
| Retention (existing customers) | Email, social organic, loyalty programs | LTV, repeat purchase rate, churn |

### Attribution Impact

Cross-channel synergy complicates attribution. A user who sees a YouTube ad, clicks a Meta retargeting ad, and converts via branded search will attribute differently depending on the model. Plan for this by using incrementality tests alongside attribution reporting, and avoid cutting channels that appear low-performing in last-click but drive upper-funnel lift.

---

## Flight Calendar Template

| Week | Channel | Daily Budget | Creative | Audience | KPI Target | Notes |
|------|---------|-------------|----------|----------|------------|-------|
| W1 | Meta - Prospecting | $X/day | Launch Set A (3 creatives) | Broad interest + lookalike | CPM < $X, Reach > X | Launch phase, monitor delivery |
| W1 | Google Search - Brand | $X/day | RSA Set 1 | Brand keywords | CPC < $X, CTR > X% | Always-on baseline |
| W2 | Meta - Prospecting | $X/day | Set A (monitor fatigue) | Same + expansion | CPM < $X | Evaluate creative performance |
| W2 | YouTube - Awareness | $X/day | 15s + 30s cuts | Affinity + custom intent | VTR > X%, CPV < $X | Frequency cap: 3/week |
| W3 | Meta - Retargeting | $X/day | Set B (testimonial) | Site visitors 7-30 days | CPA < $X | Launch retarget layer |
| W3 | Google Search - Non-Brand | $X/day | RSA Set 2 | Category keywords | CPA < $X | Bid adjustments based on W1-2 |
| W4 | All channels | Adjusted | Top performers + new test | Refined segments | Blended CPA < $X | Mid-flight optimization |

Extend the calendar for the full campaign duration. Add rows for each channel/audience combination. Review weekly and annotate with actual performance.

---

## Platform-Specific Planning Notes

### Google Ads
- Campaign types: Search, Performance Max, Display, Video (YouTube), Demand Gen, App
- Performance Max consolidates signals across channels but limits visibility; run alongside standard campaigns for control
- Budget minimums: None technically, but $50-100/day recommended per campaign for learning
- Broad match + smart bidding is Google's preferred setup; exact match still valuable for high-intent terms

### Meta (Facebook & Instagram)
- Buying types: Auction (standard), Reservation (guaranteed reach for awareness)
- Advantage+ campaigns automate targeting but reduce control; use for scaling proven concepts
- Minimum viable budget: $20/day per ad set for stable delivery
- Creative volume matters: plan for 3-5 creatives per ad set minimum

### LinkedIn
- Minimum daily budget: $10/day; minimum CPC bid: $2.00 (varies by market)
- Higher CPCs/CPMs than other social platforms; best for B2B with high LTV
- Matched Audiences (retargeting, ABM lists) outperform interest targeting significantly
- Document Ads and Thought Leader Ads typically see higher engagement than standard formats

### TikTok
- Spark Ads (boosting organic posts) outperform standard in-feed ads for authenticity
- Minimum campaign budget: $50; minimum ad group budget: $20/day
- Creative lifespan is short (7-14 days); plan for high creative volume
- Vertical 9:16 is mandatory; repurposed horizontal content underperforms significantly

### Programmatic (DSPs)
- Private Marketplace deals (PMPs) offer premium inventory with price floors; negotiate for guaranteed rates
- Open exchange provides scale but lower quality; use brand safety tools and inclusion/exclusion lists
- Minimum viable budget varies by DSP but plan $5,000-10,000/month for meaningful data
- Contextual targeting is gaining importance as cookie deprecation continues
