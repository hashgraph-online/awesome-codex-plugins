---
name: suede-paywalls
description: "Suede AI Paywall Skills: paywalls, entitlement gates, usage limits, trial expiry, screen copy, trigger rules, experiment plans, and mobile subscription-app paywalls. Use when asked \"improve this upgrade prompt\" after users experience value, or \"design our App Store subscription paywall.\" NOT FOR: public pricing-page or tier architecture (suede-pricing), cancellation and save flows (suede-churn-prevention), or unapproved billing changes."
metadata:
  display-name: "Suede AI Paywall Skills"
  version: 2.0.1
---

# Suede AI Paywall Skills

## Compatibility

Requires the entitlement model, upgrade surface, and product context. Current subscription rules require browsing for the applicable jurisdiction/platform. Produces design drafts; billing and deployment are separate actions.

For a concrete input, expected output, recovery path, and validation check, read
[the worked contract](references/worked-contract.md). Use it to check the handoff
before treating the task as complete.

Suede AI designs in-product monetization around a truthful entitlement boundary and a value-aware moment, not interruption volume. Define when the user has enough context to evaluate an upgrade, what the paid change actually unlocks, and how to test the prompt without obscuring price, consent, or exit.

## Initial Assessment

**Check for product marketing context first:**
If `.agents/product-marketing.md` exists (or `.claude/product-marketing.md`, or the legacy `product-marketing-context.md` filename, in older setups), read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Before providing recommendations, understand:

1. **Upgrade Context** - Freemium → Paid? Trial → Paid? Tier upgrade? Feature upsell? Usage limit?

2. **Product Model** - What's free? What's behind paywall? What triggers prompts? Current conversion rate?

3. **User Journey** - When does this appear? What have they experienced? What are they trying to do?

---

## Paywall Trigger Points

### Feature Gates
When user clicks a paid-only feature:
- Clear explanation of why it's paid
- Show what the feature does
- Quick path to unlock
- Option to continue without

### Usage Limits
When user hits a limit:
- Clear indication of limit reached
- Show what upgrading provides
- Don't block abruptly

### Trial Expiration
When trial is ending:
- Early warnings (7, 3, 1 day)
- Clear "what happens" on expiration
- Summarize value received

### Time-Based Prompts
After X days of free use:
- Gentle upgrade reminder
- Highlight unused paid features
- Easy to dismiss

---

## Paywall Screen Components

1. **Headline** - Focus on what they get: "Unlock [Feature] to [Benefit]"

2. **Value Demonstration** - Preview, before/after, "With Pro you could..."

3. **Feature Comparison** - Highlight key differences, current plan marked

4. **Pricing** - Clear, simple, annual vs. monthly options

5. **Social Proof** - Customer quotes, "X teams use this"

6. **CTA** - Specific and value-oriented: "Start Getting [Benefit]"

7. **Escape Hatch** - Clear "Not now" or "Continue with Free"

---

## Specific Paywall Types

### Feature Lock Paywall
```
[Lock Icon]
This feature is available on Pro

[Feature preview/screenshot]

[Feature name] helps you [benefit]:
• [Capability]
• [Capability]

[Upgrade to Pro - $X/mo]
[Maybe Later]
```

### Usage Limit Paywall
```
You've reached your free limit

[Progress bar at 100%]

Free: 3 projects | Pro: Unlimited

[Upgrade to Pro]  [Delete a project]
```

### Trial Expiration Paywall
```
Your trial ends in 3 days

What you'll lose:
• [Feature used]
• [Data created]

What you've accomplished:
• Created X projects

[Continue with Pro]
[Remind me later]  [Downgrade]
```

---

## Self-Critique Gate (run before delivering any screen copy)

Do not hand over a drafted paywall until you have re-read it against
Anti-Patterns to Avoid and Boundaries below, and answered these out loud:

1. Where is the close/dismiss control, and is it visible without scrolling or hovering?
2. Is the price (including what renews, when, and at what amount) stated on the screen?
3. Does any urgency claim ("ends today", a countdown) correspond to a real deadline?
4. Can the user reach the free path in one tap from this screen?
5. Does any copy assign blame, shame, or loss the user did not actually incur?
6. If this screen starts or renews a subscription: are the renewal price, interval, trial end date, and cancel path shown before purchase, and is auto-renewal consent separate where the law requires it?

Name every hit before delivering. A hit on 1, 3, 4, or 6 is a blocker: fix the
draft, don't ship it with a caveat.

---

## Subscription Law Check

Any paywall that starts a trial, converts a trial, or renews a subscription must meet current auto-renewal rules. Status as of October 2026, with sources, in [references/subscription-rules.md](references/subscription-rules.md). The short version:

- **US:** the FTC's 2024 click-to-cancel rule was vacated in July 2025 and the FTC is back at the advance-notice stage (March 2026), but ROSCA, FTC Act Section 5, and state laws still apply. California (since July 1, 2025) requires online click-to-cancel, limits save offers, and requires price-increase notices 7 to 30 days ahead.
- **UK:** DMCC unfair-practice fines are live; subscription rules (trial and renewal reminders, cooling-off, easy exit) are planned for January 1, 2027.
- **EU:** an online withdrawal function has been required since June 19, 2026.
- **App stores:** disclose renewal price, period, and terms on the paywall; check current external-purchase rules before linking out.

---

## Timing and Frequency

### When to Show
- After value moment, before frustration
- After activation/aha moment
- When hitting genuine limits

### When NOT to Show
- During onboarding (too early), except in consumer mobile subscription apps, where the paywall follows the first personalized result inside onboarding
- When they're in a flow
- Repeatedly after dismissal

### Frequency Rules

Defaults unless a running experiment says otherwise: ship these numbers, and
say so when a test moves them:

- Max **1** paywall impression per session.
- Cooldown **>= 7 days** after a dismiss; **>= 14 days** after a second dismiss.
- Suppress a given gate entirely after **3 lifetime dismissals**.

Instead of "annoyance signals," instrument the ones a reviewer can read: dismiss
rate per gate, post-paywall session-abandon rate, plus the impression,
click-through, completion, revenue-per-user, and post-upgrade churn metrics the
experiment reference tracks.

---

## Upgrade Flow and Testing

Keep the path from paywall to payment in-context and pre-filled, and grant
access the moment payment clears: the checkout and post-upgrade activation flow
itself belongs to `suede-onboarding`.

**For frequency, trigger-timing, copy, and price-presentation experiments**:
including which of the above defaults are worth testing first: See
[references/experiments.md](references/experiments.md). Use `suede-ab-testing`
to design and read out the test.

**For consumer iOS and Android subscription apps** (paywall inside onboarding,
yearly-first plans, trials and reminders, store fees, web checkout, revenue per
download): See
[references/mobile-subscription-paywalls.md](references/mobile-subscription-paywalls.md).

---

## Anti-Patterns to Avoid

### Dark Patterns
- Hiding the close button
- Confusing plan selection
- Guilt-trip copy
- Fake countdowns or "limited" offers with no real deadline

### Conversion Killers
- Asking before value delivered
- Too frequent prompts
- Blocking critical flows
- Complicated upgrade process

---

## Boundaries

- Do not fabricate entitlement, plan, price, conversion, trial, or usage-limit data.
- Do not change billing, entitlements, app configuration, experiments, or live paywalls without explicit authorization.
- Do not recommend hidden close controls, confusing consent, forced continuity, obstructive cancellation, or false urgency.
- Do not decide refund, tax, legal, platform-policy, accessibility, or billing-risk terms for the user.

## Routing

- Use `suede-churn-prevention` for cancel and save flows.
- Use `suede-site-alchemy` for public pricing pages and `suede-pricing` for tier architecture.
- Use `suede-onboarding` to reach first value and `suede-ab-testing` to validate paywall variations.
