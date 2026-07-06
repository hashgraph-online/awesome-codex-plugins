# Review Strategy — Generation & Management

> Systematic framework for generating, managing, and leveraging customer reviews across every major platform. Reviews are the single highest-trust signal in purchase decisions — 93% of consumers say online reviews influence their buying behavior.

---

## Platform Review Landscape

| Platform | Primary Use | Avg. Star Threshold | Solicitation Allowed? | Review Gating Legal? |
|----------|-------------|--------------------|-----------------------|----------------------|
| Google Business | Local / B2C | 4.2+ | Yes (with guidelines) | No (violates policy) |
| Yelp | Local / Hospitality | 3.8+ | **No** (strictly prohibited) | No |
| G2 | B2B SaaS | 4.0+ | Yes (incentives OK) | No |
| Capterra | B2B SaaS | 4.0+ | Yes (gift cards OK) | No |
| Trustpilot | E-commerce / SaaS | 4.2+ | Yes (via invitations) | No (violates terms) |
| Amazon | E-commerce | 4.0+ | **Restricted** (Vine only) | No |
| Glassdoor | Employer Brand | 3.8+ | Yes (encourage, no coerce) | No |
| TripAdvisor | Travel / Hospitality | 4.0+ | Yes (reminder tools) | No |

---

## Platform-Specific Solicitation Rules

### Yelp — Strict Prohibition
- **Do NOT** ask customers for Yelp reviews — ever
- No "Find us on Yelp" signage that implies review requests
- **Allowed:** Yelp check-in offers, claiming your profile, responding to reviews
- Yelp's algorithm suppresses reviews from accounts with low activity; solicited reviews often get filtered

### Amazon — Vine & Guardrails
- Sellers **cannot** offer compensation for reviews (violates ToS, risks account suspension)
- Amazon Vine program: send products to trusted reviewers (enrollment fee applies)
- "Request a Review" button in Seller Central is the only compliant solicitation method
- No follow-up emails that include review requests with discount offers

### Google — Permissive with Limits
- Solicitation is allowed; review gating is not
- Cannot offer incentives for reviews
- Cannot set up review stations at your location on a single device (IP flagging)
- Can use NFC tap-to-review stands, QR codes, email/SMS follow-ups

### Trustpilot — Invitation System
- Must use Trustpilot's invitation tools for solicitation
- Cannot cherry-pick who receives invitations (must invite all or use automatic triggers)
- Service reviews and product reviews have separate flows

---

## Review Request Templates

### Email — Post-Purchase (Send 3-7 days after delivery/service)

**Subject Line Options:**
- "How did we do, {{first_name}}?"
- "Your feedback helps us improve"
- "Quick question about your recent {{product/service}}"

**Body:**
> Hi {{first_name}},
>
> Thanks for choosing {{company}}. We hope {{product/service}} is working well for you.
>
> Would you mind sharing your experience? It takes about 60 seconds and helps other customers make informed decisions.
>
> [Leave a Review → {{direct_review_link}}]
>
> Either way, if you have any questions or concerns, reply to this email and we'll take care of it.
>
> Thank you,
> {{sender_name}}

### SMS — Post-Purchase (Send 2-5 days after delivery/service)

> Hi {{first_name}}, thanks for your recent purchase from {{company}}! We'd love to hear how it went. Leave a quick review here: {{short_link}} — Reply STOP to opt out.

---

## Review Response Templates

### Positive Review (5 stars)
> Thank you so much, {{reviewer_name}}! We're glad {{specific detail from review}} met your expectations. Your feedback means a lot to the team. We look forward to serving you again.

### Neutral Review (3 stars)
> Hi {{reviewer_name}}, thank you for sharing your honest feedback. We appreciate that {{positive aspect mentioned}} worked well. We'd love to learn more about how we can improve {{area of concern}}. Could you reach out to us at {{support_email}} so we can make things right?

### Negative Review (1-2 stars)
> {{reviewer_name}}, we're sorry to hear about your experience with {{specific issue}}. This isn't the standard we hold ourselves to. We'd like to make this right — please contact {{name}} directly at {{phone/email}} so we can resolve this for you. Thank you for bringing this to our attention.

### Suspected Fake Review
> We take all feedback seriously, but we're unable to find a record matching this review in our system. If you've done business with us, please contact {{support_email}} with your order details so we can investigate and resolve any concerns.

---

## Review Management Workflow

| Step | Action | Frequency | Owner |
|------|--------|-----------|-------|
| 1 | Monitor all platforms via aggregator (Birdeye, Podium, ReviewTrackers) | Real-time alerts | Community Manager |
| 2 | Categorize incoming reviews (positive, neutral, negative, fake) | Within 2 hours | Community Manager |
| 3 | Respond to negative reviews | Within 4 hours (business hours) | Senior CM / Manager |
| 4 | Respond to positive reviews | Within 24 hours | Community Manager |
| 5 | Escalate legal/defamation concerns | Immediately | Legal / Director |
| 6 | Flag suspected fake reviews for platform removal | Within 24 hours | Community Manager |
| 7 | Log trends and recurring themes | Weekly | Marketing Analyst |
| 8 | Report review metrics to leadership | Monthly | Marketing Manager |

---

## Review Velocity Strategy

Review velocity — the rate at which new reviews arrive — is a ranking signal on Google and influences consumer trust on all platforms.

### Velocity Targets by Business Size

| Business Size | Monthly Review Target | Tactic Mix |
|--------------|----------------------|------------|
| Local SMB | 5-15 new reviews/month | Email + in-person ask + QR codes |
| Mid-Market | 15-50 new reviews/month | Automated email sequences + SMS + NFC |
| Enterprise | 50-200+ new reviews/month | CRM-triggered automation + post-support surveys + loyalty program integration |

### Velocity Acceleration Tactics
1. **Trigger-based automation:** Send review requests after positive support interactions (CSAT 4-5)
2. **Receipt/invoice integration:** Include review link on digital receipts
3. **QR code placement:** In-store, on packaging, on business cards
4. **Employee program:** Train frontline staff to mention reviews at point of sale
5. **Loyalty program tie-in:** Offer loyalty points (not for reviews — for sharing feedback)

---

## Handling Fake Reviews

### Identification Checklist
- [ ] Reviewer has no other review history or a suspicious profile
- [ ] Review contains no specific details about the product/service
- [ ] Language matches patterns seen in competitor attack campaigns
- [ ] Multiple negative reviews posted in a short time window
- [ ] Reviewer has never been a customer (no matching records)

### Removal Process by Platform

| Platform | Process | Typical Timeline |
|----------|---------|-----------------|
| Google | Flag via Google Business Profile → "Report review" | 5-14 days |
| Yelp | Report via Business Owner tools | 7-21 days |
| Trustpilot | Report with evidence via compliance team | 3-10 days |
| Amazon | Report via Seller Central → "Report abuse" | 7-14 days |
| G2 | Contact G2 support with evidence | 5-10 days |

### If Platform Refuses Removal
1. Respond publicly with a factual, professional reply
2. Bury the fake review with legitimate positive reviews (velocity strategy)
3. Consult legal counsel if review is defamatory and demonstrably false
4. Document everything for potential future disputes

---

## Review Analytics — KPIs to Track

| Metric | Definition | Benchmark |
|--------|-----------|-----------|
| Average Star Rating | Mean rating across all platforms | 4.2+ |
| Review Volume | Total reviews per month | Varies by industry |
| Review Velocity | New reviews per week | Steady or increasing |
| Response Rate | % of reviews responded to | 100% negative, 80%+ positive |
| Response Time | Average time to first response | < 4 hrs (negative), < 24 hrs (positive) |
| Sentiment Ratio | Positive : Neutral : Negative | 70:20:10 or better |
| Review-to-Revenue Correlation | Revenue impact per 0.1 star improvement | Track via attribution |

---

## Key Principle

> Never gate reviews. Never incentivize ratings. Never ignore criticism. The goal is volume, velocity, and authenticity — not perfection. A 4.6 with 500 reviews outperforms a 5.0 with 12 reviews every time.
