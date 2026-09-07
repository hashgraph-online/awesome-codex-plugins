# Test HTTP Server Workflow

1. Test handlers with `httptest.NewRequest` and `ResponseRecorder`.
2. Assert final results through `Result()`.
3. Cover zero, exact-limit, and one-byte-over bodies plus trailing JSON.
4. Verify middleware request and response order.
5. Verify implicit 200, first status commitment, byte counts, and writer capabilities.
   - Verify every terminal error response returns immediately and no downstream
     mutation or success body runs.
6. Test mux patterns, route variables, method mismatches, and not-found behavior.
7. Use `httptest.Server` for redirects, streaming, cancellation, or transport behavior.
   - Exercise client disconnect, slow consumption, post-commit failure, and
     partial-result framing.
8. Exercise shutdown, readiness transitions, shared state, and race checks.
   - Verify both graceful drain and deadline-forced cancellation policy.
9. If `http.TimeoutHandler` is used, verify buffered behavior and reject it for
   streaming endpoints.

## Exit Criteria

- [ ] Tests cover both handler logic and actual HTTP semantics where necessary.
- [ ] No test relies on fixed ports or arbitrary sleeps.
- [ ] Lifecycle tests wait for terminal states.
