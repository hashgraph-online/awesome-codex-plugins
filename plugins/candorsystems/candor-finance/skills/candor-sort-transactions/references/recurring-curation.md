> The calls below are Candor MCP tool calls. Replace placeholders such as `TRANSACTION_ID` with values from earlier responses; where an `input` names an operation instead of showing an object, `candor_schema` lists its fields.

# Recurring curation

The recurring list is a curated schedule of predictable obligations: rent,
mortgage, subscriptions, memberships, insurance, and similar bills. Candor
detects series from posted history and fills the list on its own; you decide
which are real, what they are called, and what kind they are.

## Statuses and kinds

- `candidate`: uncertain activity awaiting your call. Candidates count toward
  nothing.
- `active`: expected to keep posting. An active detected row can still be
  unconfirmed; `confirmed` and `source` say whether the reading is yours.
- `stopped`: a real series that ended. One that posts again comes back as a
  change.
- `dismissed`: never a series. Later postings from that payee raise nothing.

`kind` decides how a series counts. `bill`, `subscription`, `loan_payment`,
and `income` are commitments. `card_payment` and `transfer` are cash
movements, totaled apart in `cash_movements`, because the purchases a card
payment settles were already counted. A mortgage is a `loan_payment`. Fix a
wrong kind with `candor_write({"operation":"recurring.update","reason":"This is the card payment, not a bill","args":{"recurring_item_id":"RECURRING_ITEM_ID","kind":"card_payment"}})`;
detection keeps your kind.

## Read a series

```text
candor_get({
  "operation": "recurring.get",
  "reason": "Read the series and its latest postings",
  "args": {
    "recurring_item_id": "RECURRING_ITEM_ID"
  }
})
candor_get({
  "operation": "transactions.list",
  "reason": "Read the series' full history",
  "args": {
    "recurring_item_id": "RECURRING_ITEM_ID",
    "limit": 100
  }
})
```

The history read covers every posting whose label, merchant, or description
names a payee in the series' `match_rule`, so one read covers each name the
bank used. Another agreement from the same payee can appear; check amounts
against `price_levels` before counting a posting as this series'.

## Dates are windows

`predicted_next_date` is the center of `predicted_window`; a posting anywhere
in the window is on time. Say "around the 3rd", never "due on the 3rd";
contractual due dates live in account terms. `overdue` is true only when a
window closed with no matching posting, judged up to the last sync, or for
an account kept by hand up to the end of its latest imported period.
`paid_this_cycle` says this occurrence is already paid.

## Confirm, rename, re-time

```text
candor_write({
  "operation": "recurring.update",
  "reason": "Confirm a series the postings support",
  "args": {
    "recurring_item_id": "RECURRING_ITEM_ID",
    "status": "active"
  }
})
candor_write({
  "operation": "recurring.update",
  "reason": "Name the gym and pin its usual day",
  "args": {
    "recurring_item_id": "RECURRING_ITEM_ID",
    "merchant_name": "Gym",
    "next_expected_date": "2026-11-03",
    "date_tolerance_days": 3
  }
})
candor_write({
  "operation": "recurring.update",
  "reason": "No posting since the cancellation",
  "args": {
    "recurring_item_id": "RECURRING_ITEM_ID",
    "status": "stopped"
  }
})
candor_write({
  "operation": "recurring.update",
  "reason": "Repeat visits, not a bill",
  "args": {
    "recurring_item_id": "RECURRING_ITEM_ID",
    "status": "dismissed"
  }
})
candor_write({
  "operation": "recurring.revert",
  "reason": "Drop an override the postings no longer support",
  "args": {
    "recurring_item_id": "RECURRING_ITEM_ID"
  }
})
```

Any field update confirms a candidate. Fields you set replace the observed
ones; the rest keep following detection. Set `ends_at` on a payment plan so
remaining payments are counted.

## Amount ranges

A posting joins a series when its amount is one of `price_levels` or near
the series' recent amounts. Set `amount_min` and `amount_max` together to
replace that range; both must contain the expected `amount`. Setting `amount`
alone drops a saved range back to the default. Use the history to choose the
range.

## Renamed payees and moved bills

A candidate's `possible_matches` names existing series it may belong to.
Inspect both, then join the new wording to the existing series:

```text
candor_write({
  "operation": "recurring.update",
  "reason": "The bank renamed the gym's billing name",
  "args": {
    "recurring_item_id": "TARGET_ID",
    "associate_from": "CANDIDATE_ID"
  }
})
```

Each match lists `differences` the write refuses until they agree. A
`cashflow_role` difference means correct the role first. An
`account_identity` difference means a moved bill: stop the old series and
confirm the new one; never associate across accounts.

## Declare a bill Candor has not seen

For a bill the person names, an annual renewal with one posting, or a plan
that has not started:

```text
candor_get({
  "operation": "accounts.list",
  "reason": "Find the account the bill posts to"
})
candor_write({
  "operation": "recurring.create",
  "reason": "The person named their rent so it shows on the schedule",
  "args": {
    "label": "Rent",
    "account_identity_id": "ACCOUNT_IDENTITY_ID",
    "direction": "outflow",
    "cadence": "monthly",
    "amount": 1500,
    "currency": "USD",
    "next_expected_date": "2026-11-01",
    "category": "Housing"
  }
})
```

If the response warns that a similar series exists, confirm that one and
dismiss the duplicate.

## What is coming up

```text
candor_get({
  "operation": "recurring.list",
  "reason": "List bills expected in the next month",
  "args": {
    "due_within": 30
  }
})
```

Overdue series come first, then by date. Totals cover the returned rows and
count excluded rows by reason; say when candidates or irregular series were
left out.

## A pass is done when

Every candidate you inspected has a disposition backed by its postings, and
anything ambiguous is left for the person. A harmless candidate needs no
write; say what you checked. Do not claim the whole list is clean.
