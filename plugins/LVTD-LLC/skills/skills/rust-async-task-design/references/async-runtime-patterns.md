# Async Runtime Patterns

Use this reference when writing Tokio or futures-based Rust.

## Spawned Task Shape

```rust
let handle = tokio::spawn(async move {
    worker.run().await
});

let result = handle.await.expect("task panicked")?;
```

Use `async move` so the task owns captured values. Preserve the handle when the
task result or panic matters.

## State Across Await

Bad:

```rust
let mut guard = state.lock().unwrap();
guard.count += 1;
do_io().await;
```

Good:

```rust
{
    let mut guard = state.lock().unwrap();
    guard.count += 1;
}
do_io().await;
```

The block ensures the guard is dropped before suspension.

## Shared State Options

| Need | Prefer |
|------|--------|
| Short synchronous mutation | `std::sync::Mutex` scoped before `.await` |
| Lock must cross `.await` | `tokio::sync::Mutex` |
| IO resource shared by many tasks | Owner task plus channels |
| Read-mostly config | `Arc<T>` or `ArcSwap` if already used |
| One-time async setup | `OnceLock<T>` for sync init; `tokio::sync::OnceCell<T>` for async init |

## Blocking Work

- Use async filesystem/network APIs when available and appropriate.
- Use `tokio::task::spawn_blocking` for blocking operations that finish.
- Use dedicated threads for long-lived or persistent blocking loops.
- Limit CPU-heavy `spawn_blocking` calls with a semaphore or use Rayon.
- Do not expect aborting a started `spawn_blocking` task to stop it.

## Cancellation Review

- What happens if the caller drops the future?
- What partial state exists after timeout?
- Are channel senders/receivers dropped to signal shutdown?
- Are cleanup tasks awaited during graceful shutdown?
