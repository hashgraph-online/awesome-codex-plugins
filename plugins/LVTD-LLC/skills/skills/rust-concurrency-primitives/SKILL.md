---
name: rust-concurrency-primitives
description: Design and review thread-based Rust concurrency with explicit ownership, sharing, and synchronization choices. Use when writing, refactoring, or reviewing threads, scoped threads, channels, Arc, Mutex, RwLock, Condvar, atomics, OnceLock, LazyLock, Send, Sync, deadlocks, or shared state.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Rust Concurrency Primitives
  category: Rust
  tags: rust,concurrency,threads,synchronization,atomics
---

# Rust Concurrency Primitives

Use this skill to design thread-based Rust concurrency with explicit ownership,
sharing, and synchronization. Prefer the simplest primitive that matches the
coordination requirement before adding shared mutable state.

## Core Workflow

1. Classify the work: independent fork-join, producer/consumer pipeline, shared
   state, one-time initialization, or low-level atomic coordination.
2. Prefer owned data per thread. Add shared ownership only when data must be
   observed or mutated by multiple threads.
3. Use `std::thread::scope` when child threads can borrow stack data and must
   finish before the function returns.
4. Use channels for ownership transfer and pipelines. Use `Arc<Mutex<T>>` or
   `Arc<RwLock<T>>` only when shared state is the clearer model.
5. Keep lock scopes short and never call user-controlled or blocking code while
   holding a lock unless that is the invariant being protected.
6. Use `OnceLock` or `LazyLock` for thread-safe one-time initialization instead
   of ad hoc global mutable state.
7. Treat atomics as a specialized tool. Use `SeqCst` by default until a weaker
   ordering is justified and documented.

## Primitive Selection

Read `references/threading-shared-state.md` before introducing a new shared
state primitive or reviewing deadlock-prone code.

| Need | Primitive |
|------|-----------|
| Borrow local data into short-lived threads | `std::thread::scope` |
| Transfer work or results | `std::sync::mpsc` or project channel crate |
| Shared read/write state | `Arc<Mutex<T>>` |
| Many readers, rare writers | `Arc<RwLock<T>>` |
| Wait for condition changes | `Condvar` with `Mutex` |
| One-time global initialization | `LazyLock` or `OnceLock` |
| Counters, flags, lock-free coordination | `std::sync::atomic` |

## Safety And Review Rules

- Require `Send` for values crossing thread boundaries and `Sync` for shared
  references used from multiple threads.
- Decide whether poisoning should propagate panic or recover with
  `PoisonError::into_inner`.
- Establish a lock ordering when more than one lock can be acquired.
- Prefer `Arc::clone(&value)` over `value.clone()` when the cloned value is an
  ownership handle and readability matters.
- Use Rayon for data parallel iteration when the problem is pure CPU data
  parallelism and the project already accepts that dependency.

## Tests

- Add deterministic tests around final state, message counts, and shutdown.
- Use barriers, channels, or scoped threads to coordinate tests; avoid sleeps.
- Add at least one test for panic, dropped sender/receiver, or cancellation
  behavior when the code depends on it.
