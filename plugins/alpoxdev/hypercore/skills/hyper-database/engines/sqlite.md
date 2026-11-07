# SQLite

Engine guide for SQLite embedded in an application or device, plus libSQL and Cloudflare D1 as SQLite dialects. Read it after `rules/engine-detection.md` routes here; for Turso or D1 platform limits, also read the platform section of `engines/distributed-sql.md`. Findings cite the `SQ-*` IDs.

## 1. Dated Facts

> Volatile. Checked 2026-11-07 against <https://www.sqlite.org/changes.html>; recheck when the bundled SQLite version matters.

| Fact | Value |
|---|---|
| Current release | 3.54.1 (2026-10-16) |
| Corruption fix floor | 3.53.0 (2026-04-09) and the 3.51.3 backport fix the WAL-reset database corruption bug; WAL databases run on one of these or newer |
| Feature floors | `STRICT` tables 3.37.0; `WITHOUT ROWID` 3.8.2; WAL 3.7.0; foreign key enforcement 3.6.19; `ALTER TABLE` adding and removing `NOT NULL` and `CHECK` constraints 3.53.0 |

The SQLite version is the library the application links (the driver's bundled copy, the OS copy, or the platform's), not the CLI on the developer machine. Check it with `SELECT sqlite_version();` from the application's own driver.

## 2. Fit

SQLite fits one application process (or a few on one host) writing, many readers, local-first and embedded data, tests, and edge reads. It does not fit many concurrent writers, network filesystems, or multi-host access to one file (DM-60).

## 3. Types and Tables

| ID | Severity | Rule |
|---|---|---|
| SQ-TYP-01 | high | Declare new tables `STRICT` (when the floor allows): without it, types are advisory and `'abc'` inserts into an `INTEGER` column. In `STRICT`, only `INT`, `INTEGER`, `REAL`, `TEXT`, `BLOB`, and `ANY` are legal. |
| SQ-TYP-02 | high | Give every primary key column an explicit `NOT NULL` in ordinary rowid tables; SQLite keeps a historical bug that lets `PRIMARY KEY` columns hold `NULL` there. `STRICT` and `WITHOUT ROWID` tables enforce it. |
| SQ-TYP-03 | medium | Use exactly `INTEGER PRIMARY KEY` for an integer key so it aliases the rowid; `INT PRIMARY KEY` does not. Skip `AUTOINCREMENT` unless deleted IDs must never be reused; it adds a table and write overhead. |
| SQ-TYP-04 | medium | Use `WITHOUT ROWID` for small-row lookup tables keyed by a non-integer; it breaks `last_insert_rowid()`, incremental BLOB I/O, and update hooks. |
| SQ-TYP-05 | medium | Pick one time encoding per column (ISO-8601 `TEXT` in UTC, Unix-epoch `INTEGER`, or Julian `REAL`); SQLite has no datetime type. Store booleans as `INTEGER NOT NULL CHECK (x IN (0,1))`. |
| SQ-TYP-06 | low | Use single quotes for strings; a double-quoted string that matches no column becomes a literal and hides typos. `upper()`/`lower()` fold ASCII only unless built with ICU. |

## 4. Connections and Durability

| ID | Severity | Rule |
|---|---|---|
| SQ-CFG-01 | high | Run `PRAGMA foreign_keys = ON` on every connection; enforcement is off by default and the setting is per connection. |
| SQ-CFG-02 | high | Use `PRAGMA journal_mode = WAL` for any database with concurrent readers; it persists in the file. Never place a WAL database on a network filesystem: all processes need the shared-memory index on one host. |
| SQ-CFG-03 | high | Set `PRAGMA busy_timeout` (for example 5000 ms) on every connection and treat `SQLITE_BUSY` as an expected, retryable result; there is one writer at a time even in WAL mode. |
| SQ-CFG-04 | medium | Open write transactions with `BEGIN IMMEDIATE` so a reader-turned-writer does not fail with `SQLITE_BUSY` midway, and keep write transactions short. |
| SQ-CFG-05 | medium | In WAL mode, `synchronous = NORMAL` is durable against application crashes but may lose the last commits on power loss; use `FULL` where that loss is unacceptable. |
| SQ-CFG-06 | medium | Keep the WAL bounded: a long read transaction blocks checkpoints and the WAL grows; cap read duration and run `PRAGMA wal_checkpoint(TRUNCATE)` in idle windows. |
| SQ-CFG-07 | low | Run `PRAGMA optimize` periodically (for example at connection close) so the planner has statistics. |

## 5. Schema Changes

| ID | Severity | Rule |
|---|---|---|
| SQ-DDL-01 | high | `ALTER TABLE` supports rename, add column, and drop column (with limits), plus constraint changes on 3.53.0+; anything else uses the documented rebuild: create the new table, copy, drop the old, rename, recreate indexes, triggers, and views, inside one transaction with foreign keys off and `PRAGMA foreign_key_check` afterwards. |
| SQ-DDL-02 | medium | Track schema versions with `PRAGMA user_version` or a migrations table; some hosted SQLite services make `user_version` read-only, so a table is the portable choice. |

## 6. Backup and Integrity

| ID | Severity | Rule |
|---|---|---|
| SQ-OPS-01 | high | Never copy a live database file with `cp`; use `VACUUM INTO`, the online backup API (`.backup` in the CLI), or a replication tool built for SQLite. Copy `-wal` and `-shm` files only as part of such a tool. |
| SQ-OPS-02 | medium | Run `PRAGMA integrity_check` (or `quick_check`) after restores and suspected corruption. |

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Release dates, the WAL-reset corruption fix, and the 3.53.0 `ALTER TABLE` constraint support | <https://www.sqlite.org/changes.html> |
| Flexible typing, `PRIMARY KEY` accepting `NULL`, foreign keys off by default, double-quoted strings, ASCII-only case folding | <https://www.sqlite.org/quirks.html> |
| `STRICT` tables | <https://www.sqlite.org/stricttables.html> |
| `WITHOUT ROWID` tables | <https://www.sqlite.org/withoutrowid.html> |
| WAL behavior, one writer, network filesystems, checkpoints, `synchronous` | <https://www.sqlite.org/wal.html> |
| The table-rebuild procedure for unsupported `ALTER TABLE` changes | <https://www.sqlite.org/lang_altertable.html> |
| `VACUUM INTO` and the backup API | <https://www.sqlite.org/lang_vacuum.html>, <https://www.sqlite.org/backup.html> |
| The rule IDs and severities | this package's chosen design, not a validated optimum |
