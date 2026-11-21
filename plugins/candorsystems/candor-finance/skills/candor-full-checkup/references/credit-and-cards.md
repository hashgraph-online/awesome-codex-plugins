> The calls below are Candor MCP tool calls. Replace placeholders such as `TRANSACTION_ID` with values from earlier responses; where an `input` names an operation instead of showing an object, `candor_schema` lists its fields.

# Credit and cards

Candor holds no credit bureau data. Never present a score, a score change, or
report contents as known.

## Utilization

```text
candor_get({
  "operation": "debts.list",
  "reason": "Read card balances, limits, and terms"
})
candor_get({
  "operation": "balances.list",
  "reason": "Check balance freshness per card",
  "args": {
    "limit": 100
  }
})
candor_query({
  "dataset": "account_terms",
  "reason": "Read statement figures and term status",
  "filters": {
    "limit": 100
  }
})
```

- Per card: balance, limit, currency, `utilization_ratio`, `as_of`, APR,
  minimum, next due date, overdue flag.
- Overall utilization = total balance / total limit over cards with both,
  per currency. Treat an overpaid card as zero; it does not offset another.
  Name the cards left out for a missing limit or stale balance.
- The current balance is not the statement balance. A mid-cycle payment
  changes what the next statement reports; say which figure you use.
- Trust a term only when its status is `observed` or `corroborated` and its
  provenance is the issuer. An `assertion` is the person's word; `stale`,
  `conflicted`, and unknown terms are unverified, not zero.
- Fill a missing or stale term from the statement or issuer page: import it
  (`candor-add-records`) or save what the person told you:
  `candor_write({"operation":"account_terms.assertion.set","reason":"Save the card limit the person gave","input":"<account_terms.assertion.set input object; candor_schema lists its fields>"})`.

## Paydown order

Ask which matters most: least interest, getting under a utilization level
before a statement date, never missing a due date, or keeping cash on hand.
Then show per card, in its currency: the amount to get strictly under the
level (rounded up to the cent), the minimum, the due date, and estimated
monthly interest at the APR, labeled an estimate (issuers accrue daily).
Save the order the person settles on as a `debt_reduction` goal with a
`debt` measure over those cards. When a utilization level is what they care
about, set the goal's target to the balance that gets them under it and say
so in `why`.

## After a payment

Payments happen outside Candor with the person's okay. Save a note with the
baseline balance and limit, the expected change, and a `revisit_at`, or a
watch on the card's payee. On revisit, check balances are newer than the
payment (for a connected card, `candor_connections({"operation":"sync.refresh","reason":"Refresh before checking the payment"})`;
for a card kept by hand, its newer statement or the balance the person
reads you), recompute utilization, and resolve the note only when the posted
balance shows it.

## Rewards and annual fees

1. Read each card's spend with
   `candor_get({"operation":"transactions.list","reason":"Read spend on this card","args":{"source_account_id":"SOURCE_ACCOUNT_ID","since":"START","until":"END","limit":100}})`.
   Follow every continuation. Do not spread aggregate spend across cards you
   cannot see.
2. Get current earning rules, caps, exclusions, credits, and the annual fee
   from the issuer's benefit guide or agreement, with the date.
3. Model only observed eligible spend: base and bonus rewards, caps, credits
   they would really use without new spending, and the fee. Keep cash value
   apart from travel-point value.
4. Routing advice (which card for groceries) can be saved as a note once
   they agree, without a separate yes.
5. Opening, closing, or downgrading a card touches credit history and
   borrowing plans: gather that context first. The application or call
   itself happens outside Candor with their okay.
