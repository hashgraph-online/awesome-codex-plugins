# Application Architecture Rules

## Commands

- Make `NewRoot(deps Dependencies) *cobra.Command` construct a fresh tree.
- Keep `RunE` thin: bind validated input, invoke a service, render the result.
- Return errors; do not call `os.Exit` or construct global clients in commands.
- Put shared persistent flags on intentional parents, not every leaf.

## Dependencies

- Pass concrete dependencies explicitly from one composition root.
- Define narrow consumer-owned interfaces only where substitution is useful.
- Discover interfaces after a real consumer needs substitution.
- Avoid service locators, hidden singleton state, and packages named only `interfaces`.
- Own cleanup where construction occurs and close in reverse dependency order.
- Do not add production `dryRun` switches solely to bypass effects in tests;
  inject the effect unless dry-run is a real user-facing capability.
- Record lifecycle ownership for HTTP transports, SQL pools, listeners, timers,
  watchers, and background goroutines.
- Classify resources as owned, borrowed, or transferred; never close a borrowed
  stream or handle.
- Cover normal, error, cancellation, and partial-startup cleanup paths.
- Close in reverse dependency order and define whether cleanup failures are material.
- Keep fallible I/O, global clients, and order-dependent construction out of `init`.
- Give detached background work bounded admission, an independent deadline,
  an error sink, shutdown ownership, and a join path.

## Configuration

- Parse bootstrap flags needed for help, version, completion, output mode, and
  config location before loading runtime dependencies. These early operations
  must not require a valid remote service or full application configuration.
- Parse, merge, validate, then publish typed immutable settings.
- If live reload is necessary, build and validate a candidate, atomically swap it,
  retain last-known-good state, and stop watchers on shutdown.
- Keep mutable records behind a store or repository with domain-shaped operations.

## Package Design

- Group by cohesive behavior and ownership, not by generic technical nouns alone.
- Use `internal/` for implementation that must not become a public import contract.
- Keep reusable public packages small and independent of the executable.
- Reject circular dependency pressure by revisiting responsibility, not adding globals.
- Prefer synchronous application APIs; expose channels only when streaming is
  part of the caller contract.
- Document ordering, partial-result, and cancellation behavior for concurrent operations.
- Route numeric, slice, map, range, and Unicode correctness to
  `go-language-correctness`.
