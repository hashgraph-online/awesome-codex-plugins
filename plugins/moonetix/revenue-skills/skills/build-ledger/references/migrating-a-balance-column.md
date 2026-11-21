# Migrating an app that only has a balance column

The starting point: a `balance` column that several code paths add to and subtract from, and no table that says why. The goal: the same column, now a cache that one function writes, with a ledger row behind every change.

The migration never changes what a user sees. The column stays, the numbers stay, the read paths stay. Only the writers move.

In the examples the balance is `users.balance` and the ledger's `account_id` points at `users.id`.

## 1. Find every writer

List every statement that changes the balance before touching anything. Search for the column name next to an assignment, in every form the stack allows:

```bash
rg -n -i 'set\s+balance|balance\s*=\s*balance' .              # raw SQL
rg -n 'balance\s*(\+=|-=|=[^=])' .                             # assignments in application code
rg -n -i 'increment\(|decrement\(|F\(.balance' .               # ORM increment helpers
```

Also look where a code search does not reach:

- database triggers, stored procedures and scheduled events,
- cron jobs and one-off scripts outside the main source tree,
- admin panels and database tools that staff use to edit rows,
- other services that share the database.

Write the list down: file and line, what the change is for, and which id identifies the event (order id, transaction id, payout id). A writer with no such id needs one before it can move: add an idempotency key to the request, or derive a reference from the business rule (`<code>:<account>` for a promo, `<account>:<date>` for a daily bonus).

## 2. Add the ledger next to the balance

Create the `ledger` table from the template for the project's database. Leave out the template's `accounts` table and reference the table that holds the balance:

```sql
account_id  BIGINT NOT NULL REFERENCES users (id),
```

Deploy the posting function with its tests. Nothing calls it yet. The application behaves exactly as before.

## 3. Post the opening balances

One entry per account that says: this is what the account held when the ledger started. The amount is the balance minus whatever the ledger already holds for the account, so the statement is correct whether it runs before or after some writers have moved.

```sql
INSERT INTO ledger (account_id, amount, kind, ref, actor, note)
SELECT u.id, u.balance - COALESCE(s.total, 0),
       'opening_balance', CAST(u.id AS TEXT), 'migration', 'carried over from users.balance'
  FROM users u
  LEFT JOIN (SELECT account_id, SUM(amount) AS total FROM ledger GROUP BY account_id) s
         ON s.account_id = u.id
  LEFT JOIN ledger o ON o.kind = 'opening_balance' AND o.ref = CAST(u.id AS TEXT)
 WHERE u.balance <> COALESCE(s.total, 0)
   AND o.id IS NULL;
```

- On MySQL write `CAST(u.id AS CHAR)`. The rest is the same on PostgreSQL, MySQL and SQLite. The ledger is read through joins, not subqueries, because MySQL does not allow a subquery on the table being inserted into.
- The reference is the account id, so running the statement twice adds nothing.
- Accounts with a zero balance get no entry. An existing negative balance gets a negative entry: the opening entry records the past, it does not judge it.
- Run it as one statement. It reads one snapshot, so a new-style writer that commits while it runs stays consistent.

Then run the reconciliation query, with `users` in place of `accounts`:

```sql
SELECT u.id, u.balance, COALESCE(SUM(l.amount), 0) AS ledger_total
  FROM users u
  LEFT JOIN ledger l ON l.account_id = u.id
 GROUP BY u.id, u.balance
HAVING u.balance <> COALESCE(SUM(l.amount), 0);
```

It returns no rows. From this moment the query is the progress report of the migration: every row it returns later was written by a path that has not moved yet. Schedule it now, hourly.

If the old history table is trustworthy, it may stay as a read-only archive for support. Do not replay it into the ledger as if those rows had been posted through the function: the opening entry is the honest statement of what is known.

## 4. Move the writers, one at a time

Each change replaces a direct write with a call to the posting function, inside a transaction, with a kind and a reference. Before:

```python
cur.execute("UPDATE users SET balance = balance + %s WHERE id = %s", (reward, user_id))
```

After:

```python
with conn.transaction():
    post_entry(conn, account_id=user_id, amount=reward, kind="offer", ref=transaction_id)
```

Rules for each move:

- **Remove the old statement in the same change.** A direct write left next to the new call applies the change twice.
- **Debits become conditional.** A writer that read the balance, compared in the application and wrote the result is replaced by the function's conditional debit. Delete the read-and-compare code, do not keep both.
- **History writes fold in.** If the writer also inserted a row into an old history table, decide with the user whether that table is still needed. Usually the ledger replaces it.
- **Order by risk.** Move the inbound credit paths first (webhooks, postbacks), then spending, then payouts, then admin tools and scripts. The first group is where a duplicate costs the most.
- **One writer per change set** where the team reviews changes, so each is easy to check against the list from step 1.

While writers are moving, accounts touched by an old writer show up in the hourly reconciliation. That is expected and it names the writer still to do.

## 5. Close the gap

When the search from step 1 finds no direct write, run the reconciliation query once more. Rows that remain are changes made by old writers after the opening entries were posted. Give each such account one closing entry with the statement from step 3 and a different kind:

```sql
INSERT INTO ledger (account_id, amount, kind, ref, actor, note)
SELECT u.id, u.balance - COALESCE(s.total, 0),
       'migration_drift', CAST(u.id AS TEXT), 'migration', 'written outside the ledger during migration'
  FROM users u
  LEFT JOIN (SELECT account_id, SUM(amount) AS total FROM ledger GROUP BY account_id) s
         ON s.account_id = u.id
  LEFT JOIN ledger o ON o.kind = 'migration_drift' AND o.ref = CAST(u.id AS TEXT)
 WHERE u.balance <> COALESCE(s.total, 0)
   AND o.id IS NULL;
```

The reconciliation now returns no rows. From here on, any row is a bug to investigate, not something to post over.

If the app can stop taking writes for a few minutes, there is a shorter route: deploy all writers at once during a maintenance window and post the opening balances while writes are stopped. Then no closing entry is needed.

## 6. Keep it closed

- **A test that searches the code.** Add a test, or a check in continuous integration, that fails when the balance column is written outside the ledger module. The search patterns from step 1, restricted to exclude that module, are enough.
- **The scheduled reconciliation** moves from hourly to nightly and stays for good.
- **Database access.** Staff who edited balances in a database tool get the adjustment endpoint. Where the database allows it, the accounts they use lose the right to update the balance column.
- **Documentation.** One line where the team keeps its conventions: balances change only through the posting function.

## What not to do

- Do not rename or drop the balance column during the migration. Every read path depends on it.
- Do not post opening entries through the application loop, one account per request. One statement is faster and reads one snapshot.
- Do not invent history. An opening entry of 4,200 is true. Forty reconstructed rows that add up to 4,200 are a guess presented as a record.
- Do not switch readers to `SUM(ledger.amount)` to "prove" the migration. The reconciliation query does that without changing behavior.
- Do not leave a feature flag that lets a writer fall back to the direct update. The fallback is the bug.
