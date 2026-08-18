# Test SQL Adapter Workflow

1. Start an isolated real database or unique local database file.
2. Apply the same migration path used by the built CLI.
3. Run happy paths plus constraint, no-row, conversion, and cancellation cases.
4. Verify nullable scans, statement and `Rows` cleanup, scan failures, and
   iteration errors.
5. Test transaction commit, rollback, and mixed-handle mistakes.
6. Exercise concurrent operations and pool limits with deadlines.
   - For SQLite, add separate-process readers, writers, and migrators against
     one temporary file; in-process goroutines are insufficient.
7. Round-trip custom `Scanner` and `Valuer` types through the driver.
8. Run tests in parallel only with isolated state.
9. Test interrupted migration/write recovery, newer-schema rejection, and
   final database integrity.
10. Test failed startup after pool creation and confirm the pool is closed.

## Exit Criteria

- [ ] The test validates SQL and driver behavior, not only a fake.
- [ ] Cleanup is reliable after failures.
- [ ] Tests cannot touch developer or production data.
