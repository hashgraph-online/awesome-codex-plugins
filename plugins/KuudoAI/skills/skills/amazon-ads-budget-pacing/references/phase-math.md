# Pacing and Allocation Math

`scripts/allocate.py` is the executable source of truth. This reference explains
its outputs; do not reproduce the calculations manually for a live proposal.

## Daily target and delivery reserve

For account-local `as_of` through the final calendar day of the month:

```text
remaining_budget = monthly_budget - mtd_actual
raw_share(day)    = dow_index[weekday] * event_multiplier[day]
today_share       = raw_share(today) / sum(raw_share(forward_days))
today_spend_target = max(remaining_budget, 0) * today_share
todays_pool        = today_spend_target / (1 + overdelivery_pct)
```

`today_spend_target` is the unconstrained pacing target. `todays_pool` is the
maximum nominal campaign-budget pool after reserving the account's configured
Amazon overdelivery allowance. A zero allowance leaves the values equal.

The hard-ceiling branch emits `pause_campaign` actions after the monthly plan is
spent. It never proposes zero-dollar budgets. Without a hard ceiling, an
overspent account proceeds only through explicit low-budget controls and warnings.

Pacing status is `mtd_actual / mtd_planned_to_date`: A-2 above 1.20 and A-3 below
0.80. It is omitted when the planned-to-date value is unavailable.

## Campaign score

Every eligible campaign must match one exact Ad Type × Strategy × Product Line
target rule.

```text
efficiency_ratio = actual_roas / target_roas
```

Use a neutral ratio of `1.0` when the campaign has fewer than three mature days
or no ROAS. A missing rule or non-positive target is an input error, not a neutral
fallback.

When a campaign exhausted before 6 PM on at least three of the last seven days:

```text
adjusted_score = efficiency_ratio *
                 (1 + pacing_health_weight * exhaustion_penalty_factor)
```

Otherwise `adjusted_score = efficiency_ratio`.

## Constraint-preserving allocation

1. Reserve the user-approved per-campaign floor.
2. Reject the run if floors exceed the account pool and explicit below-floor mode
   is disabled.
3. Reject the run if floors alone violate a product-line or strategy ceiling.
4. Distribute the remaining pool by adjusted score until a ceiling binds.
5. Remove campaigns in the saturated bucket from further increases and continue
   with eligible campaigns.
6. Apply the daily change cap.
7. Recheck every ceiling. A lower change bound that conflicts with a ceiling is
   an error.

Overlapping ceilings can leave money unallocated. The allocator reports that
amount rather than silently violating a cap. Likewise, upper change caps can
make `total_proposed` smaller than `todays_pool`.

## Reporting series

The original monthly plan is weighted across the full month. The forward planning
series reweights remaining spend over the remaining days, then replaces today's
value with `total_proposed`. Consequently, the forward series may end below the
monthly plan when today's executable constraints prevent reaching the target.
Future points are planning targets, not commitments or guaranteed delivery.

Amazon spend, attributed sales, competition, bid settings, and later pacing runs
can all change the realized trajectory.

## Classification

Prefer API ad-type metadata. Name fallback recognizes delimiter-bounded SP, SB,
SBV, and SD tokens; a substring such as `sp` inside “Display” is not a match.
Strategy tokens must also be delimiter-bounded. Product line comes from the
confirmed portfolio mapping. Any missing dimension produces A-1 and exclusion.
