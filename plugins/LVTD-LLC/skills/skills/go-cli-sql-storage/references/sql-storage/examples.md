# SQL Storage Examples

## Bounded Initialization

```go
db, err := sql.Open(driverName, dsn)
if err != nil {
    return fmt.Errorf("open database configuration: %w", err)
}

ctx, cancel := context.WithTimeout(ctx, 3*time.Second)
defer cancel()
if err := db.PingContext(ctx); err != nil {
    db.Close()
    return fmt.Errorf("connect to database: %w", err)
}
```

Choose the timeout and whether connectivity is required from the command's
offline and startup contract.

## Transaction Helper

```go
func withinTx(ctx context.Context, db *sql.DB, fn func(*sql.Tx) error) error {
    tx, err := db.BeginTx(ctx, nil)
    if err != nil {
        return err
    }
    defer tx.Rollback()

    if err := fn(tx); err != nil {
        return err
    }
    return tx.Commit()
}
```

Production code may need richer commit/rollback error composition and explicit
transaction options.

## Embedded Migrations

```go
//go:embed migrations/*.sql
var migrationFiles embed.FS
```

Pair embedded assets with version ordering, a migration ledger, locking, and
database-specific atomicity rules.
