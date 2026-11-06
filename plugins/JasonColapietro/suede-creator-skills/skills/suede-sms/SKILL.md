---
name: suede-sms
description: "Design consent-aware SMS/MMS programs: channel fit, welcome, cart recovery, post-purchase and win-back flows, exact copy, segment counts, cadence, quiet hours, platform selection, and measurement. Use when asked to \"draft our SMS welcome flow\" or audit a text program. Checks current consent, opt-out, and registration requirements. NOT FOR: email (use suede-emails), capture UX (use suede-site-alchemy), legal certification, or sending, scheduling, importing, or registering anything."
metadata:
  display-name: "Suede AI SMS Skills"
  version: 1.1.0
---

# Suede AI SMS Skills

## Compatibility

Works from supplied consent, registration, audience, and performance evidence; current legal and carrier checks need web access. No SMS connector or sending account is bundled.

For a concrete input, expected handoff, and failure check, read
[the worked handoff](references/worked-handoff.md).

Design consent-aware message programs for commerce, mobile, and SaaS
use cases where immediacy can earn its interruption cost. It combines sequence
logic, sender identity, cadence, carrier constraints, and measurement without
claiming legal certification or sending messages.

## Before Starting

**Check for product marketing context first:**
If `.agents/product-marketing.md` exists (or `.claude/product-marketing.md`, or the legacy `product-marketing-context.md` filename, in older setups), read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Gather this context (ask if not provided):

### 1. Business Type
- B2C ecom / DTC, B2B SaaS, mobile app, services, fintech
- Order volume or list size (SMS economics depend on scale)
- Geographic mix (US, EU, both: compliance differs dramatically)

### 2. Current State
- Existing SMS program (platform, list size, opt-in rate, opt-out rate, revenue/send)
- Email program (SMS works best as a layer on top, not a replacement)
- Phone number type: short code, toll-free, long code (10DLC)
- Sequences already running (so a new flow does not double-tap the same contact)

### 3. Compliance Posture
- US: A2P 10DLC registration complete? (Carriers block unregistered 10DLC traffic outright since February 1, 2025)
- Opt-in mechanism in use? (Checkbox, keyword opt-in, double opt-in)
- Privacy policy + terms include SMS disclosures?

### 4. Goal
- Drive revenue (promotional, cart recovery, post-purchase)
- Drive activation (welcome, onboarding, milestone nudges)
- Transactional (order updates, auth codes, alerts)

---

## When SMS Beats Email

SMS is not "another email." Use it where the channel's properties win:

| Use Case | SMS or Email? | Why |
|----------|---------------|-----|
| Abandoned cart recovery | **SMS first** | Texts are read within minutes; the cart is still top of mind |
| Order/shipping updates | **SMS** | Customers want it now, on their phone |
| Flash sale / limited drop | **SMS** | Urgency channel; immediate read |
| Auth codes / 2FA | **SMS** (or app) | Latency-sensitive, must arrive in seconds |
| Welcome series | **Email primary, SMS layer** | Email carries the long-form content |
| Educational nurture | **Email** | Too much text for SMS, costs add up |
| Newsletter | **Email** | Wrong channel for SMS |
| Win-back lapsed customers | **Both** | SMS for the strong nudge, email for the offer detail |
| Post-purchase upsell | **SMS** | High open rate, ride the purchase momentum |

**General rule**: SMS earns the right to interrupt because of opt-in. Use it for messages that genuinely benefit from immediacy. If it could wait 24 hours, send it via email.

---

## Compliance: Read First

**Compliance is the foundation, not an afterthought.** TCPA statutory damages run $500 per message, up to $1,500 when willful (47 U.S.C. 227(b)(3)), and class actions multiply that across every recipient. The basics:

### US: TCPA (Telephone Consumer Protection Act)

1. **Express written consent** required for marketing SMS. Implied consent doesn't count.
2. **Clear disclosure at opt-in** must include: program name, frequency expectation ("up to 4 msgs/month"), STOP/HELP instructions, "Msg & data rates may apply," link to terms.
3. **Honor opt-outs immediately and on any reasonable request.** Since April 11, 2025 the FCC requires honoring revocation made by any reasonable means, explicitly including replies of stop, quit, end, revoke, opt out, cancel, or unsubscribe, within 10 business days at the latest. Platforms should process keywords instantly; free-text requests ("please stop texting me") count too. One confirmation text is allowed within 5 minutes, with no marketing in it. The separate "revoke-all" provision (one opt-out covering unrelated message types) is delayed to January 31, 2027.
4. **Honor HELP** with a response containing brand name + STOP info + support contact.
5. **Quiet hours**: federal rules bar telephone solicitations before 8am or after 9pm recipient-local. Several state laws are stricter (Florida, Oklahoma, and Washington use 8am to 8pm, and Texas brought marketing texts under its telephone solicitation law in September 2025): default to 9am to 8pm recipient-local and check each state in scope.
6. **Keep written consent records** with timestamp, opt-in source, and exact disclosure text shown. Auditable.

### US: A2P 10DLC Registration

Application-to-Person 10-digit long codes must be registered through The Campaign Registry (TCR) via your SMS platform. Since February 1, 2025 US carriers block unregistered 10DLC traffic instead of throttling it; Twilio, for example, returns error 30034 (https://www.twilio.com/docs/api/errors/30034). Registration now also expects a privacy policy and SMS terms linked from the opt-in form, and carriers compare live traffic against the registered sample messages.

**Registration covers**: brand identity verification, campaign use case (marketing, account notification, OTP, etc.), sample messages, opt-in mechanism, opt-out language. Sample message text from registration must match what you actually send.

### EU/UK: GDPR-derived consent

- Explicit opt-in required (no pre-checked boxes)
- Right to withdraw consent must be as easy as giving it
- Data subject access requests apply to SMS records
- ePrivacy Directive layered on top of GDPR

### Canada: CASL

- Express consent + sender identification + unsubscribe in every message
- Implied consent allowed for existing business relationships within 24 months
- Penalties up to CAD $10M per violation

**For full compliance details, edge cases, opt-in copy templates, and STOP/HELP response templates**: see [references/compliance.md](references/compliance.md).

---

## Phone Number Types (US)

| Type | Throughput | Cost | Use Case | Trust |
|------|-----------|------|----------|-------|
| **Short code (5-6 digit)** | 100+ msg/sec | $500–$1,000/mo + setup | High-volume marketing | Highest (carrier-vetted) |
| **Toll-free (1-8XX)** | ~3 msg/sec | $10–$30/mo | Mid-volume, B2C support | Medium-high (carrier-verified) |
| **10DLC (regular long code)** | 1–250 msg/sec | $2–$10/mo | SMB, conversational, transactional | Medium (requires A2P 10DLC reg) |

**Rule of thumb**: list <10K = 10DLC. List 10K–100K = toll-free. List 100K+ = short code.

---

## Core Principles

### 1. Every send has a real cost
SMS isn't free. At $0.0075–$0.04 per send + carrier fees, a 100K send costs $750–$4,000. This forces relevance: you can't "blast." Segment hard.

### 2. Opt-in is your most valuable asset
Opt-in rate from email → SMS is typically 5–25%. A high-quality SMS list of 10K beats a low-quality list of 100K. Optimize opt-in quality, not volume.

### 3. Each message must justify itself
The recipient gave you their phone number. Every send should pass: "would I be glad I got this text?" If no, don't send.

### 4. Brevity + clarity
160 GSM-7 characters = 1 SMS segment. 161+ chars = 2 segments (you're billed for 2). Emojis force UCS-2 encoding (70 chars per segment). Plan for segment count.

### 5. One CTA, one link
Short links are mandatory (`klvy.co`, `txt.attn.tv`, branded short domain). Track UTM params on every link.

### 6. Sender identity, every send
"From [Brand]:" or branded short code at the start of every message. Even on automated flows. Recipients can't see "from" address: they need it inline.

---

## SMS Sequence Types

### Welcome / Opt-In Confirmation (immediate)

The confirmation text must name the program, state message frequency, and
carry "Msg & data rates may apply" plus HELP and STOP instructions.

Send 1: Confirmation + reward (immediate)
> From Acme: Thanks for joining! Here's 10% off: ACME10. Use at checkout: acme.co/sale. Reply STOP to opt out.

Optional Send 2 (24h later): Reminder + best-seller showcase

### Abandoned Cart (highest-ROI flow for ecom)

- Send 1 (30 min after abandon): "Forget something? Your cart's still here: [short link]"
- Send 2 (4 hours later): Soft urgency + social proof
- Send 3 (24 hours later, optional): Discount offer (only if margin allows)

**Note**: Discount on first message trains customers to abandon. Reserve discount for Send 2 or 3.

### Browse Abandonment

- Send 1 (1 hour after browse): Product + "Thinking it over?" + link

### Post-Purchase

- Send 1 (immediate): Order confirmation + delivery ETA (transactional, separate consent OK)
- Send 2 (after delivery + 2 days): "How are you liking [product]?" + review prompt + cross-sell

### Win-Back (lapsed)

- Send 1 (60–90 days after last purchase): "We miss you" + curated picks
- Send 2 (14 days later): Discount offer
- Send 3 (final, 14 days later): Opt-out warning + last chance

### Promotional / Campaign Sends

- Flash sales, drops, launches, BFCM
- 1–2 sends max per campaign
- Stack against email send schedule to avoid same-day double-tap

### Transactional (separate compliance bucket)

- Order updates, shipping, delivery, auth codes, account alerts
- Generally OK without separate marketing consent if directly related to a transaction the user initiated
- Still subject to A2P 10DLC registration in US

**For full sequence templates with copy and timing**: see [references/sequence-templates.md](references/sequence-templates.md).

---

## SMS Copy Guidelines

### Structure
1. **Sender ID** ("From Acme:" or brand short code): required
2. **Hook**: first 5 words decide if they read on
3. **Value**: what's in it for them, specifically
4. **CTA + short link**: single action, single URL
5. **Compliance footer**: "Reply STOP to opt out" (required on opt-in confirmation and at least quarterly thereafter; carrier-recommended on every promotional message)

### Length

- **160 chars (GSM-7)** = 1 segment. Aim here.
- **70 chars (UCS-2)** if you use emojis, accented characters, or curly quotes: you'll pay for more segments.
- **161–306 chars** = 2 segments (concatenated SMS). Acceptable for richer messages, but you're paying double per send.
- **MMS** (image + up to 1,600 chars) = 3–5× the SMS cost. Use sparingly for high-impact moments.

### Voice

- Conversational, not corporate. SMS feels personal: write like you're texting a friend.
- No subject line, no formatting, no marketing-speak.
- Emojis are fine in moderation (one per message, situationally).
- ALL CAPS reads as shouting. Avoid except for explicit codes (e.g., "Use ACME10").

**Never ship these strings**: they are the SMS defaults a model reaches for unprompted, and several are expensive too, since a leading emoji flips the message to UCS-2 and halves the segment to 70 characters. Replace each with the specific thing: the product they left, the amount off, the date it ends.

- "Don't miss out!" / "Hurry, ends soon!" / "LAST CHANCE" / "Time is running out"
- "Hey [Name]! 👋" / "Hey friend!" / "Psst..." / "We miss you 😢" / "It's been a while!"
- "Exclusive offer just for you" / "You've been selected" / "Tap here" with no statement of what is on the other side
- Flame, siren, alarm-clock, or party-popper emoji as the opener

### Personalization

- First name token only when accurate and appropriate; test its effect on the actual audience
- Recent product/category browse-based
- Location-based offers (where applicable)

---

## Platform Selection

Evaluation examples, not guaranteed integrations: this pack ships no SMS connectors. Before recommending one, verify vendor
documentation, authenticated access, per-message cost, carrier support, consent storage, quiet hours, STOP/HELP behavior, and send limits.

| Platform | Best For | Cost Tier | Verify Before Use |
|----------|----------|-----------|-------------------|
| **Klaviyo SMS** | DTC ecom already on Klaviyo email | $$ | Store integration, consent, attribution |
| **Postscript** | DTC Shopify ecom, deep integration | $$ | Store integration, consent, attribution |
| **Attentive** | Mid-market+ ecom, full-service | $$$ | Store integration, consent, attribution |
| **Twilio / Plivo** | Custom builds, transactional, devs | $ (raw API) | Number registration, throughput, callbacks |
| **Brevo SMS** | EU-focused, email + SMS combo | $ | Regional coverage, orchestration, suppression |
| **SimpleTexting** | SMB, simple needs, ease of use | $ | Regional coverage, consent record |
| **Customer.io** | Behavior-based automation + SMS | $$ | Regional coverage, orchestration, suppression |
| **AudienceTap** | Specialized DTC capture | $ | Capture method, consent record, carrier coverage |

**Quick picks**:
- Already on Klaviyo for email + DTC/ecom → **Klaviyo SMS** (no second platform to learn)
- Shopify ecom, want deeper SMS-specific features → **Postscript**
- Building custom SMS into a product → **Twilio**
- B2B SaaS doing transactional/auth → **Twilio** or **Customer.io**

**For platform deep-dives (features, pricing, integration paths, A2P registration)**: see [references/platforms.md](references/platforms.md).

---

## Measurement

### Key Metrics

| Metric | Definition | Evidence needed for a decision |
|--------|------------|--------------------------------|
| Opt-in rate | New valid consents / eligible capture impressions | Capture source, period, jurisdiction, and deduplicated denominator |
| CTR | Unique attributed clicks / delivered messages | Link tracking, delivery and click definitions, bot filtering |
| Conversion rate | Attributed conversions / delivered messages | Attribution window, event definition, comparison cohort |
| Revenue per send | Attributed revenue / sent messages | Refund handling, attribution window, gross versus net basis |
| Opt-out rate | Valid opt-outs / delivered messages | Flow, send frequency, audience, and recipient-local timing |
| Cost per send | Total messaging cost / sent messages | Provider, carrier, country, message segments, and billed fees |
| List growth | New consents minus opt-outs and invalid records | Opening population, period, and consent evidence |

Set review thresholds from the user's dated baseline, unit economics, consent
requirements, and acceptable harm. Use an external benchmark only with its
source, date, comparable audience, and metric definition; no fixed range here
establishes a healthy program or expected result.

### What to track in analytics

- UTM tag every link: `utm_source=sms&utm_medium=sms&utm_campaign=[campaign-name]`
- Conversion attribution: SMS-driven sessions, last-click revenue, assisted conversions
- LTV comparison: define cohorts, acquisition mix, observation window, margin, and censoring. A subscriber comparison is descriptive; it does not establish incremental SMS impact.

### What to A/B test

- Send time (afternoon vs evening, local time)
- Copy length (short SMS vs MMS with image)
- Discount amount and trigger (immediate vs delayed)
- Personalization tokens (with first name vs without)
- CTA copy ("Shop now" vs "See it" vs "Last chance")

---

## Output Format

When the user asks for an SMS plan, return these six sections, in this order, with these headings:

1. **Compliance check**: Are they registered for A2P 10DLC (if US)? Is the opt-in mechanism compliant? Flag blockers first.
2. **Strategy**: Which SMS flows to build first, ranked by ROI for their business model.
3. **Sequence designs**: For each priority flow, one block per message, in this exact shape:

```
Trigger: [event that fires this message]
Delay: [time after the trigger]
Copy: (NN chars, N segments, GSM-7|UCS-2)
[the message exactly as it would send, sender ID and compliance footer included]
CTA link: [short link + UTM params]
Segment: [who receives this, who is excluded]
Compliance footer: [STOP language present / not required here, and why]
```

4. **Platform recommendation**: Based on stack, list size, and complexity.
5. **Measurement plan**: KPIs, benchmarks, A/B test queue.
6. **Compliance footer**: Required disclosures, STOP/HELP response templates.

Keep recommendations specific. Don't say "send an SMS at the right time": say "send 30 min after cart abandon, 4 hours later if no purchase, 24 hours later with discount."

---

## Pre-delivery self-check

Run this on the messages you just drafted, not on the user's program: section 1 above audits the program, and nothing else checks the copy. Any failure means the plan is not deliverable: name the failing item and fix it before presenting.

- [ ] Every message carries the sender ID inline
- [ ] Every message shows its character and segment count, and stays inside the segment budget you declared
- [ ] Opt-in confirmation and at least one message per quarter carry STOP language
- [ ] Every send time falls inside 9am–8pm recipient-local
- [ ] No personal phone number appears in any draft
- [ ] The drafted copy is consistent with the sample text declared at A2P registration

---

## Common Mistakes

1. **Treating SMS like email**: sending daily promotional blasts. Opt-out rates spike, list dies.
2. **Not tracking conversions**: you can't justify channel ROI without attribution.
3. **No throttling on bulk sends**: burst sends trigger carrier filtering. Use platform throttling.

---

## Boundaries

- Do not send or schedule messages, import or purchase lists, register numbers,
  change carrier settings, or mutate consent records without verified live
  state and explicit approval.
- Do not treat this skill as legal advice or claim compliance. Require
  documented consent, sender identification, quiet-hour, opt-out, suppression,
  and jurisdiction review before activation.
- Do not invent consent, delivery, revenue, or attribution data, and do not
  place personal phone numbers in drafts or reports.

## Routing

- Use `suede-emails` for the email side of a coordinated lifecycle program.
- Use `suede-site-alchemy` for phone-number capture experiences.
- Use `suede-churn-prevention` for approved win-back strategy.
- Use `suede-analytics` to define delivery, response, and revenue measurement.
- Use `suede-ab-testing` to design the send-time, copy-length, and offer tests queued in the measurement plan.
- Use `suede-deslop` before any message goes to a real recipient.
- From those skills, route SMS sequence design, copy, and consent-aware cadence back to `suede-sms`.
