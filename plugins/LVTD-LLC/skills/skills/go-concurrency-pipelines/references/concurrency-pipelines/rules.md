# Concurrency Pipeline Rules

## Construction

- Keep stages synchronous first; add goroutines at measured concurrency boundaries.
- Declare result order, partial-result behavior, and fail-fast versus aggregate errors.
- Declare panic policy: recover at an intentional boundary, convert to a
  classified failure, or let the process fail; never silently lose a worker.
- Use directional channel types at stage boundaries.
- Defer release of semaphore tokens and other owned resources.
- Stop tickers explicitly and release derived contexts.
- Register `WaitGroup` work before launch; prefer current helper APIs only when
  the module's minimum Go version supports them.
- Keep `sync.Cond` waits in a predicate loop while holding the associated lock.
- Do not copy mutexes, wait groups, conditions, pools, or structs containing them.

## Cancellation and Completion

- Select on cancellation around blocking sends and receives.
- Stop admitting new work after cancellation.
- Wait for admitted work according to the documented drain policy.
- Ensure early consumer exit cannot strand upstream stages.
- Join every goroutine the operation creates before returning when ownership requires it.
- Keep one serializer for non-concurrent sinks such as `http.ResponseWriter`.
- Detach with `context.WithoutCancel` only after assigning a new deadline,
  bounded admission, owner, error sink, and shutdown join.

## Buffers and Fan-Out

- Size buffers from a documented burst or memory budget.
- Keep worker counts configurable and bounded.
- Preserve order deliberately; completion order is not input order.
- Prevent retries from exceeding the operation's total concurrency budget.
- Do not append concurrently to shared slices or write shared maps without
  explicit synchronization.
- Treat a copied slice header as shared storage, not a snapshot.
- Use fixed-index parallel writes only with non-overlapping indices, a stable
  slice header, and an explicit join before reads.
- Use `errgroup.SetLimit` or another explicit admission bound when fan-out is material.

## Select and Channel State

- Do not depend on which simultaneously ready select case wins.
- Inspect `v, ok := <-ch` when closure and a zero value have different meaning.
- Use nil channels only as deliberate case-disable state and test each transition.
- Document drain versus abandon behavior after error or cancellation.

## Verification

- Test zero work, one item, full capacity, blocked downstream, early stop, and cancellation.
- Test worker errors and panics according to the public contract.
- Measure maximum active work with synchronization, not sleeps.
- Run `go test -race` on exercised concurrent paths.
- Treat a clean race run as evidence, not proof of leak or race freedom.
- Run `go vet` copylock checks and test simultaneous-ready select cases.
- Gate legacy loop-capture remediation on the module or file language version.
