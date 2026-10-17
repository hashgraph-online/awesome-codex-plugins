# Triage and fingerprinting

## Goal

Answer these questions quickly:

1. What format and architecture is this target?
2. Is it stripped?
3. Is there any usable debug info?
4. How strong is the evidence that this is a Rust build?
5. What namespaces, crates, or subsystem hints are visible immediately?

## Evidence rubric for Rust confidence

### High confidence

Use **high** when multiple independent signals agree, for example:

- Rust mangling patterns in symbols
- demangled `core::`, `alloc::`, or `std::` namespaces
- panic/unwind artifacts
- multiple crate-like namespaces that fit Rust symbol structure

### Medium confidence

Use **medium** when only some of the above are present, or when the target is heavily stripped but still has strong Rust-adjacent strings.

### Low confidence

Use **low** when the target lacks symbols and strings do not clearly indicate Rust.

## Fast anchors

Start with:

```bash
file <target>
strings -a <target> | grep -E 'rust|panic|core::|alloc::|std::'
nm -an <target> | head
```

Then look for:

- raw `_R...`-style v0 symbols
- legacy `_ZN...17h...E`-style symbols
- demangled namespaces after `rustfilt`
- crate names that are not runtime crates
- imported libc / Win32 / networking APIs that indicate subsystem boundaries

## Namespace handling

Separate findings into:

- runtime crates: `core`, `alloc`, `std`, panic/unwind internals
- likely app crates
- likely third-party crates
- uncertain buckets

Do not claim a crate is “application code” from one symbol alone. Confirm with neighboring symbols, xrefs, or strings.
