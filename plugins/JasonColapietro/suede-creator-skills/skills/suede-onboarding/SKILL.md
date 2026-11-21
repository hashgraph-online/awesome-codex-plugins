---
name: suede-onboarding
description: "Suede AI Onboarding Skills: time to value, ranked friction audits, first-value flows, empty states, checklists, and measurement. Use when asked \"users sign up but never activate\" or to improve registration and first-run setup. NOT FOR: non-account forms (suede-site-alchemy), lifecycle email copy (suede-emails), paywalls (suede-paywalls), cancellation (suede-churn-prevention), or unreviewed auth deployment."
metadata:
  display-name: "Suede AI Onboarding Skills"
  version: 3.0.0
---

# Suede AI Onboarding Skills

## Compatibility

Requires supplied funnel evidence or read access to the signup/onboarding surface. Browser inspection helps audit real behavior. Design output needs no production write access; auth changes require owner review.

For a concrete input, expected output, recovery path, and validation check, read
[the worked contract](references/worked-contract.md). Use it to check the handoff
before treating the task as complete.

Suede AI treats signup and onboarding as one path: the visitor who wants the product, the account that gets created, and the first moment the product proves itself. Remove friction at the registration boundary, define activation from retention evidence, sequence the first session, and instrument every step before claiming an "aha moment."

## Initial Assessment

Read `.agents/product-marketing.md` first if it exists (or `.claude/product-marketing.md`, or the legacy `product-marketing-context.md`) and ask only for what it does not cover.

Then find where the path breaks:

1. **Product context:** B2B or B2C, web or mobile, trial, freemium, or paid.
2. **Signup state:** steps, required fields, identity options, completion rate, and whether field-level analytics exist.
3. **Activation definition:** the action that marks "gets it," and whether cohort data shows retained users do it more than churned users.
4. **Post-signup state:** what happens in the first 30 seconds, where users stall, and current activation rate.

If the break is before the account exists, run the **Signup lane**. If after, run the **First-value lane**. Many audits need both.

---

## Signup lane

Full guidance (fields, identity options, mobile, verification, audit format, patterns by product type): [references/signup-flow.md](references/signup-flow.md).

Core rules:
- Every required field must earn its place before first use; defer the rest to progressive profiling.
- Offer the identity options your audience already uses (passkeys, Google, Apple, Microsoft, GitHub, SSO for IT buyers) next to email.
- Follow current NIST password guidance: length over composition rules, breached-password screening, paste allowed, no forced rotation.
- Disclose card requirements and renewal terms at the button when a trial auto-converts; legal detail lives in `suede-paywalls`.
- Let users into the product before verification when security allows.

Signup audit output: top 8 findings ranked by effect on completion (Issue, Impact with funnel step, Fix, Priority), then quick wins, high-impact changes, and at most 3 test hypotheses. Do not open with what the flow does well.

---

## First-value lane

### Principles

1. **Time to value decides everything.** Remove every step between signup and the core outcome.
2. **One goal per session.** The first session produces one successful outcome.
3. **Do, don't show.** Doing the thing beats a tour about the thing.
4. **Progress motivates when it is honest.** Show advancement toward the activation event, not toward busywork.

**Refuse by default:** a modal tour before the user has done anything; a "Welcome! Let's get started" interstitial between the user and the first action; checklist items that are settings toggles rather than value actions.

### Define activation

The activation event is the earliest action that correlates with retention:
- What do retained users do that churned users don't?
- What is the earliest signal of continued use?

Examples: project tool, create a project and invite a teammate. Analytics, install tracking and see a first report. Design tool, create and export or share. Marketplace, complete a first transaction.

If no cohort data exists, mark the event "unverified" and plan the analysis with `suede-analytics`.

### First 30 seconds

| Approach | Fits | Risk |
|----------|------|------|
| Product-first | Simple products, B2C, mobile | Blank-slate confusion |
| Guided setup | Products that need configuration | Friction before value |
| Value-first (sample data, templates) | Products that are empty on day one | Can feel unreal |

Whatever the approach: one clear next action, no dead ends, progress shown on multi-step setup.

### Checklists

Use for self-serve B2B and products with several setup steps. 3-7 items, ordered by value, quick wins first, dismissible, progress shown only where the remaining items are the activation path, celebration on the activation event.

### Empty states

Explain what the area is for, show what it looks like with data, give one primary action, and offer sample data or a template.

### Tours and tooltips

Only for non-obvious or power features. 3-5 steps, dismissible anytime, never repeated for returning users.

### Email and in-app together

Triggered email reinforces in-app progress rather than duplicating it: welcome (immediate), incomplete setup (24h, 72h), activation reached (next step), feature discovery (days 3, 7, 14). Sequence copy and deliverability go to `suede-emails`.

### Stalled users

Define "stalled" (days inactive, setup incomplete). Recover with a value reminder and blocker help by email, an in-app "pick up where you left off," and human outreach for high-value accounts.

---

## Measurement

| Stage | Metrics |
|-------|---------|
| Signup | Form start rate, completion rate (mobile vs. desktop), field-level drop-off, identity-option mix, verification completion |
| Activation | Activation rate, time to activation, steps to activation, activation by cohort and source |
| Early retention | Day 1, 7, 30 return rates by activated vs. not activated |

Track drop-off at every step from landing to retention and fix the largest loss first.

## Output Format

**Signup audit:** the ranked format above (details in `references/signup-flow.md`).

**Onboarding flow design**, headings verbatim, in order:

- **Activation Goal**: the event, plus the retention evidence behind it or "unverified"
- **Flow**: one entry per step with trigger, user action, success signal, drop-off measurement
- **Checklist Items**: 3-7 value actions (omit if no checklist)
- **Empty State Copy**: per surface
- **Email Triggers**: event and delay for each
- **Metrics Plan**: activation rate, time to activation, per-step drop-off
- **Test Hypotheses**: at most 3, from [references/experiments.md](references/experiments.md)

## Patterns by product type

| Product | Path |
|---------|------|
| B2B SaaS | Work-email or SSO signup → setup wizard → first value action → team invite → deeper setup |
| Marketplace | Light signup → profile → browse → first transaction → repeat |
| Mobile app | Apple, Google, or passkey → permissions in context → quick win → push opt-in after value |
| Content platform | Signup → follow or customize → consume → create → engage |

## Boundaries

- Do not invent an activation event, retention correlation, cohort result, or benchmark when product data is unavailable.
- Do not deploy signup, authentication, or onboarding changes, or alter stored user data, without explicit authorization and owner review.
- Do not remove security, consent, age, identity, or legal controls to raise a conversion number.
- Do not add forced invitations, premature paywalls, deceptive defaults, or manipulative progress mechanics.
- Do not claim lift without a current baseline and completed experiment; keep personal data out of examples.

## Routing

- `suede-site-alchemy` for landing pages, lead-capture, and non-account forms.
- `suede-emails` for onboarding sequences; `suede-sms` for text-message opt-in.
- `suede-paywalls` for upgrade moments and trial-expiry screens; `suede-pricing` for trial vs. freemium strategy.
- `suede-churn-prevention` for cancel flows and win-back.
- `suede-ab-testing` to size and read out tests; `suede-analytics` to instrument the funnel.
