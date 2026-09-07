# Errors and Observability Knowledge

## Four Layers

1. **Cause**: wrapped or typed error retaining programmatic identity.
2. **Classification**: invalid input, unavailable dependency, conflict,
   cancellation, timeout, permission, or internal defect.
3. **Presentation**: concise message, relevant context, and recovery action.
4. **Process mapping**: stable exit status or structured error envelope.

Keep classification independent of prose so messages can improve without
breaking callers.

## Evidence Channels

- Normal result data belongs on stdout.
- User diagnostics and logs belong on stderr or a configured log sink.
- Debug mode increases evidence detail, not result verbosity or secret exposure.
- A correlation ID can connect a concise failure to local or remote telemetry.

`slog` supports structured records, levels, attributes, handlers, and contextual
logging. Choose keys deliberately and avoid dumping arbitrary structs.

A `slog.Handler` decorator must preserve the `Enabled`, `Handle`, `WithAttrs`,
and `WithGroup` contracts. Check levels before expensive attribute work. Clone a
record before retaining or modifying shared state, and copy retained attribute
slices. Go 1.26 adds `slog.NewMultiHandler`; verify the module's minimum Go
version before relying on it.

Error chains can be trees after `errors.Join` or multiple wrapping operands.
Prefer `errors.Is` and `errors.As`; a manual `errors.Unwrap` loop sees only the
single-error form.

## Error Ownership and Cleanup

Each failure should have one terminal owner. Intermediate layers add stable
operation context and return; the process boundary classifies, renders, logs,
and maps the exit status. Logging and returning at every layer duplicates
evidence and obscures the original failure.

When work fails and cleanup also fails, preserve the primary error while
retaining material close, flush, wait, or shutdown evidence. `errors.Join` can
represent both while keeping `errors.Is` and `errors.As` useful. Do not join
routine or ignorable cleanup noise.

Panic represents a violated invariant or unrecoverable programmer defect, not
ordinary CLI control flow. Recover only at a boundary that can restore a valid
state, record safe evidence, and choose a deliberate failure contract.

Context-derived correlation IDs are request metadata, not arbitrary
configuration. Use typed keys, validate shape, and control cardinality and
redaction before adding them to every record.

## Diagnostic Bundles

A bundle is a curated support artifact, not a filesystem or environment dump.
Define an allowlist such as version, platform, selected nonsecret settings,
sanitized logs, and a user-provided reproduction note. Show what will be
collected, redact again before serialization, and separate creation from upload.

## Profiling and Tracing

Profiles and traces can expose arguments, paths, request metadata, and workload
shape. Enable them explicitly, bind debug endpoints to loopback by default,
authenticate when exposure is possible, and impose collection limits.
