# Email Automation — Workflows & Triggers

## Trigger Taxonomy

| Trigger Type | Examples | Use Case |
|-------------|---------|----------|
| **Behavioral** | Page visit, form submit, link click, cart add, product view | Respond to user actions |
| **Time-based** | X days after signup, X days before renewal, anniversary | Lifecycle timing |
| **Attribute-based** | Segment change, lead score threshold, tag added | Profile changes |
| **Engagement** | Email opened, not opened in X days, clicked specific link | Email behavior |
| **Transactional** | Purchase made, subscription started, payment failed | Commerce events |
| **Predictive** | Churn risk score increase, predicted next purchase date | ML-based triggers |

---

## Common Automation Workflows

### Welcome Flow
```
Trigger: New subscriber / signup
→ Email 1 (immediate): Welcome + value delivery
→ Wait 2 days
→ Email 2: Quick-start guide
→ Wait 3 days
→ Email 3: Social proof / success story
→ Wait 4 days
→ Email 4: Feature highlight or tip
→ Wait 7 days
→ Email 5: Upgrade / next step CTA
→ Exit: Move to regular nurture
```

### Browse Abandonment
```
Trigger: Viewed product page, did NOT add to cart (within 1 hour)
→ Wait 2 hours
→ Email 1: "Still interested in [Product]?" + product image + reviews
→ Wait 24 hours
→ Check: Did they purchase? → Yes: Exit | No: Continue
→ Email 2: Related product recommendations
→ Exit
```

### Re-Engagement
```
Trigger: No email open or click for 60 days
→ Email 1: "We miss you" + what's new
→ Wait 7 days
→ Check: Engaged? → Yes: Return to active | No: Continue
→ Email 2: Exclusive offer or content
→ Wait 7 days
→ Check: Engaged? → Yes: Return to active | No: Continue
→ Email 3: "Last email unless you want to stay"
→ Wait 7 days
→ Check: Engaged? → Yes: Return to active | No: Suppress from marketing
```

---

## Dynamic Content Rules

| Rule Type | Logic | Example |
|-----------|-------|---------|
| **Segment-based** | Show different content per segment | Enterprise sees case study; SMB sees quick-start guide |
| **Behavioral** | Based on past actions | Show "upgrade" CTA to free users; "renew" to expiring |
| **Location** | Based on geography | Local event invites, regional offers |
| **Product interest** | Based on browsing/purchase history | Product recommendations matching viewed categories |
| **Lifecycle stage** | Based on customer stage | New customer sees onboarding; active sees advanced tips |

---

## Send Time Optimization

### Methods
1. **Historical analysis**: Send at times with highest open rates from past campaigns
2. **Per-subscriber optimization**: ML-based prediction of each subscriber's optimal time
3. **Time zone adjustment**: Send at target time in each subscriber's local time zone
4. **Day optimization**: Test different days, analyze by segment

### General Benchmarks
- B2B: Tuesday-Thursday, 9-11 AM local time
- B2C: Tuesday-Thursday, 10 AM or 7-9 PM local time
- eCommerce: Sunday evenings, Tuesday mornings (varies by industry)

---

## Frequency Capping

| Subscriber Segment | Max Emails/Week | Types |
|-------------------|----------------|-------|
| New subscriber (first 30 days) | 3-4 | Welcome + 1 marketing |
| Active engaged | 2-3 | Marketing + triggered |
| Moderately engaged | 1-2 | Marketing only |
| Low engagement | 1/2 weeks | Re-engagement only |
| Transactional-only | As needed | Receipts, notifications |

### Priority Rules
When multiple automations trigger for the same subscriber:
1. Transactional emails always send (receipts, confirmations)
2. Triggered automations take priority over scheduled campaigns
3. Most recent trigger takes priority if multiple trigger simultaneously
4. Always respect global frequency cap

---

## Automation Performance Metrics

| Metric | Target | Action if Below |
|--------|--------|----------------|
| Open rate | >25% | Test subject lines, send time, from name |
| Click rate | >3% | Improve content, CTA, personalization |
| Conversion rate | Varies by flow | Optimize offer, landing page, segmentation |
| Unsubscribe rate | <0.5% per email | Reduce frequency, improve targeting |
| Revenue per email | Increasing trend | Optimize product recommendations, offers |
| Automation completion rate | >60% | Check for friction points, improve content |
