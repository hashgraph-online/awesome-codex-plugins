> The calls below are Candor MCP tool calls. Replace placeholders such as `TRANSACTION_ID` with values from earlier responses; where an `input` names an operation instead of showing an object, `candor_schema` lists its fields.

# Impacts

An impact records what a finding is worth and what actually came back, so
"what have you saved me?" has a real answer.

## Create one when you act

Create the impact when you or the person decide to act on a specific
finding, not for every candidate.

```text
candor_write({
  "operation": "impacts.create",
  "reason": "Record the duplicate Spotify charge being pursued",
  "input": "<impacts.create input object; candor_schema lists its fields>"
})
```

- `category`: `money_recovered` (refunds, reversals, reimbursements),
  `spending_reduced` (a cancelled or cheaper service), `fees_or_interest_reduced`,
  `income_or_yield_increased`, `benefit_or_reward_captured`,
  `tax_cost_reduced`, or `time_returned`.
- `benefit_summary`: one plain sentence that still makes sense later.
- `potential_value`: `one_time` for a refund, `recurring_rate` (monthly or
  annual) for a cancelled subscription, `bounded_total` for a window. Keep
  any cost to get it separate in `implementation_cost`.
- `basis_refs`: the transactions, recurring series, or accounts behind it.

## Append as it moves

```text
candor_write({
  "operation": "impacts.record",
  "reason": "Spotify refund posted",
  "input": "<impacts.record input object; candor_schema lists its fields>"
})
```

Event `type`:

- `action_taken`: what was done ("Requested a refund through Spotify
  support").
- `value_recorded`: money observed or landed. `state` is `outcome_observed`
  or `realized`; `value_basis` says what supports it (`evidence_verified` for
  a posted deposit, `user_confirmed`, `agent_attested`).
- `potential_revised`: the expected value changed.
- `closed_without_value`: the person dropped it, or the merchant refused.
- `reverted`: a recorded value was reversed (a refund clawed back).

## Rules

- Potential is not realized. Record `realized` only from a posted
  transaction or an authoritative final status.
- Never annualize a one-time refund or mix currencies to make a figure
  bigger.
- Partial recovery: record what landed and keep the rest open.
- `candor_get({"operation":"impacts.summary","reason":"Total what has been saved or recovered"})` reports potential, observed, and realized value
  separately. `candor_get({"operation":"impacts.get","reason":"Read the saving and its history","args":{"impact_id":"IMPACT_ID"}})` reads one impact's history.
