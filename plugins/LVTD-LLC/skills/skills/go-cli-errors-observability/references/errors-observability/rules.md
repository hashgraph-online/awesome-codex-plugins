# Errors and Observability Rules

## Errors

- Wrap with operation context and `%w`; inspect with `errors.Is` and `errors.As`.
- Do not match error strings when a typed or sentinel cause is available.
- Use `errors.Is` and `errors.As` for joined as well as linear error chains.
- Include a next action when the user can recover.
- Distinguish cancellation, deadline, validation, authentication, authorization,
  conflict, transport, protocol, and internal failures.
- Centralize exit mapping and keep `os.Exit` at the process boundary.
- Assign one terminal owner to log, render, and map a returned failure.
- At intermediate layers, add context and return; do not log and return.
- Preserve a primary error plus material cleanup failure with an inspectable
  wrapper or `errors.Join`.
- Use panic only for violated invariants; recover only at an intentional boundary
  that can restore valid state and preserve evidence.

## Logs

- Use stable, low-cardinality keys and explicit values.
- Keep normal mode quiet; make debug mode opt-in and bounded.
- Send logs away from structured result stdout.
- Redact at creation and at sink boundaries.
- Do not log request bodies, tokens, cookies, passwords, or full environment maps.
- Use contextual logging methods when request-scoped metadata is required.
- Check handler `Enabled` before expensive enrichment.
- Clone retained `slog.Record` values and copy retained attribute slices.
- Preserve `WithAttrs` and `WithGroup` semantics in custom handlers.

## Diagnostics

- Allowlist collected fields; never rely on a denylist alone.
- Preview bundle contents and require explicit user consent.
- Store bundles with restrictive permissions and a clear retention story.
- Keep collection and upload separate so the user can inspect the artifact.
- Make upload cancellable and report its destination.

## Verification

- Test classification and exit mapping independently from message prose.
- Test redaction with representative secret shapes.
- Confirm debug mode cannot alter structured stdout.
- Confirm profiling endpoints are disabled by default and inaccessible remotely.
- Test joined primary/cleanup failures and verify both identities remain inspectable.
