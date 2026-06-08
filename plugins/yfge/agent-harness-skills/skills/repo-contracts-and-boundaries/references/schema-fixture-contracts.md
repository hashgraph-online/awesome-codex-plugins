# Schema And Fixture Contracts

Use this when repository boundaries are expressed through payloads, schemas, fixtures, or golden examples.

## Contract Types

- Schema contract: validates input or output shape.
- Fixture contract: stores anonymized representative examples.
- Golden payload: captures a stable expected transformation or report.
- Compatibility contract: documents tolerated legacy shape and repayment plan.

## Bootstrap Steps

1. Identify the boundary where shape drift causes real breakage.
2. Add the smallest schema, fixture, or golden payload that captures that boundary.
3. Add a checker that validates current examples and changed files.
4. Put historical exceptions in a baseline with reason and repayment direction.

## Validation

- Run the checker in changed-file mode and full audit mode when available.
- Confirm fixtures contain no sensitive real data.
- Confirm failure output names path, contract, reason, and expected direction.

## Do Not Include

- Fixtures copied from private data.
- Golden payloads that require hidden services to interpret.
- Compatibility exceptions without an owner or repayment direction.
