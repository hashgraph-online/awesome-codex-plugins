> The calls below are Candor MCP tool calls. Replace placeholders such as `TRANSACTION_ID` with values from earlier responses; where an `input` names an operation instead of showing an object, `candor_schema` lists its fields.

# Investments and retirement

## What the records can show

```text
candor_get({
  "operation": "accounts.list",
  "reason": "Find investment and retirement accounts",
  "args": {
    "limit": 100
  }
})
candor_get({
  "operation": "holdings.list",
  "reason": "Read visible holdings",
  "args": {
    "limit": 100
  }
})
candor_get({
  "operation": "portfolio.snapshot",
  "reason": "Read investment balances and allocation"
})
candor_query({
  "dataset": "investment_transactions",
  "reason": "Read investment activity",
  "filters": {
    "limit": 100
  }
})
```

- Current value is `market_value` for a quoted holding, `value` otherwise.
  `market_price_as_of` says how fresh the quote is; off hours it is the prior
  close. An account's `balance_basis` says whether its balance is
  market-valued.
- A holding with no symbol, or imported without `market: US`, keeps its
  source value and does not move with quotes.
- Use only `status: active` investment activity; removed rows are withdrawn
  evidence. `activity_kind` is Candor's shared meaning; `type` and `subtype`
  are the source's. A reinvestment is not an outside contribution.
- `investment_transactions` takes only cursor and limit: page through it and
  filter by account and date yourself. Follow every continuation before you
  call a year-to-date total complete, and check the connection's history
  reaches back that far.

Coverage notes: Plaid refreshes about 90 days of overlap and reconciles its
24-month window about monthly; a failed refresh keeps the last good window.
Read `latest_attempt_status` apart from `last_successful_sync_at`. When
coverage says `refresh_failed`, `candor_connections({"operation":"sync.refresh","reason":"Resume the staged investment refresh","args":{"force":true}})`
resumes it; repeating it cannot fix a bad record.

## Value over time

```text
candor_get({
  "operation": "metrics.history",
  "reason": "Review investment value history",
  "args": {
    "metric": "investment_value",
    "range": "3m"
  }
})
candor_query({
  "dataset": "holding_valuations",
  "reason": "Read one holding's daily values",
  "filters": {
    "holding_id": "HOLDING_ID",
    "limit": 100
  }
})
candor_changes({
  "domain": "investments",
  "reason": "Review position changes"
})
```

A period figure is value change, not return: contributions, withdrawals,
dividends, and sales are inside it until activity is reconciled. Days with
`price_source: observed` are flat source values, not market moves. Daily
holding valuations start with the first nightly valuation after the account
joined and are never backfilled. Show the picture with
`candor_visualize({"panel":"investments","reason":"Show investment value and allocation"})`.

## Fees, cash drag, concentration

1. Confirm the exact fund share class or advisory arrangement.
2. Look up current expense ratios, advisory and platform fees from the
   prospectus or fee schedule; keep publisher, date, and which holding it
   applies to.
3. Estimate yearly cost from visible value and label it an estimate; do not
   add overlapping fees.
4. Weights by account, holding, and currency are facts. Suitability, risk
   fit, and a target allocation are not in the records: ask about goals, time
   horizon, and holdings elsewhere before judging fit.

A fee saving the person acts on is an impact worth recording (see the notes
reference in `candor-finance`). Any trade, rebalance, or transfer happens
outside Candor with their okay.

## Employer match and contributions

- A connected plan shows contributions in investment activity; otherwise
  they live on paystubs. Bank deposits show net pay, not contributions.
- Get the match formula, eligibility, vesting, and true-up from the plan
  document or HR. A deposit pattern cannot establish a formula, and an
  employer deposit is match only when labeled or reconciled to a paystub.
- With the formula and pay per period, compute: contribution at the current
  rate, match earned, maximum match, and match left unclaimed this year
  (capped by remaining room). Show the arithmetic.
- Contribution limits are external and yearly: name the tax year and the
  source, and separate the employee limit from the combined limit. 401(k) and
  403(b) deferrals share one limit across plans, including a former
  employer's this year; a governmental 457(b) has its own. Without
  year-to-date deferrals from every plan sharing the limit, do not state
  remaining room.
- Payroll facts (rate, YTD) have no typed record: keep them in a note with
  the paystub date and re-check from a fresh paystub before relying on them.
  Statement balances and holdings can be imported (`candor-add-records`).
- Save a contribution plan the person settles on as a goal: `tagged` on a
  contribution tag when contributions post to a visible account, otherwise
  `recorded`.
- After they change their election, save a note with the baseline and a
  `revisit_at` on the first paycheck that should show it; the gap is closed
  only when a paystub or contribution record shows the new amount.
