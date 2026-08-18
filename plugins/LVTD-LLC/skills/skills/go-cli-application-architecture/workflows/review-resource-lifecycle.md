# Review Resource Lifecycle Workflow

Review ownership and cleanup across startup, operation, cancellation, and
shutdown without moving adapter-specific mechanics into the architecture layer.

## Workflow Steps

### 1. Inventory Resources

- [ ] List files, response bodies, rows, transactions, pools, processes,
      timers, listeners, goroutines, buffers, and diagnostic artifacts.
- [ ] Record acquisition and first-use sites.

### 2. Assign Ownership

- [ ] Mark each value as owned, borrowed, shared, or transferred.
- [ ] Identify the exact ownership-transfer point.
- [ ] Reject cores that close caller-provided streams or handles.

### 3. Trace Every Exit

- [ ] Trace success, primary failure, cancellation, panic, and partial startup.
- [ ] Close in reverse dependency order.
- [ ] Join owned background work before returning unless a bounded detached
      lifetime is an explicit contract.

### 4. Compose Failures

- [ ] Decide whether close, flush, sync, wait, or shutdown failures are material.
- [ ] Preserve the primary failure while retaining material cleanup evidence.
- [ ] Keep user presentation and exit mapping in `go-cli-errors-observability`.

### 5. Delegate Adapter Proof

- [ ] Route SQL details to `go-cli-sql-storage`.
- [ ] Route HTTP bodies and servers to the HTTP skills.
- [ ] Route subprocess trees to `go-cli-process-control`.
- [ ] Route goroutine and synchronization mechanics to `go-concurrency-pipelines`.

## Exit Criteria

- [ ] Every resource has one documented owner.
- [ ] Every exit path has bounded cleanup and joining.
- [ ] Borrowed resources remain open for their owners.
- [ ] Material cleanup failures remain observable.
