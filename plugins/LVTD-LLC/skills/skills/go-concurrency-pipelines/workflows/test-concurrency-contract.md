# Test Concurrency Contract Workflow

1. Inject work functions, clocks, and coordination seams.
2. Use barriers to establish deterministic happens-before points.
3. Assert bounds, result contract, and completion independently.
4. Exercise cancellation before admission, during work, and during result delivery.
5. Exercise downstream early stop and worker failure.
6. Exercise simultaneously ready select cases plus nil and closed-channel transitions.
7. Exercise shared map/slice aliasing, copied-lock checks, and terminal state after cancellation.
8. Run repeated tests, vetting, and the race detector.
9. Investigate leaked or blocked goroutines rather than extending timeouts.

## Exit Criteria

- [ ] Tests do not depend on arbitrary sleeps.
- [ ] Tests assert contracts, not schedule order.
- [ ] Race checks cover the relevant workload.
- [ ] Every tested operation finishes before its deadline.
