# Tying a reversal to its original

A reversal is not a new debit. It is the undoing of one earlier credit, and it must be computed from that credit: the account it went to, the amount it granted. The message that announces the reversal only says which original is meant and how much money went back.

Code that subtracts what the reversal message says fails in three ways. A reversal for something never credited still subtracts. A reversal delivered twice subtracts twice. A reversal with another user id or amount takes the wrong thing from the wrong account.

## Record the fact, then settle

Every handler in this skill has the same two steps, inside one transaction that holds a lock on the order row.

1. **Record the fact** under the id the provider gave it: this refund, this dispute. A unique key makes the second delivery a no-op.
2. **Settle the order:** compare what the stored facts require with what the ledger already shows, and post only the difference.

Settling is safe to repeat and does not care in which order the facts arrived. That is what makes duplicates, partial refunds, disputes and early reversals the same problem.

The tables for the facts are in `assets/reversals.postgres.sql`: `refunds`, `disputes`, `conversions` and `grants`. Its header lists what to change for MySQL and SQLite.

## Kinds and references

| Entry | kind | ref | reverses_id |
| --- | --- | --- | --- |
| The original credit | `purchase` | order id | |
| A refund's share | `purchase_refund` | `<provider>:<refund id>` | the purchase entry |
| A dispute taking what is left | `purchase_dispute` | `<provider>:<dispute id>` | the purchase entry |
| A won dispute giving it back | `purchase_dispute_won` | `<provider>:<dispute id>` | the purchase entry |
| A conversion and its reversal | `offer_<network>`, `offer_<network>_reversal` | the network's transaction id | the offer entry |

Every entry about one original points at that original, not at each other. What is left of a grant is then one sum.

## What is left, and taking it back

Node with the `pg` driver. `postEntry` is the project's ledger posting function, as the `build-ledger` skill builds it: it inserts under the unique (kind, ref) key, reports whether the entry was new, and lets the balance go below zero only when `allowDebt` is set.

```js
export async function lockOrder(tx, orderId) {
  const { rows } = await tx.query(
    'SELECT id, account_id, price_cents, currency FROM orders WHERE id = $1 FOR UPDATE',
    [String(orderId)],
  );
  return rows[0] ?? null;
}

async function purchaseEntry(tx, orderId) {
  const { rows } = await tx.query(
    "SELECT id, account_id, amount, ref FROM ledger WHERE kind = 'purchase' AND ref = $1",
    [orderId],
  );
  return rows[0] ?? null;
}

// What is left of a grant: its amount, minus what was taken back, plus what was given back.
async function outstanding(tx, entry) {
  const { rows } = await tx.query('SELECT COALESCE(SUM(amount), 0) AS net FROM ledger WHERE reverses_id = $1', [entry.id]);
  return Number(entry.amount) + Number(rows[0].net);
}

// Takes back up to `wanted` of what `original` granted, from the account that received it.
// Returns the amount taken: 0 when nothing is left of the grant.
async function takeBack(tx, original, { kind, ref, wanted }) {
  const amount = Math.min(wanted, await outstanding(tx, original));
  if (amount <= 0) return 0;
  const posted = await postEntry(tx, {
    accountId: original.account_id,
    amount: -amount,
    kind,
    ref,
    reversesId: original.id,
    allowDebt: true,
  });
  return posted ? amount : 0;
}
```

`takeBack` is the only place that subtracts for a reversal. The account and the upper bound come from the original entry. However many refunds and disputes pile up on one order, together they cannot take more than it granted.

The lock on the order row matters. Two reversals of one order that run at the same moment would both read the same "what is left". `FOR UPDATE` makes the second wait.

## Refunds, full and partial

```js
async function applyRefunds(tx, order, original) {
  const { rows } = await tx.query(
    'SELECT id, provider, refund_id, amount_cents, credits_taken FROM refunds WHERE order_id = $1 ORDER BY id',
    [order.id],
  );
  const price = BigInt(order.price_cents);
  const granted = BigInt(original.amount);
  let refunded = 0n;
  let assigned = 0n;
  for (const refund of rows) {
    refunded += BigInt(refund.amount_cents);
    // The share of a refund is what the running total requires, minus the shares before it.
    // Rounding cannot add up, and the refund that completes the price takes the rest.
    const target = (granted * (refunded > price ? price : refunded)) / price;
    const share = Number(target - assigned);
    assigned = target;
    if (refund.credits_taken !== null) continue;
    const taken = await takeBack(tx, original, {
      kind: 'purchase_refund',
      ref: `${refund.provider}:${refund.refund_id}`,
      wanted: share,
    });
    await tx.query('UPDATE refunds SET credits_taken = $1 WHERE id = $2', [taken, refund.id]);
  }
}

// Returns a reason when the refund cannot be matched to the app's records.
export async function recordRefund(tx, { provider, refundId, orderId, amountCents, currency }) {
  const order = await lockOrder(tx, orderId);
  if (!order) return 'unknown_order';
  if (!Number.isSafeInteger(amountCents) || amountCents <= 0 || currency !== order.currency) return 'refund_mismatch';
  await tx.query(
    `INSERT INTO refunds (provider, refund_id, order_id, amount_cents) VALUES ($1, $2, $3, $4)
     ON CONFLICT (provider, refund_id) DO NOTHING`,
    [provider, String(refundId), order.id, amountCents],
  );
  await settleOrder(tx, order);
}
```

The share of a partial refund is proportional and computed on the running total. An order of 499 cents that granted 500 credits, refunded in parts of 166, 166 and 167 cents, gives back 166, 166 and 168 credits: exactly 500. Computing each refund alone and rounding down would leave credits behind, and a user who can ask for many small refunds would keep them.

- The division rounds down, so a partial refund never takes more than its share. The refund that completes the price takes the remainder.
- A refund so small that its share is zero is still stored. It counts toward the running total.
- A refund in another currency than the order, or with a non-positive amount, is a mismatch for a person. Refunds that add up to more than the price take everything and no more.
- `BigInt` keeps the product exact. In Python integers are exact already. In PHP use `intdiv()` on integers and check the range.
- If the order granted several things, and the refund names line items, reverse those lines. Otherwise use the proportion.

Some providers report each refund as its own object with an id. Others report only the payment's running refunded total. Check the provider's documentation. With a running total, the amount of the row is the new total minus what is already stored, and its key is the payment id plus the new total.

## One function settles everything

```js
// Brings the ledger and the grants in line with every refund and dispute stored for the
// order. It posts only what is missing, so it can run any number of times. The refund
// handler, the dispute handler and the payment handler all end with it.
export async function settleOrder(tx, order) {
  const original = await purchaseEntry(tx, order.id);
  if (original) {
    await applyRefunds(tx, order, original);
    await applyDisputes(tx, order, original);
    await settleDependents(tx, original);
  }
  await syncEntitlements(tx, order);
}
```

`applyDisputes` is in [disputes-and-reporting.md](disputes-and-reporting.md). `settleDependents` and `syncEntitlements` are in [debt-entitlements-dependents.md](debt-entitlements-dependents.md).

## A reversal that arrives before its original

Providers do not promise order, and a failed delivery of the payment event can be retried after the refund event went through.

**With an order row.** `recordRefund` stores the refund even when the order was never credited: `settleOrder` finds no purchase entry and posts nothing, and `credits_taken` stays empty. The handler that credits a purchase must end with `settleOrder(tx, order)`, under the same lock. When the payment arrives, it credits, finds the waiting refund and takes it back in the same transaction. The ledger shows both entries and the balance shows the net.

**Without an order row.** A conversion reported by a network has no row on the app's side until it is credited, so the credit and the reversal need a row to meet on. Both write the `conversions` row for (network, transaction id) first. The database lets only one of them create it. Python with `psycopg`:

```python
def credit_conversion(cur, source: str, tx_id: str, account_id: int, amount: int) -> bool:
    """Credit a conversion once. False when this id was credited before or was reversed first."""
    cur.execute(
        "INSERT INTO conversions (source, tx_id, account_id, amount, status)"
        " VALUES (%s, %s, %s, %s, 'credited') ON CONFLICT (source, tx_id) DO NOTHING",
        (source, tx_id, account_id, amount),
    )
    if cur.rowcount == 0:
        return False
    post_entry(cur, account_id=account_id, amount=amount, kind=f"offer_{source}", ref=tx_id)
    return True


def reverse_conversion(cur, source: str, tx_id: str) -> int:
    """Take back what this conversion credited. Returns the amount taken, 0 when there was nothing to take."""
    cur.execute(
        "INSERT INTO conversions (source, tx_id, status)"
        " VALUES (%s, %s, 'reversed_early') ON CONFLICT (source, tx_id) DO NOTHING",
        (source, tx_id),
    )
    if cur.rowcount == 1:
        return 0  # nothing was credited; the credit that arrives later finds this row and posts nothing

    cur.execute(
        "UPDATE conversions SET status = 'reversed', reversed_at = now()"
        " WHERE source = %s AND tx_id = %s AND status = 'credited'",
        (source, tx_id),
    )
    if cur.rowcount == 0:
        return 0  # reversed before

    # The account and the amount come from the entry that was posted, never from the reversal message.
    cur.execute("SELECT id, account_id, amount FROM ledger WHERE kind = %s AND ref = %s", (f"offer_{source}", tx_id))
    original_id, account_id, amount = cur.fetchone()
    post_entry(
        cur,
        account_id=account_id,
        amount=-amount,
        kind=f"offer_{source}_reversal",
        ref=tx_id,
        reverses_id=original_id,
        allow_debt=True,
    )
    return amount
```

Both functions run inside the caller's transaction. An insert of a key that another open transaction is inserting waits for it, so the two cannot pass each other. A reversal that arrived first leaves a `reversed_early` row and the credit that follows posts nothing. Every outcome is answered with the sender's success response.

If conversions pay dependent rewards, `reverse_conversion` ends by taking them back in the same transaction, the way `settleOrder` does for orders.

Answering an early reversal with an error, so that the sender tries again after the original, is weaker: it depends on the sender retrying reversals, and it retries forever when the original never comes.

## Refunds the app issues itself

1. Only a staff session with a named permission may refund, unless the user decided on self-service.
2. Reserve the amount with a conditional update, so that two requests cannot refund more than was paid: `UPDATE orders SET refund_requested_cents = refund_requested_cents + :amount WHERE id = :id AND refund_requested_cents + :amount <= price_cents`. Stop when no row changed.
3. Store a refund request row and pass its id to the provider as the idempotency key, if the provider's API takes one. Check the provider's documentation. Release the reservation when the call fails.
4. Pass the provider's answer through `recordRefund`, with the provider's refund id. The webhook for the same refund carries the same id and finds it stored. Whichever arrives first applies it.

The take-back is never a separate piece of code in the admin tool.

## Without a ledger

The minimum is a unique key that makes the take-back happen once, in the same transaction as the balance update, with the amount read from what the original stored:

```sql
BEGIN;
UPDATE orders SET status = 'refunded' WHERE id = :order_id AND status = 'paid';
-- Only when that changed one row:
UPDATE users
   SET balance = balance - (SELECT credits FROM orders WHERE id = :order_id)
 WHERE id = (SELECT user_id FROM orders WHERE id = :order_id);
COMMIT;
```

For conversions, the `conversions` row already stores the account and the amount, and its move from `credited` to `reversed` is the key. This handles a full reversal once. Partial refunds, disputes that can be won, and any report of what was taken back need the entries a ledger keeps: tell the user that the `build-ledger` skill adds them.

## Dialect notes

- **MySQL and MariaDB:** no `ON CONFLICT`. Use a plain `INSERT` and treat error 1062 as "the row exists". Avoid `INSERT IGNORE`.
- **PostgreSQL:** the patterns assume the default isolation level, READ COMMITTED. At REPEATABLE READ or SERIALIZABLE a concurrent duplicate ends in a serialization error instead of a wait: rerun the whole transaction.
- **SQLite:** the statements work as written without `FOR UPDATE` and with `CURRENT_TIMESTAMP` or Unix seconds for `now()`. Open the transaction with `BEGIN IMMEDIATE`, which is the lock.
- **Deadlocks:** a reversal that also touches a second account, such as a referrer's, can deadlock with a transaction that touches the same two in the other order. Rerun the whole transaction, a few times at most.
