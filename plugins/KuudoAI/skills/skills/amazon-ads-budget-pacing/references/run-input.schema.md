# Run-Input Bundle

Pass one JSON object to `scripts/allocate.py`. All monetary values use
`account_context.currency_code`. The allocator fails closed on missing or
inconsistent financial inputs.

## Required top-level fields

| Field | Shape | Notes |
|---|---|---|
| `as_of` | `YYYY-MM-DD` | Account-local run date. |
| `account_context` | object | Selected advertiser and marketplace scope. |
| `data_provenance` | object | Actual source names, retrieval times, and maturity. |
| `amazon_budget_controls` | object | Amazon overdelivery setting and active budget rules. |
| `portfolio_product_lines` | object | Confirmed portfolio name/ID → product-line mapping. |
| `controls` | object | Allocation controls. |
| `monthly_plan` | object | `month`, `budget`, and `mtd_actual`. |
| `target_rules` | array | Exact Ad Type × Strategy × Product Line targets. |
| `campaigns` | array | Enabled daily-budget campaigns and trailing metrics. |

Optional objects are `dow_index`, `event_multipliers`, `daily_actuals`,
`product_line_ceilings`, and `strategy_ceilings`. `mtd_planned_to_date` is an
optional number used only for pacing alerts.

## `account_context`

```json
{
  "advertiser_account_id": "amzn1.ads-account.g.example",
  "profile_id": "1234567890",
  "marketplace": "US",
  "currency_code": "USD",
  "timezone": "America/Los_Angeles"
}
```

Resolve these values from the selected account. Do not substitute one identifier
type for another. `currency_code` is a three-letter uppercase code; `timezone`
is an IANA name used to interpret `as_of` and completed days.

## `data_provenance`

```json
{
  "current_budgets": {
    "source": "fixture://campaign-snapshot",
    "retrieved_at": "2026-06-15T07:00:00-07:00"
  },
  "performance_actuals": {
    "source": "fixture://performance-report",
    "retrieved_at": "2026-06-15T07:05:00-07:00",
    "data_through": "2026-06-14",
    "roas_data_through": "2026-06-12",
    "preliminary": true
  }
}
```

Use the real connector, report, file, or manual source. `roas_data_through` must
exclude the two most recent days because attributed sales can still mature.

## `amazon_budget_controls`

```json
{
  "average_daily_budget_overdelivery_pct": 0.25,
  "active_budget_rules": []
}
```

The overdelivery percentage is the account's current Amazon setting from `0` to
`1`. The allocator divides today's spend target by `1 + percentage` to reserve
worst-case delivery headroom. It rejects any active budget rule until that rule's
cumulative effect is explicitly modeled.

## `portfolio_product_lines`

Map each campaign portfolio name or ID to the product-line label used by target
rules and ceilings. An unmapped portfolio is not assumed to be its own product
line; classification may instead use a delimiter-bounded product-line token in
the campaign name, otherwise the campaign is excluded.

## `controls`

| Field | Type | Meaning |
|---|---|---|
| `min_daily_budget` | number | User-approved campaign floor. |
| `hard_spend_ceiling` | boolean | Propose campaign pauses after the monthly plan is spent. |
| `honor_minimums_at_low_budget` | boolean | Error when the pool cannot fund floors; `false` explicitly permits below-floor scaling. |
| `apply_dow_seasonality` | boolean | Apply the supplied weekday index. |
| `pacing_health_weight` | number | Exhaustion-boost weight from `0` to `1`. |
| `exhaustion_penalty_factor` | number | Non-negative exhaustion multiplier. |
| `max_daily_change_pct` | number or `null` | Clamp daily moves; conflicts with ceilings are errors. |

Every control is required in a run bundle and must be shown to the user. The
engine's dataclass defaults exist only for direct unit-level use.

## `target_rules[]`

```json
{
  "ad_type": "SP",
  "strategy": "Non-Branded",
  "product_line": "Product A",
  "target_roas": 4.0,
  "lookback_days": 14
}
```

Every eligible campaign requires one exact tuple. `target_roas` must be positive
and `lookback_days` at least three. No cross-product-line fallback is allowed.

## `campaigns[]`

```json
{
  "campaign_id": "234567890",
  "name": "Example | Product A | Non-Branded | SP | Broad",
  "portfolio": "Product A",
  "ad_type": "SP",
  "current_daily_budget": 120.0,
  "actual_roas": 5.1,
  "days_of_data": 14,
  "exhausted_before_6pm_days_l7": 4,
  "enabled": true
}
```

Campaign IDs must be unique. Prefer API `ad_type` metadata. Name fallback uses
delimiter-aware exact tokens; missing classifications are excluded with A-1.
Use the selected profile timezone when evaluating “before 6 PM.”

## Other inputs

- `daily_actuals`: completed dates before `as_of`; values must reconcile exactly
  to `monthly_plan.mtd_actual`.
- `dow_index`: weekday → non-negative index.
- `event_multipliers`: date → non-negative multiplier.
- `product_line_ceilings` and `strategy_ceilings`: bucket → share from `0` to
  `1`. Floors that make a ceiling impossible cause an error.

## Output

The plan includes `proposal_id`, account and provenance records,
`today_spend_target`, `todays_pool`, `total_proposed`, `proposed_changes[]`,
`proposed_actions[]`, alerts, warnings, exclusions, and `daily_series[]`.

`proposed_changes[]` contains budget changes only. `proposed_actions[]` contains
state changes such as `pause_campaign`; these require a campaign-state operation,
not a budget value of zero. Today's `daily_series.revised_forward_target` equals
`total_proposed`; later values are planning targets, not committed forecasts.
