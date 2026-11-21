# Schema and posting

The ledger is two tables and one function. The templates in `assets/` hold the full schema for PostgreSQL, MySQL and SQLite. This file explains the columns, the posting function and the differences between the three databases.

## The two tables

`accounts` holds one row per balance. `ledger` holds one row per change to a balance.

| Column | Purpose |
| --- | --- |
| `account_id` | The account whose balance changes. A foreign key, so an entry cannot point at nothing. |
| `amount` | Signed whole number in the smallest unit. Positive adds, negative takes. Never zero. |
| `kind` | What sort of event this is: `purchase`, `offer`, `spend`, `payout`, `adjustment`. |
| `ref` | The id of the event in the system that produced it: order id, provider transaction id, payout id. |
| `actor` | Who caused the entry: `system`, a provider name, or `staff:<id>` for a person. |
| `note` | The reason, for entries made by a person. |
| `reverses_id` | For an entry that takes back or corrects an earlier one, the id of that entry. |
| `created_at` | Set by the database, never by the client. |

The unique constraint on (`kind`, `ref`) carries the design. The same event can only be recorded once, however many times it is delivered and however many workers receive it. It also gives every entry a pointer back to the outside world, which a refund or an investigation needs later.

Ledger rows are append-only. The templates enforce it with triggers that reject `UPDATE` and `DELETE`.

Amounts are integers. If the app must store fractions of the smallest unit, use a fixed-scale decimal type (`NUMERIC(20,4)`) in both tables and a decimal library in the application. Never use a floating point type.

## Choosing kind and ref

The reference must be the same every time the same event arrives. Take it from the event, not from a random generator at posting time.

| Change | kind | ref |
| --- | --- | --- |
| Credits bought | `purchase` | order id |
| Refund of that purchase | `purchase_refund` | order id, or the refund id when refunds can be partial |
| Reward from an offer or conversion | `offer` | the network's transaction id |
| That conversion taken back | `offer_reversal` | the same transaction id |
| Spend | `spend` | purchase id, or `<account>:<idempotency key>` sent by the client |
| Give-back after a failed delivery | `spend_refund` | the same id as the spend |
| Transfer between accounts | `transfer_out` and `transfer_in` | transfer id |
| Promo code, once per account | `promo` | `<code>:<account>` |
| Daily bonus | `daily_bonus` | `<account>:<date>` |
| Payout, and its return on failure | `payout`, `payout_refund` | payout id |
| Manual adjustment | `adjustment` | request id from the admin tool |

Three things follow from the table.

- A reversal uses its own kind with the reference of the original. That makes "reverse once" a property of the schema.
- The key can express a business rule. `promo` with `<code>:<account>` is "one redemption per account" without a separate table.
- When two providers can issue the same id, scope it: one kind per provider (`offer_<network>`), or a prefix in the reference (`<provider>:<id>`).

If an entry arrives for an existing (kind, ref) but with a different account or amount, the first one stands. Log the second: it is a provider bug or someone testing the endpoint.

## Posting an entry

PostgreSQL, with Node and the `pg` driver. The same shape works in any language: insert, look at the row count, then update.

```js
export class InsufficientFunds extends Error {}

export async function withTransaction(pool, work) {
  const tx = await pool.connect();
  try {
    await tx.query('BEGIN');
    const result = await work(tx);
    await tx.query('COMMIT');
    return result;
  } catch (err) {
    await tx.query('ROLLBACK');
    throw err;
  } finally {
    tx.release();
  }
}

// Returns true when the entry was posted, false when (kind, ref) was already there.
// Throws InsufficientFunds when a debit would overdraw; the transaction must then roll back,
// because the ledger row of this call is already inserted.
export async function postEntry(tx, entry) {
  const { accountId, amount, kind, ref, actor = 'system', note = null, reversesId = null, allowDebt = false } = entry;
  if (!Number.isSafeInteger(amount) || amount === 0) throw new TypeError('amount must be a non-zero integer');

  const inserted = await tx.query(
    `INSERT INTO ledger (account_id, amount, kind, ref, actor, note, reverses_id)
     VALUES ($1, $2, $3, $4, $5, $6, $7)
     ON CONFLICT (kind, ref) DO NOTHING`,
    [accountId, amount, kind, String(ref), actor, note, reversesId],
  );
  if (inserted.rowCount === 0) return false;

  if (amount > 0 || allowDebt) {
    const added = await tx.query('UPDATE accounts SET balance = balance + $1 WHERE id = $2', [amount, accountId]);
    if (added.rowCount !== 1) throw new Error(`account ${accountId} not found`);
  } else {
    const taken = await tx.query(
      'UPDATE accounts SET balance = balance - $1 WHERE id = $2 AND balance >= $1',
      [-amount, accountId],
    );
    if (taken.rowCount !== 1) throw new InsufficientFunds();
  }
  return true;
}
```

A caller:

```js
const posted = await withTransaction(pool, (tx) =>
  postEntry(tx, { accountId: user.id, amount: reward, kind: 'offer', ref: transactionId }),
);
// posted === false: this transaction id was credited before. Answer the sender with success.
```

Why it holds under concurrency: when two transactions insert the same (kind, ref), the second waits for the first. If the first commits, the second inserts nothing and skips the balance update. If the first rolls back, the second proceeds. No check in application code is involved.

Notes for PostgreSQL:

- Do not replace `ON CONFLICT DO NOTHING` with a plain insert and a caught error. A failed statement aborts the whole transaction in PostgreSQL.
- At the default isolation level, READ COMMITTED, the conditional update waits for a concurrent writer and then re-checks `balance >= $1` against the new value. At REPEATABLE READ or SERIALIZABLE it fails with a serialization error instead: rerun the whole transaction, a few times at most.
- The `pg` driver returns `BIGINT` columns as strings. Convert with `Number()` while values stay below 2^53, or use `BigInt` throughout. Comparing a string from the database with a number from an event is a common source of false mismatches.

## MySQL and MariaDB

Two differences matter.

**Duplicates.** MySQL has no `ON CONFLICT`. Use a plain `INSERT` and treat error 1062 (duplicate key) as "seen before". InnoDB rolls back only the failed statement, so the transaction stays usable. Avoid `INSERT IGNORE`: it also swallows other errors, such as a failed foreign key, and a lost credit then looks like a duplicate. Avoid counting affected rows of `ON DUPLICATE KEY UPDATE`: the count depends on a client flag that several frameworks set.

**Lock order.** The foreign key check of the insert takes a shared lock on the account row. Two transactions that each hold that lock and then update the balance deadlock. Lock the account row first.

```php
<?php
declare(strict_types=1);

final class InsufficientFunds extends RuntimeException {}

/**
 * Call inside an open transaction. Returns true when the entry was posted,
 * false when (kind, ref) was already there.
 */
function post_entry(
    PDO $db,
    int $accountId,
    int $amount,
    string $kind,
    string $ref,
    string $actor = 'system',
    ?string $note = null,
    ?int $reversesId = null,
    bool $allowDebt = false,
): bool {
    if ($amount === 0) {
        throw new InvalidArgumentException('amount must not be zero');
    }
    if (!$db->inTransaction()) {
        throw new LogicException('post_entry() must run inside a transaction');
    }

    // Lock the account row before the insert. The foreign key check of the insert takes a
    // shared lock on it, and two transactions that hold one and then update would deadlock.
    $lock = $db->prepare('SELECT id FROM accounts WHERE id = ? FOR UPDATE');
    $lock->execute([$accountId]);
    if ($lock->fetchColumn() === false) {
        throw new RuntimeException("account $accountId not found");
    }

    try {
        $db->prepare(
            'INSERT INTO ledger (account_id, amount, kind, ref, actor, note, reverses_id)
             VALUES (?, ?, ?, ?, ?, ?, ?)'
        )->execute([$accountId, $amount, $kind, $ref, $actor, $note, $reversesId]);
    } catch (PDOException $e) {
        if (($e->errorInfo[1] ?? null) === 1062) {
            return false;
        }
        throw $e;
    }

    if ($amount > 0 || $allowDebt) {
        $db->prepare('UPDATE accounts SET balance = balance + ? WHERE id = ?')->execute([$amount, $accountId]);
        return true;
    }
    $take = $db->prepare('UPDATE accounts SET balance = balance - ? WHERE id = ? AND balance >= ?');
    $take->execute([-$amount, $accountId, -$amount]);
    if ($take->rowCount() !== 1) {
        throw new InsufficientFunds();
    }
    return true;
}
```

```php
$db->beginTransaction();
try {
    $posted = post_entry($db, accountId: $userId, amount: $reward, kind: 'offer', ref: $txId);
    $db->commit();
} catch (Throwable $e) {
    $db->rollBack();
    throw $e;
}
```

PDO must throw on errors (`PDO::ERRMODE_EXCEPTION`, the default since PHP 8.0). On a deadlock (error 1213) InnoDB rolls the transaction back: rerun it.

## SQLite

The PostgreSQL statements work unchanged, including `ON CONFLICT (kind, ref) DO NOTHING`. Read the number of changed rows from the statement result. Three settings matter:

- Start write transactions with `BEGIN IMMEDIATE`, so the write lock is taken at the start and not in the middle.
- Run `PRAGMA foreign_keys = ON` on every connection.
- Set a busy timeout and use WAL mode when more than one process writes. SQLite allows one writer at a time, which also means two debits cannot interleave.

## With an ORM

Keep the two statements. Most ORMs can express them without loading the row:

- The insert: an "insert or ignore" call that reports whether a row was written, or a create inside a savepoint that catches the unique violation (Django's `get_or_create` does this and returns a `created` flag).
- The debit: an update with a filter on the balance and an increment expression, such as Django's `filter(pk=id, balance__gte=n).update(balance=F('balance') - n)`, Laravel's `where('balance', '>=', $n)->decrement('balance', $n)` or Prisma's `updateMany` with `decrement`. Each returns the number of rows changed. Check it.

Loading the account object, changing `balance` and calling `save()` is the read-compute-write bug in ORM form.

## Debits and the order of work

When a debit pays for something outside the database, the order is: take the funds, commit, act, and give the funds back if the action fails.

```js
export async function spend(pool, deliver, { accountId, item, price, purchaseId }) {
  let charged;
  try {
    charged = await withTransaction(pool, (tx) =>
      postEntry(tx, { accountId, amount: -price, kind: 'spend', ref: purchaseId }),
    );
  } catch (err) {
    if (err instanceof InsufficientFunds) return { status: 402, error: 'insufficient_balance' };
    throw err;
  }
  if (!charged) return { status: 200, repeated: true };

  try {
    await deliver(accountId, item);
  } catch {
    await withTransaction(pool, (tx) =>
      postEntry(tx, { accountId, amount: price, kind: 'spend_refund', ref: purchaseId }),
    );
    return { status: 502, error: 'delivery_failed_funds_returned' };
  }
  return { status: 200 };
}
```

`price` comes from the server's own price table, never from the request. `purchaseId` is `<account>:<idempotency key>` when the client sends a key, so a retried request is charged once. `InsufficientFunds` is caught outside the transaction, after the rollback has removed the ledger row.

Never call the external service between the check and the debit, and never hold the transaction open across a network call.

## When a balance may go below zero

Only when an entry takes back value the account should not have: a refund, a chargeback, a reversed conversion, or a staff correction of a named earlier entry. Those callers pass `allowDebt`, and the entry carries `reverses_id`. Every other debit is conditional and fails instead.

A negative balance then blocks further spending and payouts by itself: no conditional debit can succeed against it, and new credits repay the debt first.

## Two accounts in one move

A transfer is two entries with the same reference and two kinds, in one transaction. Validate the amount as greater than zero before negating it.

```js
export async function transfer(pool, { fromId, toId, amount, transferId }) {
  if (!Number.isSafeInteger(amount) || amount <= 0 || fromId === toId) throw new TypeError('invalid transfer');
  return withTransaction(pool, async (tx) => {
    const out = { accountId: fromId, amount: -amount, kind: 'transfer_out', ref: transferId };
    const into = { accountId: toId, amount, kind: 'transfer_in', ref: transferId };
    // Lower account id first, so two opposite transfers cannot wait on each other.
    const [first, second] = fromId < toId ? [out, into] : [into, out];
    const posted = await postEntry(tx, first);
    if (posted) await postEntry(tx, second);
    return posted;
  });
}
```

If the debit fails, the transaction rolls back and the credit that was posted first disappears with it.
