# Pricing-page design: cases and conversion patterns

A reference complementing `hicks-law-pricing` with case patterns from real pricing-page design and the conversion-rate-optimization literature.

## The 3-tier convention's history

The 3-tier (Bronze / Silver / Gold; Starter / Pro / Enterprise; Free / Plus / Premium) layout descends from earlier print-and-direct-mail pricing presentation. Magazines offered "1 year / 2 year / 3 year" subscriptions; phone companies offered "Basic / Standard / Premium" plans; insurance offered "Catastrophic / Standard / Comprehensive."

The recurring three-options pattern works for the same reasons across centuries:

- It maps to a natural mental model (small, medium, large).
- It enables the **anchoring effect**: a high-priced option makes the middle look reasonable; a low-priced option makes the middle look like a real value.
- It limits Hick's Law cost (log₂(4) ≈ 2 — minimal decision time).

## The middle-tier dominance pattern

Across many product categories, the middle tier captures 50–75% of conversions when:

- It's labeled as "Recommended" or "Most Popular."
- It's visually emphasized (border, badge, slight size increase).
- The features list shows enough above the cheap tier to justify the upgrade and enough below the expensive tier to make the next jump feel discretionary.

This is sometimes called "decoy pricing" or the **decoy effect** — an option whose primary purpose is to make another option look better. Done honestly (the middle tier is genuinely the right fit for most users), it's good design. Done manipulatively (the cheap tier is artificially crippled to push users up; the expensive tier is added solely to make the middle look reasonable), it's a dark pattern.

## A/B testing findings

Common pricing-page A/B test results from CRO literature (anonymized aggregations):

- **Adding a "Recommended" badge to the middle tier**: +5 to +25% conversion lift toward that tier.
- **Highlighting middle tier with brand color border**: +10 to +20% lift.
- **Adding a 4th tier**: usually neutral to slight negative on total conversion; revenue may shift between tiers.
- **Removing a tier (4 → 3)**: usually neutral to slight positive; reduces cognitive load.
- **Annual-billing discount toggle defaulted to "Annual"**: +30 to +60% on annual-plan selection (with proportional revenue lift if your unit economics support it).
- **Showing per-user pricing vs. flat pricing**: per-user often better for SMB segments; flat better for SOHO.

These are illustrative; your product's audience and market will produce different numbers.

## Cross-domain examples

### Subscription magazines

The "1 year / 2 year / Lifetime" pattern. Lifetime is rare; 1-year is typical; 2-year is the recommended-and-discounted middle.

### SaaS canonical layouts

Atlassian, Slack, Asana, Notion, Linear, and dozens more: same 3-tier (or 3+free) structure. Convergence isn't accidental; it's optimization across many A/B tests.

### Mobile carriers

US mobile pricing has historically been 3-tier ("Basic / Plus / Unlimited") with each tier carrying many bundled features, plus add-ons. The complexity pushed users into the most expensive tier as the "safe" choice — which is one read on why telco pricing has been disliked.

### Charity giving

Donation forms often show preset amounts ($10 / $25 / $50 / $100 / Custom). The middle preset typically captures plurality. Defaults work the same way as in product pricing.

## Common pricing-page mistakes

- **Hiding pricing.** "Contact sales" on a tier that should be self-serve. Conversion drops; competitors with published prices win.
- **No "Recommended" highlight.** Three equally-weighted tiers; users gravitate to the cheapest by default.
- **Feature wall.** A 30-row × 5-column comparison matrix at the top of the page. Most users bounce before scanning.
- **Free tier given full visual weight.** Free is often loss-leader; over-emphasizing it pushes users into a tier that doesn't pay.
- **Confusing per-user math.** "$8 per user per month, billed annually." Users do the wrong math at checkout. Show monthly-equivalent and annual-total on the page.
- **Hidden enterprise.** Enterprise tier with no information at all. Sales-led customers want to qualify themselves before they talk.

## Resources

- **Price Intelligently** (Patrick Campbell) — pricing-research firm with extensive blog content on tier design.
- **Reforge** — has materials on pricing strategy and UI.
- **Demand Curve** and **Conversion Rate Experts** — agency blog content on pricing-page CRO.

## Closing

A pricing page is the most quantitatively-tested surface in many products — every change becomes measurable revenue. The Hick's Law principle stays constant: keep the visible decision space small, default the middle, anchor with the extremes, and let the user say yes without thinking.
