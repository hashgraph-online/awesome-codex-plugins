# Return-rate methods

Return counts and return rates answer different questions. A return rate needs
a compatible activity denominator and an explicit time relationship between
the numerator and denominator.

The labels below are analytical labels used by this skill, not official Amazon
metric names.

## `share_of_returns`

```text
product return units / all return units in the analyzed returns source
```

This measures composition or concentration. It is useful without shipment
data, but it is not a return rate. Say “share of return units” and identify
whether the numerator counts units, requests, orders, or rows.

## `window_biased`

```text
returns whose return event falls in W / shipments whose shipment event falls in W
```

The numerator and denominator usually represent different order cohorts.
Returns in the window often originate from earlier shipments, while some
shipments in the denominator will return after the window closes. Treat the
result as directional.

Expected directional effect when return latency is otherwise stable:

- For a rapidly growing ASIN, older shipment cohorts are smaller than current
  shipment volume, so the same-window metric tends to **understate** the
  eventual cohort rate.
- For a rapidly shrinking ASIN, older shipment cohorts are larger than current
  shipment volume, so the metric tends to **overstate** the eventual cohort
  rate.
- Promotions, stockouts, seasonality, and changes in return latency can alter
  the direction. Do not claim a deterministic correction factor.

Quote this as, for example, `8.4% (window_biased)` and explain the event dates.

## `cohort_overlap`

This is a supplementary same-window view restricted to products present in
both the returns and shipment datasets. It can reveal how unmatched products
affect the portfolio number, but it does not fix the cohort mismatch. Never
present it as a true cohort rate.

## `true_cohort`

Define a shipment cohort, join later returns to the originating shipment using
compatible order and product identifiers, and observe each shipment for a
stated follow window:

```text
returned units attributed to the shipment cohort / units in the shipment cohort
```

State:

- cohort start and end;
- follow-window end or duration;
- join keys and match rate;
- treatment of replacements, cancellations, multiple units, and partial
  returns; and
- unresolved and late-arriving returns.

The follow window should follow the use case, category, and available evidence.
Do not claim that one duration captures a universal percentage of returns.

## Alignment checklist

Before quoting any rate, verify:

1. **Marketplace:** numerator and denominator cover the same marketplace set.
2. **Channel:** do not divide mixed-channel returns by an FBA-only denominator.
3. **Item grain:** child ASIN, parent ASIN, SKU, and FNSKU are not
   interchangeable without a mapping.
4. **Unit grain:** both sides count compatible units rather than mixing rows,
   requests, orders, and units.
5. **Dates:** identify return, return-request, shipment, and cohort dates.
6. **Coverage:** compare actual source coverage, not only requested dates.
7. **Zero denominator:** return `N/A`, not infinity, zero, or 100%.
8. **Join quality:** for cohort rates, report matched and unmatched records.
9. **Comparability:** use identical definitions for current and prior periods.

## Reporting contract

For each rate, show:

- numerator value and definition;
- denominator value and definition;
- method label;
- date or cohort basis;
- exclusions and unresolved records; and
- the practical limitation that matters to the decision.

If no compatible denominator exists, stop at counts, concentration, and
`share_of_returns`.
