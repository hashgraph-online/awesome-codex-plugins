---
name: rust-ownership-borrowing
description: Design and review Rust ownership, borrowing, lifetimes, and interior mutability so data flow matches the domain model. Use when writing, refactoring, or reviewing Rust code that hits move, borrow checker, aliasing, Clone, Copy, Rc, Arc, RefCell, or lifetime problems.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Rust Ownership Borrowing
  category: Rust
  tags: rust,ownership,borrowing,lifetimes,borrow-checker
---

# Rust Ownership Borrowing

Use this skill to make ownership shape match the program's data flow. Treat
borrow-checker errors as design feedback: decide who owns each value, how long
access must last, and whether mutation needs exclusivity or a different data
shape.

## Core Workflow

1. Identify the owner of each value crossing the failing code path.
2. Decide the required access for each function: own, shared borrow, mutable
   borrow, or shared ownership.
3. Shorten borrows before changing types. Introduce blocks, temporary values,
   helper functions, or earlier extraction so references end before mutation.
4. Prefer moving values when the caller no longer needs them. Prefer borrowing
   when the caller retains ownership. Clone only when duplicate ownership is
   intentional and the cost is acceptable.
5. Replace self-referential or graph-like designs with IDs, indices, arenas, or
   ownership trees before reaching for `Rc<RefCell<_>>`.
6. Use `Rc` for single-threaded shared ownership and `Arc` for cross-thread
   shared ownership. Add `Cell`, `RefCell`, `Mutex`, or `RwLock` only when the
   mutation model is explicit.
7. Add tests that exercise the ownership-sensitive behavior, not just the
   compiler error that prompted the change.

## Signature Rules

- Take `T` when the function consumes or stores the value.
- Take `&T` when the function only reads during the call.
- Take `&mut T` when the function must mutate and no other access should occur.
- Return owned values unless the returned reference is clearly tied to an input
  lifetime.
- Avoid accepting `&Vec<T>`, `&String`, or `&PathBuf` when `&[T]`, `&str`, or
  `&Path` expresses the needed capability.
- Avoid adding lifetime parameters to structs unless the struct truly borrows
  data owned elsewhere. Owned fields are usually simpler.

## Common Fix Patterns

Read `references/borrow-patterns.md` when resolving non-trivial compiler
errors or reviewing a borrow-heavy patch.

- Narrow the scope of immutable borrows before taking a mutable borrow.
- Use `Option::take`, `std::mem::take`, or `std::mem::replace` to move a field
  out while leaving a valid value behind.
- Use collection APIs such as `split_at_mut`, `get_mut`, `entry`, `drain`, and
  `retain` instead of indexing patterns that create overlapping borrows.
- Clone handles like `Arc`, `Rc`, and cheap IDs freely when that is the intended
  ownership handle; avoid cloning payloads to silence the compiler.
- Convert iterator chains to explicit loops only when it makes borrow lifetimes
  clearer or avoids hidden captures.

## Review Checklist

- Ownership follows the domain model; types are not wrapped just to bypass the
  borrow checker.
- `Clone` is deliberate and tested for semantic independence where relevant.
- Interior mutability has a clear invariant and a small access surface.
- Lifetimes describe real borrowing relationships, not guesses added until the
  compiler accepts the code.
- Async or threaded code uses `Arc` plus the right synchronization primitive;
  `Rc` and `RefCell` stay out of cross-thread paths.
