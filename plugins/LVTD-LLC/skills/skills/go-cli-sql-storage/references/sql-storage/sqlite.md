# SQLite for Multi-Process CLIs

## Data and Location

Resolve cache paths with `os.UserCacheDir` or application configuration. Keep
the database on a local filesystem when using WAL. Separate reconstructible
cache data from authoritative offline state.

## Connections and Pragmas

Each CLI process owns one pool. Configure required pragmas consistently on
every physical connection according to the selected driver's mechanism:

- foreign-key enforcement;
- bounded busy handling;
- journal mode, commonly WAL for multi-process readers;
- an explicit synchronous/durability policy.

SQLite still serializes writers. An in-process mutex cannot coordinate separate
CLI processes. Start with one open connection per process unless measured
parallel-read requirements justify more.

## Migration Coordination

Acquire a driver-supported write or migration lock, then reread the migration
ledger. Apply and record each migration atomically where supported. A second
process waits within its bounded busy policy, then rereads the ledger after the
first process commits.

Do not mix raw transaction-control statements with `database/sql` transaction
objects without verified driver semantics. Reject unknown newer schemas.

## Backup and Recovery

Do not raw-copy an active WAL database. Use a supported online backup mechanism
or `VACUUM INTO` when appropriate. On corruption, preserve and quarantine the
original. Rebuild automatically only when all data is reconstructible;
otherwise stop with explicit recovery instructions.

## Verification

Build the CLI and launch separate processes against one temporary database.
Test concurrent readers, writers, and migrators; bounded busy failures;
interruption; restart; schema compatibility; and final integrity. Native tests
on every supported OS are required because cross-compilation proves no runtime
locking or driver behavior.

## Official References

- WAL: https://sqlite.org/wal.html
- Transactions: https://sqlite.org/lang_transaction.html
- Backup API: https://sqlite.org/backup.html
