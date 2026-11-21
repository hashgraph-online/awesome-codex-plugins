# SQLx Official Docs Summary

last_verified_at: 2026-11-05

## Contents

- Stable package snapshot
- Confirmed points from official docs
- Query and offline mode
- Migrations and transactions
- How this affects the skill
- Sources

## Stable package snapshot

Verified from crates.io, docs.rs, and the SQLx changelog on 2026-11-05.

| Package | Stable | Notes |
|---|---:|---|
| `sqlx` | 0.9.0 | MSRV 1.94; runtime and TLS features are separate; optional `sqlx-toml` feature |
| `sqlx-cli` | 0.9.x | `prepare`, `migrate`, `database` subcommands; CLI TLS features are named `rustls`/`native-tls` |

The upstream repository moved from `launchbadge/sqlx` to `transact-rs/sqlx`; old links redirect.

## Confirmed points from official docs

1. Runtime features are `runtime-tokio` and `runtime-async-std`; TLS features are `tls-rustls` (with `tls-rustls-ring` or `tls-rustls-aws-lc-rs`) and `tls-native-tls`. Combined runtime+TLS feature names from older versions no longer exist.
Source: [sqlx docs](https://docs.rs/sqlx/latest/sqlx/), [sqlx CHANGELOG](https://github.com/transact-rs/sqlx/blob/main/CHANGELOG.md)

2. `Pool` is `Send + Sync + Clone`; cloning is a cheap reference-counted handle. `PoolOptions` configures `max_connections` and `acquire_timeout`. The 0.9.0 source defaults are 10 connections and a 30-second acquire timeout, but the rendered docs do not state defaults.
Source: [Pool](https://docs.rs/sqlx/latest/sqlx/struct.Pool.html), [PoolOptions](https://docs.rs/sqlx/latest/sqlx/self/struct.PoolOptions.html), [v0.9.0 options source](https://github.com/transact-rs/sqlx/blob/v0.9.0/sqlx-core/src/pool/options.rs)

3. `query!` checks SQL at compile time against `DATABASE_URL` or committed `.sqlx` data and returns an anonymous struct. `query_as!` maps to an explicitly declared struct and does not require `FromRow`.
Source: [query!](https://docs.rs/sqlx/latest/sqlx/macro.query.html), [query_as!](https://docs.rs/sqlx/latest/sqlx/macro.query_as.html)

4. In 0.9, `query*` functions take `impl SqlSafeStr`, implemented for `&'static str` and `AssertSqlSafe`. Dynamically built SQL must be wrapped deliberately.
Source: [sqlx CHANGELOG](https://github.com/transact-rs/sqlx/blob/main/CHANGELOG.md)

5. `sqlx.toml` can rename `DATABASE_URL`, set type overrides, and rename the migrations table. The library does not enable the `sqlx-toml` feature by default; the CLI does.
Source: [sqlx CHANGELOG](https://github.com/transact-rs/sqlx/blob/main/CHANGELOG.md)

6. A transaction starts with `Pool::begin` or `Connection::begin`, ends with `commit` or `rollback`, and rolls back on drop. `&mut *tx` is the executor form used inside the transaction.
Source: [Transaction](https://docs.rs/sqlx/latest/sqlx/struct.Transaction.html)

## Query and offline mode

1. `cargo install sqlx-cli`
2. With `DATABASE_URL` set and the database migrated: `cargo sqlx prepare` or `cargo sqlx prepare --workspace`
3. Commit `.sqlx/`
4. Build without `DATABASE_URL`; use `SQLX_OFFLINE=true` if a value may still be present
5. Gate CI with `cargo sqlx prepare --check`

Source: [query! offline mode](https://docs.rs/sqlx/latest/sqlx/macro.query.html), [sqlx-cli](https://github.com/transact-rs/sqlx/tree/main/sqlx-cli)

## Migrations and transactions

- `sqlx migrate add <name>` creates `migrations/<timestamp>_<name>.sql`.
- `sqlx migrate add -r <name>` creates paired `.up.sql` and `.down.sql` files.
- `sqlx migrate run` applies pending migrations; `sqlx migrate revert` reverts the last one.
- `sqlx migrate info` reports applied and pending state.
- A dropped transaction rolls back, but explicit `commit`/`rollback` keeps intent visible.

Source: [sqlx-cli](https://github.com/transact-rs/sqlx/tree/main/sqlx-cli), [Transaction](https://docs.rs/sqlx/latest/sqlx/struct.Transaction.html)

## How this affects the skill

- The skill requires one pool built at startup, one query mode per crate, and a committed migration history.
- The 0.9 feature rename means a copy-pasted old `runtime-tokio-native-tls` line is a finding, not a preference.
- `AssertSqlSafe` is treated as a review flag because it exists to make dynamic SQL visible.

## Sources
> Checked 2026-11-05.
| Claim | Source | Checked |
|---|---|---|
| 0.9.0 changes, MSRV, feature split, `AssertSqlSafe`, `sqlx.toml` | <https://github.com/transact-rs/sqlx/blob/main/CHANGELOG.md> | 2026-11-05 |
| Pool and `PoolOptions` behavior | <https://docs.rs/sqlx/latest/sqlx/struct.Pool.html> | 2026-11-05 |
| Compile-time query macros and offline mode | <https://docs.rs/sqlx/latest/sqlx/macro.query.html> | 2026-11-05 |
| Migration commands and naming | <https://github.com/transact-rs/sqlx/tree/main/sqlx-cli> | 2026-11-05 |
| Transaction lifecycle | <https://docs.rs/sqlx/latest/sqlx/struct.Transaction.html> | 2026-11-05 |
