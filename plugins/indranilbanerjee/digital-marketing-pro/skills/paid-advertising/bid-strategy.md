# Bid Strategy — Optimization & Management

## Bid Strategy Decision Tree by Objective

```
START: What is your primary campaign objective?
│
├── Drive Conversions (Leads, Sales, Sign-ups)
│   ├── Have a target CPA? ──────────────────→ Target CPA (tCPA)
│   │   └── Enough volume? (30+ conv/month) → Yes: tCPA | No: Max Conversions
│   ├── Have a target ROAS? ─────────────────→ Target ROAS (tROAS)
│   │   └── Enough volume? (50+ conv/month) → Yes: tROAS | No: Max Conv Value
│   └── No specific target? ─────────────────→ Maximize Conversions (uncapped)
│
├── Drive Traffic / Clicks
│   ├── Budget-efficient clicks? ────────────→ Maximize Clicks (set CPC cap)
│   └── Engagement-focused? ─────────────────→ Maximize Clicks (no cap)
│
├── Build Awareness / Reach
│   ├── Impression share goal? ──────────────→ Target Impression Share
│   ├── Maximum reach? ──────────────────────→ CPM bidding (Meta, TikTok, Programmatic)
│   └── Video views? ───────────────────────→ CPV / ThruPlay bidding
│
└── Need Full Manual Control
    ├── Very low volume (<15 conv/month)? ──→ Manual CPC
    ├── Regulatory / compliance constraints? → Manual CPC
    └── Testing new campaigns? ─────────────→ Manual CPC → transition to automated
```

## Bid Strategy Comparison Across Platforms

| Strategy | Google Ads | Meta Ads | LinkedIn Ads | TikTok Ads | Programmatic (DSP) |
|---|---|---|---|---|---|
| Max Conversions | Maximize Conversions | Maximize Conversions | Maximize Conversions | Maximum Conversion | Auto-optimize to conversion |
| Target CPA | tCPA | Cost per result goal | Target cost | Cost cap | Target CPA |
| Target ROAS | tROAS | ROAS goal (Adv+) | N/A | ROAS goal | Target ROAS |
| Max Clicks | Maximize Clicks | Maximize Link Clicks | Maximize Clicks | Maximize Clicks | Max clicks optimization |
| Impression-based | Target Imp. Share | Maximize Reach (CPM) | N/A | Reach (CPM) | Fixed / Floor CPM |
| Manual | Manual CPC | Bid cap | Manual bid | Bid cap | Fixed CPM / Max bid |
| Value-based | Max Conv Value | Highest Value | N/A | Max Value | Maximize revenue |

## Learning Phase Management

### What Is the Learning Phase?
When you launch a new campaign or make significant changes, the platform's algorithm needs data to optimize delivery. During this period, performance fluctuates as the system explores which users, placements, and times convert best.

### Learning Phase Duration by Platform

| Platform | Typical Duration | Conversions Needed | Reset Triggers |
|---|---|---|---|
| Google Ads | 1–2 weeks | 30–50 conversions | Budget change >20%, bid strategy change, conversion action change |
| Meta Ads | 7 days (or 50 conversions) | 50 conversions per ad set | Budget change >20%, bid change, audience change, creative change, 7-day pause |
| LinkedIn Ads | 1–2 weeks | ~15 conversions | Bid change, audience change, budget change |
| TikTok Ads | 4–7 days (or 50 conversions) | 50 conversions per ad group | Budget change >50%, bid change, targeting change |
| Programmatic | Varies by DSP | Campaign-dependent | Major targeting or budget shifts |

### Learning Phase Best Practices
- [ ] Do not make changes during the learning phase — let the algorithm stabilize
- [ ] Set budgets high enough to generate required conversions within the window
- [ ] Use broader targeting at launch to give the algorithm room to explore
- [ ] Batch your changes — make all edits at once rather than incremental tweaks
- [ ] If CPA is 3x+ target during learning, consider pausing and restructuring
- [ ] Track "Learning" and "Learning Limited" statuses — the latter signals insufficient data
- [ ] Plan for 20–30% higher CPA during learning as a normal cost of optimization

### Learning Phase Budget Formula
```
Minimum daily budget = Target CPA x 5 (Google)
Minimum daily budget = Target CPA x 10 (Meta, TikTok)

Example: If target CPA = $50
  Google: $250/day minimum per campaign
  Meta:   $500/day minimum per ad set
```

## Portfolio Bid Strategies (Google Ads)

### What Are Portfolio Strategies?
Portfolio bid strategies apply a single automated bid strategy across multiple campaigns, allowing the algorithm to optimize holistically rather than per-campaign.

### Portfolio Strategy Types

| Strategy | How It Works | Best For |
|---|---|---|
| Portfolio tCPA | Averages CPA across campaigns | Multiple campaigns with same CPA goal |
| Portfolio tROAS | Averages ROAS across campaigns | E-commerce with varied product campaigns |
| Portfolio Max Clicks | Maximizes total clicks across campaigns | Traffic-focused multi-campaign setups |
| Portfolio Target Impression Share | Maintains impression share across campaigns | Brand defense across multiple brand terms |

### When to Use Portfolio Strategies
- [ ] 3+ campaigns sharing the same conversion goal
- [ ] Individual campaigns have low conversion volume (< 30/month)
- [ ] You want the system to shift budget toward best-performing campaigns
- [ ] Seasonal campaigns where volume fluctuates
- [ ] Brand campaigns where impression share consistency matters

### Portfolio Strategy Checklist
- [ ] Group campaigns with similar goals and conversion types
- [ ] Set a shared target (CPA or ROAS) that reflects the portfolio average
- [ ] Minimum 50 total conversions per month across the portfolio
- [ ] Monitor individual campaign performance — don't let one campaign starve
- [ ] Review and adjust targets quarterly based on business goals

## Bid Adjustments

### Adjustment Types and Ranges

| Dimension | Available On | Range | When to Use |
|---|---|---|---|
| Device (Mobile, Desktop, Tablet) | Google, Microsoft | -100% to +900% | Significant device performance gap |
| Location (Geo) | Google, Microsoft | -90% to +900% | Regional performance variation |
| Audience (RLSA, In-Market, etc.) | Google, Microsoft | -90% to +900% | High-value audience segments |
| Time of Day / Day of Week | Google, Microsoft | -90% to +900% | B2B (business hours), local businesses |
| Demographics (Age, Gender, Income) | Google, Microsoft | -90% to +900% | Clear demographic performance differences |
| Placement (websites, apps) | Meta (manual bidding) | Varies | Over/underperforming placements |

### Bid Adjustment Decision Framework

| Performance Gap | Recommended Adjustment | Review Period |
|---|---|---|
| Conv rate 50%+ higher | +20% to +50% | Wait for statistical significance (100+ clicks) |
| Conv rate 20–50% higher | +10% to +20% | 2–4 weeks of data |
| Conv rate within 20% | No adjustment | Normal variance |
| Conv rate 20–50% lower | -10% to -30% | 2–4 weeks of data |
| Conv rate 50%+ lower | -30% to -60% | Consider exclusion instead |
| Zero conversions, high spend | -100% (exclude) | After 3x CPA spend |

### Important Notes on Bid Adjustments + Smart Bidding
- **Smart bidding (tCPA, tROAS, Max Conversions) already adjusts bids** by device, location, time, audience, and more
- Layering manual bid adjustments on top of smart bidding creates **compounding effects** and can cause instability
- The only bid adjustment that works with smart bidding: **device -100%** (to fully exclude a device)
- For smart bidding campaigns, optimize through **targeting and audience signals**, not bid adjustments

## Manual vs Automated Bidding

### Comparison Matrix

| Factor | Manual Bidding | Automated Bidding |
|---|---|---|
| Control | Full — you set every bid | Limited — algorithm decides |
| Data requirement | Low (can work with few conversions) | High (30–50+ conversions/month) |
| Optimization speed | Slow (human-limited) | Fast (real-time auction signals) |
| Signal utilization | Limited to visible metrics | Uses 100+ signals per auction |
| Time investment | High (daily monitoring and adjustment) | Low (set strategy, monitor outcomes) |
| Best for | Low volume, strict compliance, testing | Scale, performance, efficiency |
| Risk | Under-optimization (missed signals) | Over-spending during learning phase |

### Transition Path: Manual to Automated
1. **Start with Manual CPC** — establish baseline CPA and conversion volume
2. **Accumulate 30+ conversions/month** — minimum data for automated bidding
3. **Switch to Maximize Conversions (no cap)** — let algorithm learn without constraints
4. **After 2–4 weeks, add tCPA** — set target at 10–20% above current average CPA
5. **Gradually tighten target** — reduce tCPA by 5–10% increments every 2 weeks
6. **Monitor for volume vs efficiency tradeoff** — tighter targets reduce volume

## Seasonality Adjustments

### Google Ads Seasonality Adjustments
- [ ] Use the Seasonality Adjustments tool in Google Ads for **short-term events** (1–7 days)
- [ ] Input expected conversion rate change (e.g., +30% for Black Friday)
- [ ] Set date range, device, and campaign scope
- [ ] The algorithm pre-adjusts bids for the event period and reverts afterward
- [ ] Not needed for gradual seasonal shifts — smart bidding learns those organically

### Seasonal Planning Calendar

| Season / Event | Typical Impact | Advance Planning |
|---|---|---|
| Q4 Holiday (Nov–Dec) | CPMs +30–80%, CVR +20–40% | Budget approved by September; creative by October |
| Black Friday / Cyber Monday | CPMs +50–100%, CVR +30–60% | Campaigns live 1–2 weeks early for learning |
| Back-to-School (Jul–Sep) | CPMs +10–20% | Plan by June |
| Valentine's Day / Mother's Day | Category-specific CPM spikes | 3–4 weeks advance |
| Post-Holiday (Jan) | CPMs drop 30–50%, opportunity for efficiency | Plan January campaigns in December |
| Industry-specific events | Varies | Map your vertical's seasonal calendar |

### Seasonal Budget Allocation Framework
```
Standard Month Budget:  100% (baseline)
Pre-Peak Month:         120–140% (build audiences, test creative)
Peak Month:             150–200% (maximize capture during high-intent period)
Post-Peak Month:        80–90% (efficiency gains, lower CPMs)
```

## Budget Pacing

### Pacing Models

| Model | Description | Best For |
|---|---|---|
| **Even pacing (standard)** | Spread budget evenly across the flight | Most campaigns; predictable delivery |
| **Accelerated pacing** | Spend as fast as possible | Limited-time offers, events, flash sales |
| **Front-loaded** | Heavy spend early, taper off | Product launches, awareness bursts |
| **Back-loaded** | Light spend early, ramp up | Sales events, building toward a deadline |
| **Dayparted** | Concentrate spend in specific hours | B2B (business hours), restaurants (meal times) |

### Pacing Monitoring Checklist
- [ ] Check daily spend vs expected daily pace (total budget / flight days)
- [ ] Alert threshold: +/-15% off pace for 3+ consecutive days
- [ ] Under-pacing fix: broaden targeting, increase bids, add placements
- [ ] Over-pacing fix: tighten targeting, reduce bids, add frequency caps
- [ ] Use automated rules or scripts for daily pacing alerts
- [ ] Account for weekday/weekend variance (B2B weekday heavy, B2C weekend heavy)

### Budget Pacing Formula
```
Expected daily spend = Total budget / Total campaign days
Actual pace % = (Spend to date / Expected spend to date) x 100

On pace:  95–105%
Slightly off: 85–95% or 105–115%
Action required: <85% or >115%
```

## Cross-Platform Bid Coordination

### Multi-Platform Budget Allocation

| Platform | Role in Media Mix | Budget Share (Typical) | Primary KPI |
|---|---|---|---|
| Google Search | Demand capture | 30–40% | CPA, ROAS |
| Meta Ads | Demand generation + retargeting | 20–30% | CPA, ROAS, CPL |
| YouTube / CTV | Awareness + consideration | 10–15% | CPV, VCR, Brand Lift |
| LinkedIn | B2B demand gen | 10–15% (B2B) | CPL, SQL rate |
| TikTok | Discovery + awareness | 5–15% | CPA, engagement |
| Programmatic Display | Retargeting + reach | 5–10% | CPM, viewability |

### Cross-Platform Optimization Strategy
- [ ] Establish unified conversion tracking (GA4, CDP, or attribution platform)
- [ ] Use consistent UTM taxonomy across all platforms
- [ ] Set platform-specific CPA/ROAS targets that roll up to blended goal
- [ ] Shift budget toward platforms with best incrementality (not just last-click)
- [ ] Run holdout tests per platform to measure true incremental impact
- [ ] Weekly cross-platform reporting to identify over/under-investment
- [ ] Account for attribution overlap — Google and Meta will both claim the same conversions

## Troubleshooting Guide

| Symptom | Likely Cause | Diagnosis | Fix |
|---|---|---|---|
| CPA spiked after bid strategy change | Learning phase reset | Check "Learning" status | Wait 2 weeks; revert if CPA > 3x target |
| Budget not spending (under-delivery) | Target too restrictive | Check impression share lost to rank | Raise tCPA/tROAS by 10–20% or broaden targeting |
| Spending too fast, poor CPA | Target too loose or algorithm chasing volume | Review conversion quality | Tighten tCPA, check for spam conversions, review search terms |
| "Learning Limited" status | Insufficient conversions | Need 50+ conversions in 7 days (Meta) | Consolidate ad sets, broaden audience, increase budget |
| Erratic daily spend | Algorithm exploring | Normal in first 7–14 days | Monitor weekly averages, not daily; adjust only if weekly CPA off |
| Good CPA but low volume | Target too aggressive | Impression share lost to budget/rank | Raise tCPA by 10%, increase budget, add keywords/audiences |
| High impression share but low conversions | Winning wrong auctions | Check search terms, audience overlap | Add negatives, refine audiences, check landing page conversion rate |
| Performance degradation over time | Audience fatigue, competitive pressure | Check frequency, auction insights | Refresh creative, expand audiences, test new channels |
| Portfolio strategy starving a campaign | Uneven performance distribution | Review per-campaign metrics | Consider removing underperformer from portfolio or adjusting structure |

### Bid Strategy Change Protocol
1. Document current performance (CPA, ROAS, volume, spend) as baseline
2. Make the change during a low-traffic period (Monday AM, not Friday PM)
3. Do not change anything else simultaneously (creative, targeting, budget)
4. Allow full learning phase before evaluating (2 weeks minimum)
5. Compare at the weekly level, not daily
6. Decision framework: if week 3 CPA is within 20% of target, continue; if 20–50% above, adjust target; if 50%+ above, revert and diagnose
