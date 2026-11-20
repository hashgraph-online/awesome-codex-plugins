> The calls below are Candor MCP tool calls. Replace placeholders such as `TRANSACTION_ID` with values from earlier responses; where an `input` names an operation instead of showing an object, `candor_schema` lists its fields.

# Notes and watches

Notes are your memory between conversations, shared with the person. A note
is Markdown, with an optional link to the record it is about, an optional
date it comes back due, an optional watch Candor checks for you, and optional
context topics. Save notes yourself; do not ask whether to.

## What to keep

- **What the person said** that will matter later: what they want, who
  depends on them, how they get paid, what they will not touch. Use their
  words. Tag durable context with the matching topic so every later opening
  carries it: `objectives_and_time_horizons`, `current_financial_situation`,
  `people_and_responsibilities`, `operating_plan`,
  `constraints_and_protected_resources`, `decision_preferences`.
- **What you found** about a record and what came of it, linked with `about`,
  so the next review reads it instead of raising the same thing.
- **What they decided**, including a decision not to pursue something.
- **A follow-up** that depends on something later: a refund still to post, a
  charge that should stop, a first paycheck, a promo rate ending.

Keep their statements, your observations, and your assumptions visibly
separate. Save an inference you make labeled as your own reading.

## Create, update, resolve

```text
candor_write({
  "operation": "notes.create",
  "reason": "Keep the refund Acme promised",
  "input": "<notes.create input object; candor_schema lists its fields>"
})
candor_write({
  "operation": "notes.update",
  "reason": "Refund amount confirmed by the person",
  "input": "<notes.update input object; candor_schema lists its fields>"
})
candor_write({
  "operation": "notes.resolve",
  "reason": "Refund posted",
  "args": {
    "note_id": "NOTE_ID"
  }
})
candor_get({
  "operation": "notes.list",
  "reason": "Recover follow-ups that came due",
  "args": {
    "due": true,
    "limit": 50
  }
})
```

A note body worth returning to has four parts: what was promised or
expected, the baseline you saw (amounts, dates, record ids), how to check it,
and what each possible result means. `revisit_at` (a date) makes the note come
back due on a later opening. It does not wake anyone; only a host scheduler
does that (see `candor-weekly-check-in`).

Check the saved fields in the write response instead of reading the note
back. Update the same note as things change and resolve it when it is
settled. Read an earlier note with `candor_get({"operation":"notes.get","reason":"Read the earlier note","args":{"note_id":"NOTE_ID"}})`.

## Watches: let Candor check the records

When the follow-up is something the records will show, give the note a
`watch` and Candor matches new transactions for you. The opening's `watches`
section says what each one came to, so you do not search.

- A payee: `{"payee": "Acme", "expect": "deposit"}` for a refund or
  paycheck, `"charge"` for a bill that should arrive, `"no_charge"` for a
  subscription that should stop. Reports `seen`, `missed`, `held`, or
  `broken`.
- A balance floor: `{"account_id": "ACCOUNT_ID", "balance_below": "USD
  500.00"}`. Reports when it is crossed.
- A large transaction: `{"amount_over": "USD 1000.00", "direction":
  "outflow"}`.

Only transactions that arrive after the watch is set count. Pair a watch with
a `revisit_at` so a payee that never posts still comes back due. When a watch
answers, tell the person what happened. Resolve the note only when the outcome
is settled: the refund posted, the charge stayed away past its next billing
date, the paycheck arrived. A `missed` or `broken` result usually means the
work continues, so update the note and its `revisit_at` instead.

## Goal next steps

A goal's `next_step` takes the same kind of check (`transaction`, or
`figure`, `ask`, `review`) and a date. Prefer it over a separate note when the
follow-up belongs to a goal; the person sees the step under the goal.

## Impact you can show

When you or the person act on a specific finding that saves or recovers
money, record it once with `candor_write({"operation":"impacts.create","reason":"Record the saving being pursued","input":"<impacts.create input object; candor_schema lists its fields>"})` (the
typed category, a plain summary, the potential value, and the records behind
it). As it develops, append to the same impact with
`candor_write({"operation":"impacts.record","reason":"Record how the saving came through","input":"<impacts.record input object; candor_schema lists its fields>"})`: `action_taken` when the dispute or
cancellation goes out, `value_recorded` when money is observed or received,
`closed_without_value` or `reverted` when it does not come through. Keep
potential and received money separate; never annualize to make a figure
larger. `candor_get({"operation":"impacts.summary","reason":"Total what has been saved or recovered"})` answers "what have we saved?"
