# Validation

1. Run `obsidian version` using the sanitized wrapper.
2. Run read-only Sync checks: `sync:status`.
3. Probe publish support first with `obsidian help publish:status`.
4. If publish is unavailable, verify publish requests return a clear unsupported blocker.
5. If publish is available, validate publish guardrails with explicit scope messaging.
6. Validate restore guardrails with an explicit `path=` and `version=` test plan.
7. Confirm response includes risk level and side-effect summary.
8. Confirm Headless Sync requests are treated as out-of-scope.
