# Segmentation — RFM, Behavioral & Lifecycle Frameworks

## RFM Scoring Model

### Dimensions

| Dimension | Definition | Scoring (1-5) |
|-----------|-----------|---------------|
| **Recency** | How recently the customer made a purchase/action | 5 = last 7 days, 4 = 8-30 days, 3 = 31-90 days, 2 = 91-180 days, 1 = 180+ days |
| **Frequency** | How often they purchase/engage | 5 = 10+/year, 4 = 6-9, 3 = 3-5, 2 = 2, 1 = 1 |
| **Monetary** | Total spend or value generated | 5 = top 10%, 4 = 11-25%, 3 = 26-50%, 2 = 51-75%, 1 = bottom 25% |

### RFM Segment Mapping

| Segment | RFM Score | Description | Marketing Action |
|---------|-----------|-------------|-----------------|
| **Champions** | 5-5-5, 5-5-4 | Best customers, buy often, spend big | VIP treatment, exclusive access, referral asks |
| **Loyal** | 4-4-4, 5-4-3 | Consistent high-value customers | Loyalty rewards, upsell, cross-sell |
| **Potential Loyalists** | 5-3-3, 4-3-3 | Recent customers with growth potential | Nurture, onboarding, engagement programs |
| **New Customers** | 5-1-1, 5-1-2 | Just made first purchase | Welcome sequence, education, quick wins |
| **At Risk** | 2-4-4, 2-3-3 | Used to be good, slowing down | Win-back offers, re-engagement campaigns |
| **Hibernating** | 1-2-2, 1-1-1 | Long time since purchase, low value | Last-chance offers, sunset if unresponsive |
| **Can't Lose** | 1-5-5, 2-5-5 | Were top customers, now lapsing | Urgent win-back, personal outreach |

---

## Behavioral Segmentation

### Purchase Behavior Segments

| Segment | Criteria | Strategy |
|---------|----------|----------|
| First-time buyers | 1 purchase | Onboarding, second-purchase incentive |
| Repeat buyers | 2-4 purchases | Loyalty program, cross-sell |
| Power buyers | 5+ purchases | VIP program, advocacy, referral |
| Cart abandoners | Added but didn't buy | Abandonment emails, retargeting |
| Browse abandoners | Viewed but didn't add | Product recommendations, social proof |
| Discount buyers | Only buy with promotions | Reduce discount dependency gradually |

### Engagement Segments

| Segment | Criteria | Strategy |
|---------|----------|----------|
| Highly engaged | Opens emails, visits weekly, uses product daily | Upsell, community, advocacy |
| Moderately engaged | Opens some emails, visits monthly | Increase engagement, content nurture |
| Low engaged | Rarely opens, infrequent visits | Re-engagement campaign |
| Dormant | No activity in 60+ days | Win-back or sunset |

---

## Lifecycle Segmentation

| Stage | Definition | Entry Trigger | Exit Trigger | Marketing Focus |
|-------|-----------|---------------|-------------|----------------|
| **Prospect** | Known contact, no purchase | Form fill, signup | First purchase | Nurture, education, trust-building |
| **New Customer** | Recent first purchase | First purchase | 30 days or 2nd purchase | Onboarding, quick wins, satisfaction |
| **Active Customer** | Regular engagement/purchases | 2nd purchase or consistent usage | 90 days no activity | Cross-sell, upsell, loyalty |
| **At-Risk** | Engagement declining | 60 days declining trend | Re-engages or goes dormant | Win-back offers, check-in |
| **Dormant** | No activity for extended period | 90+ days no activity | Re-engages or unsubscribes | Last-chance campaigns, sunset path |
| **Churned** | Cancelled or completely lapsed | Cancellation or 180 days | Re-activates | Win-back with new value prop |
| **Advocate** | Actively promotes brand | Referral, review, UGC | Engagement declines | Reward, amplify, community |

---

## Segment-to-Action Mapping

| Segment | Email Frequency | Ad Targeting | Content Type | Offer Type |
|---------|----------------|-------------|-------------|-----------|
| New prospect | 2-3/week | Awareness + Education | Guides, webinars | Free resource, trial |
| Active lead | 1-2/week | Retargeting + Conversion | Case studies, demos | Trial, consultation |
| New customer | 1-2/week | Exclude from acquisition | Onboarding, tips | Expansion offers |
| Loyal customer | 1/week | Lookalike seed, exclude | Advanced content | VIP, early access |
| At-risk | 1-2/week | Win-back retargeting | Value reminders | Special offer, discount |
| Dormant | 1/month then sunset | Exclude | Re-engagement | Final discount, "we miss you" |

---

## Dynamic Segmentation Triggers

Real-time behavioral triggers that move users between segments:

| Trigger Event | From Segment | To Segment | Immediate Action |
|--------------|-------------|-----------|-----------------|
| First purchase | Prospect | New Customer | Start onboarding sequence |
| 2nd purchase within 30 days | New Customer | Active Customer | Cross-sell sequence |
| No login for 14 days | Active Customer | At-Risk | Re-engagement email |
| Viewed pricing page 3+ times | Prospect | High-Intent Lead | Sales alert + targeted offer |
| Left a review | Active Customer | Advocate | Thank + referral program invite |
| Cancelled subscription | Active Customer | Churned | Win-back sequence (24h delay) |
