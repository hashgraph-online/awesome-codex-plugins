---
name: rust-async-task-design
description: Design and review Rust async code around task ownership, suspension points, cancellation, blocking work, and runtime boundaries. Use when writing, refactoring, or reviewing futures, async functions, Tokio tasks, spawn, JoinHandle, Send futures, async traits, cancellation, or mutexes across await points.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Rust Async Task Design
  category: Rust
  tags: rust,async,tokio,futures,tasks
---

# Rust Async Task Design

Use this skill to make Rust async code explicit about task ownership, suspension
points, blocking work, and cancellation. Async is a concurrency model, not a
default replacement for threads or a performance guarantee.

## Core Workflow

1. Identify the async boundary: runtime entrypoint, handler, client call,
   stream, background task, or trait method.
2. Mark every `.await` as a possible suspension point. Check what state is held
   across it.
3. Use `tokio::spawn(async move { ... })` only when the task can own everything
   it needs and its future is `Send + 'static` on the selected runtime.
4. Keep `JoinHandle`s when task success, panic, cancellation, or shutdown
   matters. Do not silently detach important work.
5. Keep blocking IO and CPU-heavy work out of async tasks. Use async APIs,
   `spawn_blocking`, Rayon, or dedicated threads as the workload requires.
6. Do not hold a synchronous `MutexGuard`, `RefCell` borrow, or non-`Send` value
   across `.await`.
7. Add tests for timeout, cancellation, dropped channel, and failed task paths
   when those outcomes affect behavior.

## Runtime Rules

Read `references/async-runtime-patterns.md` when reviewing task spawning,
shared state in async code, or blocking work.

- Use `std::sync::Mutex` in async code only for short, low-contention critical
  sections that do not cross `.await`.
- Use `tokio::sync::Mutex` when a lock must be held across `.await`, but first
  consider moving the state behind a task and interacting by messages.
- Use `spawn_blocking` for blocking operations that eventually finish. Limit
  parallelism for CPU-heavy work; Tokio's blocking pool can grow large.
- Use `tokio::time::timeout` or explicit cancellation tokens for bounded
  operations.
- Use `select!` carefully: dropping a future can cancel it. Check cancellation
  safety before using it around IO or partially completed work.

## Async Trait Rules

- Native `async fn` in traits is fine for private traits and static dispatch
  when callers do not need to add bounds to the returned future.
- Public traits that need `Send` futures should usually spell the method as
  `fn name(...) -> impl Future<Output = T> + Send` or use `trait-variant` to
  offer local and `Send` variants.
- Public traits that need dynamic dispatch usually need an explicit boxed
  future return type, such as `Pin<Box<dyn Future<Output = T> + Send + '_>>`.
  Use `async-trait` as an ergonomics layer only when the dependency and
  allocation tradeoff are acceptable.
- Avoid leaking executor-specific types from a trait unless the trait is
  intentionally runtime-specific.

## Review Checklist

- No lock or borrow crosses `.await` accidentally.
- Spawned tasks own their inputs with `async move`.
- Important `JoinHandle`s are awaited, monitored, or aborted on shutdown.
- Blocking work is isolated and bounded.
- Error paths preserve context instead of becoming `JoinError` or timeout noise.
