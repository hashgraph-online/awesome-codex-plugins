# Product-Led Growth — Strategy & Frameworks

> PLG is a go-to-market strategy where the product itself drives acquisition, expansion, and retention. Users experience value before committing budget.

---

## PLG Flywheel

The PLG engine follows a four-stage flywheel. Each stage feeds the next.

```
Value Delivery → Habit Formation → Expansion → Advocacy
      ↑                                          |
      └──────────────────────────────────────────┘
```

| Stage | Objective | Key Lever | Example |
|---|---|---|---|
| Value Delivery | Get user to "aha moment" fast | Frictionless onboarding | Slack — send first message in <2 min |
| Habit Formation | Embed product into daily workflow | Triggers + variable rewards | Notion — daily workspace opens |
| Expansion | Grow revenue within accounts | Usage-based pricing, seat expansion | Figma — designer invites developer |
| Advocacy | Turn users into acquisition channels | Referral loops, social proof | Calendly — every invite link = marketing |

---

## Freemium vs Free Trial Decision Tree

Use this framework to select the right model for your product.

| Factor | Favors Freemium | Favors Free Trial |
|---|---|---|
| Time-to-value | Long (user needs weeks to see ROI) | Short (value apparent within days) |
| Marginal cost per user | Near zero | Meaningful infrastructure cost |
| Network effects | Strong (more users = more value) | Weak or absent |
| Product complexity | Low — self-explanatory UI | High — requires setup, training |
| Competitive landscape | Crowded — need to remove risk | Differentiated — value is clear |
| Virality potential | High (free users spread product) | Low (usage is private/internal) |
| Average deal size | Low ACV (<$5K/yr) | High ACV (>$15K/yr) |
| Sales involvement | Minimal — self-serve dominant | Required — consultative sale |

**Hybrid approach:** Offer freemium for individuals and free trials for team/enterprise tiers. This captures both bottoms-up adoption and top-down evaluation.

---

## Activation Metric Identification

Activation is the single most important PLG metric. It defines the moment a user first experiences meaningful value.

### How to Find Your Activation Metric

1. **Pull behavioral data** — Export event logs for the first 7-14 days of all users
2. **Segment by outcome** — Split users into retained (active at Day 30+) vs churned
3. **Compare behaviors** — Identify actions that retained users performed at significantly higher rates
4. **Rank by correlation** — Find the action with the strongest correlation to retention
5. **Validate causation** — Run an experiment: guide new users toward that action and measure retention lift
6. **Set the threshold** — Define the minimum frequency or depth (e.g., "created 3 projects in first 7 days")

### Activation Metric Examples

| Product | Activation Metric | Threshold |
|---|---|---|
| Slack | Messages sent in a channel | 2,000 team messages |
| Dropbox | File saved in Dropbox folder | 1 file in first session |
| HubSpot | Contacts imported + email sent | Within first 7 days |
| Zoom | Hosted a meeting with 2+ participants | First 48 hours |
| Figma | Created and shared a design file | First 7 days |

---

## PQL (Product-Qualified Lead) Scoring Model

PQLs replace MQLs in PLG. A PQL is a user whose product behavior signals buying intent.

### PQL Scoring Components

| Signal Category | Weight | Examples |
|---|---|---|
| Activation completion | 25% | Completed onboarding, hit aha moment |
| Usage depth | 25% | Features used, frequency, session duration |
| Usage breadth | 15% | Number of team members active, departments involved |
| Growth signals | 20% | Seat additions, hitting plan limits, API usage |
| Firmographic fit | 15% | Company size, industry, tech stack match |

### Scoring Tiers

| Tier | Score Range | Action |
|---|---|---|
| Hot PQL | 80-100 | Sales outreach within 24 hours |
| Warm PQL | 60-79 | Automated nurture + contextual in-app upgrade prompts |
| Developing PQL | 40-59 | Product-led nurture sequences, feature discovery nudges |
| Early PQL | 0-39 | Onboarding optimization, activation campaigns |

---

## Self-Serve Onboarding Optimization

### Onboarding Checklist

- [ ] Time-to-first-value is under 5 minutes
- [ ] Sign-up requires no more than 3 fields (email, name, password — or SSO)
- [ ] Welcome flow asks 1-2 segmentation questions to personalize experience
- [ ] Empty states include templates, sample data, or guided actions
- [ ] Progress indicators show completion status
- [ ] Tooltips and contextual help are triggered by user behavior, not timers
- [ ] Email sequence supplements in-app guidance (Day 0, 1, 3, 7)
- [ ] Users can invite teammates before completing onboarding
- [ ] Mobile experience is functional even if desktop is primary
- [ ] Exit points offer help (chat, docs, video) before abandonment

### Onboarding Anti-Patterns

| Anti-Pattern | Why It Hurts | Fix |
|---|---|---|
| Feature tour on first login | Overwhelms user before they have context | Defer tours until relevant feature is needed |
| Mandatory profile completion | Adds friction before value delivery | Make optional, ask progressively |
| No segmentation | Generic experience misses user needs | Ask role/goal upfront, customize flow |
| Long email verification loop | Delays activation by hours or days | Allow limited access immediately, verify later |
| Hiding the upgrade path | Users can't self-serve to paid | Show pricing contextually at limit moments |

---

## PLG Metrics Dashboard

### Primary Metrics

| Metric | Formula | Benchmark (B2B SaaS) |
|---|---|---|
| Activation Rate | Activated users / Sign-ups | 20-40% |
| Time-to-Value (TTV) | Median time from sign-up to activation | <5 minutes (ideal), <24 hours (acceptable) |
| Free-to-Paid Conversion | Paid users / Free users | 2-5% (freemium), 10-25% (free trial) |
| Expansion Revenue (% of ARR) | Expansion MRR / Starting MRR | >30% Net Revenue Retention |
| Viral Coefficient (K-factor) | Avg invites per user x invite conversion rate | >0.5 (good), >1.0 (viral) |
| Revenue Per User (RPU) | Total revenue / Active users | Varies — track trend over time |
| Natural Rate of Growth (NRG) | Annual growth rate from organic + PLG channels | >50% = strong PLG motion |

### Cohort Tracking

Track these for each weekly or monthly sign-up cohort:

- [ ] Day 1, Day 7, Day 30, Day 90 retention
- [ ] Activation rate within first 7 days
- [ ] Median time-to-activation
- [ ] Free-to-paid conversion by Day 30, 60, 90
- [ ] Expansion revenue generated by Day 180
- [ ] Referrals generated per cohort

---

## PLG for Different Business Models

| Business Model | PLG Approach | Key Challenge | Example |
|---|---|---|---|
| Horizontal SaaS | Freemium + viral sharing | Activation across many use cases | Notion, Airtable |
| Vertical SaaS | Free trial + guided setup | Domain-specific onboarding required | Gusto, Procore |
| API / Developer Tools | Free tier + usage-based pricing | Docs and DX are the product | Stripe, Twilio |
| Marketplace / Platform | Free buyer side, monetize supply | Cold start problem | Airbnb, Upwork |
| Infrastructure | Free tier with generous limits | Expansion triggers at scale | AWS, Vercel |
| Collaboration Tools | Free for small teams, paid at scale | Must reach team-level adoption | Slack, Figma |

### PLG + Sales-Assist Hybrid

Most successful PLG companies add sales as they scale. The model evolves:

```
Stage 1: Pure self-serve (0 → $1M ARR)
Stage 2: Self-serve + inbound sales for large accounts ($1M → $10M ARR)
Stage 3: PLG-qualified pipeline feeds AE team ($10M → $50M ARR)
Stage 4: Full hybrid — PLG for SMB, sales-led for enterprise ($50M+ ARR)
```

### Implementation Priority

| Priority | Action | Impact |
|---|---|---|
| 1 | Define and instrument activation metric | Foundation for all PLG |
| 2 | Reduce time-to-value to under 5 minutes | Directly lifts conversion |
| 3 | Build PQL scoring and alerting | Connects product usage to revenue |
| 4 | Implement in-app upgrade prompts at limit moments | Captures expansion intent |
| 5 | Add viral loops (invites, sharing, embedding) | Compounds growth over time |
| 6 | Launch referral program for activated users | Reduces CAC systematically |

---

*PLG compounds because every user is a potential acquisition channel, every team is an expansion opportunity, and every integration deepens retention. The product is the growth engine.*
