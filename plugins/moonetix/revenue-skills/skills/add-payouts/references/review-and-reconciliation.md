# Manual review and reconciliation

Limits and the state machine stop the mistakes a program can recognize. Review is for the ones only a person can judge. Reconciliation is the proof, every day, that what the app believes it paid is what the provider sent.

## The review queue

A payout in `in_review` has its funds taken and waits. Staff either clear it or decline it. Both are guarded moves, so two reviewers who click at the same moment produce one result.

```js
import { endWithoutPaying, move } from './payouts.mjs';
import { withTransaction } from './ledger.mjs';

// staff comes from the authenticated staff session, never from the request body.
export async function approvePayout(pool, payoutId, staff) {
  return withTransaction(pool, async (tx) => {
    const own = await tx.query('SELECT 1 FROM payouts WHERE id = $1 AND account_id = $2', [payoutId, staff.accountId]);
    if (own.rowCount > 0) throw new Error('staff cannot approve a payout of their own account');
    return (await move(tx, payoutId, 'in_review', 'pending', { reviewedBy: `staff:${staff.id}` })) !== null;
  });
}

export async function rejectPayout(pool, payoutId, staff, reason) {
  if (typeof reason !== 'string' || reason.trim().length < 5) throw new TypeError('a reason is required');
  return withTransaction(pool, (tx) =>
    endWithoutPaying(tx, payoutId, 'in_review', 'rejected', { reviewedBy: `staff:${staff.id}`, failureCode: reason.trim() }),
  );
}

// The user withdraws a request that has not been handed to the provider yet.
export async function cancelPayout(pool, payoutId, accountId) {
  return withTransaction(pool, async (tx) => {
    const mine = await tx.query('SELECT status FROM payouts WHERE id = $1 AND account_id = $2', [payoutId, accountId]);
    const status = mine.rows[0]?.status;
    if (status !== 'in_review' && status !== 'pending') return false;
    return endWithoutPaying(tx, payoutId, status, 'canceled');
  });
}
```

- An approved payout becomes `pending` and is sent by the same code as any other. The claim checks the account's flags again, so an approval does not override a ban that came later.
- A rejection returns the funds to the balance. If the earnings themselves were fraudulent, take them back through the reversal path with its own entries (the `handle-refunds-and-reversals` skill). Do not hide a confiscation inside a rejected payout.
- Approval rights are a named permission. Above a second threshold, require a second person. Nobody approves a payout of their own account.
- Every decision stores who and when on the row and in the audit log. Tell the user the outcome. A request that sits in review without a word looks like theft.
- Review has a time limit. A payout older than the promised review time shows up in the stuck query below.

### What staff see

The decision is only as good as the screen. For each payout in the queue show the reason it is there and the account's history, so that approving is not a reflex.

```sql
SELECT p.id, p.account_id, p.amount, p.review_reason, p.created_at, p.destination,
       (SELECT COUNT(*) FROM payouts x WHERE x.account_id = p.account_id AND x.status = 'paid') AS paid_before,
       (SELECT COUNT(DISTINCT o.account_id)
          FROM payout_destinations d
          JOIN payout_destinations o ON o.fingerprint = d.fingerprint AND o.account_id <> d.account_id
         WHERE d.id = p.destination_id) AS other_accounts_on_destination
  FROM payouts p
 WHERE p.status = 'in_review'
 ORDER BY p.created_at;

SELECT kind, COUNT(*) AS entries, SUM(amount) AS total, MIN(created_at) AS first_at, MAX(created_at) AS last_at
  FROM ledger
 WHERE account_id = $1
 GROUP BY kind
 ORDER BY kind;
```

Next to these: the account's age and sign-up signals, where its earnings came from, how much of them was reversed, the history of its destinations, and the other accounts that share a destination, device or address with it. Mask destination details for staff who do not need them in full.

## Reconcile the payouts with the ledger

These run on a schedule on all three databases (write `NOW() - INTERVAL 6 HOUR` in MySQL). Any row is an alert.

```sql
-- Every payout took its funds once, and gave them back exactly when it ended without paying.
SELECT p.id, p.status, p.amount
  FROM payouts p
  LEFT JOIN ledger l ON l.ref = p.id AND l.kind IN ('payout', 'payout_refund')
 GROUP BY p.id, p.status, p.amount
HAVING COALESCE(SUM(CASE WHEN l.kind = 'payout' THEN l.amount ELSE 0 END), 0) <> -p.amount
    OR COALESCE(SUM(CASE WHEN l.kind = 'payout_refund' THEN l.amount ELSE 0 END), 0)
       <> CASE WHEN p.status IN ('failed', 'rejected', 'canceled') THEN p.amount ELSE 0 END;

-- A payout entry in the ledger with no payout row behind it.
SELECT l.id, l.kind, l.ref
  FROM ledger l
  LEFT JOIN payouts p ON p.id = l.ref
 WHERE l.kind IN ('payout', 'payout_refund') AND p.id IS NULL;

-- Stuck: not resolved by the provider, not sent by a worker, or not decided by staff.
SELECT id, status, created_at, sent_at
  FROM payouts
 WHERE (status = 'sending' AND sent_at < now() - interval '6 hours')
    OR (status = 'pending' AND created_at < now() - interval '1 hours')
    OR (status = 'in_review' AND created_at < now() - interval '72 hours');
```

## Reconcile with the provider

Once a day, fetch the provider's own record of what it sent: a report, an export or a list call. Check the provider's documentation for which one exists, how it is paged, which field carries your payout id, and in which time zone its days are cut. Map each record to `reference` (your payout id), `state`, `amount_minor` and `currency`, then compare. Take the provider's records for a window one day wider on each side than your own, so a payout near midnight is not reported as missing.

Python, with no database or provider code in it, so it can be tested with plain lists:

```python
NOT_PAID = {"failed", "rejected", "canceled"}


def reconcile(ours, theirs):
    """Compare payout rows with the provider's records. Returns a list of (problem, id, detail).

    ours:   dicts with id, status, payout_minor, currency.
    theirs: dicts with reference (our payout id as sent), state, amount_minor, currency.
            state is "completed" for money that left, anything else for money that did not.
    """
    problems = []
    by_id = {row["id"]: row for row in ours}
    completed = {}
    for record in theirs:
        if record["reference"] not in by_id:
            problems.append(("not_ours", record["reference"], "the provider sent money this app has no payout for"))
        elif record["state"] == "completed":
            completed.setdefault(record["reference"], []).append(record)

    for payout_id, records in completed.items():
        payout = by_id[payout_id]
        if len(records) > 1:
            problems.append(("paid_twice", payout_id, f"{len(records)} completed transfers for one payout"))
        if payout["status"] in NOT_PAID:
            problems.append(("paid_but_refunded", payout_id, f"status is {payout['status']} and the funds went back"))
        elif payout["status"] != "paid":
            problems.append(("paid_not_recorded", payout_id, f"status is still {payout['status']}"))
        first = records[0]
        if (first["amount_minor"], first["currency"]) != (payout["payout_minor"], payout["currency"]):
            problems.append(("amount_mismatch", payout_id, f"sent {first['amount_minor']} {first['currency']}"))

    for payout in ours:
        if payout["status"] == "paid" and payout["id"] not in completed:
            problems.append(("recorded_not_paid", payout["id"], "marked paid, but the provider shows no completed transfer"))
    return problems
```

| Problem | What it means | First action |
| --- | --- | --- |
| `not_ours` | Money left the provider account without a payout row. A leaked API key, a manual transfer, or a second system. | Rotate the key, find the sender. |
| `paid_twice` | Two transfers for one payout: the idempotency key was not sent, or was changed between attempts. | Stop the sender, recover the second transfer. |
| `paid_but_refunded` | A failure was assumed, the funds went back, and the provider paid anyway. | Take the refund back with a reversal entry that names the payout. |
| `paid_not_recorded` | The answer was lost and the resolver has not caught up, or the payout was sent from a status that should not send. | Apply `paid` if it is `sending`. Investigate if it is anything else. |
| `recorded_not_paid` | Marked `paid` on an answer that was not final, or the provider returned the money later. | Ask the provider, then pay again as a new payout or credit the account. |
| `amount_mismatch` | A conversion, fee or currency error. | Fix the conversion before the next run. |

- Reconciliation reports. It does not repair. Every problem goes to a person, with the payout id and the provider's record side by side.
- Also compare totals: the sum of `payout_minor` over payouts settled as `paid` in the period against what the provider debited from the platform balance, fees shown separately.
- Keep each run's result. "No problems on 41 payouts" is evidence too.
- Watch the provider balance itself. An empty platform account is an operations problem, and users should not see it as a failed payout of their own: check the balance before the send job runs, and when it cannot cover the queue, pause sending, leave the payouts `pending` and alert.
