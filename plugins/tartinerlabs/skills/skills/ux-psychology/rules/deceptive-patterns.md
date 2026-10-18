---
title: Deceptive Patterns
impact: CRITICAL
tags: dark-patterns, ethics, consent, urgency, cancellation, legal
---

**Rule**: Never use psychology against the user's interest. Every persuasion technique in this skill becomes a deceptive pattern the moment it relies on false information, hidden costs, or making the user's real choice hard.

**Evidence**: Mathur et al. 2019, "Dark Patterns at Scale" (CSCW) — a crawl of ~11K shopping sites found dark patterns on about 11% of them. Brignull, *Deceptive Patterns* (2023) and deceptive.design catalogue the types. Regulators now act on them: the FTC staff report "Bringing Dark Patterns to Light" (2022); the EU Digital Services Act, Art. 25; and the CJEU's *Planet49* ruling (2019) that a pre-ticked box is not valid consent.

### When Building

Do not build, even when asked casually — flag it and offer the honest version:

- **Fake urgency or scarcity** — countdown timers that reset, "only 2 left" that isn't true, "12 people are viewing this" without real data
- **Confirmshaming** — decline options that insult the user ("No thanks, I don't like saving money")
- **Roach motel** — sign-up in one click, cancellation behind calls, chats, or five screens
- **Sneaking** — items, insurance, or donations added to the cart by default; costs revealed only at the last step
- **Pre-ticked consent** — marketing, data sharing, or add-ons opted in by default
- **Disguised ads and fake system UI** — ads styled as content, pre-permission screens styled as OS dialogs
- **Nagging** — the same request after every dismissal
- **Trick wording** — double negatives in opt-outs, "Accept" large and "Reject" hidden in a link
- **Fake social proof** — invented reviews, counters, or testimonials

### When Auditing

- Timers, stock counts, and "people viewing" numbers: are they backed by real data in the code?
- Cancellation, unsubscribe, and account deletion: count the steps against sign-up
- Checkboxes and toggles for consent or paid extras: what is the default?
- Cookie and consent banners: is "Reject" as easy as "Accept"?
- Pricing: is the total shown before the final step?

Report each as CRITICAL with the regulation or source it conflicts with.

### Correct

```tsx
// Opt-in is unchecked; declining is a neutral, equal-weight option
<Checkbox checked={marketing} onChange={setMarketing}>
  Email me product updates (about once a month)
</Checkbox>
<Button variant="secondary" onPress={skip}>Not now</Button>
```

### Why This Matters

Deceptive patterns raise one metric briefly and pay for it in refunds, chargebacks, support load, churn, app-store rejection, and regulatory fines. Users who feel tricked do not come back and tell others.

### Alternatives

Real urgency stated honestly is fine — an actual sale end date, real low stock from inventory data, a genuine limited cohort. Defaults that favour the business are acceptable when they also serve the user and are easy to change (`rules/defaults.md`). The line is truth and an easy, equally visible way out.
