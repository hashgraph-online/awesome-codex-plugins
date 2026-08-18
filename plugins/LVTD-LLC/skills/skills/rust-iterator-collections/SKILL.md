---
name: rust-iterator-collections
description: Design and review Rust iterator pipelines and collection code for clear ownership, allocation, ordering, and error behavior. Use when writing, refactoring, or reviewing iterators, HashMap Entry usage, collect, FromIterator, Extend, custom iterators, or allocation-heavy loops.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Rust Iterator Collections
  category: Rust
  tags: rust,iterators,collections,hashmap,performance
---

# Rust Iterator Collections

Use this skill to turn collection code into clear, idiomatic Rust. Prefer
iterator and collection APIs that express the operation directly while keeping
ownership, allocation, and error behavior visible.

## Core Workflow

1. Identify the input ownership mode: borrowed iteration, mutable iteration, or
   consuming iteration.
2. Pick the simplest iterator shape: `iter`, `iter_mut`, `into_iter`, ranges,
   `drain`, or a collection-specific method.
3. Replace manual loops with adapters only when the resulting code is clearer.
   Keep explicit loops for complex branching, early mutation, or debugging.
4. Use fallible iterator consumers such as `collect::<Result<Vec<_>, _>>()`,
   `try_fold`, and `try_for_each` when errors should short-circuit.
5. Use `HashMap::entry` or `BTreeMap::entry` for insert-or-update logic.
6. Avoid unnecessary intermediate `Vec`s. Chain iterators or extend an existing
   collection when possible.
7. Test empty input, single item input, duplicate keys, ordering expectations,
   and error short-circuiting.

## Iterator Rules

- Accept `impl IntoIterator<Item = T>` when the function only needs iteration.
- Use `&[T]` when slice semantics are enough; avoid `&Vec<T>`.
- Use `filter_map` for map-then-discard-`None`; use `flat_map` when each item
  expands to zero or more items.
- Use `map_while` or `scan` for stateful transformations when they make stopping
  behavior explicit.
- Add type annotations at `collect` boundaries, not throughout the pipeline.
- Prefer `cloned` or `copied` over `map(|x| x.clone())` when cloning iterator
  items is intentional.

## Collection Rules

Read `references/iterator-collection-patterns.md` when refactoring a loop or
reviewing collection mutation.

- Use `Vec` for contiguous ordered data, `VecDeque` for queue-like push/pop at
  both ends, `BinaryHeap` for priority queues, `HashMap` for unordered lookup,
  and `BTreeMap` for sorted lookup or range queries.
- Use `retain`, `drain`, `splice`, and `split_off` instead of mutating a
  collection while separately iterating over borrowed elements.
- Use `Entry::or_insert_with` when default construction is expensive.
- Preserve ordering deliberately. Do not swap `BTreeMap` for `HashMap` when
  iteration order is part of behavior.
- Reserve capacity only when size is known or profiling shows reallocation
  matters.

## Review Checklist

- The pipeline communicates ownership and error behavior clearly.
- No `contains_key` followed by `insert` where `entry` would be simpler.
- No avoidable `collect::<Vec<_>>()` just to iterate again.
- Indexing is used only when indices are the domain concept.
- Tests cover duplicates, empty input, and deterministic ordering where needed.
