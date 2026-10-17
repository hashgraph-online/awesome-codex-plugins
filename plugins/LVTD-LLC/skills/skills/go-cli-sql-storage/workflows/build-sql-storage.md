# Build SQL Storage Workflow

1. Classify data as reconstructible cache or authoritative local state, then
   define operations, invariants, concurrency, durability, backup, and atomicity.
2. Select database and driver from platform, CGO, locking, and deployment needs.
3. Keep consumer interfaces narrow; implement a concrete adapter.
4. Open, tune, inject, and close one pool at the composition root.
5. Add bounded startup verification if the command requires connectivity.
6. Add versioned, serialized migrations and define supported old/new binary overlap.
7. Parameterize queries and map driver errors.
8. Test the adapter with the real driver and production migration path.
9. Build and smoke-test the distributable artifact.
   - For SQLite, run parallel CLI processes against one isolated database.

## Exit Criteria

- [ ] Pool and transaction ownership are explicit.
- [ ] Schema upgrades are versioned and coordinated.
- [ ] Driver details do not leak into domain contracts.
- [ ] Real-driver tests exercise the shipped schema.
