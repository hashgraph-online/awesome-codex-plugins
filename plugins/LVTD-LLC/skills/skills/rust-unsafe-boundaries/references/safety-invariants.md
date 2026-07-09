# Safety Invariants

Use this reference when writing or reviewing unsafe Rust.

## Unsafe Block Audit

For every unsafe block, identify:

- Which unsafe operations occur?
- What preconditions does each operation require?
- Where are those preconditions checked or guaranteed?
- Can panic, early return, or drop violate the invariant?
- Can safe callers reach undefined behavior through this API?

## Raw Pointer Checklist

- Pointer is non-null when null is invalid.
- Pointer is aligned for the target type.
- Memory is initialized before reads.
- Memory is valid for the required size and lifetime.
- Aliasing rules are respected: no mutable reference aliases active shared
  references, and no two mutable references exist.
- Ownership of allocation and deallocation is clear.

## MaybeUninit Checklist

- Do not call `assume_init` until every element or field is initialized.
- Use guards or careful length updates for panic safety.
- Dropping `MaybeUninit<T>` does not drop `T`; manually drop initialized values
  on failure paths.
- Prefer library helpers such as array initialization APIs when they fit.

## Validation Commands

Run what the project supports:

```bash
cargo test
cargo clippy --all-targets --all-features -- -D warnings
cargo miri test
```

If Miri is unavailable, say so explicitly and rely on tests plus focused unsafe
review.
