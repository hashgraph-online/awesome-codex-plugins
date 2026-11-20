> The calls below are Candor MCP tool calls. Replace placeholders such as `TRANSACTION_ID` with values from earlier responses; where an `input` names an operation instead of showing an object, `candor_schema` lists its fields.

# Imports in detail

## Holdings

- Put every holding in the account that owns it: `source_account_id` for an
  existing manual account; for a new manual account, send its identity and
  holdings together and use the returned account id afterward. The same
  symbol in two accounts is two positions.
- Keep each holding's name, symbol, quantity, price, value, cost basis,
  currency, valuation time, source locator, and extraction confidence as the
  source shows them.
- Send `market: US` with the `symbol` of every US-listed stock, ETF, or
  mutual fund. That is what lets Candor quote it every market day and value
  the account at current prices; without it the holding keeps its imported
  price.
- Record cash, sweep, and money-market lines as positions too. An account
  that reports positions is valued from them, with the reported total kept
  beside it as `reported_balance`, so a missing cash line understates it.

## Unknown quantities

A value-only holding is valid. Do not substitute zero or one.

- For a current value of a USD-listed `stock`, `equity`, or `etf`, you can
  ask Candor to estimate quantity: send `estimate_quantity: true`, `symbol`,
  `market: US`, `type`, and `value`, without quantity or price, plus `as_of`
  when the source value has a known time. The preview returns, per row, an
  `estimated` outcome with the quantity and quote time, or `value_only` when
  no quote was available. Check each one before applying.
- When value, per-unit price, and time are all independently sourced, you can
  compute quantity = value / price yourself and send
  `quantity_source: derived` with `price_source_locator` and `as_of`.
- Never estimate from a historical value, or for options, contracts, bonds,
  private assets, or anything priced by multiplier, NAV, or face value.

## How sure the evidence is

Use `statement_reconciled` only for broker or source evidence transcribed
faithfully and reconciled to its totals. Use `agent_curated_unreconciled`
for partial or unreconciled evidence. Holding value and cost basis are
rounded half-even to the currency's cents with a preview warning;
`manual_correction` rejects extra precision instead.

## Incremental versus complete snapshots

By default an import is incremental: positions you leave out are not
touched. Update or remove each intended position explicitly.

For a complete same-time snapshot of an existing manual account (every
position on one statement date), set `holdings_scope: complete` with that
`source_account_id`, a dated closing balance, quantity or value on every row,
and the same `as_of` on every row. The preview turns positions you left out
into reversible removals; check each one. Never combine complete scope with
`estimate_quantity`, partial evidence, or a connected account.

## Change or remove a manual holding

- **Change:** submit a later import to the same account reusing the holding's
  returned `row_key`. Only the fields you send change.
- **Remove:** read `candor_get({"operation":"holdings.list","reason":"Find the holding to remove","args":{"source_account_id":"SOURCE_ACCOUNT_ID"}})`,
  then import `operation: remove` with its `holding_id` or `row_key` and the
  owning `source_account_id`. The preview shows `remove_holding`. Removal
  keeps past balance history and creates no trade or cash movement, and the
  new batch can be reverted.

## Batches

`candor_get({"operation":"imports.list","reason":"Review recent imports","args":{"limit":25}})` shows
recent batches with their status, account, period, and row counts.
`candor_get({"operation":"imports.get","reason":"Read one batch's rows","args":{"import_batch_id":"IMPORT_BATCH_ID"}})` returns
one batch's full rows and reconciliation. Keep the batch id with your notes so
the import can be undone later.
