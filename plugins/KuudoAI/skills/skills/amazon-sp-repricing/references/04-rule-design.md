# Designing the rules

A repricing strategy is a small number of rules applied to segments, plus the
guardrails that keep those rules from doing damage when the market behaves
strangely. Most bad strategies are one rule applied to everything.

## Segment before writing a single rule

The same rule cannot serve a private-label SKU with no competition and a
wholesale SKU with fourteen sellers on it. Segment on what changes the correct
behaviour:

| Axis | Why it changes the rule |
|---|---|
| Competitive structure | Sole seller, a handful, or crowded. A sole seller on their own ASIN has nobody to match and should not be running a matching rule at all |
| Your role on the ASIN | Brand owner versus reseller sharing a listing |
| Margin headroom | Distance between current price and floor decides whether you can compete at all |
| Inventory cover | Weeks of stock decides whether volume is worth buying |
| Velocity | A SKU selling three units a month does not justify aggressive tactics |
| Price band | A percentage rule behaves very differently at $8 and $800 |

A useful first pass is competitive structure crossed with margin headroom.
That alone usually splits a catalog into four groups needing genuinely
different treatment, and it is computable from data you already pulled.

## Rule archetypes

| Archetype | Use when | Behaviour |
|---|---|---|
| **Hold** | Sole seller, or brand-controlled ASIN | Do not react to noise. Price to strategy, not to competitors |
| **Match** | Comparable competitor, you have fulfillment advantage | Match the best comparable landed price and let fulfillment win it |
| **Beat by increment** | Comparable competitor, no fulfillment edge | Undercut by the smallest increment that matters, never by a percentage |
| **Target expected price** | Marketplace supports it | Price at the featured-offer expected price, subject to floor |
| **Seek high** | You hold the offer uncontested | Walk the price up in small steps until you lose it, then step back. This is where repricing makes money rather than spending it |
| **Stock-out defence** | Cover is short and replenishment is far | Price up. Slowing sales on a SKU you cannot restock is the correct move |

**Seek-high is the archetype sellers most often lack.** A repricer that only
moves down converts a competitive advantage into a discount. If you hold the
Featured Offer without contest, the current price is a floor on what the market
will bear, not a ceiling.

## Guardrails

Rules decide direction. Guardrails decide how much damage a wrong decision can
do.

- **Floor**, computed per SKU, never catalog-wide. See
  [`02-floor-and-margin.md`](02-floor-and-margin.md).
- **Ceiling**, to keep a follow-the-competitor rule from walking a listing into
  a fair-pricing problem.
- **Maximum change per cycle**, so a bad data point cannot move a price 40%.
- **Cooldown** between changes on the same SKU, which is the main defence
  against oscillation.
- **Minimum increment**, so you never undercut by an amount too small to
  change a buyer's decision but large enough to trigger the competitor's
  repricer.
- **Exclusions**, for SKUs under promotion, subject to MAP-style agreements,
  or in a launch period where price is a strategy rather than a lever.

## The race to the bottom, and how it actually starts

Two automated repricers set to undercut the lowest offer will drive each other
to their floors within hours, and both sellers end up at minimum margin
holding the same share they started with. It is the defining failure of naive
repricing.

Three things prevent it, and they work together:

1. **A real floor**, so the descent stops somewhere survivable.
2. **A cooldown**, so you are not responding to your own move reflected back.
3. **A comparable-offers filter**, so you are not undercutting an offer that
   was never going to win anyway. This is the one most often missing.

Filter out, before choosing a target: used and refurbished offers when you sell
new, offers that cannot currently fulfil, sellers whose delivery promise is far
worse than yours, and offers whose landed price differs from their item price
in a way that makes them uncompetitive. What remains is the set worth reacting
to, and it is usually much smaller than the raw offer list.

## Cadence

Match refresh rate to what the SKU is worth. A crowded, high-velocity SKU may
justify event-driven reaction through offer-change notifications. A long-tail
SKU selling occasionally does not justify any automated reaction at all, and
polling it frequently spends rate limit that a valuable SKU needs.

Tier the catalog explicitly. Rate limits and batch sizes make "reprice
everything constantly" impossible above a modest catalog size, so the tiering
is forced whether or not you plan it.

Time-of-day and day-of-week rules are popular and mostly noise. The cases that
hold up are structural rather than clock-based: stock-out risk, a known
seasonal demand shift, or a competitor who reliably goes out of stock.

## Anti-patterns

- One floor for the whole catalog, or a floor set as a round number.
- Undercutting by a percentage. Increments should be small and absolute.
- Reacting to every offer in the list rather than the comparable ones.
- Repricing on ASINs where you are the only seller.
- Measuring success as Featured Offer share alone, with no contribution figure
  beside it.
- Matching an FBA competitor's price from a merchant-fulfilled offer and
  expecting to win.
