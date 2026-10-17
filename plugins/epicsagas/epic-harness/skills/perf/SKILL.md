---
name: perf
dimension: evaluation_and_reward
description: "Performance optimizer for loops, DB queries, rendering, and batch operations. Catches N+1 queries, missing indexes, and unnecessary re-renders."
---

# Perf — Performance Review

## Process

1. Identify performance-sensitive code paths from the diff (loops, queries, rendering, batch ops)
2. Run the Checklist below, marking each item as pass, fail, or N/A with reason
3. For each failure, cite the file and line number with a one-line fix hint
4. Report findings using the Evidence Required section

## When to Trigger
- Database queries inside loops
- Large data set processing
- Rendering or UI update logic
- API endpoint that could receive high traffic
- File I/O in hot paths

## Checklist

### Database
- [ ] No N+1 queries (use JOIN, eager loading, or batch) — N+1 queries cause latency to scale linearly with row count, turning a 1ms query into seconds under load.
- [ ] Indexes exist for frequently queried columns — without indexes, the database performs full table scans, collapsing read throughput.
- [ ] Pagination for large result sets — fetching all rows at once exhausts memory and increases response time for every consumer.
- [ ] Connection pooling configured — opening a new connection per request adds network round-trip overhead and can exhaust database connection limits.

### Memory
- [ ] No unbounded arrays or caches growing indefinitely — unbounded growth causes gradual memory exhaustion and eventual OOM kills with no warning.
- [ ] Event listeners properly removed / unsubscribed — leaked listeners hold references to their context, preventing garbage collection of entire object graphs.
- [ ] Large objects released after use — holding references to large payloads keeps them in the heap, increasing GC pressure and pause times.
- [ ] Streams used for large file processing (not loading entire file) — loading a multi-GB file into RAM blocks other allocations and risks crashing the process.

### Computation
- [ ] Expensive calculations memoized where appropriate — recomputing pure results on every call wastes CPU cycles that compound in hot paths.
- [ ] No redundant re-renders (React: useMemo, useCallback) — unnecessary re-renders cascade through the component tree, causing layout thrash and dropped frames.
- [ ] Async operations don't block the main thread — blocking the main thread stalls all concurrent requests, degrading throughput for every user.
- [ ] Debounce/throttle on frequent events (scroll, input) — unthrottled handlers fire hundreds of times per second, overwhelming the event loop.

### Network
- [ ] Responses compressed (gzip/brotli) — uncompressed JSON/HTML can be 5-10x larger, wasting bandwidth and increasing time-to-first-byte.
- [ ] Static assets cached with proper headers — missing cache headers force the browser to re-download unchanged assets on every page load.
- [ ] No unnecessary API calls (cache, dedupe) — duplicate requests waste server resources and increase latency for legitimate traffic.

See `references/performance.md` for the full checklist.

## Anti-Rationalization

| Excuse | Rebuttal | What to do instead |
|--------|----------|--------------------|
| "Premature optimization is the root of all evil" | Knuth said "about 97% of the time" — the other 3% matters. N+1 queries are never premature. | Check for N+1 queries and missing indexes before merging. |
| "It works fine on my machine" | Your machine is not production. Profile under realistic conditions. | Run the perf checklist against realistic data volumes. |
| "We can optimize later" | Performance debt is invisible until it's catastrophic. Measure now. | Add a benchmark or load test for the critical path today. |

## Evidence Required

Before claiming performance review is complete, show ALL applicable:

- [ ] No N+1 queries: show the query plan or eager-loading code
- [ ] Pagination present: show limit/offset or cursor implementation
- [ ] No unbounded collections: show size caps or streaming for large data
- [ ] Async I/O in request paths: show `await` or stream usage (no sync fs/net)

**"Looks fine" is not a review. Show the query or the code path.**

## Red Flags
- Loading all records when only count is needed
- Synchronous file I/O in request handlers
- Missing pagination on list endpoints
