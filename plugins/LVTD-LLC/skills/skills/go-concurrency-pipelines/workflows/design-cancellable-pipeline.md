# Design Cancellable Pipeline Workflow

1. Define the sequential operation and caller-visible contract.
2. Classify the workload as CPU, I/O, blocking dependency, or mixed and measure
   a sequential baseline.
3. Mark only the stages that benefit from overlap.
4. Assign goroutine, shared-state, lock, channel, timer, and closure ownership.
5. Set worker, queue, retry, result, and memory bounds.
6. Add cancellation to every blocking edge.
7. Define error, partial-result, ordering, and drain behavior.
8. Implement completion and joining before tuning buffers.
9. Verify success, failure, cancellation, blocked consumers, and early exit.

## Exit Criteria

- [ ] Every goroutine has an owner and completion path.
- [ ] Every queue and concurrency dimension is bounded.
- [ ] Early stop cannot strand a sender.
- [ ] The public contract states ordering and partial-result behavior.
- [ ] The chosen concurrency improves a representative workload over sequential execution.
