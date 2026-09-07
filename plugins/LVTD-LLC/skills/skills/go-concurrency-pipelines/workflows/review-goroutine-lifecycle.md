# Review Goroutine Lifecycle Workflow

For every goroutine, record:

- who starts it;
- what stops it;
- which resources it owns;
- which sends, receives, locks, or waits can block;
- who observes its error or panic;
- who waits for completion.

Also record:

- whether request cancellation was detached and what new deadline replaces it;
- which lock protects each shared collection or state transition;
- whether a synchronization value is copied after first use;
- whether formatting or callbacks can re-enter while a lock is held;
- whether cancellation is followed by an actual join.

Trace success, first error, deadline, caller cancellation, panic, and consumer
abandonment. Reject any path that can return while an owned goroutine remains
blocked without an explicit background-lifetime contract.
