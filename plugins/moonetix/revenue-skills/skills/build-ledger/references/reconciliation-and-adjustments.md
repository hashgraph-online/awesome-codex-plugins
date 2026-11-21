# Reconciliation, adjustments and reading

A ledger that is never checked drifts without anyone noticing. This file covers the check, what to do when it fails, how people change a balance, and how balances and history are read.

## The reconciliation query

Every account whose cached balance differs from the sum of its entries:

```sql
SELECT a.id, a.balance, COALESCE(SUM(l.amount), 0) AS ledger_total
  FROM accounts a
  LEFT JOIN ledger l ON l.account_id = a.id
 GROUP BY a.id, a.balance
HAVING a.balance <> COALESCE(SUM(l.amount), 0);
```

It runs unchanged on PostgreSQL, MySQL and SQLite. The `LEFT JOIN` matters: an account with a balance and no entries at all is the most common mismatch, and an inner join would hide it.

Run it as one statement. A single statement reads one consistent snapshot, so entries posted while it runs cannot produce false alarms. Two separate queries, one for balances and one for sums, can.

The expected result is no rows, always. There is no tolerance: with integer amounts a difference of one unit is a bug.

## The scheduled check

Wrap the query in a command that exits with an error when it finds anything, and schedule it with what the project already uses: cron, a job queue, a scheduled task of the hosting platform. Python with `psycopg`:

```python
#!/usr/bin/env python3
"""Exit status 1 when a cached balance differs from the sum of its ledger entries."""
import os
import sys

import psycopg

MISMATCHES = """
SELECT a.id, a.balance, COALESCE(SUM(l.amount), 0) AS ledger_total
  FROM accounts a
  LEFT JOIN ledger l ON l.account_id = a.id
 GROUP BY a.id, a.balance
HAVING a.balance <> COALESCE(SUM(l.amount), 0)
 ORDER BY a.id
 LIMIT 100
"""


def main() -> int:
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        rows = conn.execute(MISMATCHES).fetchall()
    for account_id, balance, ledger_total in rows:
        print(f"account {account_id}: balance {balance}, ledger {ledger_total}, drift {balance - ledger_total}")
    return 1 if rows else 0


if __name__ == "__main__":
    sys.exit(main())
```

Requirements for the job:

- A failure reaches a person: a page, a chat alert, an email to a monitored address. A log line nobody reads is not a check.
- It runs at least nightly. Hourly is reasonable while a migration is in progress.
- It also runs in the test suite, after the tests that move balances.
- On a large ledger, run it against a read replica, or check only the accounts that have entries since the last run and keep the full pass for the weekend. Add the condition `WHERE a.id IN (SELECT account_id FROM ledger WHERE created_at >= :since)`.

## When it finds a mismatch

A mismatch means a write happened outside the posting function. Do not make the alert go away by overwriting one side.

1. **Freeze the evidence.** Record the account, both numbers and the time.
2. **Find the writer.** Search the code and the database for writes to the balance column: a handler that was missed, a script, a console session, a database trigger, another service. The account's recent entries and the application log around the time of the last correct check narrow it down.
3. **Fix the writer** so that it posts through the function.
4. **Record the correction.** Decide which side is right. If the balance is right and the ledger lacks a row, post the missing entry with a kind that says what it was, a reference that names the incident, and a staff actor. If the ledger is right and the cache is wrong, post nothing and rebuild the cache for that account inside a transaction:

```sql
UPDATE accounts
   SET balance = (SELECT COALESCE(SUM(amount), 0) FROM ledger WHERE account_id = :id)
 WHERE id = :id;
```

This statement is the one permitted write to the balance outside the posting function. Keep it in a named maintenance command, never in a request handler, and log each use.

## Against the outside world

The first check proves that the app agrees with itself. A second one proves that it agrees with the companies that send and receive the money. On a schedule that matches their reports (daily or weekly):

- Payments: the count and total of `purchase` entries per day against the payment provider's settlement or balance report. Refund and dispute entries against the same report.
- Conversions: `offer` and `offer_reversal` entries per network against the network's statistics for the same period.
- Payouts: `payout` entries against the payout provider's list of transfers.

Check the provider's documentation for the report or API that lists settled transactions. Match by the provider's id, which is the `ref` of the entry. An item that exists on one side only is either a lost event or a forged one. Both need a person.

## Manual adjustments

Staff need a way to correct balances. Without one they will use the database console, which leaves no trace. The adjustment path is an ordinary posting with stricter inputs:

```js
const MAX_ADJUSTMENT = 100_000;

// staff comes from the authenticated session, never from the request body.
export async function adjustBalance(pool, staff, { accountId, amount, reason, requestId, reversesId = null }) {
  if (!staff?.permissions?.includes('ledger:adjust')) return { status: 403 };
  const inRange = Number.isSafeInteger(amount) && amount !== 0 && Math.abs(amount) <= MAX_ADJUSTMENT;
  const reasonOk = typeof reason === 'string' && reason.trim().length >= 10;
  if (!inRange || !reasonOk || !/^[\w-]{8,64}$/.test(requestId ?? '')) return { status: 400 };
  if (staff.accountId === accountId) return { status: 403 };

  const posted = await withTransaction(pool, (tx) =>
    postEntry(tx, {
      accountId,
      amount,
      kind: 'adjustment',
      ref: requestId,
      actor: `staff:${staff.id}`,
      note: reason.trim().slice(0, 500),
      reversesId,
      // Only a correction of a named earlier entry may push the balance below zero.
      allowDebt: reversesId !== null,
    }),
  );
  return { status: 200, posted };
}
```

What makes it safe:

- **Who.** The actor is the signed-in staff member, taken from the session. A shared admin key attributes nothing: if the project has only that, record at least the key's name and add per-person accounts to the work list.
- **Why.** A reason is required and stored with the entry.
- **Once.** The admin form creates the request id when it is opened and sends it with the submission. A double click or a retried request posts one entry.
- **How much.** A cap per adjustment. Above the cap, require a second staff member to approve, and store both names.
- **Not for yourself.** Staff cannot adjust an account they own.
- **No overdraft by default.** A manual debit is conditional like any other. Only a correction that names the entry it takes back may create debt.

The endpoint is reachable only with a staff session and is covered by the same authentication, logging and rate limits as the rest of the admin area. Review the adjustment entries regularly: the query is `SELECT * FROM ledger WHERE kind = 'adjustment' ORDER BY id DESC`.

## Append-only in practice

- The triggers in the templates reject updates and deletes. Where the database supports it, also withhold the `UPDATE` and `DELETE` privileges on the ledger from the application's database user.
- A wrong entry is corrected by a new entry with the opposite amount and `reverses_id` set to the wrong one. Both stay visible.
- Closing a user account does not delete its entries. Remove or anonymize the personal data on the user row and keep the account row and its ledger. How long financial records must be kept depends on the jurisdiction: that is the user's decision, and the default is to keep them.
- `created_at` is set by the database. If the event carries its own time (when the provider says the payment happened), store it in an extra column next to it, not instead of it.

## Reading

The balance is read from the cached column: `SELECT balance FROM accounts WHERE id = :id`. Do not compute it from the ledger on every page view.

History is read from the ledger, newest first, paged by id so that new entries do not shift the pages:

```sql
SELECT id, amount, kind, ref, created_at
  FROM ledger
 WHERE account_id = :account_id
   AND id < :before_id          -- omit on the first page
 ORDER BY id DESC
 LIMIT 50;
```

Show users a label derived from `kind`, not the raw `ref`, `actor` or `note`. Those are for staff.

Questions such as "how much did this account earn from offers" or "how much was paid out in the last 24 hours" are sums over the ledger by kind and time. Limits and hold periods built on such sums belong inside the same transaction as the debit they guard.
