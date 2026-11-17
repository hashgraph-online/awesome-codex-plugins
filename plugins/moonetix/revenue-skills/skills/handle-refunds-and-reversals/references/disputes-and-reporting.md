# Disputes and reporting

A dispute (chargeback) is a refund the buyer's bank forces, with a twist: it can be undone. The provider reports it in stages, each stage can be delivered more than once, and the stages can arrive in any order.

## The life cycle

```text
            +--> won   (the money comes back; give back what the dispute took)
open  ------+
            +--> lost  (final; nothing more to take)
```

| Stage | What usually happens to the money | Default effect in the app |
| --- | --- | --- |
| Opened | The provider takes the disputed amount from the merchant, often with a fee | Take back what is left of the grant now. Suspend what the order granted. Mark the account for review and hold its payouts. |
| Won | The disputed amount is returned | Give back exactly what the opening took. Restore the grants the dispute revoked. |
| Lost | The amount stays with the buyer | Nothing more on the balance. The grants stay revoked. The account stays restricted until a person decides. |

Check the provider's documentation for the event names of each stage, whether the funds leave at opening or at the decision, and whether earlier warnings or inquiries are sent before a formal dispute. Map each documented event to `open`, `won` or `lost`, and ignore the rest with a 2xx.

Why take the value back at opening and not at the decision: a dispute runs for weeks. An account that keeps its credits for that time can spend or withdraw them, and a lost dispute then has nothing left to take. If the user prefers to freeze instead of take, the freeze must block spending and payouts the same way.

## The code

`applyDisputes` is called by `settleOrder`, described in [tie-reversals-to-originals.md](tie-reversals-to-originals.md), which also holds `lockOrder`, `purchaseEntry` and `takeBack`.

```js
async function applyDisputes(tx, order, original) {
  const { rows } = await tx.query(
    "SELECT id, provider, dispute_id FROM disputes WHERE order_id = $1 AND credits_taken IS NULL AND status <> 'won' ORDER BY id",
    [order.id],
  );
  for (const dispute of rows) {
    const taken = await takeBack(tx, original, {
      kind: 'purchase_dispute',
      ref: `${dispute.provider}:${dispute.dispute_id}`,
      wanted: Number(original.amount),
    });
    await tx.query('UPDATE disputes SET credits_taken = $1 WHERE id = $2', [taken, dispute.id]);
  }
}

// status is 'open', 'won' or 'lost', mapped from the provider's event by the caller.
export async function recordDispute(tx, { provider, disputeId, orderId, status }) {
  const order = await lockOrder(tx, orderId);
  if (!order) return 'unknown_order';
  const key = [provider, String(disputeId)];

  // Every dispute event runs the opening step first. It does nothing when it ran before,
  // so a closing event that arrives without its opening event is still handled in full.
  await tx.query(
    `INSERT INTO disputes (provider, dispute_id, order_id) VALUES ($1, $2, $3)
     ON CONFLICT (provider, dispute_id) DO NOTHING`,
    [...key, order.id],
  );
  await settleOrder(tx, order);
  if (status === 'open') return;

  const closed = await tx.query(
    "UPDATE disputes SET status = $3, closed_at = now() WHERE provider = $1 AND dispute_id = $2 AND status = 'open'",
    [...key, status],
  );
  if (closed.rowCount === 0) return;

  if (status === 'won') {
    const { rows } = await tx.query('SELECT credits_taken FROM disputes WHERE provider = $1 AND dispute_id = $2', key);
    const taken = Number(rows[0].credits_taken ?? 0);
    const original = await purchaseEntry(tx, order.id);
    if (original && taken > 0) {
      await postEntry(tx, {
        accountId: original.account_id,
        amount: taken,
        kind: 'purchase_dispute_won',
        ref: key.join(':'),
        reversesId: original.id,
      });
    }
    // A refund recorded while the dispute held everything took nothing. It applies now.
    await tx.query('UPDATE refunds SET credits_taken = NULL WHERE order_id = $1 AND credits_taken = 0', [order.id]);
  }
  await settleOrder(tx, order);
}
```

What keeps it from acting twice:

- **The dispute row** is unique per provider and dispute id. `credits_taken` is set once, by the opening step, and records what this dispute took. That may be less than the grant when a refund came first.
- **The close is a conditional move** from `open`. A second "won", a "lost" after a "won" and a late "opened" all change no row.
- **The give-back is the amount that was taken,** read from the row, under its own ledger key. It is not the grant and not the amount in the event.
- **`takeBack` is bounded** by what is left of the grant, so a refund and a dispute on one payment cannot take it twice.

## Sequences that must come out right

Write a test for each. The grant is 500 credits.

| Events, in the order delivered | Balance change in total |
| --- | --- |
| paid, opened, opened | 0 |
| paid, opened, won, won | +500 |
| paid, opened, won, opened (late copy), lost (contradicts) | +500 |
| paid, lost (no opening event seen) | 0 |
| paid, won (no opening event seen) | +500, with a take and a give-back entry |
| paid, refund of half, opened, won | +250 |
| paid, opened, full refund, won | 0 |
| opened, paid, lost | 0 |
| paid, opened (dispute 1), won, opened (dispute 2), lost | 0 |

A dispute that the provider reopens after a win arrives either under a new id, which the code handles as a second dispute, or as a new stage of the same id. Check the provider's documentation. For the second form, allow the move from `won` back to `open` and clear `credits_taken`, so that the opening step runs again.

## Around the dispute

- **The fee.** Record it for the report. By default it is a cost of the business and is not charged to the user's balance.
- **A dispute after a full refund** takes nothing, because nothing is left. It is still stored, and it still marks the account.
- **Evidence.** Answering a dispute at the provider is a business process. The ledger entries of the order, with their times, are what staff will want to attach.
- **Repeat disputes.** An account with a lost dispute should not be able to buy and dispute again without a person looking. Decide the restriction with the user.

## Reporting

Reversals are a cost and a fraud signal. Three queries cover most questions. PostgreSQL syntax; MySQL uses `DATE(created_at)` and `NOW() - INTERVAL 30 DAY`, SQLite uses `date(created_at, 'unixepoch')` and a number of seconds.

What was taken back and given back, per day and kind:

```sql
SELECT date_trunc('day', created_at) AS day, kind, COUNT(*) AS entries, SUM(amount) AS net
  FROM ledger
 WHERE reverses_id IS NOT NULL
   AND created_at >= now() - interval '30 days'
 GROUP BY 1, 2
 ORDER BY 1, 2;
```

Accounts whose grants are reversed again and again, the shape of a refund loop:

```sql
SELECT g.account_id,
       COUNT(DISTINCT g.id) AS grants,
       COUNT(DISTINCT r.reverses_id) AS reversed
  FROM ledger g
  LEFT JOIN ledger r ON r.reverses_id = g.id AND r.amount < 0
 WHERE g.reverses_id IS NULL
   AND g.amount > 0
   AND g.created_at >= now() - interval '90 days'
 GROUP BY g.account_id
HAVING COUNT(DISTINCT r.reverses_id) >= 3
 ORDER BY reversed DESC;
```

Run the same grouping by network or offer for conversions: a source whose reversal rate climbs is sending traffic that does not stay paid.

Facts that are stored but not applied, which should be empty or short-lived:

```sql
SELECT 'refund' AS what, provider AS source, refund_id AS id, received_at AS since
  FROM refunds WHERE credits_taken IS NULL AND received_at < now() - interval '1 day'
UNION ALL
SELECT 'dispute', provider, dispute_id, opened_at
  FROM disputes WHERE credits_taken IS NULL AND status <> 'won' AND opened_at < now() - interval '1 day'
UNION ALL
SELECT 'early reversal', source, tx_id, created_at
  FROM conversions WHERE status = 'reversed_early' AND created_at < now() - interval '1 day';
```

A refund that waits for days belongs to an order whose payment event never arrived: find out why. An early reversal that is never matched is harmless, and many of them from one network are a question for that network.

Add the accounts in debt from [debt-entitlements-dependents.md](debt-entitlements-dependents.md) and the open disputes by age, and the report is complete enough to act on.

**Reconcile with the provider.** Events get lost. On a schedule, read the provider's list of refunds and disputes for the last days, through its API or its report export, and pass every one through `recordRefund` or `recordDispute`. The ones already stored do nothing. The ones that were missed are applied. This is the same code path as the webhook, which is the point.

**Alerts.** A reversal rate above the usual level for a day, one account over the threshold of the loop query, and any row in the "not applied" query older than the limit should reach a person.
