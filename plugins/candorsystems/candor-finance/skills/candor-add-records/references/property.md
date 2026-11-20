> The calls below are Candor MCP tool calls. Replace placeholders such as `TRANSACTION_ID` with values from earlier responses; where an `input` names an operation instead of showing an object, `candor_schema` lists its fields.

# Property

A property's value is an estimate or appraisal with a date and a source, not
cash and not a sale price. Estimated rent is not income received.

## Find or add the property

```text
candor_get({
  "operation": "properties.list",
  "reason": "Check whether this property is already tracked",
  "args": {
    "limit": 25
  }
})
candor_get({
  "operation": "properties.get",
  "reason": "Read the property and its value history",
  "args": {
    "property_id": "PROPERTY_ID",
    "limit": 100
  }
})
```

Match on the full address, including the unit, before creating anything.
Use the canonical property id for every later change; a provider's id is not
it.

## Preview and apply

```text
candor_write({
  "operation": "properties.preview",
  "reason": "Preview the property the person described",
  "input": "<properties.preview input object; candor_schema lists its fields>"
})
candor_write({
  "operation": "properties.apply",
  "reason": "Track the reviewed property",
  "args": {
    "preview_id": "PREVIEW_ID"
  }
})
```

Send the complete intended property input (include `property_id` for an
existing one). Check the preview's address, amounts, date, ownership share,
and `effect` before applying that exact preview. A changed input needs a
fresh preview; never create a second property as a workaround.

- A current manual value switches the property to manual tracking and stops
  automatic estimates.
- An older appraisal has `effect: history_only`: it extends history and
  changes nothing current.
- In manual mode, omit `monthly_rent` to keep the current estimate, or send
  `monthly_rent: null` to clear it. Zero means a real zero.
- Rent estimates say whether they are for the whole property or one unit.
  Per-unit estimates are not multiplied by a guessed unit count.

## Ownership and the mortgage

- Value is whole-property; the owned value applies the recorded ownership
  share once.
- Link the loan account once. Set `mortgage_balance_scope: full_account` only
  when the whole recorded loan balance belongs in this property's equity.
  Ownership share does not establish who owes the debt; when that is unclear,
  leave equity unknown rather than inventing a split. One loan links to one
  property.
- A property confirmed paid off needs no loan link; a recorded zero balance
  is also fine.

## Check the result

Re-read the property and `candor_get({"operation":"net_worth.summary","reason":"Check the property's effect on net worth"})`.
History-only changes must not move current net worth. Value changes are not
investment returns or income.

## Estimates and refresh

Automatic estimates use a US provider about every 30 days. Ordinary reads
never contact it; a preview may. On `property_rate_limited` or
`property_provider_budget_exhausted`, wait `retry_after_seconds` before
another estimate; saved estimates and manual tracking keep working. A failed
refresh keeps the last estimate: report its original date.

## Undo or stop tracking

- `candor_write({"operation":"properties.revert","reason":"Undo the latest property change","args":{"preview_id":"PREVIEW_ID"}})`
  reverses the latest import unless newer evidence arrived; then submit a
  correction instead.
- `candor_write({"operation":"properties.archive","reason":"Stop tracking the sold property","args":{"property_id":"PROPERTY_ID"}})`
  stops tracking and keeps history. It does not record a sale or pay off the
  loan.
