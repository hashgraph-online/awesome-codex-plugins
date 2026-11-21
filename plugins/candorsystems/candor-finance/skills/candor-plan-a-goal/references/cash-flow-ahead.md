> The calls below are Candor MCP tool calls. Replace placeholders such as `TRANSACTION_ID` with values from earlier responses; where an `input` names an operation instead of showing an object, `candor_schema` lists its fields.

# Cash flow ahead

Use for "can I afford it", "will I make it to payday", runway, or a planned
big expense. The answer is usually the lowest balance ahead and its date.

## Build the baseline

```text
candor_get({
  "operation": "coverage.get",
  "reason": "Check balances and bills are current enough to project"
})
candor_get({
  "operation": "balances.list",
  "reason": "Read starting balances",
  "args": {
    "limit": 50
  }
})
candor_get({
  "operation": "recurring.list",
  "reason": "Read bills and income in the horizon",
  "args": {
    "limit": 100
  }
})
candor_get({
  "operation": "transactions.list",
  "reason": "Include pending and future-dated transactions",
  "args": {
    "since": "TODAY",
    "until": "HORIZON_END",
    "limit": 100
  }
})
candor_get({
  "operation": "notes.list",
  "reason": "Recover expected one-offs saved earlier",
  "args": {
    "after": "HORIZON_START_ISO",
    "before": "HORIZON_END_ISO",
    "limit": 100
  }
})
```

Notes take ISO timestamps (`2026-11-01T00:00:00.000Z`); transactions take
plain dates. Follow every continuation: a missed bill always makes the
projection look better than it is. If balances cover fewer accounts than
exist, say so before projecting.

1. Start from current balances, per account.
2. Add only `active` recurring series on their `predicted_next_date`.
   Candidates are not commitments. Do not rebuild a next date from the last
   payment; a null date is undated.
3. Take income from recurring inflows. Do not average past deposits into
   future income unless the person confirms it.
4. Count a bill already showing as pending once. Card payments and transfers
   move one account's balance even though they net out for the household.
5. Keep everyday spending as a stated range, apart from committed bills.
6. Report the lowest balance, its date, and the bills that drive it.

## A planned expense or a scenario

Get the amount, date, and account if any is missing. Re-run with the change
and compare the two low points; say plainly if it creates a shortfall. Save
the expense as a note with `revisit_at` on its date so later projections
include it. A scenario becomes the plan only when the person settles on it, as
a goal or budget change.

## Runway

Months of runway = cash they would live on divided by monthly spending. Use
the `cover` measure's figure when a reserve goal exists. Say what the figure
leaves out (irregular income, annual bills).
