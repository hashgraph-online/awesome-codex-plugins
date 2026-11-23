# PlaceCall: Items: `items`

Part of the PlaceCall skill ([`SKILL.md`](../SKILL.md)). Read it for sending `items` with a call.

Optional: a list of what the call must find out or get done, each an object
you key yourself.

```json
"items": [
  {"id": "hours.sat", "ask": "What are the Saturday opening hours?"},
  {"id": "parking", "ask": "Is there parking on site?"}
]
```

- `id`: 1-64 letters, digits, `_`, `.` or `-`, each id once per request.
- `ask`: one plain question or task, 1-120 characters.
- At most 12 items. A list that breaks a rule is refused with `422` and
  nothing is reserved, dialed or charged: `too_many_items`, `item_too_long`,
  `items_invalid` (not a non-empty list of `{"id", "ask"}` objects, a bad
  `id`, a blank `ask` or one with a control character), `items_duplicate`.
  `output_schema` in the body is refused as `field_reserved`.

On the call, the agent works through your items in your order instead of the
asks it would read from the brief. The brief still gives the context: who,
where, how to behave, and whether it is a booking or a question. Each `ask` is
screened with the brief, so an ask the screen would refuse in the brief is
refused the same way (`422 brief_policy_violation`). Items are part of the
request for `Idempotency-Key`, in their order: the same items in another
order are a different body.
