# Duplicate credit

**Class id:** `duplicate-credit`

Providers deliver events at least once. They retry on timeouts, on any answer that is not 2xx, and sometimes for no visible reason. Users double-click, mobile apps retry, and an attacker who has seen one genuine request can send it again. If the same event credits twice, every retry is free money.

## Where to look

Every "in" path, and every "moves" or "out" path a client can call twice: purchases, transfers, redemptions, withdrawals.

## Shapes that are bugs

**No memory of the event.** The handler credits and stores nothing that identifies the event.

**Check, then insert, with nothing tying them together.**

```php
$seen = $db->query("SELECT 1 FROM tx WHERE tx_id = ?", [$tx])->fetch();
if (!$seen) {
    credit($userId, $reward);                                  // two requests both get here
    $db->query("INSERT INTO tx (tx_id) VALUES (?)", [$tx]);
}
```

Read the schema. Without a unique index on `tx_id`, two deliveries that arrive together both pass the check. With one, the second insert fails, but only if the insert happens before or in the same transaction as the credit.

**The wrong key.** Deduplicating on a timestamp, on the user id, on the amount, or on an id the sender chooses freely. The key must be the provider's event or transaction id, scoped to the provider. Some providers send a delivery id that changes on replay next to the event id, and some send no event id at all: see [payment-providers.md](payment-providers.md).

**A memory that forgets.** Event ids kept in a cache with a time-to-live shorter than the provider's retry window (often days), or in process memory that is lost on restart or not shared between workers.

**State that never closes.** An order is credited whenever a "paid" event arrives, without checking that it is still pending:

```sql
UPDATE orders SET status = 'paid' WHERE id = :id;              -- runs happily a second time
UPDATE users SET balance = balance + :coins WHERE id = :user;
```

**Marking and crediting apart.** The event is marked processed in one statement and the credit happens in another, with no transaction around them. A crash between the two either loses the credit or lets it repeat.

**Client actions without an idempotency key.** A purchase or withdrawal endpoint that creates a new operation for every request, when clients retry on network errors.

## What correct looks like

One transaction that records the event under a unique constraint and applies the credit:

```sql
BEGIN;
INSERT INTO ledger (kind, ref, user_id, amount) VALUES ('offer', :tx_id, :user, :reward)
  ON CONFLICT (kind, ref) DO NOTHING;                          -- 0 rows: seen before, stop
UPDATE users SET balance = balance + :reward WHERE id = :user;  -- only when 1 row was inserted
COMMIT;
```

For orders, a conditional transition does the same job: `UPDATE orders SET status = 'paid' WHERE id = :id AND status = 'pending'`, and the credit runs only when one row changed.

A duplicate should be answered with 2xx so the sender stops retrying.

## How to prove it

```bash
node scripts/probe.mjs replay webhook.json --times 2 --observe me.json     # sequential retry
node scripts/probe.mjs race postback.json --parallel 10 --observe me.json  # deliveries that overlap
```

Compare the change in balance with the value of one event. Run both: check-then-insert code usually survives `replay` and fails `race`.

## Not a bug

- The unique constraint exists and the insert precedes the credit inside one transaction, even if the handler has no explicit "already seen" branch.
- The provider's SDK or a queue in front of the handler deduplicates by event id for at least the retry window. Name it.
- The operation is naturally idempotent: setting a subscription to "active until date X" twice changes nothing.

## Severity

Replay by anyone who can see or guess a request: critical. Double credit only on provider retries or overlapping deliveries: high. It still costs money every day without any attacker.
