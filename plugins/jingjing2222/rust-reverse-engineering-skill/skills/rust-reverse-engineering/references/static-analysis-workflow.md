# Static analysis workflow

## Recommended order

1. Load the binary and run auto-analysis
2. Apply Rust demangling if the tool did not do it well enough
3. Identify runtime crates and mentally de-prioritize them
4. Build a namespace inventory
5. Start from one feature path only

## Best anchors

Prefer:

- exports
- imports
- strong strings and xrefs
- config/env parsing
- network and filesystem APIs
- panic/error boundaries

Avoid starting from:

- giant dispatcher functions with no good anchors
- massive formatting helpers
- allocator internals
- generic runtime glue

## Rename strategy

Use consistent prefixes such as:

- `rt_` for runtime helpers
- `ffi_` for ABI boundaries
- `app_` for likely application entry points
- `sub_` for unresolved but grouped subsystems

Do not over-rename early. Keep uncertainty visible.

## What to recover first

Recover in this order:

1. startup path
2. exports/imports
3. one subsystem
4. one end-to-end call flow
5. supporting helpers only as needed
