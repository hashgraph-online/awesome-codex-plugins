> The calls below are Candor MCP tool calls. Replace placeholders such as `TRANSACTION_ID` with values from earlier responses; where an `input` names an operation instead of showing an object, `candor_schema` lists its fields.

# Debt payoff and promo rates

## Read the debts

```text
candor_get({
  "operation": "debts.list",
  "reason": "Read balances, rates, minimums, and due dates"
})
candor_query({
  "dataset": "account_terms",
  "reason": "Read card and loan terms with their sources",
  "filters": {
    "limit": 100
  }
})
candor_get({
  "operation": "transactions.list",
  "reason": "Read the payments actually made",
  "args": {
    "since": "START",
    "until": "END",
    "cashflow_role": "debt_payment",
    "limit": 100
  }
})
```

`debts list` carries each balance with its effective APR, minimum, and due
date where known; `account_terms` says where each value came from and flags
conflicts or stale values. A card that shows nothing left unpaid and charged
no interest is not costing anything, whatever its rate.

## Fill missing terms

Never estimate a rate or minimum from transactions.

- From a statement or the lender's site: import it as a curated record (the
  `candor-add-records` workflow) so it joins the account's term history.
- From the person ("my card is 24.99%"): save it as an assertion with their
  words in `note`, preview first:

```text
candor_preview({
  "operation": "account_terms.assertion.preview",
  "reason": "Check the rate the person gave",
  "input": "<account_terms.assertion.preview input object; candor_schema lists its fields>"
})
candor_write({
  "operation": "account_terms.assertion.set",
  "reason": "Save the rate the person gave",
  "input": "<account_terms.assertion.set input object; candor_schema lists its fields>"
})
```

Revert with `candor_write({"operation":"account_terms.assertion.revert","reason":"Drop the rate the person gave now that the statement shows it","args":{"account_identity_id":"ACCOUNT_IDENTITY_ID","field":"FIELD"}})`
when better evidence replaces it.

## Model the payoff

1. Model the current course (what they pay now) and at least one
   alternative: highest rate first (least interest), smallest balance first
   (fastest wins), or a fixed monthly amount.
2. State the assumptions: starting balances and their date, rates, payment
   amount and timing, fees, promo expiry, and that new charges are left out.
3. Show the payoff date, total interest, and the monthly cash each path
   needs. Show what happens if the payment drops or a rate rises.
4. Recommend an order for this person's cash and goals, and say why. Save
   the plan as a `debt_reduction` goal with a `debt` measure over the cards or
   loans it pays down.

## Promo deadlines

For a 0% or deferred-interest balance, confirm from the statement or issuer:
the balance covered, the end date, what happens after (deferred interest can
charge back to the start), the required payments, and what voids the promo.
Store the end date as an account term (import or assertion) so the opening
raises it 30 days ahead. Work back from the deadline with a few days of
processing buffer, and give the monthly amount that clears it in time.

A payment, balance transfer, refinance, or application is an action outside
Candor: do it only with the person's okay, through your own tools if you have
them, or give them the exact steps.
