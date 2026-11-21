# Races on a balance

**Class id:** `balance-races`

A handler reads a balance, decides, and writes. If a second request reads before the first has written, both decide on the same funds. The user spends or withdraws the same money twice, or a limited coupon is redeemed past its limit.

## Where to look

Every path that lowers a balance or consumes something limited: spending, transfers, withdrawals, redemptions, "first 100 users" promotions, stock, seats, daily claims.

## Shapes that are bugs

**Read, compute in the application, write the result.**

```js
const user = await db.one('SELECT balance FROM users WHERE id = $1', [id]);
if (user.balance < price) return res.status(402).end();
await deliver(id, item);                                         // any await here widens the gap
await db.none('UPDATE users SET balance = $1 WHERE id = $2', [user.balance - price, id]);
```

Ten parallel requests each read 300, each deliver, each write 0. Ten items for the price of one.

**The ORM version of the same thing.**

```python
wallet = Wallet.objects.get(user=user)
if wallet.balance >= amount:
    wallet.balance -= amount
    wallet.save()                    # writes the value computed from a stale read
```

**Check, call out, then deduct.** A withdrawal that verifies the balance, calls the payout provider, and only then subtracts. Parallel requests all pass the check and all get paid. Even a relative update (`balance = balance - :amt`) does not help here: the money has already left.

**A transaction that does not serialize.** Wrapping the read and the write in a transaction at the default isolation level (READ COMMITTED in PostgreSQL, REPEATABLE READ in MySQL) does not stop two transactions from reading the same balance. Without `SELECT ... FOR UPDATE`, a conditional update or a serializable level with retry, the lost update is still there.

**Counting, then inserting.** `SELECT COUNT(*) FROM redemptions WHERE code = ?` followed by an insert when the count is under the cap. Parallel requests all see the same count.

**Non-atomic cache operations.** `GET` then `SET` on a counter in Redis instead of `DECRBY` with a floor check in one script.

## What correct looks like

Let the database decide, in one statement, and act on the outcome:

```sql
UPDATE users SET balance = balance - :price
 WHERE id = :id AND balance >= :price;      -- 0 rows changed: not enough funds, stop
```

Or lock the row first inside a transaction (`SELECT balance FROM users WHERE id = :id FOR UPDATE`), or run at SERIALIZABLE and retry on serialization failure.

Take the funds **before** the external effect. Deliver or pay out afterwards, and return the funds if that step fails. For one-per-user limits use a unique constraint; for global caps use a counter row updated with a condition (`SET used = used + 1 WHERE code = :c AND used < :cap`).

## How to prove it

```bash
node scripts/probe.mjs race spend.json --parallel 10 --observe me.json
node scripts/probe.mjs race payout.json --parallel 5 --observe me.json
```

Count what left the system: items delivered, payouts created, redemption rows. Compare with what the starting balance could pay for. Run a race three times before deciding it does not trigger. If it never triggers locally but the code has a read, an await or network call, and a write with nothing serializing them, record a trace. Production has more parallelism than a laptop.

Single-process runtimes are not immune: in Node, any `await` between the read and the write lets another request run.

## Not a bug

- The deduction is a single conditional statement and the code checks how many rows changed.
- The handler holds a row lock or an advisory lock for the user for the whole read-decide-write sequence.
- All writes for a user go through one queue worker that processes them one at a time.
- A unique constraint makes the second insert fail, and the failure aborts the credit.

## Severity

Double spending or double withdrawal by any signed-in user: critical when value leaves the system (payouts, deliverable goods), high when it stays inside (a wrong internal balance that later checks would catch).
