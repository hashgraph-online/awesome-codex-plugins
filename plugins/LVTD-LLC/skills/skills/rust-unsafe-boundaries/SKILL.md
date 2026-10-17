---
name: rust-unsafe-boundaries
description: Isolate and review unsafe Rust behind small, documented, testable boundaries with explicit invariants. Use when writing, refactoring, or reviewing unsafe code, raw pointers, unsafe functions, unsafe traits, MaybeUninit, pointer aliasing, panic safety, Miri checks, or safe abstractions over unsafe internals.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Rust Unsafe Boundaries
  category: Rust
  tags: rust,unsafe,raw-pointers,memory-safety,miri
---

# Rust Unsafe Boundaries

Use this skill to isolate unsafe Rust behind small, documented, testable
boundaries. Unsafe code is acceptable only when a safe API cannot express the
needed operation with acceptable correctness and performance.

## Core Workflow

1. Try the safe design first. Check standard APIs, ownership restructuring,
   iterators, synchronization primitives, and existing crates.
2. State the invariant that safe Rust cannot prove. If the invariant cannot be
   written down, do not write unsafe code yet.
3. Keep unsafe blocks tiny. Put runtime checks and setup in safe code before the
   block.
4. Add a `// SAFETY:` comment immediately before each unsafe block explaining
   why every unsafe operation inside is valid.
5. Mark a function `unsafe fn` only when callers must uphold extra conditions.
   Document those conditions in a `# Safety` section.
6. Enable or respect `unsafe_op_in_unsafe_fn`; unsafe operations inside unsafe
   functions should still be wrapped in explicit unsafe blocks.
7. Test normal behavior, boundary cases, panic paths, and drop behavior. Run
   Miri when the project supports it.

## Boundary Rules

Read `references/safety-invariants.md` before adding or approving unsafe code.

- Prefer private unsafe internals plus a safe public wrapper.
- Prefer `MaybeUninit<T>` over deprecated or ad hoc uninitialized memory
  patterns.
- Never create references from raw pointers unless validity, alignment,
  initialization, aliasing, and lifetime are all proven.
- Do not use `set_len`, pointer arithmetic, or `from_raw_parts` without proving
  capacity, initialization, and ownership.
- Make panic safety explicit when partially initialized values, manual drops, or
  length changes are involved.
- Avoid `static mut`; prefer `OnceLock`, `LazyLock`, atomics, or locked state.

## Documentation Pattern

```rust
/// # Safety
///
/// `ptr` must be non-null, aligned for `T`, initialized, and valid for reads
/// for the returned lifetime. No mutable reference may alias the same value.
pub unsafe fn read_ref<'a, T>(ptr: *const T) -> &'a T {
    // SAFETY: The caller guarantees `ptr` satisfies the documented contract.
    unsafe { &*ptr }
}
```

## Review Checklist

- Every unsafe block has a local `SAFETY` explanation.
- Every `unsafe fn` or unsafe trait has a `# Safety` contract.
- Public safe APIs cannot be used to violate internal invariants.
- Drop, panic, and early-return paths preserve initialization and ownership.
- Tests or Miri cover the dangerous edge, not only the happy path.
