# Period P&L: the margin cascade

Run by `scripts/pnl.py`. This is the period-level companion to the per-unit model in
`margin.py`, and it is a genuinely different calculation — not the same model summed up.

**Net margin = Net Operating Profit ÷ Net Revenue.** Precisely, this is net *operating*
margin: before financing costs and income tax. It is not the after-tax net profit
margin an accountant reports, and should not be compared to one. Always state the
numerator and the denominator.

Neither number appears in Seller Central. Amazon shows gross sales that overstate
revenue and has no idea what the products or the team cost. The waterfall has to be
built.

## The eight steps and four checkpoints

```
    Gross Ordered Revenue            everything ordered, at the price ordered
(-) Cancelled Orders
  = Gross Shipped Revenue            what actually left the warehouse
(-) Refunds
(-) A-to-Z Claims
(-) Chargebacks
  = Net Product Revenue              the product money actually kept
(+) Shipping Revenue
(+) Gift Wrap Revenue
(-) Shipping Refunds
  = NET REVENUE                      ← checkpoint. The denominator for everything below
(-) COGS (landed)
  = PRODUCT MARGIN                   ← what the product earns before any selling cost
(-) Amazon Fees
  = CHANNEL MARGIN                   ← what survives the channel
(-) Advertising
(+) Reimbursements
  = GROWTH MARGIN                    ← what survives paying for growth
(-) Allocated Overheads
  = NET OPERATING PROFIT
```

**The final number says how much was made. The checkpoints say why.** Report the
checkpoints, not just the bottom line — the gap between Product Margin and Channel
Margin *is* the cost of selling on Amazon, in points, and it is worth tracking period
over period because fee creep is real and silent.

Express each cost as points of net revenue. That is what makes one period comparable to
another, and `pnl.py` emits it as `points_of_net_revenue`. Supply a `prior` block and it
also reports each checkpoint's movement as `deltas_in_points` — in points, so −2.9 means
the checkpoint gave up 2.9 points of net revenue. That is the fastest way to answer "why
did margin drop."

A rough read on the result: operators commonly treat 15%+ as healthy, 20%+ as strong,
and under 10% as fragile, since one fee increase erases it. These are rules of thumb,
not laws. The more useful habit is watching your own checkpoints move.

## Date basis — decide this first

One decision shapes every number: which date a unit of currency belongs to. Three
defensible answers, each right for a different job:

| Basis | Answers | Use for |
| --- | --- | --- |
| **Order date** | How did the business perform in March? | Margin analysis and decisions — it follows demand as it happened |
| **Shipment date** | What can finance sign? | The accounts. Under ASC 606 and IFRS 15 revenue is recognised when control transfers, which for a typical FBA order is shipment — though contract terms can put it at delivery, and the auditor decides |
| **Settlement date** | Why did the payout look like that? | Cash and bank reconciliation. Caveat: one settlement mixes orders, refunds and fees from different periods |

All three are needed for different jobs. **Mixing them in one calculation is how
spreadsheets quietly break.** `pnl.py` warns when the basis is not stated.

Related trap at Step 2: a matured order cohort, where every order has either shipped or
cancelled, reconciles exactly. A current-period shipment report contains orders placed
earlier and is missing orders placed now that have not shipped. State which view is in
use and where the cutoff sits.

## VAT stays outside

VAT is money collected on behalf of a tax authority. It is never revenue and never
cost. Put it inside the P&L and it either inflates revenue (VAT-inclusive prices) or
invents a phantom expense line — both distort every margin below.

Keep it as a **memo**, outside the waterfall, clearly marked as not affecting profit,
because sellers still need to know the cash amount involved. Pass it as `vat_memo`.

Same logic on the cost side: recoverable input VAT is not a cost. Where VAT is *not*
recoverable — because of registration status or the nature of the expense — it does
form part of that cost, and belongs in the line it attaches to, not in a VAT line.

This is consistent with the per-unit model, which divides the price by (1 + VAT rate)
to reach net revenue. Both keep VAT out of the profit math.

## Failure patterns to check for

These five inflate margins constantly. Check for each before trusting a result:

1. **Starting from the wrong revenue.** Seller Central's headline "sales" is gross
   ordered revenue, including orders that will be cancelled and refunded. A margin on
   that base is inflated before a single cost is counted.

2. **Forgetting the refund family.** Refunds are the visible leak. A-to-Z claims and
   chargebacks also claw revenue back and live in different reports, so spreadsheets
   routinely omit them.

3. **Ignoring reimbursements.** Amazon owes money for inventory it loses and damages.
   This is a positive line. Omitting it understates profit and removes the incentive to
   claim it.

4. **Mixing VAT in.** See above.

5. **Stopping at fees.** Revenue − COGS − Amazon fees is *Channel Margin*, not net
   margin. Advertising and overheads still have to come out. Calling channel margin
   "net margin" is the most common overstatement in the category.

Two more worth watching:

**Double counting in the refund family.** Match each claw-back to its order. An A-to-Z
claim that Amazon settles by refunding the order appears once — as a refund *or* as a
claim, not both. A later reversal reverses the original line rather than adding a new
one.

**Prep cost booked twice.** Prep belongs in landed COGS per unit *or* in overheads as a
period cost. Never both.

## ACoS vs TACoS

ACoS is ad spend ÷ ad-attributed sales. TACoS is ad spend ÷ total revenue.

**For margin purposes TACoS is the honest number**, because the P&L does not care which
sales the ads claim credit for. The default denominator here is net revenue; some tools
use gross sales, which produces a smaller and flattering percentage. `pnl.py` reports
which denominator it used — state it whenever comparing against a benchmark.

This is the same convention the per-unit model uses when it divides ad spend by total
units rather than ad-attributed units.

## Where each number comes from

The reason so few sellers have a true net margin: the inputs live in six places.

| Lines | Source |
| --- | --- |
| Ordered revenue, cancellations | Order reports |
| Refunds, claims, chargebacks, every fee type | Settlement and payments reports |
| Advertising | Ads API |
| Reimbursements | Their own report — plus unclaimed ones, which are only in your own claims process |
| COGS, overheads | Your side of the business. Amazon has never seen them |

See `references/sourcing.md` for the specific calls.

## Cadence

Weekly for the trend, monthly for the full picture with overheads allocated, quarterly
for pricing and product-line decisions. Investigate any checkpoint that moves more than
a couple of points.

## Validation

`pnl.py` reproduces the published Clarisix worked quarter exactly — Net Revenue
€27,224.4, Product Margin 66.8%, Channel Margin 36.4%, Growth Margin 29.2%, Net
Operating Margin 24.2%, TACoS 8.0%. It ships as
`scripts/fixtures/period-worked-quarter.json`. Re-run it after any change:

```bash
python scripts/validate_fixtures.py
```
