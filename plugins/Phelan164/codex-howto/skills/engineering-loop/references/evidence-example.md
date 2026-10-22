# Evidence handoff example

Illustrative checkout fix, not a real run or benchmark. Replace every command,
result, path, and revision with observed evidence. Omit irrelevant fields.

```text
Result: Empty-cart checkout returns the existing validation error without
calling the payment client. Valid-cart behavior and response schema are unchanged.
Changed: src/cart/checkout.ts; tests/checkout.test.ts.
Before: npm test -- checkout.test.ts — the new regression failed because the
payment mock received one call; expected zero.
After: npm test -- checkout.test.ts — 8 tests passed, including valid-cart coverage.
Required checks: npm test — 42 passed; npm run lint — passed.
Review: Self-review found and fixed a missing early return; all checks above
were rerun after that edit.
Limitations: Payment integration was mocked; live payment processing was not tested.
```

If independent review ran, name the actual reviewer, exact candidate revision,
confirmed findings and disposition, and whether later edits were reviewed.
An empty findings list is not a guarantee of correctness.

## When no automated tests exist

Report the repeatable command or manual steps, inputs, expected and observed
behavior, and before/after difference. A local empty-cart request may verify
the error response but not the absence of a downstream payment call. Use an
observable local stub or trace for that side effect; if unavailable, record it
as unverified. Do not equate limited manual evidence with full coverage.

## Evaluating this revision

Use the existing [measurement protocol](../../../resources/engineering-loop-measurement.md)
to compare previous and revised skills with a no-skill baseline. Freeze the
skill revision, model/effort, repository starting state, and acceptance checks;
use independent fresh runs and include failed or stopped attempts. Compare
acceptance and defects before time or tokens. Include reviewer usage and human
correction effort; leave unavailable usage unknown. Shorter instructions alone
do not establish better engineering efficiency.
