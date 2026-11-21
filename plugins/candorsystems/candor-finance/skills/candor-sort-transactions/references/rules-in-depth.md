> The calls below are Candor MCP tool calls. Replace placeholders such as `TRANSACTION_ID` with values from earlier responses; where an `input` names an operation instead of showing an object, `candor_schema` lists its fields.

# Rules in depth

## How a rule behaves

- A rule is declarative. While active it applies to every record it matches,
  past and future, pending and posted, refunds included. Saving it starts a
  background walk; rows update as it lands.
- A rule changes how records read: category, label, cashflow role, review
  status, or tags. Category and role are independent. `set_category` only
  regroups; `set_cashflow_role` changes whether a record counts as income,
  expense, transfer, debt payment, or refund.
- Add `match_direction`, `match_account_role`, or an amount bound only when
  the meaning depends on it. Rent paid by card depends on the account's
  role; the role survives a reconnect and an account id does not.

## Read the reach

```text
candor_get({
  "operation": "rules.get",
  "reason": "Read the rule's walk and counts",
  "args": {
    "rule_id": "RULE_ID"
  }
})
candor_preview({
  "operation": "rules.preview",
  "reason": "Read a sample of what the saved rule reaches",
  "args": {
    "rule_id": "RULE_ID"
  }
})
```

`materialization.status` moves through pending, applying, and applied;
`applied_count` says how many records it reached. A nonzero `skipped_count`
names records that already carry the most applications a record can hold;
they keep their current fields.

The preview's `matched_count` is every match. `matches` is a sample of up to
25 rows covering each distinct label first, each with its `proposed` change.
Judge from the sample and `match_label_counts`; you do not need every row.
`scan_truncated` means the counts are lower bounds; the rule still applies to
all matches.

## Exceptions and priority

An exception is a second rule with a smaller `priority` number than the rule
it overrides. The default is 50 and a smaller number wins for label,
category, role, and review status, so give an exception 10. Tags are added
and removed in application order instead. An exact correction beats every
rule on those same fields. Both rules stay active.

## Undo

```text
candor_write({
  "operation": "rules.disable",
  "reason": "The anchor reached a second merchant",
  "args": {
    "rule_id": "RULE_ID"
  }
})
candor_write({
  "operation": "rules.revert",
  "reason": "Keep this one record out of the rule",
  "args": {
    "rule_application_id": "APPLICATION_ID"
  }
})
```

Disabling reverts every application in the background, and `rules get`
then reports `reverted`. Reverting one application keeps that record out of
the rule for good, through later syncs; use it for a deliberate exception,
and a correction when the record needs a different meaning. The record's
`applied_rules` carries the application id.

## Explain a record that reads wrong

```text
candor_get({
  "operation": "transactions.get",
  "reason": "Explain why the record reads this way",
  "args": {
    "transaction_id": "TRANSACTION_ID"
  }
})
candor_get({
  "operation": "transactions.get",
  "reason": "List every active rule and the criterion each failed",
  "args": {
    "transaction_id": "TRANSACTION_ID",
    "rules": "all"
  }
})
```

- `effective_category.provenance` says whether a rule, a correction, the
  record itself, or the bank's category supplied the value.
- `rules_considered` lists rules that matched or applied, with `applied` and
  `not_applied_reason`; with the rules scope set to all, each active rule
  shows `matched` and `failed_criteria`. `omitted_count` says how many active
  rules did not match.
- `pending`: the rule matches and its walk has not reached this record yet.
  Read `rules get` for progress.
- `reverted`: an earlier application was undone here on purpose and will not
  return. Read the actions around `reverted_at` for why, and leave it.
- A `disabled` rule was switched off on purpose. Do not recreate it for one
  record.
- When two applied rules disagree, the smaller `priority` number wins; on a
  tie the newer rule wins. Disable the one that should not apply rather than
  writing a third rule for the same merchant.
- `truncated` means the workspace has more active rules than one explanation
  lists. Read the rules list for the merchant before concluding none covers
  it.

## Tags for goals

A `tagged` goal reads the monthly net (or money in, or money out) of
transactions carrying its tags. Tag income and costs alike when the figure is
a net. Dry-run first, then save:

```text
candor_preview({
  "operation": "rules.preview",
  "reason": "Check which records the shop tag would reach",
  "args": {
    "match_merchant_contains": "ETSY",
    "add_tag": "shop"
  }
})
candor_write({
  "operation": "rules.create",
  "reason": "Tag the shop's sales for its goal",
  "args": {
    "name": "Etsy is the shop",
    "match_merchant_contains": "ETSY",
    "add_tag": "shop",
    "authority": "person_stated",
    "basis_reason": "The person said Etsy deposits are shop sales."
  }
})
```

A rule keeps tagging new transactions as they arrive. Read tagged rows with
`candor_get({"operation":"transactions.list","reason":"Check what the shop tag covers","args":{"tag":"shop","limit":100}})`.
