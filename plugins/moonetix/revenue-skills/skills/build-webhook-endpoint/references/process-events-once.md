# Processing an event once

A verified event is genuine. It may still be a copy, it may be late, it may arrive before the event that should precede it, and it may describe a payment that does not match the order. This file covers what happens between "the signature is valid" and the answer.

## Two keys, not one

| Layer | Key | What it stops |
| --- | --- | --- |
| Delivery | The provider's event id, scoped to the provider | The same event delivered again: a retry, a replay inside the timestamp window |
| Business | The order id or transaction id, as a conditional state change or a unique ledger key | Two different events about the same fact, such as a "checkout completed" and a "payment succeeded" for one order, or an event the provider sends again under a new id |

Both are needed. The event id alone lets two events credit one order. The business key alone works, but leaves no record of what was received and no place to park an event that needs a person.

Events without an id of their own, such as query-string postbacks, have only the second layer. See [signed-postbacks.md](signed-postbacks.md).

## The event store

`assets/webhook-events.postgres.sql` holds the table: provider, event id, type, status, a detail text, the payload and the time. The primary key is (provider, event id). Its header lists what to change for MySQL and SQLite. The one that matters: on MySQL the id columns need a binary collation, because the default ones ignore case and two different event ids would collide.

Keep the rows. An id that is deleted can be replayed, so delete ids only when the secret that signed them is no longer accepted. The payload is different: it may carry personal data, so clear it after the retention period the user chose and keep the rest of the row.

## One transaction

The event row, the state change and the ledger entry commit together or not at all. Node with the `pg` driver. `withTransaction` and `postEntry` are the project's transaction helper and ledger posting function, as the `build-ledger` skill builds them.

```js
const PROVIDER = 'payments';

// Each handler checks first and writes second. It returns a reason when the event is
// genuine but must not be applied, and nothing when it ran to the end.
const handlers = {
  async 'payment.succeeded'(tx, data) {
    const found = await tx.query(
      'SELECT id, account_id, credits, price_cents, currency FROM orders WHERE id = $1 FOR UPDATE',
      [String(data.order_id)],
    );
    const order = found.rows[0];
    if (!order) return 'unknown_order';
    if (data.amount_cents !== Number(order.price_cents) || data.currency !== order.currency) return 'amount_mismatch';

    const paid = await tx.query("UPDATE orders SET status = 'paid' WHERE id = $1 AND status = 'pending'", [order.id]);
    if (paid.rowCount === 0) return;
    await postEntry(tx, { accountId: order.account_id, amount: Number(order.credits), kind: 'purchase', ref: order.id });
  },
};

export async function handlePaymentWebhook(pool, config, { rawBody, signatureHeader }) {
  if (!verifyTimestamped(rawBody, signatureHeader, config.webhookSecrets, config.toleranceSeconds)) {
    return { status: 400, body: { error: 'bad_signature' } };
  }
  let event;
  try {
    event = JSON.parse(rawBody.toString('utf8'));
  } catch {
    return { status: 400, body: { error: 'invalid_json' } };
  }
  if (typeof event?.id !== 'string' || typeof event.type !== 'string' || typeof event.data !== 'object' || !event.data) {
    return { status: 400, body: { error: 'invalid_event' } };
  }
  const handler = Object.hasOwn(handlers, event.type) ? handlers[event.type] : null;
  if (!handler) return { status: 200, body: { received: true, outcome: 'ignored' } };

  // An error thrown in here rolls everything back, the event row included. The caller
  // answers 5xx and the provider's next attempt starts from nothing.
  const outcome = await withTransaction(pool, async (tx) => {
    const stored = await tx.query(
      `INSERT INTO webhook_events (provider, event_id, type) VALUES ($1, $2, $3)
       ON CONFLICT (provider, event_id) DO NOTHING`,
      [PROVIDER, event.id, event.type],
    );
    if (stored.rowCount === 0) return 'duplicate';
    const problem = await handler(tx, event.data);
    if (!problem) return 'processed';
    await tx.query(
      "UPDATE webhook_events SET status = 'rejected', detail = $3 WHERE provider = $1 AND event_id = $2",
      [PROVIDER, event.id, problem],
    );
    return 'rejected';
  });

  if (outcome === 'rejected') await config.alert(`webhook event ${event.id} (${event.type}) was rejected`);
  return { status: 200, body: { received: true, outcome } };
}
```

Why each part is there:

- **The insert comes first.** Two deliveries of one event at the same moment both try to insert the same key. The second waits for the first to commit, then inserts nothing and returns `duplicate`. No `SELECT` beforehand: a check followed by an insert lets both through.
- **The grant comes from the order.** The event says which order was paid. What the order is worth is read from the app's own row, never from the event.
- **The status change is conditional.** `WHERE status = 'pending'` matches once. A second event for the same order, under any id, changes no row and posts nothing.
- **`Object.hasOwn`** keeps an event type such as `constructor` from resolving to something inherited.
- **The answer is sent after the commit.** If the process dies before the commit, nothing was stored and the provider tries again. If it dies after the commit and before the answer, the retry finds the event id and is answered as a duplicate.

Add the payload to the insert when the user wants it kept. Store the raw text that was verified, not a re-serialized object.

## Content checks

Run all of them before the first write. A handler that returns a reason after it has written something would commit half an effect.

| Check | Why |
| --- | --- |
| The event type means settled money | "Created", "pending" and "authorized" are not payment. Credit on the one type the provider documents as final. |
| The order exists and is the app's own | An event for an unknown order may belong to another app on the same provider account, or to another environment. |
| Amount and currency equal the order's | Otherwise one cent, or 499 units of a cheaper currency, buys the full grant. Compare integers in the smallest unit. |
| The account named by the event, if any, owns the order | The order row decides who is credited. |
| Live or test mode matches the environment | Many providers mark test events with a flag. Production must refuse them. Check the provider's documentation for the field. |
| The receiving account or app id is the app's own | For store notifications, the bundle or package id. For platforms, the connected account id. |

The app must commit its order row before it sends the user to the provider. An "unknown order" is then always permanent and can be rejected. If the app can receive an event before its own row exists, throw instead of returning a reason, so the provider retries.

## Out of order

Providers do not promise order. A refund can arrive before the payment it refunds, and an old "updated" event after a newer one. Three patterns cover it.

**A state machine with conditional moves.** Each event tries one move, and the `WHERE` clause lists the states it may start from. An event that is late or repeated matches nothing.

```sql
UPDATE orders SET status = 'paid'      WHERE id = :id AND status IN ('pending', 'expired');
UPDATE orders SET status = 'cancelled' WHERE id = :id AND status = 'pending';
```

Whichever of the two arrives first wins, and the other changes no row. Decide with the user what a payment for an expired order does. By default it is honored, because the money arrived, which is why `'expired'` is a state the "paid" move may start from.

**Newer wins.** For objects that only have a current state, such as a subscription, store the provider's time or sequence number of the last applied event and apply an event only when it is newer.

```sql
UPDATE subscriptions
   SET status = :status, period_end = :period_end, provider_updated_at = :event_time
 WHERE id = :id AND provider_updated_at < :event_time;
```

Check the provider's documentation for a field that orders events. Two events in the same second cannot be ordered this way.

**Ask for the truth.** Treat the event as a signal that something changed, fetch the object from the provider's API and store what the API says. This is always current and costs one request per event. It is the only choice when events carry no usable order.

Reversing events (refund, dispute, reversal status) are routed to the project's reversal code, which the `handle-refunds-and-reversals` skill covers, including a reversal that arrives before its original. If that code does not exist yet, store these events with status `received` and tell the user. Do not acknowledge and drop them.

## What to answer

| Situation | Answer | Stored |
| --- | --- | --- |
| Signature invalid, body unreadable | 400 | Nothing |
| Event type the app does not handle | 2xx | Nothing |
| Applied, or nothing left to apply | 2xx, after the commit | `processed` |
| Seen before | 2xx | Unchanged |
| Genuine, but the content check failed | 2xx by default, after the commit, plus an alert | `rejected` with the reason |
| Database or dependency failure | 5xx | Nothing, the transaction rolled back |

A rejected event will not become valid by being sent again, which is why the default acknowledges it and hands it to a person. The user may prefer a 4xx answer so that the failure shows in the provider's dashboard. Then do not store the row, or the retry is answered as a duplicate.

Subscribe only to the event types the app handles. Everything else is noise that still has to be verified.

## When the work does not fit in the request

Providers wait a few seconds for the answer. Crediting an order fits. Sending mail, calling other services or rebuilding a report does not, and none of it belongs inside the transaction.

- **Inline (default).** Verify, run the transaction, answer. Start slow follow-up work after the commit, from a job the project's queue retries.
- **Queued.** Verify, insert the event with status `received` and its payload, commit, answer 2xx. A worker then claims rows and runs the same handlers, marking the row `processed` in the same transaction as the effect.

```sql
SELECT provider, event_id, type, payload
  FROM webhook_events
 WHERE status = 'received'
 ORDER BY received_at
 LIMIT 10
   FOR UPDATE SKIP LOCKED;
```

In the queued form the 2xx means "stored durably", and the stored row is the promise to apply it. The worker needs retries, and rows that stay `received` for long need an alert. An in-memory queue or a "respond, then keep working in the same process" pattern is neither: a restart loses the event after the provider was told it arrived.

`SKIP LOCKED` exists in PostgreSQL, MySQL 8 and MariaDB 10.6. SQLite has one writer at a time, so a single worker is enough there.

## Without a ledger

The minimum is the conditional status change on the order, with the balance update in the same transaction and only when one row changed:

```sql
BEGIN;
UPDATE orders SET status = 'paid' WHERE id = :id AND status = 'pending';
-- Only when that changed one row:
UPDATE users SET balance = balance + :credits WHERE id = :user;
COMMIT;
```

For events with no order row, use the `credited_transactions` table from the asset file as the unique key. This makes the effect happen once. It does not give a history, a way to reverse one credit, or a check that balances are right. Tell the user that the `build-ledger` skill adds those.

## Dialect notes

- **MySQL and MariaDB:** no `ON CONFLICT`. Use a plain `INSERT` and treat error 1062 as "seen before"; InnoDB rolls back only that statement. Avoid `INSERT IGNORE`, which hides other errors.
- **PostgreSQL:** do not catch a unique violation from a plain `INSERT` instead of using `ON CONFLICT`. A failed statement aborts the whole transaction.
- **SQLite:** `ON CONFLICT DO NOTHING` works as written. Open the transaction with `BEGIN IMMEDIATE`. `FOR UPDATE` does not exist and is not needed.
