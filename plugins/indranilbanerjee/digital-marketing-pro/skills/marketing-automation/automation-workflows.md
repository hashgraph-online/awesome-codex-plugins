# Automation Workflows Reference

Comprehensive reference for designing, building, and optimizing marketing automation workflows across platforms and business models.

---

## Trigger Types

Every automation workflow begins with a trigger — the event or condition that enrolls a contact into the flow.

### Time-Based Triggers
- **Date-based**: Enrollment date, subscription anniversary, contract renewal date, birthday
- **Delay-based**: X days after signup, X hours after last purchase, X weeks since last engagement
- **Scheduled**: Weekly digest, monthly recap, quarterly review reminder
- **Best for**: Lifecycle campaigns, recurring communications, anniversary/renewal workflows

### Event-Based Triggers
- **Form submission**: Lead magnet download, demo request, contact form, webinar registration
- **Purchase event**: First purchase, repeat purchase, high-value order, specific product/category
- **Account event**: Signup, trial start, plan upgrade, plan downgrade, cancellation
- **Best for**: Immediate-response workflows where timing sensitivity is high

### Behavioral Triggers
- **Email engagement**: Opens, clicks, replies, forwards, or lack thereof
- **Website behavior**: Page visit (especially pricing, comparison, case study pages), session duration, scroll depth
- **Product usage**: Feature activation, usage milestone, inactivity, approaching usage limit
- **Content consumption**: Blog reads, video views, podcast listens, resource downloads
- **Best for**: Intent-based workflows that respond to prospect signals

### Conditional Triggers
- **Score threshold**: Lead score crosses MQL or SQL threshold
- **Property change**: Job title change, company size change, lifecycle stage change
- **List membership**: Added to or removed from a specific segment or list
- **Deal stage change**: Opportunity created, moved to negotiation, closed-won, closed-lost
- **Best for**: CRM-driven workflows and lifecycle stage transitions

### Hybrid Triggers
- **Compound conditions**: Behavioral trigger AND score threshold (e.g., visited pricing page AND score > 50)
- **Time-bounded behavior**: Specific action within a time window (e.g., 3 page visits in 7 days)
- **Negative triggers**: Absence of expected behavior within a window (e.g., no login within 14 days of signup)
- **Best for**: Sophisticated workflows that require multiple signals before activation

---

## Workflow Patterns

### 1. Welcome Series

| Element | Detail |
|---|---|
| **Trigger** | New subscriber, account signup, or first form submission |
| **Goal** | Orient, build trust, set expectations, drive first meaningful action |
| **Steps** | 3-5 emails over 7-14 days |
| **Timing** | Email 1: immediate. Email 2: day 2. Email 3: day 5. Email 4: day 8. Email 5: day 12. |
| **Exit conditions** | Completed series, unsubscribed, or converted to next lifecycle stage |
| **Success metrics** | Open rate >50%, click rate >15%, completion rate >60%, first action rate |

**Sequence structure:**
1. **Welcome + value delivery** (immediate) — Thank them, deliver promised asset, set expectations for what comes next
2. **Brand story + social proof** (day 2) — Who you are, who you serve, proof it works
3. **Quick win content** (day 5) — Actionable tip or resource they can use immediately
4. **Feature/benefit deep dive** (day 8) — Showcase your primary value proposition with specifics
5. **Soft CTA** (day 12) — Invite to next step (demo, trial, purchase, consultation)

### 2. Abandoned Cart Recovery

| Element | Detail |
|---|---|
| **Trigger** | Cart created but checkout not completed within 1 hour |
| **Goal** | Recover abandoned revenue |
| **Steps** | 3 emails + optional SMS over 72 hours |
| **Timing** | Email 1: 1 hour. Email 2: 24 hours. SMS (optional): 36 hours. Email 3: 72 hours. |
| **Exit conditions** | Purchase completed, cart emptied, or unsubscribed |
| **Success metrics** | Recovery rate 5-15%, revenue recovered, AOV of recovered carts |

**Sequence structure:**
1. **Reminder** (1 hour) — "You left something behind." Show cart contents. No discount.
2. **Urgency + social proof** (24 hours) — Reviews, stock scarcity, or shipping deadline. Still no discount.
3. **SMS nudge** (36 hours, optional) — Brief "Still thinking it over?" with cart link
4. **Incentive** (72 hours) — Discount or free shipping only as last resort. If margin allows, 10-15% off.

**Critical rule**: Never train customers to expect discounts by offering incentives in email 1. Start with value, escalate to urgency, and use discounts only as a final recovery attempt.

### 3. Re-Engagement (Win-Back)

| Element | Detail |
|---|---|
| **Trigger** | No email opens or clicks in 60-90 days (B2C) or 90-120 days (B2B) |
| **Goal** | Reactivate dormant contacts or confirm they should be suppressed |
| **Steps** | 3-4 emails over 21-30 days |
| **Timing** | Email 1: day 0. Email 2: day 7. Email 3: day 14. Email 4 (sunset): day 21-30. |
| **Exit conditions** | Re-engaged (opened/clicked), unsubscribed, or completed sunset (moved to suppressed) |
| **Success metrics** | Reactivation rate 5-12%, list cleaned of truly inactive contacts |

**Sequence structure:**
1. **"We miss you"** — Highlight what they are missing, new features, or popular content since they disengaged
2. **Best content** — Send your highest-performing content piece to maximize re-engagement chance
3. **Preference update** — Ask if they want to change frequency or topics (give control, not just unsubscribe)
4. **Sunset warning** — "We will stop emailing you unless you click here." Remove non-responders from active list.

**Critical rule**: Do not keep emailing truly inactive contacts. They damage sender reputation. The sunset email is not optional — it is deliverability hygiene.

### 4. Post-Purchase Follow-Up

| Element | Detail |
|---|---|
| **Trigger** | Purchase completed |
| **Goal** | Reduce buyer's remorse, drive product adoption, encourage review, create repeat buyer |
| **Steps** | 4-6 emails over 30-60 days |
| **Timing** | Email 1: immediate. Email 2: day 3. Email 3: day 7-10. Email 4: day 14. Email 5: day 30. Email 6: day 45-60. |
| **Exit conditions** | Completed series or made second purchase (move to loyalty track) |
| **Success metrics** | Review rate, NPS response, repeat purchase rate, support ticket rate |

**Sequence structure:**
1. **Order confirmation + expectations** (immediate) — Confirm purchase, set delivery expectations, provide tracking
2. **Getting started** (day 3) — How to use the product, setup guides, tips for first use
3. **Check-in** (day 7-10) — "How is it going?" Link to support if needed
4. **Review request** (day 14) — Ask for review/rating once they have had time to use it
5. **Cross-sell/upsell** (day 30) — Complementary products based on purchase
6. **Replenishment or loyalty** (day 45-60) — Reorder reminder (consumables) or loyalty program invite

### 5. Lead Nurture (B2B)

| Element | Detail |
|---|---|
| **Trigger** | Lead created (form fill, content download, webinar registration) but not yet MQL |
| **Goal** | Educate, build trust, and move lead toward MQL threshold |
| **Steps** | 5-8 emails over 4-8 weeks |
| **Timing** | Every 5-7 days for B2B (less frequent than B2C) |
| **Exit conditions** | MQL score reached, meeting booked, unsubscribed, or disqualified |
| **Success metrics** | MQL conversion rate, time to MQL, content engagement rates |

**Sequence structure:**
1. **Value delivery** — Deliver the promised content, introduce who you are
2. **Problem education** — Expand on the pain point, share industry data
3. **Solution framework** — How problems like theirs get solved (methodology, not product pitch)
4. **Social proof** — Case study or customer story relevant to their industry/size
5. **Deep dive content** — Webinar, guide, or report that demonstrates expertise
6. **Comparison/evaluation** — Help them evaluate options (including yours) fairly
7. **Soft CTA** — Offer a consultation, demo, or assessment
8. **Direct CTA** — Specific next step with urgency or value-add

### 6. SaaS Onboarding

| Element | Detail |
|---|---|
| **Trigger** | Trial started or account created |
| **Goal** | Drive activation (reach "aha moment"), reduce time-to-value, convert trial to paid |
| **Steps** | 5-7 emails over trial period (7-30 days) |
| **Timing** | Email 1: immediate. Then based on activation milestones + time-based fallbacks. |
| **Exit conditions** | Converted to paid, trial expired, or account deleted |
| **Success metrics** | Activation rate, feature adoption, trial-to-paid conversion rate |

**Sequence structure:**
1. **Welcome + quick start** (immediate) — Shortest path to first value. One action to complete.
2. **Activation milestone 1** (day 1-2) — Guide to completing the first key action
3. **Feature highlight** (day 3-5) — Showcase the feature that correlates highest with conversion
4. **Social proof** (day 5-7) — Customer success story of similar user/company
5. **Advanced tips** (day 7-10) — Power user features, integrations, team collaboration
6. **Conversion CTA** (3-5 days before trial end) — Upgrade prompt with plan comparison
7. **Last chance** (day before expiration) — Final conversion push, limited-time offer if appropriate

**Branch logic**: If user completes activation milestones early, skip educational emails and move to conversion track. If inactive after day 3, trigger a re-engagement branch.

### 7. Win-Back (Churned Customer)

| Element | Detail |
|---|---|
| **Trigger** | Subscription cancelled or no purchase in X days (2x average purchase cycle) |
| **Goal** | Recover churned customers |
| **Steps** | 3-5 emails over 30-60 days |
| **Timing** | Email 1: 3 days post-churn. Email 2: 14 days. Email 3: 30 days. Email 4: 45 days. Email 5: 60 days. |
| **Exit conditions** | Reactivated, unsubscribed, or completed series (move to long-term dormant) |
| **Success metrics** | Win-back rate 5-15%, reactivation revenue |

### 8. Feedback Collection

| Element | Detail |
|---|---|
| **Trigger** | Post-interaction event (purchase, support ticket resolved, onboarding complete, event attended) |
| **Goal** | Collect NPS, CSAT, or product feedback |
| **Steps** | 2-3 emails over 7-10 days |
| **Timing** | Email 1: 1-3 days post-event. Email 2: 5-7 days. Email 3 (thank you): immediate after response. |
| **Exit conditions** | Survey completed or series finished |
| **Success metrics** | Response rate >15%, NPS score, actionable feedback volume |

### 9. Anniversary/Birthday

| Element | Detail |
|---|---|
| **Trigger** | Date-based: customer anniversary, birthday, or signup anniversary |
| **Goal** | Build loyalty, drive engagement, create a purchase occasion |
| **Steps** | 1-2 emails |
| **Timing** | Email 1: on the day (or 1-3 days before). Email 2: reminder 3-5 days after if offer unused. |
| **Exit conditions** | Offer redeemed, expired, or unsubscribed |
| **Success metrics** | Redemption rate, revenue generated, engagement lift |

### 10. Subscription Renewal

| Element | Detail |
|---|---|
| **Trigger** | Subscription renewal date approaching (30-60 days out) |
| **Goal** | Retain subscriber, reduce involuntary churn, upsell to annual |
| **Steps** | 3-5 emails over 30-45 days |
| **Timing** | Email 1: 30-45 days before. Email 2: 14 days before. Email 3: 3 days before. Email 4: renewal day. Email 5: post-renewal/lapsed. |
| **Exit conditions** | Renewed, cancelled, or payment failed (move to dunning workflow) |
| **Success metrics** | Renewal rate, voluntary churn rate, annual plan upgrade rate |

---

## Decision Logic & Branching

### If/Then Branching Patterns

**Engagement-based branching:**
```
IF opened email 1 → send content-focused email 2
IF did NOT open email 1 → resend with new subject line after 48 hours
  IF still no open → send SMS (if consent exists) or skip to email 3
```

**Score-based branching:**
```
IF lead score >= 75 → exit nurture, trigger MQL handoff workflow
IF lead score 50-74 → continue nurture with middle-funnel content
IF lead score < 50 → continue nurture with top-funnel educational content
```

**Behavior-based branching:**
```
IF visited pricing page → fast-track to demo offer email
IF downloaded case study → send related customer success story
IF attended webinar → send on-demand recording + consultation offer
IF no engagement in 30 days → move to re-engagement branch
```

### Engagement Gates

An engagement gate pauses a sequence until the contact demonstrates engagement. This prevents sending deeper content to contacts who are not reading earlier messages.

**Gate logic:**
```
Send email 1 → Wait 3 days
  IF opened OR clicked → proceed to email 2
  IF no engagement → wait 4 more days, resend with new subject
    IF still no engagement → exit sequence, mark as low-engagement
```

Gates protect deliverability by ensuring you only continue emailing people who are reading.

---

## Cross-Channel Orchestration

### Channel Priority & Coordination

| Channel | Use When | Typical Content |
|---|---|---|
| **Email** | Primary communication, content delivery, nurture | Long-form, educational, promotional, transactional |
| **SMS** | Time-sensitive, high-urgency, brief messages | Appointment reminders, flash sales, shipping updates, abandoned cart |
| **Push notifications** | App users, real-time engagement, ephemeral messages | Feature updates, activity alerts, personalized recommendations |
| **In-app messaging** | User is actively in the product, contextual guidance | Onboarding tooltips, feature announcements, upgrade prompts |
| **Direct mail** | High-value accounts, re-engagement, brand moments | Welcome kits, anniversary gifts, win-back offers |
| **Retargeting ads** | Awareness reinforcement, stays visible between emails | Brand awareness, social proof, offer reinforcement |

### Orchestration Rules

1. **Never send the same message through multiple channels simultaneously** — Coordinate so each channel serves a distinct purpose
2. **Respect channel preferences** — If a contact opts out of SMS, do not attempt to compensate by emailing twice as often
3. **Use channel escalation** — Start with email. If no engagement, escalate to SMS (with consent). If high-value, consider direct mail.
4. **Time-zone awareness** — Send emails during business hours (B2B) or active hours (B2C) in the contact's time zone
5. **Global frequency cap** — Total touches across all channels should not exceed a weekly maximum (3-5 for B2B, 5-7 for B2C)

### Example: Multi-Channel Abandoned Cart

```
Hour 0: Cart abandoned
Hour 1: Email — "You left items in your cart" with product images
Hour 12: Push notification (if app user) — "Your cart is waiting"
Hour 24: Email — Social proof + urgency ("Selling fast")
Hour 36: SMS (if opted in) — Short message with cart link
Hour 48: Retargeting ad activated — Show cart products on social/display
Hour 72: Final email — Discount offer (last resort)
```

---

## Testing Automation Workflows

### Pre-Launch Testing

1. **Path testing**: Send test contacts through every possible branch path. Verify each route delivers the correct content in the correct order.
2. **Trigger verification**: Confirm the trigger fires correctly (and only when intended). Test edge cases: what happens if the trigger fires twice? What happens if the contact already exists in the workflow?
3. **Timing validation**: Verify wait steps use the correct durations. Check time zone handling.
4. **Suppression testing**: Confirm contacts in suppression lists or other active workflows are properly excluded.
5. **Exit condition testing**: Verify contacts exit when they should (conversion, unsubscribe, disqualification). Confirm they do NOT exit prematurely.
6. **Integration testing**: Verify CRM records update, scores change, handoff notifications fire, and list memberships update correctly.

### In-Flow A/B Testing

- **Subject line tests**: Test within the same email step. Split 50/50 with a winner declared after 24-48 hours or sufficient volume.
- **Content variant tests**: Test different content approaches at the same sequence step.
- **Timing tests**: Test different wait durations between emails (e.g., 3-day gap vs. 5-day gap).
- **Branch path tests**: Test whether behavioral branching outperforms a single linear path.
- **Minimum sample**: Do not declare winners with fewer than 100 contacts per variant. For low-volume workflows, run tests longer rather than reducing sample size.

### Ongoing Monitoring

- **Enrollment rate**: Are contacts entering at expected volume?
- **Step completion rate**: What percentage reach each step? Where is the drop-off?
- **Error rate**: Are any steps failing (bounces, integration errors, send failures)?
- **Goal completion rate**: What percentage achieve the workflow's defined goal?
- **Time-to-goal**: How long does it take to achieve the goal? Is this improving over time?
- **Unsubscribe rate per step**: Identify specific emails that drive unsubscribes.

---

## Common Mistakes and Anti-Patterns

### 1. No Exit Conditions
**Problem**: Contacts loop endlessly or receive redundant messages after converting.
**Fix**: Every workflow must have explicit exit conditions. At minimum: goal achieved, unsubscribed, or maximum time elapsed.

### 2. Overlapping Workflows Without Suppression
**Problem**: A contact is in a welcome series AND a promotional campaign AND a re-engagement flow simultaneously, receiving 3+ emails per day.
**Fix**: Build a priority hierarchy. Use suppression lists or workflow exclusion rules. Implement a global frequency cap.

### 3. Sending Too Frequently
**Problem**: Daily emails that ignore engagement signals.
**Fix**: Gate progression on engagement. Reduce cadence for non-openers. Respect the 3-5 touches per week maximum across all channels.

### 4. One-Size-Fits-All Content
**Problem**: The same nurture sequence for every persona, industry, and lifecycle stage.
**Fix**: Segment workflows by at least one dimension (persona, industry, or lifecycle stage). Use dynamic content blocks for personalization within shared workflows.

### 5. "Set and Forget" Mentality
**Problem**: Workflows built once and never reviewed, even as products, messaging, and audience evolve.
**Fix**: Quarterly workflow audits. Monthly performance reviews. Annual full rebuild for core workflows.

### 6. Ignoring Negative Signals
**Problem**: Continuing to email contacts who have shown disengagement signals (multiple unopens, spam complaints).
**Fix**: Build negative-signal branches that reduce frequency, change approach, or trigger sunset. Protecting sender reputation is more important than reaching one more contact.

### 7. Premature Discount Offering
**Problem**: Abandoned cart flows that immediately offer 20% off, training customers to abandon on purpose.
**Fix**: Lead with value, not discounts. Use social proof, urgency, and product benefits before any incentive. If you must discount, do so only in the final email, and use the smallest effective amount.

### 8. Skipping Warm-Up for New Workflows
**Problem**: Launching a workflow to 50,000 contacts on day one, triggering spam filters.
**Fix**: Start with a small segment (5-10%), monitor deliverability, and scale up over 2-4 weeks. This applies to new IPs, new domains, and new high-volume workflows.
