# Threading And Shared State Patterns

Use this reference when choosing primitives or reviewing lock-heavy code.

## Scoped Threads

`std::thread::scope` lets child threads borrow local data and guarantees they
are joined before the scope exits.

```rust
let mut output = vec![0; input.len()];

std::thread::scope(|scope| {
    for (src, dst) in input.chunks(1024).zip(output.chunks_mut(1024)) {
        scope.spawn(move || dst.copy_from_slice(src));
    }
});
```

## Lock Hygiene

- Acquire locks as late as possible and release them as early as possible.
- Use a block to make release points obvious.
- Never hold a lock while waiting on a channel send/receive that might need the
  same lock to make progress.
- If two locks are needed, document and enforce acquisition order.

## Mutex Poisoning

`Mutex::lock` returns a `Result` because a panic while holding the lock may have
left protected data inconsistent.

- Use `.expect("...")` when poisoned state should abort the operation.
- Use `into_inner` only after explicitly deciding the invariant is still valid
  or can be repaired.

## Atomics

Use atomics for small, independent state such as counters, cancellation flags,
or one-word publication. Default to `Ordering::SeqCst` unless there is a
measured reason and a documented proof for weaker ordering.

## Once Initialization

- Use `LazyLock<T>` for simple `static` initialization from a closure.
- Use `OnceLock<T>` when initialization needs runtime input, staged setup, or
  fallible initialization patterns.
