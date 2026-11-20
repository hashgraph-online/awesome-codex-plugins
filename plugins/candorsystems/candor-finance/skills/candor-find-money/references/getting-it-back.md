> The calls below are Candor MCP tool calls. Replace placeholders such as `TRANSACTION_ID` with values from earlier responses; where an `input` names an operation instead of showing an object, `candor_schema` lists its fields.

# Getting it back

Every step here is outside Candor. Do it only with the person's okay for that
specific action. Then do it yourself if you have the tools: a browser signed
in as them, their email, a form. If you do not, hand them a ready message or
call script. Never ask for passwords or codes in chat.

## What to have ready

- The merchant and the account or plan identity (never a full card number).
- The exact charges: dates and amounts.
- What was promised or expected, and where it came from.
- What you are asking for: a refund of $X, a reversal, a cancellation
  effective today, the old price.
- A deadline, if one applies (a dispute window, a trial end).

## By situation

- **Duplicate or wrong charge:** ask the merchant first through their help
  page or support email. If they refuse or do not answer, a card dispute is
  the fallback; most issuers allow 60 days from the statement.
- **Bank fee:** ask the bank to waive it, citing the account's history.
  First-time and occasional fees are often waived.
- **Missing refund or reimbursement:** check the merchant's or employer's
  portal status first. Then a short follow-up quoting the original promise.
- **Price increase:** ask for the old price or a retention offer, or compare
  current plans from the merchant's own site. Do not promise an offer exists.
- **Cancel a subscription or trial:** cancel on the merchant's site or app
  before the next billing date and keep the confirmation. Say in the note
  when the last charge should be.

## Message template

```text
Hi, I was charged [amount] twice on [date] for [service/order]. I only made one purchase. Please refund the duplicate [amount] to the original card. Account: [account email or number, last 4 only]. Thank you.
```

## After acting

1. Record the step: `candor_write({"operation":"impacts.record","reason":"Refund requested from Spotify","input":"<impacts.record input object; candor_schema lists its fields>"})` (`action_taken`).
2. Save or update the note with a `watch` and a `revisit_at`: a `deposit`
   watch on the payee for a refund, `no_charge` for a cancellation.
3. On a cancellation, update the series once the last expected posting has
   passed:

```text
candor_write({
  "operation": "recurring.update",
  "reason": "Cancelled; the last charge has passed",
  "args": {
    "recurring_item_id": "RECURRING_ITEM_ID",
    "status": "stopped"
  }
})
```

A stopped series that posts again comes back as a change; that is a charge
after cancellation.

## Trials

When the person starts a trial or asks you to keep an eye on one, recover the
merchant, end date, price, and cadence from the signup confirmation (unknown
is fine, write it down as unknown). Save a note linked to the signup
authorization with a `watch` on the payee: `charge` if they plan to keep it,
`no_charge` if they plan to cancel. Set `revisit_at` to a few days after the
end date. If they want to cancel, offer to do it before the end date.
