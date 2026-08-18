# SQLx Patterns

Use SQLx's compile-time checked macros when the SQL shape is known at compile
time. They catch column names, nullability, and type mismatches before runtime.

## Pool Injection

Create the pool at startup and pass it through application state:

```rust
pub struct AppState {
    pub db_pool: sqlx::PgPool,
}

pub async fn create_pool(database_url: &str) -> Result<sqlx::PgPool, sqlx::Error> {
    sqlx::postgres::PgPoolOptions::new()
        .max_connections(10)
        .connect(database_url)
        .await
}
```

Repository functions should accept `&PgPool`, `&mut PgConnection`, or
`&mut Transaction<'_, Postgres>` depending on the needed boundary.

## Query Macros

```rust
let user = sqlx::query!(
    r#"
    select id, email, password_hash
    from users
    where email = $1
    "#,
    email.as_str(),
)
.fetch_optional(pool)
.await?;
```

Use `query_as!` when mapping into a concrete struct:

```rust
#[derive(Debug)]
pub struct SubscriberRow {
    pub id: uuid::Uuid,
    pub email: String,
}

let rows = sqlx::query_as!(
    SubscriberRow,
    "select id, email from subscriptions where status = $1",
    "confirmed",
)
.fetch_all(pool)
.await?;
```

## Transactions

Use transactions for workflows that update multiple rows or combine persistence
with idempotency state:

```rust
let mut tx = pool.begin().await?;

insert_issue(&mut tx, issue).await?;
mark_idempotency_key_used(&mut tx, key).await?;

tx.commit().await?;
```

Pass `&mut tx` down rather than starting nested transactions in helpers.

## Offline Mode

SQLx macros need either `DATABASE_URL` at build time or a checked-in `.sqlx/`
metadata directory. For Docker or CI builds without a database:

```bash
cargo sqlx prepare --workspace -- --all-targets --all-features
SQLX_OFFLINE=true cargo build --release
```

Keep `.sqlx/` in sync when migrations or query shapes change.

## Feature Flags

Common dependencies:

```toml
sqlx = { version = "0.8", default-features = false, features = [
  "runtime-tokio-rustls",
  "postgres",
  "uuid",
  "chrono",
  "migrate",
] }
```

Match features to actual column types. Missing `uuid`, `chrono`, `time`, or
`json` features often show up as macro compilation errors.
