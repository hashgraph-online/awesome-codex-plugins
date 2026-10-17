---
name: hicks-law-pricing
description: 'Use this skill when designing pricing tables, plan pickers, tier selectors, or any conversion surface where the choice itself is the conversion event. Trigger when laying out 3-tier or 4-tier pricing, when arguing about whether to add a fourth plan, when designing the "Choose your plan" step of onboarding, or when fixing low conversion on a pricing page. Pricing pages are a special Hick''s Law case: the decision is the entire purpose of the page, and decision fatigue equals lost revenue. Sub-aspect of `hicks-law`; read that first if you haven''t already.'
---

# Hick's Law on pricing pages

A pricing page is a Hick's Law surface where the decision *is the page*. Every option you add increases consideration time and abandonment risk; every option you remove may push some users toward the wrong tier. The right number of tiers is one of the most studied design decisions in conversion-rate-optimization research, and the answer is consistent: **fewer is usually better**.

## The standard answer: 3 tiers

The 3-tier pricing layout (often labeled Starter / Pro / Enterprise, or Free / Pro / Team) is the convention because it works. Three options:

- Lets users compare meaningfully (anchoring effect: the middle option looks reasonable against both extremes).
- Stays inside the easy-Hick's-Law range (log₂(4) ≈ 2 — minimal decision time).
- Maps cleanly to user mental models (small / medium / large).

Adding a fourth tier rarely helps. It increases consideration time, splits revenue across more buckets, and dilutes the framing of the middle tier as "the obvious choice." Companies that ship 5- or 6-tier pricing tables usually do so because internal consensus couldn't agree which features belonged where, not because users wanted more choice.

## The role of the middle tier

In 3-tier pricing, the middle tier typically captures the bulk of conversions. Designers exploit this with the **anchoring effect**:

- The cheapest tier sets a low anchor (so the middle tier doesn't look expensive).
- The most expensive tier sets a high anchor (so the middle tier looks reasonable, almost a deal).
- The middle tier is highlighted as recommended.

This is well-studied in pricing psychology (Ariely; Thaler & Sunstein on choice architecture). It's effective. It's also ethically defensible *when the middle tier is genuinely the right choice for most users* — and dishonest when the middle tier is engineered to drive revenue regardless of fit.

## How to design the 3-tier table

### Visual hierarchy

Highlight the recommended (middle) tier with stacked emphasis cues:

- Slightly larger card.
- Brand-color top border or accent.
- "Recommended" or "Most popular" badge.
- Slightly heavier shadow.
- The strongest CTA (filled button vs. outlined buttons on adjacent tiers).

Do not over-do this. One tier highlighted; the other two visibly available but recessive. Three equally-emphasized tiers undo the recommendation effect.

```html
<div class="pricing-grid">
  <article class="plan">
    <h3>Starter</h3>
    <p class="price">$9 / mo</p>
    <ul>
      <li>1 user</li>
      <li>5 projects</li>
      <li>Email support</li>
    </ul>
    <button class="outline">Start free trial</button>
  </article>

  <article class="plan plan--featured">
    <span class="badge">Recommended</span>
    <h3>Pro</h3>
    <p class="price">$29 / mo</p>
    <ul>
      <li>5 users</li>
      <li>Unlimited projects</li>
      <li>Priority support</li>
    </ul>
    <button class="primary">Start free trial</button>
  </article>

  <article class="plan">
    <h3>Team</h3>
    <p class="price">$99 / mo</p>
    <ul>
      <li>25 users</li>
      <li>Unlimited projects</li>
      <li>SSO + audit log</li>
    </ul>
    <button class="outline">Talk to sales</button>
  </article>
</div>
```

### Feature comparison

Don't list 30 features in each card. List the 3–6 differentiators that matter for the tier choice. A user comparing 3 tiers across 30 features each is doing a 90-cell evaluation; abandonment spikes.

If you must list comprehensive features, put the comparison in a separate section *below* the cards (often a "Compare all features" toggle that reveals an exhaustive table). That defers Hick's Law cost to the small fraction of users who care to dig.

### Pricing display

Lead with the price for the most-likely billing cycle (usually monthly, though "per user / mo billed annually" is increasingly the default). Offer a billing-cycle toggle (Monthly / Annually) above the cards — annual is typically discounted to nudge that selection.

```html
<div class="billing-toggle" role="radiogroup" aria-label="Billing cycle">
  <button aria-pressed="false">Monthly</button>
  <button aria-pressed="true">Annual <span class="discount">-20%</span></button>
</div>
```

Keep the toggle proximate to the cards so the relationship is obvious.

### "Free" and "Enterprise"

Two common edge cases:

- **Free tier.** Useful as a low-friction entry point. Treat as a 4th tier visually demoted, *not* as the leftmost tier with full visual weight. Free dominates user attention disproportionately.
- **Enterprise / Custom.** No published price, "Contact sales" CTA. Recede the visual weight here too — Enterprise is for the user who already knows they need it; don't compete with the published tiers.

A workable layout: Starter / Pro / Team in three cards; Free as a small banner above; Enterprise as a small panel below. Three is still the visible decision space.

### CTA copy on each tier

The CTA should make the user's next step obvious and concrete:

- Free trial: "Start free trial" (matches expectation).
- Self-serve paid: "Choose Pro" or "Get Pro" (commits the user to the tier).
- Enterprise: "Talk to sales" (signals sales process).

Avoid identical "Sign up" CTAs across all tiers — Hick's Law cost is *higher* when nothing differentiates the action labels.

## When to deviate from 3 tiers

### 2 tiers

When the product is genuinely simple and there are only two meaningful states (free vs. paid; basic vs. premium). 2 tiers is a strong "make the simpler choice" stance. Conversion-rate research suggests 2 tiers can outperform 3 when feature parity is tight.

### 4 tiers

Justified when:

- A genuine usage-based segment exists (a "Studio" plan for individuals, "Team" for small companies, "Business" for mid-market, "Enterprise" for large).
- Each tier captures meaningful market share — not internal-roadmap convenience.

If you can't articulate the persona for each of 4 tiers in a sentence, you have 3 tiers and one of them is confused.

### 5+ tiers

Almost always wrong. Reasons companies end up here: (1) Sales tiering ("we want a plan for $499 and one for $2,999"); (2) feature-debt where every customer's special request became a tier; (3) failure to consolidate after a tier was added. Restructure.

The pricing page that takes the user 3 minutes to scan is a pricing page that loses conversions.

## Beyond the cards: progressive disclosure

For products with genuinely complex pricing (consumption-based, hybrid SaaS-plus-usage, multiple add-ons), apply progressive disclosure:

1. **Top of page:** the 3 simple tiers with a representative price.
2. **Middle:** "Pricing details" section explaining usage, overages, add-ons.
3. **Bottom:** comparison table for power-shoppers.
4. **Calculator:** for usage-based, an interactive calculator the user can play with.

The casual visitor sees three tiers and a price. The serious shopper finds the depth as they scroll.

## Anti-patterns

- **The "compare all" wall.** A pricing page that opens with a 30-row × 5-column comparison matrix. Cognitive load is enormous; conversion drops.
- **The tier without a buyer.** A tier that exists "just in case" — usually the cheapest — that no actual segment wants. It splits attention without earning revenue.
- **Identical visual weight across tiers.** No recommended highlight. Users default to the cheapest (Hick's Law + price-anchoring against $0).
- **The decoy that's not a decoy.** Three tiers where the most expensive is *clearly* a worse value than the middle — the classic decoy structure — but priced so close to the middle that the middle no longer looks like a deal.
- **Hidden pricing for self-serve plans.** "Contact sales for pricing" on a tier that should be self-serve. Users bounce; competitors with published prices win.
- **The annual-default trick.** Showing annual prices by default but billed monthly (so the monthly cost feels lower than reality). Users discover at checkout; trust collapses.

## Heuristics

1. **The 30-second test.** Land a fresh user on the pricing page. After 30 seconds, can they articulate which tier is for them? If not, the page is too dense.
2. **The middle-tier conversion check.** What percentage of paid signups land on the middle tier? Strong recommendation effect lands at 60–75%. Below that, the recommendation isn't reading; above 90%, the middle might be too dominant or other tiers misconfigured.
3. **The competitor walk-through.** Open three competitors' pricing pages. Spend 30 seconds on each. Which felt easiest? Almost always the one with the cleanest hierarchy and clearest tier count. Match that experience or beat it.

## Related sub-skills

- **`hicks-law`** (parent).
- **`hicks-law-defaults`** — the recommended-tier highlight is a defaulting pattern.
- **`hicks-law-menus`** — pricing tables are a special case of menus.
- **`comparison`** (cognition) — pricing is a comparison surface; align comparable features.
- **`framing`** (cognition) — how each tier is labeled changes which one users pick.
- **`anchoring`** (related; not in book) — the high-tier anchor makes the middle tier read as reasonable.
- **`veblen-effect`** (aesthetics) — the very-high-priced enterprise tier earns desirability from its price.
