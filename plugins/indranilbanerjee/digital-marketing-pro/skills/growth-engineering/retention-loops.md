# Retention Loops — Engagement & Churn Prevention

> Retention is the foundation of sustainable growth. No acquisition strategy survives a leaky bucket. This guide covers frameworks for building habit-forming products, predicting churn, and re-engaging lapsed users.

---

## Hook Model Framework

Nir Eyal's Hook Model explains how products create habitual usage through a four-step loop.

```
Trigger → Action → Variable Reward → Investment
   ↑                                      |
   └──────────────────────────────────────┘
```

### Step 1: Trigger

Triggers prompt the user to take action. They come in two forms.

| Trigger Type | Description | Examples |
|---|---|---|
| **External triggers** | Environmental cues that prompt action | Push notification, email, ad, CTA button, colleague mention |
| **Internal triggers** | Emotional states or routines that prompt action | Boredom (scroll Instagram), anxiety (check Slack), curiosity (open Reddit) |

**Goal:** Start with external triggers, then associate the product with internal triggers through repeated positive experiences.

### Step 2: Action

The simplest behavior done in anticipation of a reward. Follows BJ Fogg's behavior model: B = MAT (Behavior = Motivation + Ability + Trigger).

| Design Principle | Implementation |
|---|---|
| Reduce friction | Fewer clicks, faster load, simpler UI |
| Increase motivation | Clear value proposition at point of action |
| Ensure trigger visibility | Notification lands when user can act on it |

### Step 3: Variable Reward

The reward must be variable (unpredictable) to maintain engagement over time. Fixed rewards lose their power.

| Reward Type | Description | Product Example |
|---|---|---|
| Rewards of the Tribe | Social validation, acceptance, belonging | Likes, comments, follower counts |
| Rewards of the Hunt | Resources, information, deals | News feed content, search results, deal alerts |
| Rewards of the Self | Mastery, competence, completion | Leveling up, skill badges, streak counts |

### Step 4: Investment

The user puts something into the product that makes it more valuable over time and increases switching costs.

| Investment Type | Example | Retention Effect |
|---|---|---|
| Data | Saved preferences, history, files | More personalization, harder to leave |
| Content | Posts, documents, projects | Accumulated value stored in product |
| Reputation | Reviews, ratings, follower count | Social capital that cannot transfer |
| Skill | Learned workflows, keyboard shortcuts | Efficiency advantage in current product |
| Social connections | Team members, contacts, followers | Network locked into the platform |

---

## Churn Prediction Models

### Leading Indicators of Churn

Identify users at risk before they cancel. These signals typically appear 2-4 weeks before churn.

| Signal Category | Specific Indicators | Risk Level |
|---|---|---|
| **Usage decline** | Login frequency drops 40%+, session duration decreases, fewer core actions | High |
| **Feature disengagement** | Stops using advanced features, reverts to basic usage only | Medium-High |
| **Support signals** | Multiple unresolved tickets, negative CSAT scores, complaint escalation | High |
| **Billing signals** | Failed payment, downgrade inquiry, cancellation page visit | Critical |
| **Team signals** | Admin account goes inactive, seat count decreases, key user leaves | High |
| **Engagement signals** | Stops opening emails, ignores in-app messages, unsubscribes from updates | Medium |
| **Competitive signals** | Visits competitor pricing pages (if tracked), mentions competitors in support | Medium-High |

### Churn Risk Scoring Model

| Factor | Weight | Score Range | Scoring Method |
|---|---|---|---|
| Login frequency trend (14-day) | 25% | 0-100 | 100 if stable/growing, 0 if >60% decline |
| Core feature usage (14-day) | 20% | 0-100 | Based on actions vs historical average |
| Support ticket sentiment | 15% | 0-100 | NLP sentiment analysis on recent tickets |
| Days since last login | 15% | 0-100 | 100 if <3 days, 50 if 3-7, 25 if 7-14, 0 if >14 |
| Contract/billing status | 10% | 0-100 | 100 if healthy, 0 if payment failed or cancel page visited |
| Onboarding completion | 10% | 0-100 | Percentage of onboarding steps completed |
| NPS / CSAT score | 5% | 0-100 | Latest survey response normalized to 0-100 |

**Risk Tiers:**
- 80-100: Healthy — nurture and upsell
- 60-79: Monitor — proactive check-in
- 40-59: At risk — intervention required
- 0-39: Critical — immediate personal outreach

---

## Win-Back Sequences

### Email Win-Back Flow

| Email | Timing After Churn | Subject Line Approach | Content Strategy |
|---|---|---|---|
| 1 | Day 1 | "We're sorry to see you go" | Ask for feedback, offer help resolving issues |
| 2 | Day 7 | "Here's what you're missing" | Highlight new features or improvements since they left |
| 3 | Day 14 | "We've made changes based on your feedback" | Show specific improvements relevant to their churn reason |
| 4 | Day 30 | "Come back with [X% discount / free month]" | Time-limited incentive to return |
| 5 | Day 60 | "A lot has changed at [Product]" | Major update roundup, no hard sell |
| 6 | Day 90 | "Last chance: special offer for returning customers" | Final incentive, then move to quarterly nurture |

### Win-Back Tactics by Churn Reason

| Churn Reason | Win-Back Approach | Offer |
|---|---|---|
| Price / budget | Downgrade option, annual discount, pause subscription | 20-30% discount or free month |
| Missing feature | Notify when feature ships, invite to beta | Early access to requested feature |
| Poor experience | Personal apology from leadership, dedicated support | White-glove onboarding, dedicated CSM |
| Switched to competitor | Competitive comparison content, migration assistance | Free migration service, extended trial |
| No longer needed | Stay in touch with value content, seasonal re-engagement | Free tier to maintain relationship |
| Bad onboarding | Offer guided setup session, improved onboarding flow | 1-on-1 onboarding call with product expert |

---

## Cohort Analysis Methodology

### Setting Up Cohort Analysis

```
Cohort Definition: Group users by sign-up week or month
Metric: Retention rate (% of cohort still active in period N)
Periods: Week 0, Week 1, Week 2, ... Week 12 (or Month 0-12)
```

### Cohort Retention Table Template

| Cohort | Week 0 | Week 1 | Week 2 | Week 4 | Week 8 | Week 12 |
|---|---|---|---|---|---|---|
| Jan W1 (500 users) | 100% | 45% | 32% | 22% | 18% | 15% |
| Jan W2 (600 users) | 100% | 48% | 35% | 25% | 20% | 17% |
| Jan W3 (550 users) | 100% | 52% | 38% | 28% | 23% | 20% |

### What to Look For

| Pattern | Interpretation | Action |
|---|---|---|
| Retention curve flattens | Users who survive early weeks tend to stick | Focus on improving early retention (Week 1-2) |
| Recent cohorts retain better | Product or onboarding improvements are working | Continue iterating on what changed |
| Recent cohorts retain worse | Something broke — regression, quality issue, wrong audience | Investigate recent changes, review acquisition sources |
| Sharp drop at specific week | Users hit a wall at that point in their journey | Map user journey to that week, identify friction |
| One segment retains much better | You have found your ideal customer profile | Double down on acquiring that segment |

---

## Habit Loop Design

### Daily Active Usage Checklist

Design your product to support daily habits.

- [ ] There is a clear daily use case (not just a weekly/monthly tool)
- [ ] Users receive a meaningful trigger each day (notification, email digest, dashboard)
- [ ] The first action upon opening the product takes less than 5 seconds
- [ ] Variable content or data refreshes daily (new insights, updated feeds, fresh tasks)
- [ ] Completing the core action delivers immediate visible feedback
- [ ] Users invest something with each session (data, content, preferences)
- [ ] Streak or consistency tracking is visible (optional but powerful)
- [ ] Social elements create accountability (team visibility, shared goals)

### Habit Formation Timeline

| Phase | Duration | User Behavior | Product Role |
|---|---|---|---|
| Learning | Days 1-7 | Exploring, evaluating, deciding | Hand-hold through activation, demonstrate value |
| Practicing | Days 8-21 | Using with conscious effort, building routine | Reinforce triggers, celebrate progress |
| Habituation | Days 22-60 | Usage becomes automatic, part of workflow | Reduce friction further, introduce advanced features |
| Mastery | Days 60+ | Power user, advocate, invested | Expansion opportunities, referral prompts, community |

---

## Re-Engagement Triggers

### Trigger Types and Timing

| Trigger | Channel | Timing | Content |
|---|---|---|---|
| Inactivity nudge | Email | 3 days without login | "Your [project/task/data] is waiting for you" |
| Social trigger | Push / Email | When a teammate takes action | "Alex commented on your document" |
| Value trigger | Email | Weekly | Personalized digest of insights, metrics, or updates |
| Achievement trigger | In-app + Email | Upon milestone | "You're 80% to your goal — keep going" |
| Content trigger | Email | When new relevant content is published | "New template in your category" |
| Feature trigger | In-app + Email | When relevant new feature ships | "New: the feature you requested is live" |
| External trigger | Push | Calendar-based or event-based | "Your report is ready for Monday's meeting" |
| FOMO trigger | Email / Push | When peers are active | "Your team completed 15 tasks this week" |

### Re-Engagement Priority Matrix

| User Segment | Days Inactive | Priority | Approach |
|---|---|---|---|
| High-value, recently lapsed | 3-7 days | Critical | Personal outreach, in-app message, email |
| High-value, moderately lapsed | 7-30 days | High | Win-back email sequence, phone call from CSM |
| Low-value, recently lapsed | 3-7 days | Medium | Automated nudge email, push notification |
| Low-value, moderately lapsed | 7-30 days | Low | Automated email sequence, no manual effort |
| Any segment, long-term lapsed | 30+ days | Evaluate | Cost-benefit analysis — may not be worth pursuing |

---

## Retention Benchmarks by Business Model

### Monthly Retention (% active after N months)

| Business Model | Month 1 | Month 3 | Month 6 | Month 12 | Notes |
|---|---|---|---|---|---|
| B2B SaaS (SMB) | 70-80% | 55-65% | 45-55% | 35-45% | Higher if annual contracts |
| B2B SaaS (Enterprise) | 90-95% | 85-92% | 80-88% | 75-85% | Multi-year contracts stabilize |
| Consumer Subscription | 60-70% | 40-50% | 30-40% | 20-30% | Highly variable by category |
| Mobile App (Social) | 25-35% | 12-18% | 8-12% | 5-8% | Day 1 retention: 25-40% |
| Mobile App (Utility) | 30-40% | 18-25% | 12-18% | 8-12% | Higher if daily use case exists |
| E-commerce (Repeat Purchase) | 25-35% | 15-22% | 10-15% | 8-12% | Measured by repeat purchase |
| Marketplace | 30-40% | 20-30% | 15-22% | 10-18% | Supply-side retains better than demand |

### Net Revenue Retention Benchmarks (B2B SaaS)

| NRR Range | Assessment | Examples |
|---|---|---|
| >130% | Elite — expansion significantly outpaces churn | Snowflake, Twilio, Datadog |
| 110-130% | Strong — healthy expansion motion | HubSpot, Slack, Zoom |
| 100-110% | Acceptable — expansion roughly offsets churn | Most mature B2B SaaS |
| 90-100% | Concerning — slight net contraction | Churn problem emerging |
| <90% | Critical — revenue is shrinking from existing customers | Urgent retention intervention needed |

---

## Customer Health Scoring

### Health Score Components

| Component | Weight | Data Source | Scoring |
|---|---|---|---|
| Product usage depth | 25% | Product analytics | Features used / Total features available |
| Usage frequency | 20% | Product analytics | Actual logins / Expected logins for plan |
| Support health | 15% | Help desk | Inverse of open tickets + sentiment |
| Relationship depth | 15% | CRM | Number of stakeholders engaged, executive sponsor |
| Contract value trend | 10% | Billing system | Growing, stable, or declining |
| Onboarding progress | 10% | Onboarding tracker | % of implementation milestones completed |
| Survey sentiment | 5% | NPS / CSAT tool | Latest survey score |

### Health Score Actions

| Health Score | Label | Color | Action |
|---|---|---|---|
| 85-100 | Thriving | Green | Upsell/expand, request referral, case study candidate |
| 70-84 | Healthy | Light Green | Standard check-ins, feature adoption nudges |
| 50-69 | Neutral | Yellow | Proactive outreach, usage review call, training offer |
| 30-49 | At Risk | Orange | Escalate to CSM, executive check-in, create success plan |
| 0-29 | Critical | Red | Immediate intervention, executive-to-executive call, save offer |

### Health Score Review Cadence

- [ ] Automated alerts for any account dropping below 50 (immediate)
- [ ] Weekly review of all accounts in Yellow or below by CS team
- [ ] Monthly health score trend analysis across full customer base
- [ ] Quarterly correlation analysis: health score vs actual churn outcomes (calibrate model)
- [ ] Semi-annual model refinement based on prediction accuracy

---

*Retention is not a feature. It is the cumulative result of delivering consistent value, building habits, and catching problems before users give up. Every percentage point of improved retention compounds into dramatically better unit economics.*
