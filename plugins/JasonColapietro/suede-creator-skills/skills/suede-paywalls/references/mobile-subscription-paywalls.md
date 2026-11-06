# Mobile Subscription App Paywalls

Consumer iOS and Android subscription apps (fitness, learning, focus, faith, scanners) run on different paywall mechanics from a SaaS upgrade screen. The app stores handle billing. The paywall usually sits inside onboarding. Most revenue comes from a yearly plan sold on day one. Use this reference for those apps; the rest of the skill still governs copy, design, testing, the self-critique gate, and the subscription law check.

## Contents

- Placement: after the first personalized result
- Hard paywall vs. freemium
- Plan presentation
- Trials
- One abandon offer
- Store fees and web checkout
- Unit economics per download
- App Store review checklist

## Placement: after the first personalized result

The common sequence is **onboarding, then a personalized result, then the paywall**. Onboarding asks a few questions about the user's goal. The app shows something built for them: a plan, a score, a first analysis. The paywall follows while that result is still on screen, because the result is the value moment the paywall points at. A paywall on first launch, before anything personal has happened, asks for money with nothing to show.

## Hard paywall vs. freemium

Both are legitimate. A hard paywall blocks core use without a trial or purchase; freemium keeps a capped free tier. RevenueCat's State of Subscription Apps 2026 found hard-paywall apps converting roughly five times as many users to paid in the first 35 days as freemium apps, while one-year retention of yearly subscribers was about the same for both (27% vs. 28%). Freemium still fits when the free tier drives sharing or word of mouth. If you keep one, cap it daily so the user feels the limit inside the habit, not a month later.

## Plan presentation

1. **Lead with the yearly plan**, with the per-week or per-month equivalent as supporting text ("$0.58/week, billed $29.99 yearly"). The billed amount and period stay clear. The breakdown frames the price; it never replaces it.
2. **Offer at most one shorter option** (weekly or monthly) as the comparison.
3. **Localize prices by storefront** instead of converting one price.
4. **Test price, plan mix, trial length, and design remotely** so a change does not wait on an app release. Paywall platforms such as Superwall, RevenueCat Paywalls, and Adapty do this. Choose on fit with the stack; none is the default.

## Trials

- **Put a free trial on the yearly plan** and schedule a reminder before it ends. Surprise renewals drive refunds, one-star reviews, and chargebacks.
- **Trial length is a test, not a default.** RevenueCat's 2026 data shows trials of 17 days or more converting at a higher median rate than trials of four days or less, at the cost of waiting longer for revenue. Short trials suit apps where value lands in a day or two. Longer trials suit habits that take a week to form.

## One abandon offer

When someone closes the paywall without starting a trial, one discounted yearly offer is a standard move. Show it **once**, not on every close. It still follows the main skill's rules: respect the no, and no fake countdowns.

## Store fees and web checkout

Fees change and differ by country. Treat these as an October 2026 snapshot and check current terms before modeling:

- **Apple:** members of the App Store Small Business Program (under $1M in annual proceeds) pay 15% on subscriptions. Everyone else pays 30% in a subscriber's first year and 15% after.
- **Google Play (US, UK, EEA, from June 30, 2026):** a 10% service fee on subscriptions plus a 5% billing fee when Google Play billing is used, so 15% in practice. The 10% service fee also applies when users pay through an alternative biller or a web link; only the billing fee drops away. Other markets follow on later dates.
- **US iOS link-outs to web checkout** are allowed, and Apple's commission on them is still being set in court. Model the web path across a range of possible rates, not at zero.

**Web-to-app funnel:** ad, then a web onboarding quiz, then a web paywall, then a download link. It moves payment off the store and lets you test onboarding without app releases, but it adds a step between the ad and the app. Check each storefront's link-out rules before building it, and see [subscription-rules.md](subscription-rules.md) for the disclosure side.

## Unit economics per download

```
revenue per download = trial start rate × trial-to-paid rate × yearly price × (1 − store fee)
```

One founder's working estimate is 30% of downloads starting a trial and 30% of trials paying about $30 a year: roughly $2.70 per download before fees. Use that only as a starting assumption, and replace it with the app's own rates within a few weeks of launch. Revenue per download sets how much you can pay per install on ads or creators; do not set install bids off the borrowed estimate.

## App Store review checklist

- [ ] Price, billing period, trial length, and "auto-renews until cancelled" shown on the paywall
- [ ] Links to Terms of Use (EULA) and Privacy Policy
- [ ] Restore Purchases
- [ ] A visible close button and no dark patterns
- [ ] Trial-ending reminder scheduled
- [ ] `paywall_viewed`, `trial_started`, and `subscription_started` events fire with the paywall variant ID

---

*Patterns adapted from Blake Anderson's ai-app-playbook (MIT, October 2026). Conversion and trial-length data from RevenueCat's State of Subscription Apps 2026. Fees from Google's Android Developers Blog (June 2026), Apple's Small Business Program terms, and coverage of the Epic v. Apple link-out proceedings.*
