# Migration Safety

Review migrations as production changes, not just local setup.

## Safe Sequencing

Prefer expand/backfill/contract:

1. Expand: add a table, nullable column, index, or non-enforced path.
2. Deploy code that writes both old and new shapes if needed.
3. Backfill existing data in bounded batches.
4. Add constraints after data is valid.
5. Remove old columns or tables only after callers no longer depend on them.

## Checks Before Merging

- Does the migration run on an empty database?
- Does it run on a database with realistic existing data?
- Are large table rewrites avoided or explicitly planned?
- Are new indexes needed before new query paths ship?
- Are uniqueness constraints backed by product behavior and tests?
- Does rollback policy match the team's migration style?

## Constraint Errors

Map expected constraint failures to domain errors:

- Unique email or username: conflict or validation error.
- Foreign key missing: bad request or internal bug depending on caller.
- Check constraint violation: validation error if caused by user input.

Do not expose raw database error strings to users.
