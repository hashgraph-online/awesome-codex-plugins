# Subscription and Auto-Renewal Rules for Paywalls

Status checked October 23, 2026. This is a design checklist for the user's counsel, not legal advice. Rules change; re-check the sources before shipping a paywall that starts or renews a subscription.

## United States

**FTC click-to-cancel rule: not in force.** The FTC's amended Negative Option Rule (October 2024) was vacated in full by the Eighth Circuit in July 2025 on procedural grounds. The FTC formally conformed the rule to that decision in February 2026, then published an advance notice of proposed rulemaking on March 13, 2026 (docket FTC-2026-0265, comments closed April 13, 2026). As of October 2026 no proposed or final rule has followed. Sources: [FTC Negative Option Rule page](https://www.ftc.gov/legal-library/browse/rules/negative-option-rule), [Federal Register ANPRM](https://www.federalregister.gov/documents/2026/03/13/2026-04952/rule-concerning-the-use-of-prenotification-negative-option-plans).

**What still applies federally:**
- **ROSCA** (Restore Online Shoppers' Confidence Act, 15 U.S.C. 8401-8405): before collecting billing information, clearly disclose all material terms; get express informed consent before charging; provide a simple mechanism to stop recurring charges.
- **FTC Act Section 5**: the FTC continues to bring negative-option cases (deceptive enrollment, hidden terms, obstructed cancellation) without the vacated rule.

**State auto-renewal laws.** Roughly 30 states have them. California's amended Automatic Renewal Law (AB 2863, in force July 1, 2025) is the strictest common baseline:
- Express affirmative consent to the auto-renewal itself, with the charge amount and frequency disclosed before billing details are confirmed; keep consent records for 3 years or 1 year after the contract ends, whichever is longer.
- Free-to-paid trial conversions are covered.
- If sign-up was online, cancellation must be available online through a "click to cancel" link or button.
- Save offers during online cancellation are allowed only while the click-to-cancel option stays prominently and continuously displayed next to them.
- Price increases need clear notice 7 to 30 days before they apply, with cancellation instructions.
- An annual reminder stating the product, charge amount and frequency, and how to cancel.
Source summary: [Kilpatrick Townsend on AB 2863](https://ktslaw.com/en/insights/alert/2024/10/california-latest-automatic-renewal-law-amendments-take-effect-in-july-2025); statute: Cal. Bus. & Prof. Code §17600 et seq.

## United Kingdom

- **Unfair commercial practices (DMCC Act 2024, Part 4)** have been directly enforceable by the CMA since April 6, 2025, with fines up to 10% of global turnover. Misleading urgency, hidden mandatory fees (drip pricing), and fake reviews are in scope. Source: [CMA207 guidance](https://www.gov.uk/government/publications/unfair-commercial-practices-cma207).
- **Subscription contracts regime (DMCC Act, Part 4 Chapter 2)** is planned to start January 1, 2027 for contracts made on or after that date. The draft Consumer Subscription Contracts (Cancellation and Information) Regulations 2026 were laid before Parliament on October 19, 2026 and still need approval. Expect: key information before contract, reminders before a free or discounted trial ends and before certain renewals, a 14-day cooling-off period at the start and after trials and some renewals, and an easy way to exit. Build to it now if UK subscribers matter.

## European Union

- **Withdrawal button.** Directive (EU) 2023/2673 added Article 11a to the Consumer Rights Directive: since June 19, 2026, traders selling online must provide a clearly labeled withdrawal function so consumers can exercise their 14-day right of withdrawal as easily as they signed up. Source: [Directive (EU) 2023/2673](https://eur-lex.europa.eu/eli/dir/2023/2673/oj).
- **Unfair Commercial Practices Directive** Annex I blacklists false "available for a very limited time only" claims made to force an immediate decision.
- A proposed Digital Fairness Act targeting dark patterns and subscription traps has been in preparation; check its status before planning EU-wide paywall changes.

## App stores

- **Apple:** subscription paywalls must show the renewal price, billing period, and what the user gets before purchase, plus links to terms and privacy (App Review Guidelines 3.1.2). US-storefront rules on linking to outside purchase methods have been in active litigation since 2025 and were still moving in 2026; read the current Guidelines 3.1.1 and 3.1.3 and the latest court status before designing an external-checkout path.
- **Google Play:** subscription offers must clearly disclose price, billing frequency, trial terms, and how to cancel, per the current Play Developer Program Policy on subscriptions.

## Paywall design checklist

1. Price, billing interval, renewal date, and trial end date visible on the paywall, not behind a link.
2. Separate, unchecked consent for auto-renewal where required.
3. Trial reminders before conversion (UK requires them from 2027; many teams send them everywhere).
4. Online cancellation as easy as sign-up, reachable in-product.
5. Save offers never block or bury the cancel path.
6. Price-increase notices with cancellation instructions inside the required window.
7. Consent and disclosure records retained.
