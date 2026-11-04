---
name: suede-churn-prevention
description: "Suede AI Churn Prevention Skills. Use when asked to \"reduce subscription churn\" or design cancel flows, reason-matched save offers, failed-payment recovery and win-back measurement. NOT FOR: lifecycle email copy (suede-emails), pricing architecture (suede-pricing), paywalls (suede-paywalls), or tracking implementation (suede-analytics)."
metadata:
  display-name: "Suede AI Churn Prevention Skills"
  version: 2.1.0
---

# Suede AI Churn Prevention Skills

Read [the worked delivery contract](references/worked-contract.md) for a concrete
input, expected artifact, failure response and validation example.

## Compatibility

Works from subscription cohorts, cancel reasons and payment-status exports; current official policy/legal sources for applicable cancellation requirements. Live billing mutations require existing authorized access.

Use this retention playbook to reduce voluntary and involuntary churn through transparent cancel flows, bounded save offers, proactive signals, and payment recovery.

## Before Starting

**Check for product marketing context first:**
If `.agents/product-marketing.md` exists (or `.claude/product-marketing.md`, or the legacy `product-marketing-context.md` filename, in older setups), read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Gather this context (ask if not provided):

### 1. Current Churn Situation
- What's your monthly churn rate? (Voluntary vs. involuntary if known)
- How many active subscribers?
- What's the average MRR per customer?
- Do you have a cancel flow today, or does cancel happen instantly?

### 2. Billing & Platform
- What billing provider? (Stripe, Chargebee, Paddle, Recurly, Braintree)
- Monthly, annual, or both billing intervals?
- Do you support plan pausing or downgrades?
- Any existing retention tooling? (Churnkey, ProsperStack, Raaft)

### 3. Product & Usage Data
- Do you track feature usage per user?
- Can you identify engagement drop-offs?
- Do you have cancellation reason data from past churns?
- What's your activation metric? (What do retained users do that churned users don't?)

### 4. Constraints
- B2B or B2C? (Affects flow design)
- Which states and countries are customers in? (California and other automatic
  renewal laws require online cancellation; see Cancellation law below)
- Brand tone for offboarding? (Empathetic, direct, playful)

---

## How This Skill Works

Churn has two types requiring different strategies:

| Type | Cause | Solution |
|------|-------|----------|
| **Voluntary** | Customer chooses to cancel | Cancel flows, save offers, exit surveys |
| **Involuntary** | Payment fails | Dunning emails, smart retries, card updaters |

Voluntary churn is typically 50-70% of total churn. Involuntary churn is 30-50% but is often easier to fix.

This skill supports three modes:

1. **Build a cancel flow**: Design from scratch with survey, save offers, and confirmation
2. **Optimize an existing flow**: Analyze cancel data and improve save rates
3. **Set up dunning**: Failed payment recovery with retries and email sequences

---

## Cancel Flow Design

### The Cancel Flow Structure

Every cancel flow follows this sequence:

```
Trigger → Survey → Dynamic Offer → Confirmation → Post-Cancel
```

**Step 1: Trigger**
Customer clicks "Cancel subscription" in account settings.

**Step 2: Exit Survey**
Ask why they're cancelling. This determines which save offer to show.

**Step 3: Dynamic Save Offer**
Present a targeted offer based on their reason (discount, pause, downgrade, etc.)

**Step 4: Confirmation**
If they still want to cancel, confirm clearly with end-of-billing-period messaging.

**Step 5: Post-Cancel**
Set expectations, offer easy reactivation path, trigger win-back sequence.

### Exit Survey Design

The exit survey is the foundation. Good reason categories:

| Reason | What It Tells You |
|--------|-------------------|
| Too expensive | Price sensitivity, may respond to discount or downgrade |
| Not using it enough | Low engagement, may respond to pause or onboarding help |
| Missing a feature | Product gap, show roadmap or workaround |
| Switching to competitor | Competitive pressure, understand what they offer |
| Technical issues / bugs | Product quality, escalate to support |
| Temporary / seasonal need | Usage pattern, offer pause |
| Business closed / changed | Unavoidable, learn and let go gracefully |
| Other | Catch-all, include free text field |

**Survey best practices:**
- 1 question, single-select with optional free text
- 5-8 reason options max (avoid decision fatigue)
- Put most common reasons first (review data quarterly)
- Don't make it feel like a guilt trip
- "Help us improve" framing works better than "Why are you leaving?"

### Dynamic Save Offers

The key insight: **match the offer to the reason.** A discount won't save someone who isn't using the product. A feature roadmap won't save someone who can't afford it.

**Offer-to-reason mapping:**

| Cancel Reason | Primary Offer | Fallback Offer |
|---------------|---------------|----------------|
| Too expensive | Discount (20-30% for 2-3 months) | Downgrade to lower plan |
| Not using it enough | Pause (1-3 months) | Free onboarding session |
| Missing feature | Roadmap preview + timeline | Workaround guide |
| Switching to competitor | Competitive comparison + discount | Feedback session |
| Technical issues | Escalate to support immediately | Credit + priority fix |
| Temporary / seasonal | Pause subscription | Downgrade temporarily |
| Business closed | Skip offer (respect the situation) | n/a |

### Save Offer Types

**Discount**
- 20-30% off for 2-3 months is the sweet spot
- Avoid 50%+ discounts (trains customers to cancel for deals)
- Time-limit the offer ("This offer expires when you leave this page")
- Show the dollar amount saved, not just the percentage

**Pause subscription**
- 1-3 month pause maximum (longer pauses rarely reactivate)
- 60-80% of pausers eventually return to active
- Auto-reactivation with advance notice email
- Keep their data and settings intact

**Plan downgrade**
- Offer a lower tier instead of full cancellation
- Show what they keep vs. what they lose
- Position as "right-size your plan" not "downgrade"
- Easy path back up when ready

**Feature unlock / extension**
- Turn on a premium feature they haven't tried
- Extend trial of a higher tier
- Works best for "not getting enough value" reasons

**Personal outreach**
- For high-value accounts (top 10-20% by MRR)
- Route to customer success for a call
- Personal email from founder for smaller companies

### Cancellation law (checked October 2026)

- **Federal:** the FTC's 2024 "click-to-cancel" amendments to the Negative
  Option Rule were vacated by the Eighth Circuit on July 8, 2025, before their
  compliance date. The Restore Online Shoppers' Confidence Act (ROSCA) still
  requires simple cancellation for online negative-option offers, and the FTC
  keeps enforcing it.
- **California:** the amended Automatic Renewal Law (AB 2863), effective
  July 1, 2025, requires online cancellation through a prominent direct link or
  button for subscriptions sold online, and a save offer may appear only if the
  customer is told they can still cancel and can do so without engaging with it.
- **Other states** have their own automatic renewal laws. Treat the strictest
  one in your market as the floor.

Design rule that satisfies all of the above: one save offer, a visible
"continue to cancel" control on every screen, and a cancellation that completes
online in the same session. Legal review decides edge cases, not this skill.

Sources: Mayer Brown, "Click-to-Cancelled: Eighth Circuit Vacates FTC's
Revised Negative Option Rule" (July 18, 2025); Lowenstein Sandler, "FTC
Click-to-Cancel Rule on Hold, but California's Automatic Renewal Law Remains
Intact" (July 16, 2025).

### Cancel Flow UI Patterns

**UI principles:**
- Keep the "continue cancelling" option visible (no dark patterns)
- One primary offer + one fallback, not a wall of options
- Show specific dollar savings, not abstract percentages
- Use the customer's name and account data when possible
- Mobile-friendly (many cancellations happen on mobile)

Read [references/cancel-flow-patterns.md](references/cancel-flow-patterns.md)
before designing a flow: it carries the patterns by industry and billing
provider, the segment-specific variants, the post-cancel sequence, and screen
mockups of the survey and offer steps.

---

## Churn Prediction & Proactive Retention

The best save happens before the customer ever clicks "Cancel."

### Risk Signals

Track these leading indicators of churn:

| Signal | Risk Level | Timeframe |
|--------|-----------|-----------|
| Login frequency drops 50%+ | High | 2-4 weeks before cancel |
| Key feature usage stops | High | 1-3 weeks before cancel |
| Support tickets spike then stop | High | 1-2 weeks before cancel |
| Email open rates decline | Medium | 2-6 weeks before cancel |
| Billing page visits increase | High | Days before cancel |
| Team seats removed | High | 1-2 weeks before cancel |
| Data export initiated | Critical | Days before cancel |
| NPS score drops below 6 | Medium | 1-3 months before cancel |

### Health Score Model

Build a simple health score (0-100) from weighted signals:

```
Health Score = (
  Login frequency score × 0.30 +
  Feature usage score   × 0.25 +
  Support sentiment     × 0.15 +
  Billing health        × 0.15 +
  Engagement score      × 0.15
)
```

| Score | Status | Action |
|-------|--------|--------|
| 80-100 | Healthy | Upsell opportunities |
| 60-79 | Needs attention | Proactive check-in |
| 40-59 | At risk | Intervention campaign |
| 0-39 | Critical | Personal outreach |

### Proactive Interventions

**Before they think about cancelling:**

| Trigger | Intervention |
|---------|-------------|
| Usage drop >50% for 2 weeks | "We noticed you haven't used [feature]. Need help?" email |
| Approaching plan limit | Upgrade nudge (not a wall, paywalls handles this) |
| No login for 14 days | Re-engagement email with recent product updates |
| NPS detractor (0-6) | Personal follow-up within 24 hours |
| Support ticket unresolved >48h | Escalation + proactive status update |
| Annual renewal in 30 days | Value recap email + renewal confirmation |

---

## Involuntary Churn: Payment Recovery

Failed payments cause 30-50% of all churn but are the most recoverable.

### The Dunning Stack

```
Pre-dunning → Smart retry → Dunning emails → Grace period → Hard cancel
```

### Pre-Dunning (Prevent Failures)

- **Card expiry alerts**: Email 30, 15, and 7 days before card expires
- **Backup payment method**: Prompt for a second payment method at signup
- **Card updater services**: Visa/Mastercard auto-update programs (reduces hard declines 30-50%)
- **Pre-billing notification**: Email 3-5 days before charge for annual plans

### Smart Retry Logic

Not all failures are the same. Retry strategy by decline type:

| Decline Type | Examples | Retry Strategy |
|-------------|----------|----------------|
| Soft decline (temporary) | Insufficient funds, processor timeout | Retry on the canonical schedule below |
| Hard decline (permanent) | Card stolen, account closed | Don't retry: ask for new card |
| Authentication required | 3D Secure, SCA | Send customer to update payment |

**Canonical retry schedule:** one schedule governs this skill: the manual retry
table in [references/dunning-playbook.md](references/dunning-playbook.md)
§Retry Schedule by Provider (Day 1 / 3 / 5 / 7 / 10, fifth attempt last before
the grace period ends). Read it before configuring retries and do not restate a
different schedule anywhere.

### Dunning Email Sequence

Four emails on Day 0 / 3 / 7 / 10. The timing, tone, and full copy for each live
in [references/dunning-playbook.md](references/dunning-playbook.md) §Dunning
Email Sequence: read it before writing or configuring the sequence.

**Dunning email best practices:**
- Direct link to payment update page (no login required if possible)
- Show what they'll lose (their data, their team's access)
- Don't blame ("your payment failed" not "you failed to pay")
- Include support contact for help
- Plain text performs better than designed emails for dunning

### Recovery Benchmarks

| Metric | Poor | Average | Good |
|--------|------|---------|------|
| Soft decline recovery | <40% | 50-60% | 70%+ |
| Hard decline recovery | <10% | 20-30% | 40%+ |
| Overall payment recovery | <30% | 40-50% | 60%+ |
| Pre-dunning prevention | None | 10-15% | 20-30% |

These bands are industry ranges for calibrating a recommendation. Never assert
them as this product's result.

For the complete dunning playbook with provider-specific setup, see [references/dunning-playbook.md](references/dunning-playbook.md).

---

## Metrics & Measurement

### Key Churn Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| Monthly churn rate | Churned customers / Start-of-month customers | <5% B2C, <2% B2B |
| Revenue churn (net) | (Lost MRR - Expansion MRR) / Start MRR | Negative (net expansion) |
| Cancel flow save rate | Saved / Total cancel sessions | 25-35% |
| Offer acceptance rate | Accepted offers / Shown offers | 15-25% |
| Pause reactivation rate | Reactivated / Total paused | 60-80% |
| Dunning recovery rate | Recovered / Total failed payments | 50-60% |
| Time to cancel | Days from first churn signal to cancel | Track trend |

### Cohort Analysis

Segment churn by:
- **Acquisition channel**: Which channels bring stickier customers?
- **Plan type**: Which plans churn most?
- **Tenure**: When do most cancellations happen? (30, 60, 90 days?)
- **Cancel reason**: Which reasons are growing?
- **Save offer type**: Which offers work best for which segments?

### Cancel Flow A/B Tests

Test one variable at a time:

| Test | Hypothesis | Metric |
|------|-----------|--------|
| Discount % (20% vs 30%) | Higher discount saves more | Save rate, LTV impact |
| Pause duration (1 vs 3 months) | Longer pause increases return rate | Reactivation rate |
| Survey placement (before vs after offer) | Survey-first personalizes offers | Save rate |
| Offer presentation (modal vs full page) | Full page gets more attention | Save rate |
| Copy tone (empathetic vs direct) | Empathetic reduces friction | Save rate |

**How to run cancel flow experiments:** Route the hypothesis, sample, duration,
and stopping rule to `suede-ab-testing`. Use an authorized experimentation
system that can assign users consistently and read each funnel step (survey →
offer → accept/decline → confirm). Verify the system's current official
implementation guidance, assignment behavior, and event readback before launch.

---

## Common Mistakes

- **No cancel flow at all**: Instant cancel leaves money on the table. Even a simple survey + one offer saves 10-15%
- **Not tracking save offer LTV**: A "saved" customer who churns 30 days later wasn't really saved
- **No post-cancel path**: Make reactivation easy and trigger win-back emails, because some churned users will want to come back

---

## Tool Integrations

This pack does not ship retention, billing, or analytics connectors. Select an
authorized system from the user's actual stack and verify its current official
documentation, account plan, test mode, and rollback path before configuration.

### Capability Checklist

- Cancel-flow routing, survey capture, and an unobstructed final cancel action
- Stable experiment assignment and step-level event readback
- Pause, downgrade, and save-offer rules with explicit eligibility
- Payment-retry state, card-updater state, and customer-notification controls
- Audit history, test mode, role controls, and rollback or disable behavior

### Implementation Routing

- Route message writing to `suede-emails`.
- Route event schemas and readback to `suede-analytics`.
- Route test design to `suede-ab-testing`.
- Treat billing retries, discounts, subscription changes, and activation as
  separately authorized mutations.

### Halt Format for Billing Mutations

Before any change to a live billing object (retry rules, discounts, plan
changes, pauses, cancellations, subscription state, or customer-facing billing
messages), stop and emit this block, then wait. Inferred consent is not
authorization, and "the user asked for a cancel flow" is not authorization to
configure one.

```
HALT: billing mutation requires authorization

Mutation: <the exact change, e.g. "enable 5-attempt retry rule">
Objects touched: <provider, environment, subscriptions/customers/coupons affected, count>
Reversible by: <the exact rollback, or "not reversible">

Options:
1. Proceed in test mode only
2. Proceed on live objects as specified
3. Narrow the scope to <smaller set> and proceed
4. Abandon this mutation

Waiting for your choice.
```

---

## Boundaries

- Do not obstruct cancellation, hide downgrade paths, manufacture urgency, or use deceptive retention friction.
- Do not change subscriptions, retry rules, discounts, billing objects, or customer messaging without explicit authorization.
- Do not claim saved revenue or churn reduction without a defined cohort, window, denominator, and verified payment state.
- Do not decide which individual customer should receive a sensitive offer from protected traits or unsupported inference.

## Routing

- Need retention, dunning, or win-back messages -> use `suede-emails`.
- Need plan structure or offer economics -> use `suede-pricing` or `suede-offers`.
- Need paywall or trial-expiry UX -> use `suede-paywalls`.
- Need churn events or a controlled retention test -> use `suede-analytics` or `suede-ab-testing`.
- From those skills, route cancellation and payment-recovery strategy back to `suede-churn-prevention`.
