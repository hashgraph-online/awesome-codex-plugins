# The Featured Offer, and why price-only repricing loses

The Featured Offer is the offer selected when a customer presses Add to Cart.
Most sellers call it the Buy Box. Winning it is the point of most repricing,
and the common mistake is treating it as an auction that the lowest price
wins. It is not, and a repricer built on that assumption spends margin without
buying wins.

## Eligibility comes before price

A seller who is not eligible cannot win at any price, so check this first. The
gates are a Professional selling account, the item in a condition that is
eligible on that listing, and account performance in acceptable ranges. If a
seller's metrics have slipped, the repricing conversation is the wrong
conversation and you should say so rather than tuning rules that cannot fire.

Diagnose it directly: pull the offers on the ASIN and look at whether your
offer appears as a featured buying option at all, and at what the current
winner looks like. An eligible seller losing on price looks different from an
ineligible seller losing on everything.

## What Amazon weighs

Amazon's own framing is prices, availability, and delivery speed. In practice
the inputs that move the outcome are:

- **Landed price**, meaning item plus shipping. A merchant-fulfilled offer
  with paid shipping competes at its landed price, not its item price. This is
  the single most common misreading of a competitor set.
- **Fulfillment and delivery speed.** Prime-eligible fulfillment carries real
  weight. An FBA competitor at your exact price will typically take the offer,
  which is why matching an FBA seller from a merchant-fulfilled offer is a
  losing trade rather than a close one.
- **Availability.** Out of stock cannot win, and low stock can affect
  standing.
- **Seller performance.** Order defect rate, late shipment, cancellation.
- **Condition.** New and used compete in separate tracks.

The practical consequence: the gap you must close against an FBA competitor
from an MFN offer is not zero, and it is often larger than the margin you have.
Where that is true, the honest recommendation is to change fulfillment or stop
competing on that ASIN, not to keep cutting.

## Two failure states worth recognising

**Nobody has it.** Amazon can show no Featured Offer at all when no offer is
priced competitively against its reference. The page then pushes buyers into
the offer list, and conversion drops for everyone. If your monitoring shows no
winner rather than a competitor winning, the fix is a price move toward the
reference, not a fight with a rival.

**It rotates.** More than one seller can share the offer over time. A snapshot
showing you losing may be a moment inside a rotation you partly win. This is
why point-in-time offer data cannot tell you whether a strategy is working and
featured-offer share over a period can. Read them together.

## Getting to a target price

Two routes, and which one you have depends on the marketplace.

**Where Featured Offer Expected Price is available**, ask for it. It returns
the price at or below which you can expect to become the Featured Offer, which
is the answer rather than an input to guessing it. Coverage has expanded over
time and current documentation describes it as broadly available, so check the
seller's marketplace rather than assuming either way. The conditions that hold
are new condition, nationwide shipping, and featured-offer eligibility.

It is an expectation and not a guarantee. Competing offers move, and
fulfillment capability to a particular customer can still decide the winner, so
a SKU priced exactly at its expected price will not win every time.

**Where it is not available**, infer. Pull the offer set, filter it to offers
that are genuinely comparable to yours, and work from the best comparable
landed price. Filtering is the part people skip, and it is where the money
leaks: a used offer, an unfulfillable offer, a seller with poor metrics, or a
merchant-fulfilled offer with a two-week delivery promise are not competitors
you need to undercut. Chasing them drags your price below the level that would
have won.

## Measuring whether any of it worked

Featured-offer share over a period, from the sales and traffic business
report, is the outcome metric. Pair it with contribution rather than revenue,
because a repricer can lift both share and revenue while destroying profit,
and that combination looks like success on every dashboard that omits cost.

The pairing to watch: share up and contribution per unit down means you bought
the offer at a price you should not have. Share flat and contribution up means
the floor discipline is working and you were previously giving away margin you
did not need to.

---

**Provenance:** Featured Offer definition, the prices/availability/delivery
speed framing, and Featured Offer Expected Price behaviour and marketplace
restrictions come from Amazon's SP-API Product Pricing documentation and the
Price Adjustment Automation Workflows guide, consulted 2026-09-08.
Eligibility criteria and performance thresholds are Seller Central policy and
change; confirm current requirements before telling a seller they are
ineligible.
