# Concurrency Pipeline Knowledge

## API Before Topology

Concurrency is an implementation choice unless the caller must coordinate a
stream. Prefer `[]T`, `(T, error)`, or `iter.Seq`/`iter.Seq2` when they preserve
the contract. Exposed channels commit callers to receiving, closure, ordering,
and cancellation semantics.

## Ownership

The goroutine that completes all sends owns closing its outbound channel.
Receivers do not close channels they do not own. A coordinator may close a
fan-in channel only after every forwarding goroutine has stopped.

For a worker pool, a coordinator owns admission and final output closure.
Workers do not close shared result channels. A separate wait path closes the
result channel only after every admitted worker exits.

## Backpressure and Bounds

An unbuffered channel couples producer progress to a consumer. A bounded buffer
absorbs a known burst; it does not remove backpressure. Bound active workers,
queued work, retries, result buffering, and retained payload size as one budget.

## Cancellation

Propagate `context.Context` as the first parameter. Every potentially blocking
stage must observe cancellation. Preserve diagnostic causes when useful, but
keep `context.Canceled` and `context.DeadlineExceeded` inspectable.

Cancellation is cooperative. A work function that ignores context can prevent
prompt shutdown; give such work an isolating process, transport timeout, or
other enforceable boundary when deadlines are mandatory.

`context.WithoutCancel` detaches cancellation and deadlines; it does not create
a safe background lifetime. Detached work needs independent admission and time
bounds, an owner, an observable error sink, and a shutdown join policy.

## Shared State and Synchronization

Choose channels when ownership transfer or event sequencing is the central
contract. Choose mutexes when protecting shared state directly is clearer.
Neither primitive makes an unbounded lifetime or workload safe.

Slice assignment copies a descriptor, not elements. Concurrent append may race
with readers or other appenders regardless of current capacity. Concurrent map
writes require synchronization. Fixed-index writes can be safe only when
indices do not overlap, the slice header is not mutated, and a join establishes
visibility before reading results.

Register `WaitGroup` work before it can finish, keep `Cond` waits inside a
predicate loop, and never copy a synchronization value after first use.
`errgroup` coordinates error and cancellation but still needs a deliberate
concurrency limit and context-cooperative tasks.

## Channel States

When multiple `select` cases are ready, selection is nondeterministic. A receive
from a closed channel returns immediately; inspect the `ok` result when closure
differs from a zero value. A nil channel disables its select case and can be
used deliberately in a state machine.

## Iterators

`iter.Seq` supports push-style streaming and early stop through `yield(false)`.
When converting with `iter.Pull`, call `stop` if consumption ends early. Do not
call pull functions concurrently.

## Testing

Use barrier channels to establish ordering points. Assert invariants such as
maximum concurrency, completion, cancellation, and result sets without
depending on incidental scheduling order.
