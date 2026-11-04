---
name: suede-emails
description: "Use when asked \"build a welcome email sequence\" or to design nurture, onboarding, win-back, post-purchase or trigger-based lifecycle email flows. Suede AI returns entry and exit criteria, timing, exact copy, sender-rule checks and a measurement plan. NOT FOR: cold outbound (use suede-cold-email), SMS (use suede-sms), in-product onboarding (use suede-onboarding), or broader lifecycle operations (use suede-revops)."
metadata:
  display-name: "Suede AI Lifecycle Email Skills"
  version: 2.1.0
---

# Suede AI Lifecycle Email Skills

Design lifecycle email as a consent-aware system of triggers, message roles, pacing, and measurable next actions. Create sequences that move a known audience toward value without inventing intent, exhausting the list, or confusing lifecycle messaging with cold outreach.

## Compatibility

Any agent with product, consent and lifecycle context. Current deliverability checks need web access; producing a handoff does not require an email-service integration.

## Initial Assessment

**Check for product marketing context first:**
If `.agents/product-marketing.md` exists (or `.claude/product-marketing.md`, or the legacy `product-marketing-context.md` filename, in older setups), read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Before creating a sequence, understand:

1. **Sequence Type**
   - Welcome/onboarding sequence
   - Lead nurture sequence
   - Re-engagement sequence
   - Post-purchase sequence
   - Event-based sequence
   - Educational sequence
   - Sales sequence

2. **Audience Context**
   - Who are they?
   - What triggered them into this sequence?
   - What do they already know/believe?
   - What's their current relationship with you?
   - What other emails are they already receiving?
   - What's the current email performance to beat?

3. **Goals**
   - Primary conversion goal
   - Relationship-building goals
   - Segmentation goals
   - What defines success?

---

## Core Principle

One email, one job: a single purpose and a single primary CTA per email. Everything downstream, sequence length, roles, copy, follows from that.

---

## Email Sequence Strategy

Sequence lengths are set per type in Sequence Types Overview below; use those numbers, not a generic range. Adjust for sales-cycle length, product complexity, and relationship stage.

### Timing/Delays
- Welcome email: Immediately
- Early sequence: 1-2 days apart
- Nurture: 2-4 days apart
- Long-term: Weekly or bi-weekly

Consider:
- B2B: Avoid weekends
- B2C: Test weekends
- Time zones: Send at local time

### Subject Line Strategy
- Clear > Clever
- Specific > Vague
- Benefit or curiosity-driven
- 40-60 characters, front-loading the words that matter for mobile truncation
- Test emoji (they're polarizing)
- Judge subject tests on clicks or conversions, not opens: Apple Mail Privacy
  Protection preloads images and inflates open rates

**Patterns that work:**
- Question: "Still struggling with X?"
- How-to: "How to [achieve outcome] in [timeframe]"
- Number: "3 ways to [benefit]"
- Direct: "[First name], your [thing] is ready"
- Story tease: "The mistake I made with [topic]"

### Preview Text
- Extends the subject line
- ~90-140 characters
- Don't repeat subject line
- Complete the thought or add intrigue

---

## Sequence Types Overview

### Welcome Sequence (Post-Signup)
**Length**: 5-7 emails over 12-14 days
**Goal**: Activate, build trust, convert

Key emails:
1. Welcome + deliver promised value (immediate)
2. Quick win (day 1-2)
3. Story/Why (day 3-4)
4. Social proof (day 5-6)
5. Overcome objection (day 7-8)
6. Core feature highlight (day 9-11)
7. Conversion (day 12-14)

### Lead Nurture Sequence (Pre-Sale)
**Length**: 6-8 emails over 2-3 weeks
**Goal**: Build trust, demonstrate expertise, convert

Key emails:
1. Deliver lead magnet + intro (immediate)
2. Expand on topic (day 2-3)
3. Problem deep-dive (day 4-5)
4. Solution framework (day 6-8)
5. Case study (day 9-11)
6. Differentiation (day 12-14)
7. Objection handler (day 15-18)
8. Direct offer (day 19-21)

### Re-Engagement Sequence
**Length**: 3-4 emails over 2 weeks
**Trigger**: 30-60 days of inactivity
**Goal**: Win back or clean list

Key emails:
1. Check-in (genuine concern)
2. Value reminder (what's new)
3. Incentive (special offer)
4. Last chance (stay or unsubscribe)

### Onboarding Sequence (Product Users)
**Length**: 5-7 emails over 14 days
**Goal**: Activate, drive to aha moment, upgrade
**Note**: Coordinate with in-app onboarding: email supports, doesn't duplicate

Key emails:
1. Welcome + first step (immediate)
2. Getting started help (day 1)
3. Feature highlight (day 2-3)
4. Success story (day 4-5)
5. Check-in (day 7)
6. Advanced tip (day 10-12)
7. Upgrade/expand (day 14+)

**For detailed templates**: See [references/sequence-templates.md](references/sequence-templates.md)

---

## Email Types by Category

Six categories: Onboarding · Retention · Billing · Usage · Win-Back · Campaigns.

Read [references/email-types.md](references/email-types.md) when you need to pick or design an individual email type: it carries the trigger, timing, role, and copy pattern for each one, plus an email audit checklist.

---

## Email Copy Guidelines

### Structure
1. **Hook**: First line grabs attention
2. **Context**: Why this matters to them
3. **Value**: The useful content
4. **CTA**: What to do next
5. **Sign-off**: Human, warm close

### Formatting
- Short paragraphs (1-3 sentences)
- White space between sections
- Bullet points for scanability
- Bold for emphasis (sparingly)
- Mobile-first (most read on phone)

### Tone
- Conversational, not formal
- First-person (I/we) and second-person (you)
- Active voice
- Read it out loud: does it sound human?

**Never ship these strings.** They are the lifecycle-email defaults a model reaches for unprompted, and every one of them is a slot where a specific sentence should be:

- "We're thrilled to have you aboard!" / "We're excited to have you!"
- "Welcome to the family!" / "You're in good company"
- "Here's what you can do next" / "Let's get you started"
- "Don't miss out" / "Act now" / "Limited time only"
- "Quick question" / "Just checking in" / "Just following up"
- "We noticed you haven't..." / "We miss you!"
- "Ready to take your [X] to the next level?"
- "Unlock the full power of..." / "Supercharge your..."
- "As a valued customer" / "We value your feedback"

The replacement is always the same shape: name the specific thing this reader did, or the specific thing they get next. If a sentence would be true for any recipient of any product, it is one of these in disguise.

### Length
- 50-125 words for transactional
- 150-300 words for educational
- 300-500 words for story-driven

### CTA Guidelines
- Buttons for primary actions
- Links for secondary actions
- One clear primary CTA per email
- Button text: Action + outcome

**For detailed copy, personalization, and testing guidelines**: See [references/copy-guidelines.md](references/copy-guidelines.md)

---

## Output Format

### Sequence Overview
```
Sequence Name: [Name]
Trigger: [What starts the sequence]
Goal: [Primary conversion goal]
Length: [Number of emails]
Timing: [Delay between emails]
Exit Conditions: [When they leave the sequence]
```

### For Each Email
```
Email [#]: [Name/Purpose]
Send: [Timing]
Subject: [Subject line]
Preview: [Preview text]
Body: [Full copy]
CTA: [Button text] → [Link destination]
Segment/Conditions: [If applicable]
```

### Metrics Plan
```
Per email: open rate, click rate, unsubscribe rate
Per sequence: completion rate, primary-conversion rate, revenue or signups attributed
Baseline: [the user's current numbers for this audience, or "none supplied"]
Review point: [when to read results and what number would trigger a rewrite]
```

---

## Pre-delivery self-check

Run this on the drafted sequence before presenting it. Each box checks a rule this skill already states, against the copy you just wrote.

- [ ] Every email has exactly one primary CTA
- [ ] Every subject line is 40-60 characters: count them, do not estimate
- [ ] No preview text repeats its subject line
- [ ] Every body is inside the word band for its type (50-125 transactional / 150-300 educational / 300-500 story-driven)
- [ ] Exit conditions are specified for the sequence
- [ ] No string from the Tone blocklist appears anywhere in the copy
- [ ] The consent and suppression assumption is stated explicitly rather than assumed: say which list, which opt-in, and what excludes a contact
- [ ] Every marketing email is marked for one-click unsubscribe (RFC 8058 headers) and the plan says unsubscribes are honored within 48 hours
- [ ] The re-engagement or win-back flow ends by suppressing contacts who never re-engage

Any box that fails means fix it before presenting. Do not deliver the sequence with the failure noted as a caveat.

---

## Implementation Hand-off

Choose the provider only after reading the user's installed tools and live account state. Customer.io, Mailchimp, Resend, SendGrid, Kit, and similar services may support parts of the workflow, but this public Suede skill does not assume that any provider, connector, account, or permission is available.

Before implementation, return:

1. The required trigger, audience, fields, suppression rules, and exit criteria
2. The provider-neutral sequence and event contract
3. The exact account or integration that must be inspected
4. The deliverability checklist from
   [references/deliverability.md](references/deliverability.md): SPF, DKIM,
   DMARC alignment, one-click unsubscribe, complaint-rate monitoring below
   0.1%, and separated transactional and marketing streams. Gmail began
   rejecting non-compliant bulk mail more aggressively in November 2025, and
   Microsoft has enforced its high-volume rules since May 2025.
5. A preview-and-approval checkpoint before any live change or send

---

## Boundaries

- Do not send, schedule, import contacts, alter automations, or change suppression lists without explicit authorization.
- Do not invent consent, deliverability, attribution, audience, or performance data.
- Do not promise inbox placement or revenue; separate observed results from projections.
- Do not decide legal compliance, transactional classification, or contact eligibility on the user's behalf.

## Routing

- Use `suede-lead-magnets` for the asset that feeds a nurture sequence.
- Use `suede-churn-prevention` for cancellation, save, and dunning strategy.
- Use `suede-onboarding` for in-product activation and `suede-copy` for destination-page copy.
- Use `suede-ab-testing` for sequence experiments and `suede-revops` for lifecycle-stage orchestration.
- Use `suede-sms` when the same lifecycle program should also reach people by text: SMS layers on top of email, it does not replace it.
- Use `suede-deslop` before any email in the sequence goes to a real recipient.
- From those skills, route lifecycle sequence design, cadence, and message roles back to `suede-emails`.

## Worked contract

[Worked contract](references/usage-contract.md) gives a bounded input, expected output and failure check for this workflow.
