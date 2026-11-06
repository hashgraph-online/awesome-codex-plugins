# Signup Flow: Account Creation, Registration, and Trial Start

The first half of the activation path: from "I want this" to a created account. Read this when the job is signup conversion. Post-account activation lives in SKILL.md.

## Contents
- Intake
- Field-by-field guidance
- Identity options (passkeys, social sign-in, SSO, magic links)
- Single-step vs. multi-step
- Trust and friction
- Mobile
- Post-submit and verification
- Measurement
- Common patterns by product type

---

## Intake

1. **Flow type:** free trial, freemium, paid account, waitlist, B2B or B2C.
2. **Current state:** steps or screens, required fields, completion rate, where drop-off happens, and whether field-level analytics exist or only funnel totals.
3. **Constraints:** what data is truly needed before first use, compliance needs (age gates, consent, KYC), and what happens immediately after submit.

## Principles

- **Every required field must justify itself before first use.** Can it wait for progressive profiling? Can it be inferred (company from email domain)?
- **Value before commitment.** Let people see or try something before the account wall when the product allows it.
- **Lower perceived effort.** Group fields, show progress on multi-step flows, use smart defaults and autofill.
- **No surprises.** Say how long it takes and what happens next.

## Field-by-field guidance

**Email.** One field (no "confirm email"), inline format validation, typo suggestions for common domains, clear errors.

**Password.** Current NIST guidance (SP 800-63B-4, final August 2025): require at least 15 characters when the password is the only factor (at least 8 when it is part of multi-factor), allow at least 64 characters including spaces and Unicode, impose no composition rules (no forced symbols or digits), screen against breached and common-password lists, and do not force periodic rotation. Allow paste and password managers. Show requirements up front, offer a show-password toggle. Source: [NIST SP 800-63B-4](https://pages.nist.gov/800-63-4/sp800-63b.html).

**Name.** Ask only if used immediately. Test one "Full name" field against a first/last split.

**Phone.** Defer unless essential (SMS verification, sales callback). If collected for marketing texts, consent rules apply; route to `suede-sms`.

**Company, role, team size.** Defer when possible, infer from email domain, auto-suggest as they type. One use-case question at most at signup; the rest belongs in first-run onboarding.

## Identity options

| Option | When it fits | Watch for |
|---|---|---|
| **Passkeys** | Consumer and prosumer apps, repeat-login products | Offer alongside another method until coverage is proven in your analytics; support account recovery |
| **Social sign-in** (Google, Apple, Microsoft, GitHub) | B2C: Google and Apple. B2B: Google and Microsoft. Developer tools: GitHub | iOS apps that offer third-party social login generally must also offer Sign in with Apple or an equivalent privacy-focused option; check current App Store Review Guideline 4.8 |
| **Enterprise SSO** (SAML, OIDC) | B2B with IT buyers | Usually a paid-tier feature; route packaging to `suede-pricing` |
| **Magic link or one-time code** | Low-frequency products, mobile-first | Email deliverability becomes signup reliability |

Place the most-used option first and separate it visually from the email form.

## Single-step vs. multi-step

**Single-step** fits three fields or fewer, simple B2C, and high-intent traffic.
**Multi-step** fits four or more fields or B2B segmentation. Show progress, lead with easy fields, put harder ones later, allow back navigation, and save progress across refresh.

Progressive pattern: (1) email or identity provider, (2) password or passkey plus name, (3) optional customization.

## Trust and friction

- "No credit card required" only when true. If a card is required, say when the first charge happens and how to cancel, next to the button. Auto-renewing trials carry disclosure and consent rules; see `suede-paywalls` for the current US, UK, and EU requirements.
- A privacy line and a link to the policy near the submit button.
- Inline validation, specific errors with a recovery path ("Email already registered: sign in or reset password"), never clear the form on error, move focus to the problem field.
- Visible labels; placeholders are examples, not labels.
- Bot protection: prefer invisible or risk-based checks over puzzle CAPTCHAs, and measure completion before and after.

## Mobile

Touch targets at least 44 by 44 points (iOS) or 48 by 48 dp (Android), correct keyboard types, autofill and one-time-code autofill, single column, sticky primary button, real-device testing.

## Post-submit and verification

- Clear confirmation and one next step.
- If email verification is required: say what to do, offer resend, mention spam folders, allow changing the address.
- Prefer letting users explore before verification and gating only the actions that need a verified address.
- Auto-login after signup unless security rules require otherwise.

## Measurement

- Form start rate (landed to first interaction)
- Completion rate (started to submitted), split mobile and desktop
- Field-level drop-off and error rate by field
- Identity-option mix (passkey, social, email)
- Time to complete
- Verification completion and time to verify

## Signup audit output

Do not open with what the flow does well. Rank findings by effect on completion and return the top 8; list any remainder by name in one line. Cap test hypotheses at 3.

For each finding: **Issue**, **Impact** (mechanism and the funnel step: start, field, submit, verification; give a number only when labeled modeled with its assumption and measured baseline), **Fix**, **Priority**.

Then: quick wins (same day), high-impact changes (week-level), test hypotheses (at most 3). If a redesign is requested: field set with rationale, order, label, placeholder, button, and error copy, and layout notes.

## Common patterns by product type

| Product | Pattern |
|---|---|
| B2B SaaS trial | Google or Microsoft sign-in or email, then name and company (role optional), then first-run onboarding |
| B2C app | Apple, Google, or passkey, then straight into the product, profile later |
| Waitlist | Email only, optional use-case question, confirmation with position or timing |
| E-commerce | Guest checkout by default, optional account after purchase |
