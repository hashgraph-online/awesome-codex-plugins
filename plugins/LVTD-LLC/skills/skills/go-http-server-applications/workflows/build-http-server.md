# Build HTTP Server Workflow

1. Define endpoints, methods, schemas, limits, and domain error mappings.
2. Build application services independently from HTTP.
3. Construct handlers and a dedicated mux with explicit dependencies.
4. Order recovery, correlation, logging, metrics, auth, and endpoint middleware.
5. Bound and validate request bodies; encode responses before commitment.
   - For batch or streaming endpoints, also bound item count, per-item size,
     result buffering, and slow-client write time.
   - Define stream framing, ordering, partial results, and post-commit errors.
6. Configure the explicit `http.Server` and listener.
7. Add signal cancellation and deadline-bounded shutdown.
   - Choose graceful drain and forced-cancellation behavior for active requests.
8. Add liveness and readiness with distinct semantics.
9. Test handlers, routes, middleware, lifecycle, and concurrent state.

## Exit Criteria

- [ ] Inputs and server resources are bounded.
- [ ] Domain code is independent of HTTP.
- [ ] Startup and shutdown errors are observed.
- [ ] Health semantics match deployment behavior.
