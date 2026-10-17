# Apply Schema Migrations Workflow

1. Inspect current schema version and deployment concurrency.
2. Define forward change, compatibility window, and recovery plan.
   - Prefer additive expand-first changes during old/new binary overlap.
   - Reject unknown newer schemas rather than guessing.
3. Verify database-specific DDL transaction and locking behavior.
4. Package ordered migrations and checksums with the artifact.
5. Acquire the chosen migration lock or coordinator.
6. Apply each unapplied migration and record it atomically where supported.
7. Release coordination and verify the resulting schema.
8. Test clean install, upgrade, repeated invocation, and interrupted application.
   - Use explicit failpoints or process termination at migration boundaries.
   - Verify checksum mismatch and no version advancement after failure.

Do not assume that `embed.FS` supplies any of these lifecycle guarantees.
