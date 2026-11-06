---
name: suede-referrals
description: "Design a referral and affiliate program with incentives, commission and payout rules, fraud controls, disclosure, attribution, and cohort measurement. Use when asked to \"design our referral program\" or repair customer, ambassador, or partner incentives. Returns a program spec, economics, tooling options, and launch checklist. NOT FOR: payouts or billing changes, brand partnerships (use suede-co-marketing), launch packaging (use suede-launch-packaging), or lifecycle messages (use suede-emails)."
metadata:
  display-name: "Suede AI Referral Skills"
  version: 2.1.0
---

# Suede AI Referral Skills

## Compatibility

Uses supplied margin, LTV, and cohort data; current platform and disclosure checks need web access. Program design does not require a live payout or affiliate integration.

For a concrete input, expected handoff, and failure check, read
[the worked handoff](references/worked-handoff.md).

Suede AI Referrals designs measurable customer, affiliate, and partner loops from
incentive economics through attribution and fraud controls. It separates
modeled loop performance from observed results and keeps activation and payouts
behind approval.

## Before Starting

**Check for product marketing context first:**
If `.agents/product-marketing.md` exists (or `.claude/product-marketing.md`, or the legacy `product-marketing-context.md` filename, in older setups), read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Gather this context (ask if not provided):

### 1. Program Type
- Customer referral program, affiliate program, or both?
- B2B or B2C?
- What's the average customer LTV?
- What's your current CAC from other channels?

### 2. Current State
- Existing referral/affiliate program?
- Current referral rate (% who refer)?
- What incentives have you tried?

### 3. Product Fit
- Is your product shareable?
- Does it have network effects?
- Do customers naturally talk about it?

### 4. Resources
- Tools/platforms you use or consider?
- Budget for referral incentives?

---

## Referral vs. Affiliate

### Customer Referral Programs

**Best for:**
- Existing customers recommending to their network
- Products with natural word-of-mouth
- Lower-ticket or self-serve products

**Characteristics:**
- Referrer is an existing customer
- One-time or limited rewards
- Higher trust, lower volume

### Affiliate Programs

**Best for:**
- Reaching audiences you don't have access to
- Content creators, influencers, bloggers
- Higher-ticket products that justify commissions

**Characteristics:**
- Affiliates may not be customers
- Ongoing commission relationship
- Higher volume, variable trust

---

## Referral Program Design

### The Referral Loop

```
Trigger Moment → Share Action → Convert Referred → Reward → (Loop)
```

### Step 1: Identify Trigger Moments

**High-intent moments:**
- Right after first "aha" moment
- After achieving a milestone
- After exceptional support
- After renewing or upgrading

**Prompt cadence for customers who have not referred:** day 7, day 30, day 60,
and after any milestone. The timing is this skill's call; the message copy is
not: hand that to `suede-emails`.

### Step 2: Design Share Mechanism

**Ranked by effectiveness:**
1. In-product sharing (highest conversion)
2. Personalized link
3. Email invitation
4. Social sharing
5. Referral code (works offline)

### Step 3: Choose Incentive Structure

**Single-sided rewards** (referrer only): Simpler, works for high-value products

**Double-sided rewards** (both parties): Higher conversion, win-win framing

**Tiered rewards**: Gamifies referral process, increases engagement

**For program patterns and incentive sizing**: See [references/program-examples.md](references/program-examples.md)

---

## Program Optimization

### Improving Referral Rate

**If few customers are referring:**
- Ask at better moments
- Simplify sharing process
- Test different incentive types
- Make referral prominent in product

**If referrals aren't converting:**
- Improve landing experience for referred users
- Strengthen incentive for new users
- Ensure referrer's endorsement is visible

### A/B Tests to Run

**Incentive tests:** Amount, type, single vs. double-sided, timing

**Messaging tests:** Program description, CTA copy, landing page copy

**Placement tests:** Where and when the referral prompt appears

### Common Problems & Fixes

| Problem | Fix |
|---------|-----|
| Low awareness | Add prominent in-app prompts |
| Low share rate | Simplify to one click |
| Low conversion | Optimize referred user experience |
| Fraud/abuse | Apply the fraud controls below |
| One-time referrers | Add tiered/gamified rewards |

### Fraud Controls

Read [references/affiliate-programs.md](references/affiliate-programs.md)
§Fraud Prevention before designing rewards or writing program terms: it carries
the technical, policy, and structural control set (delayed payout after
activation, device and IP signals, clawback on refunds, per-period caps,
manual review of suspicious patterns). Every program in this skill uses it,
customer referral programs included, not only affiliate programs.

Set these thresholds explicitly, because the reference leaves them open:
- Name the qualifying downstream event that releases a reward (a paid conversion
  or day-N retention, N stated), never signup alone.
- Hold payouts until the refund/chargeback window has closed, and state that
  window in days.
- State the dollar amount above which a payout goes to manual review before it
  is released.

---

## Measuring Success

### Key Metrics

**Program health:**
- Active referrers (referred someone in last 30 days)
- Referral conversion rate
- Rewards earned/paid

**Business impact:**
- % of new customers from referrals
- CAC via referral vs. other channels
- LTV of referred customers
- Referral program ROI

### Typical Findings

Peer-reviewed field research (for example "Referral Programs and Customer
Value," Journal of Marketing, 2011, a study of bank customers) found referred
customers more valuable and less likely to churn than other customers; vendor
reports claim a wide range of larger effects with undisclosed methods. Treat
any figure as a hypothesis: compare referred and non-referred cohorts on
retention, LTV, and onward referral rate in this product's own data before
claiming an effect.

### Disclosure and incentive rules

- Referrers and affiliates who are paid or rewarded must clearly disclose that
  connection where they recommend you (FTC Endorsement Guides, revised 2023:
  [FTC guidance](https://www.ftc.gov/business-guidance/resources/ftcs-endorsement-guides-what-people-are-asking)).
- Do not reward reviews conditioned on positive sentiment, and do not suppress
  negative ones (FTC Consumer Reviews and Testimonials Rule, effective October
  21, 2024).
- Contests and milestone giveaways can fall under sweepstakes law; payouts can
  create tax reporting duties. Flag both for the user's counsel and finance owner.

---

## Launch Checklist

### Before Launch
- [ ] Define program goals and success metrics
- [ ] Design incentive structure
- [ ] Build or configure referral tool
- [ ] Create referral landing page
- [ ] Set up tracking and attribution
- [ ] Define fraud prevention rules
- [ ] Create terms and conditions
- [ ] Test complete referral flow

### Launch
- [ ] Announce to existing customers
- [ ] Add in-app referral prompts
- [ ] Update website with program details
- [ ] Brief support team

### Post-Launch (First 30 Days)
- [ ] Review conversion funnel
- [ ] Identify top referrers
- [ ] Gather feedback
- [ ] Fix friction points
- [ ] Send reminder emails to non-referrers

---

## Affiliate Programs

**For affiliate program design, commission structures, recruitment, fraud
prevention, and tools**: See [references/affiliate-programs.md](references/affiliate-programs.md)

---

## Tool Integrations

These are evaluation examples, not guaranteed integrations. Verify current
vendor documentation, pricing, account access, attribution behavior, payout
controls, tax support, and data-export terms before recommending a platform.

| Tool | Best For | Verify Before Use |
|------|----------|-------------------|
| **Rewardful / Tolt** | SaaS affiliate programs | Billing integration, attribution, payouts |
| **Mention Me** | Enterprise referral programs | Identity, fraud, and reporting controls |
| **Dub.co** | Link tracking and attribution | Attribution window and privacy settings |
| **Stripe** | Commission-related payment records | Live objects, fees, approvals, tax workflow |
| **Introw** | Tiered channel partner operations | Deal registration and payout governance |
| **PartnerStack** | Enterprise partner ecosystems | Fees, attribution, approval, data export |

---

## Boundaries

- Do not enable a program, create affiliate accounts, issue links, execute
  payouts, or change billing and commission objects without verified live state
  and explicit approval.
- Do not invent attribution, conversion, fraud, or viral-coefficient results;
  distinguish modeled economics from observed data.
- Do not decide tax, labor, privacy, contest, endorsement, or incentive
  compliance. Surface the jurisdiction-specific review needed before launch.

## Routing

- Use `suede-launch-packaging` to coordinate the approved program launch.
- Use `suede-emails` for referral invitation and nurture sequences.
- Use `suede-offers` (behavioral-models catalog) to frame incentive tests as evidence-tiered hypotheses.
- Use `suede-ab-testing` to design and evaluate the incentive, messaging, and placement tests above.
- Use `suede-analytics` to define and read referral attribution.
