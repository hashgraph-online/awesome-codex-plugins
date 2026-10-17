# Funnel Gap Analysis — Framework & Prioritization

## Gap Identification Methodology

### Data-Driven Analysis

1. **Pull funnel metrics** for each stage (volume, conversion rate, time-in-stage)
2. **Compare to benchmarks** from funnel-templates.md for your business model
3. **Calculate drop-off** between each stage: Drop-off % = 1 - (Stage N+1 / Stage N)
4. **Identify outliers**: Any stage with conversion rate >20% below benchmark is a gap
5. **Trend analysis**: Is any stage getting worse over time? (even if currently above benchmark)

### Qualitative Signals

- Customer feedback mentioning friction at specific stages
- Sales team reporting common objections or drop-off points
- Support tickets clustering around specific journey moments
- Session recordings showing user confusion or abandonment
- NPS/CSAT scores that drop at specific touchpoints

---

## Common Gap Patterns by Business Model

### B2B SaaS
| Gap Pattern | Symptom | Likely Cause |
|-------------|---------|-------------|
| Awareness gap | Low organic traffic, poor brand search volume | Weak content strategy, poor SEO |
| Activation gap | High signup rate, low product usage | Poor onboarding, unclear time-to-value |
| MQL→SQL gap | Marketing generates leads, sales rejects them | Misaligned lead scoring, wrong audience |
| Trial→Paid gap | Users try but don't convert | Pricing friction, insufficient value demonstration |
| Expansion gap | Customers stay but don't grow | No upsell triggers, feature awareness gap |

### eCommerce
| Gap Pattern | Symptom | Likely Cause |
|-------------|---------|-------------|
| Discovery gap | Low traffic despite good products | Distribution problem, poor channel mix |
| Browse→Cart gap | High traffic, low cart adds | Product-market fit, pricing, UX issues |
| Cart abandonment | 70%+ abandonment | Surprise costs, complex checkout, trust deficit |
| Repeat purchase gap | One-time buyers don't return | No retention program, poor post-purchase experience |

### B2B Services
| Gap Pattern | Symptom | Likely Cause |
|-------------|---------|-------------|
| Trust gap | Traffic but no inquiries | Insufficient social proof, thought leadership |
| Consultation gap | Leads inquire but don't book | Slow response, friction in booking process |
| Proposal gap | Many proposals, low win rate | Pricing, positioning, or proposal quality |

---

## Gap Severity Scoring

### ICE Framework (Impact × Confidence × Ease)

Score each identified gap on three dimensions (1-10):

| Dimension | What It Measures | Scoring Guide |
|-----------|-----------------|---------------|
| **Impact** | How much revenue/growth fixing this gap would unlock | 10 = >50% improvement, 5 = 10-25%, 1 = <5% |
| **Confidence** | How sure are we this is the real problem and our fix will work | 10 = data-backed, tested before, 5 = educated guess, 1 = speculation |
| **Ease** | How easy is it to implement the fix | 10 = same day, no dev, 5 = 1-2 weeks, 1 = months + engineering |

**ICE Score** = (Impact + Confidence + Ease) / 3

### Priority Tiers

| ICE Score | Priority | Action |
|-----------|----------|--------|
| 8-10 | P1 — Immediate | Fix this week |
| 6-7.9 | P2 — Near-term | Plan for next sprint/month |
| 4-5.9 | P3 — Backlog | Schedule when resources allow |
| <4 | P4 — Monitor | Track but don't invest yet |

---

## Gap-to-Action Mapping

| Gap Type | Recommended Tactics |
|----------|-------------------|
| **Awareness gap** | Content marketing, SEO, paid social, PR, influencer partnerships |
| **Consideration gap** | Comparison content, case studies, webinars, retargeting |
| **Trust gap** | Social proof, reviews, media coverage, security certifications |
| **Activation gap** | Onboarding optimization, in-app guidance, success milestones |
| **Conversion gap** | CRO, pricing optimization, urgency/scarcity, checkout simplification |
| **Retention gap** | Email nurture, loyalty programs, feature adoption campaigns |
| **Expansion gap** | Upsell triggers, usage-based alerts, customer success outreach |
| **Referral gap** | Referral programs, NPS follow-up, advocacy campaigns |

---

## Measurement Framework

### Before/After Tracking

For each gap fix, document:

1. **Baseline metric**: Stage conversion rate before the fix (2-4 weeks of data)
2. **Fix description**: Exactly what was changed
3. **Implementation date**: When the fix went live
4. **Post-fix metric**: Stage conversion rate after the fix (2-4 weeks of data)
5. **Statistical significance**: Was the change significant or within normal variance?
6. **Revenue impact**: Estimated revenue change from the conversion rate improvement

### Calculating Revenue Impact of a Gap Fix

```
Current monthly revenue: $X
Stage conversion rate (before): A%
Stage conversion rate (after): B%
Improvement multiplier: B/A

Estimated revenue uplift = $X × (B/A - 1) × [weight of that stage in overall funnel]
```

### Ongoing Funnel Health Monitoring

- **Weekly**: Check conversion rates at each stage, flag anomalies
- **Monthly**: Full funnel analysis, compare to benchmarks, update gap priorities
- **Quarterly**: Strategic funnel review, reassess architecture, plan next optimization cycle
