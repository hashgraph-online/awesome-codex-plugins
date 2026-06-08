# Environment Bootstrap

Use this when validation needs setup checks before functional commands can be trusted.

## Minimum Surface

- Setup command or documented preparation steps.
- Example configuration file with placeholder values.
- Doctor or readiness command that checks required tools, generated files, and external dependency reachability.
- CI-safe fallback for checks that cannot run in every environment.

## Bootstrap Steps

1. Inventory required tools, generated assets, local services, and external dependencies.
2. Split setup checks from behavior checks.
3. Make readiness failures explicit and non-destructive.
4. Document fallback or skip reasons with the validation result.

## Validation

- Run the readiness command from a clean checkout or documented setup.
- Confirm failures name the missing prerequisite and next action.
- Confirm CI does not require private credentials or private machines.

## Do Not Include

- Hidden local setup.
- Credentials or account names in setup docs.
- A single heavyweight command that mixes setup, behavior, and delivery checks.
