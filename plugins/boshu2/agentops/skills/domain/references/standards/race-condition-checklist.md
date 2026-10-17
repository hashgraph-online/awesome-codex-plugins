# Race Condition Checklist

Domain-specific checklist for concurrent, parallel, or multi-process code.

## Mandatory Checks

### Shared State
- [ ] All shared mutable state protected by mutex/lock/atomic
- [ ] No global mutable variables accessed from multiple goroutines/threads
- [ ] Map/dict access synchronized (Go maps are NOT goroutine-safe)
- [ ] Slice/list append operations synchronized when shared
- [ ] Read-write locks used where reads dominate (not exclusive mutex everywhere)

### File System Races
- [ ] Check-then-act on files uses atomic operations (temp file + rename)
- [ ] File locks used for multi-process coordination
- [ ] PID files checked with `flock` or equivalent, not just `[ -f ]`
- [ ] Directory creation uses `mkdir -p` (idempotent), not check-then-create
- [ ] Log file rotation handles concurrent writers

### Database Races
- [ ] Upsert uses `INSERT ... ON CONFLICT` (not check-then-insert)
- [ ] Counter increments use `UPDATE ... SET x = x + 1` (not read-modify-write)
- [ ] Unique constraint violations handled with retry (not just error)
- [ ] Optimistic locking uses version column for concurrent updates
- [ ] Queue consumers use `SELECT ... FOR UPDATE SKIP LOCKED`

### API / Network Races
- [ ] Idempotency keys used for non-idempotent API calls
- [ ] Retry logic uses exponential backoff (not fixed delay)
- [ ] Circuit breaker pattern for failing external services
- [ ] Request deduplication for concurrent identical requests
- [ ] Webhook handlers are idempotent (same event delivered twice = same result)

### Go-Specific
- [ ] Channel sends/receives have timeout or context cancellation
- [ ] `sync.WaitGroup` counter matches goroutine count exactly
- [ ] `defer mu.Unlock()` immediately after `mu.Lock()` (no early return gap)
- [ ] Race detector run: `go test -race ./...`
- [ ] Context propagation through goroutine chains (no orphaned goroutines)

### Python-Specific
- [ ] `threading.Lock` used for shared state (GIL doesn't protect everything)
- [ ] `asyncio` tasks properly awaited (no fire-and-forget without tracking)
- [ ] `multiprocessing` shared state uses `Manager` or `Value`/`Array`
- [ ] File I/O in async code uses `aiofiles` (not blocking `open()`)

### Testing
- [ ] Concurrent tests exist (multiple goroutines/threads hitting same code)
- [ ] Race detector enabled in CI (`go test -race`, `PYTHONFAULTHANDLER=1`)
- [ ] Stress tests for hot paths (100+ concurrent operations)
- [ ] Deterministic ordering tests (verify no output depends on scheduling)

## When to Apply

Load this checklist when:
- Code uses goroutines, threads, `asyncio`, `multiprocessing`, or `concurrent.futures`
- Multiple processes read/write the same files
- Database operations involve concurrent access patterns
- Plan mentions "parallel", "concurrent", "async", "worker pool", or "queue"
- Code uses `sync.Mutex`, `threading.Lock`, `asyncio.Lock`, or similar primitives
