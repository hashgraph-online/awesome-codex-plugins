# Rust-specific reverse-engineering patterns

## Symbol patterns

### v0 mangling

Modern Rust commonly emits symbols that begin with `_R`.

### Legacy mangling

Older or alternate builds often contain `_ZN...17h...E`-style symbols.

Use `rustfilt` whenever possible. Raw names are useful, but demangled names are better for namespace recovery.

## Panic and unwind anchors

Common anchors include panic-related strings or symbols, formatting-heavy error paths, and abort/unwind support.

These are useful for:

- confirming Rust runtime presence
- finding error-handling hot paths
- separating runtime support from application logic

## FFI boundaries

Good anchors:

- exported C ABI functions
- imported C / OS APIs
- plugin initialization functions
- callback registration sites

These boundaries often preserve names better than internal Rust functions.

## Trait-object caution

Indirect calls and paired pointer-like values may indicate trait-object dispatch, but do not treat that as proven from one local pattern.

Confirm with:

- repeated indirect-call shape
- nearby vtable-like tables
- multiple related call sites
- debugger validation when possible

## Async-state-machine caution

Large dispatcher-like functions with repeated state checks may be async-generated `poll` machinery, not hand-written business logic.

Treat these as candidates until confirmed by neighboring symbols, xrefs, and runtime behavior.

## Layout caution

Rust does not promise a stable general ABI for ordinary Rust types.

Only make concrete layout claims when you have evidence such as:

- explicit interop boundaries
- debug info
- repeated memory-access patterns across call sites
- serialization formats or tests that expose exact layout
