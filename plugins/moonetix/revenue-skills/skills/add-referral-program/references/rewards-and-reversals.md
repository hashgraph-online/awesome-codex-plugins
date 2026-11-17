# Rewards and reversals

A reward is paid for what the referred account did, not for its existence. The activity must be something the server verified and that costs real money or effort: a paid order, a verified conversion, a paid subscription period. And when that activity is taken back, the reward goes with it.

## The life of a referral

| Status | Meaning | Ledger |
| --- | --- | --- |
| `pending` | Signed up with the code. Has not qualified. | nothing |
| `qualified` | Verified activity reached the threshold. The reward waits until `reward_at`. | nothing |
| `rewarded` | The reward was posted. | one `referral` entry, reference = referred account id |
| `reversed` | The activity was reversed after the reward. | one `referral_reversal` entry, same reference |
| `blocked` | Held by a same-person check, a cap or staff. Pays nothing until released. | nothing |

```text
pending   -> qualified            verified activity reaches the threshold
qualified -> pending              the activity is reversed before the reward was posted
qualified -> rewarded | blocked   reward_at has passed: pay, or hold when a cap or the referrer's state says so
rewarded  -> reversed             the activity falls below the threshold again
```

The reference of the reward is the referred account's id. With the ledger's unique (kind, reference) key that is "one reward per referred account" as a property of the schema: no retry, race or second qualifying purchase can post another. `reversed` is final for the same reason.

## One function settles a referral

Node with node-postgres. `postEntry` and `withTransaction` are the posting function and helper of the project's ledger, as built by the `build-ledger` skill.

```js
import { postEntry, withTransaction } from './ledger.mjs';

export const PROGRAM = {
  bonus: 500,
  // Net verified value the referred account must reach, in ledger units, and the kinds
  // that count toward it. Reversal kinds are in the list, so the sum falls when they post.
  qualifyingAmount: 1000,
  qualifyingKinds: ['purchase', 'purchase_refund', 'offer', 'offer_reversal'],
  holdSeconds: 14 * 86_400,
  maxRewardsPer30Days: 20,
};

// Call inside the transaction that posted a verified credit or a reversal for the referred
// account, and from the scheduled job. Returns the status the referral ends in, or null.
export async function settleReferral(tx, referredId, program = PROGRAM) {
  const found = await tx.query('SELECT referrer_id, status FROM referrals WHERE referred_id = $1 FOR UPDATE', [referredId]);
  const referral = found.rows[0];
  if (!referral || referral.status === 'blocked' || referral.status === 'reversed') return referral?.status ?? null;

  const sum = await tx.query(
    'SELECT COALESCE(SUM(amount), 0) AS verified FROM ledger WHERE account_id = $1 AND kind = ANY($2)',
    [referredId, program.qualifyingKinds],
  );
  const qualifies = Number(sum.rows[0].verified) >= program.qualifyingAmount;
  let status = referral.status;

  if (status === 'pending' && qualifies) {
    await tx.query(
      `UPDATE referrals SET status = 'qualified', qualified_at = now(), reward_at = now() + make_interval(secs => $2)
        WHERE referred_id = $1`,
      [referredId, program.holdSeconds],
    );
    status = 'qualified';
  }
  if (status === 'qualified' && !qualifies) {
    await tx.query(`UPDATE referrals SET status = 'pending', qualified_at = NULL, reward_at = NULL WHERE referred_id = $1`, [referredId]);
    return 'pending';
  }
  if (status === 'qualified') return payReward(tx, referredId, referral.referrer_id, program);
  if (status === 'rewarded' && !qualifies) return takeBackReward(tx, referredId, referral.referrer_id);
  return status;
}

async function payReward(tx, referredId, referrerId, program) {
  // The lock makes this referrer's rewards take turns, so the cap is counted correctly.
  await tx.query('SELECT id FROM accounts WHERE id = $1 FOR UPDATE', [referrerId]);
  const recent = await tx.query(
    `SELECT COUNT(*) AS rewards FROM referrals
      WHERE referrer_id = $1 AND status = 'rewarded' AND rewarded_at > now() - interval '30 days'`,
    [referrerId],
  );
  const active = await tx.query(`SELECT 1 FROM users WHERE id = $1 AND status = 'active'`, [referrerId]);
  const hold = active.rowCount === 0 ? 'referrer_not_eligible' : Number(recent.rows[0].rewards) >= program.maxRewardsPer30Days ? 'referrer_cap' : null;

  // reward_at is compared in the database, so the hold cannot be skipped by a clock that is off.
  const moved = await tx.query(
    `UPDATE referrals SET status = $2, blocked_reason = $3, rewarded_at = CASE WHEN $4 THEN now() ELSE NULL END
      WHERE referred_id = $1 AND status = 'qualified' AND reward_at <= now()`,
    [referredId, hold ? 'blocked' : 'rewarded', hold, hold === null],
  );
  if (moved.rowCount === 0) return 'qualified';
  if (hold) return 'blocked';
  await postEntry(tx, { accountId: referrerId, amount: program.bonus, kind: 'referral', ref: String(referredId) });
  return 'rewarded';
}

// Takes back exactly what was posted, whatever the bonus is today. The referrer may have
// spent it: the balance then goes below zero, as with any reversal.
export async function takeBackReward(tx, referredId, referrerId, actor = 'system') {
  const moved = await tx.query(`UPDATE referrals SET status = 'reversed' WHERE referred_id = $1 AND status = 'rewarded'`, [referredId]);
  if (moved.rowCount === 0) return null;
  const paid = await tx.query(`SELECT id, amount FROM ledger WHERE kind = 'referral' AND ref = $1`, [String(referredId)]);
  const { id: reversesId, amount } = paid.rows[0];
  const entry = { accountId: referrerId, amount: -Number(amount), kind: 'referral_reversal', ref: String(referredId) };
  await postEntry(tx, { ...entry, reversesId, actor, allowDebt: true });
  return 'reversed';
}

// Scheduled, every few minutes to every hour: pays the referrals whose hold has ended.
export async function payDueReferrals(pool, program = PROGRAM, limit = 200) {
  const due = await pool.query(
    `SELECT referred_id FROM referrals WHERE status = 'qualified' AND reward_at <= now() ORDER BY reward_at LIMIT $1`,
    [limit],
  );
  let paid = 0;
  for (const { referred_id: referredId } of due.rows) {
    if ((await withTransaction(pool, (tx) => settleReferral(tx, referredId, program))) === 'rewarded') paid += 1;
  }
  return paid;
}
```

## Where it is called

`settleReferral` runs after every event that can change the answer, in the transaction of that event:

```js
// In the handler of the verified payment event, after the purchase entry was posted.
const posted = await postEntry(tx, { accountId: order.account_id, amount: order.credits, kind: 'purchase', ref: order.id });
if (posted) await settleReferral(tx, order.account_id);
```

- **Every verified credit** of a qualifying kind: the paid order, the credited conversion.
- **Every reversal** of one: the refund, the chargeback, the reversed conversion. This call is the one that gets forgotten. Without it the reward stays when the purchase is gone. The `handle-refunds-and-reversals` skill builds those paths. Each of them ends with this call.
- **The scheduled job,** for referrals whose hold has ended.
- **Never** the sign-up handler, an email confirmation, a profile completion or anything else the client can produce for free.

A threshold of one paid order is the same code: set `qualifyingAmount` to the smallest pack and `qualifyingKinds` to purchases and their refunds. If "qualified" is a rule the ledger cannot express (30 days of a paid subscription), compute `qualifies` from the table that holds that fact and keep the rest.

## The hold

Between `qualified` and `rewarded` lies the time in which the qualifying activity can still be reversed cheaply: the refund window, the network's reversal window. A reward posted inside that window is spent before the refund arrives.

- Reward can be withdrawn as money, or is large: hold for the full reversal window. 14 days is a common floor.
- Reward is small and can only be spent in the app: a hold of zero is defensible. `settleReferral` then pays in the same transaction that qualified.
- After the hold a reversal can still come (a chargeback months later). `takeBackReward` handles it, and the referrer's balance may go below zero.

Whether referral rewards may be withdrawn at all is a payout rule. The `add-payouts` skill keeps bonus kinds out of the withdrawable amount by default.

## Percentage of earnings

The other model: the referrer receives a share of what the referred account earns, for a limited time. Each commission is tied to one earning, so "once" and "take back" are again a matter of the reference.

PHP with PDO on PostgreSQL. `post_entry` is the ledger's posting function. On MySQL write `NOW() - INTERVAL ? DAY` for the time limit.

```php
<?php
declare(strict_types=1);

const REFERRAL_PLAN = [
    'rate_bps' => 1000,          // 10 percent, in basis points
    'days' => 365,               // commission is earned for this long after sign-up
    'cap_per_referred' => 50000, // most that one referred account can ever produce
];

/**
 * Call inside the transaction that posted the referred account's earning, with the
 * reference of that earning. Returns the commission posted, or 0.
 */
function post_referral_commission(PDO $db, int $referredId, int $earned, string $earningRef, array $plan = REFERRAL_PLAN): int
{
    $find = $db->prepare(
        "SELECT referrer_id FROM referrals
          WHERE referred_id = ? AND status <> 'blocked' AND created_at > now() - make_interval(days => ?) FOR UPDATE"
    );
    $find->execute([$referredId, $plan['days']]);
    $referrerId = $find->fetchColumn();
    if ($referrerId === false || $earned <= 0) {
        return 0;
    }

    $sum = $db->prepare("SELECT COALESCE(SUM(amount), 0) FROM referral_commissions WHERE referred_id = ? AND status = 'posted'");
    $sum->execute([$referredId]);
    $room = $plan['cap_per_referred'] - (int) $sum->fetchColumn();
    // Rounded down, once. Whole units only, and a commission of zero posts nothing.
    $commission = min(intdiv($earned * $plan['rate_bps'], 10000), $room);
    if ($commission <= 0) {
        return 0;
    }
    if (!post_entry($db, accountId: (int) $referrerId, amount: $commission, kind: 'referral_commission', ref: $earningRef)) {
        return 0;
    }
    $db->prepare('INSERT INTO referral_commissions (earning_ref, referred_id, referrer_id, amount) VALUES (?, ?, ?, ?)')
       ->execute([$earningRef, $referredId, (int) $referrerId, $commission]);
    return $commission;
}

/** Call inside the transaction that reverses the earning. Takes back what that earning paid, once. */
function reverse_referral_commission(PDO $db, string $earningRef): int
{
    $find = $db->prepare("SELECT referrer_id, amount FROM referral_commissions WHERE earning_ref = ? AND status = 'posted' FOR UPDATE");
    $find->execute([$earningRef]);
    $row = $find->fetch(PDO::FETCH_ASSOC);
    if ($row === false) {
        return 0;
    }
    $db->prepare("UPDATE referral_commissions SET status = 'reversed' WHERE earning_ref = ? AND status = 'posted'")
       ->execute([$earningRef]);
    post_entry($db, accountId: (int) $row['referrer_id'], amount: -(int) $row['amount'],
        kind: 'referral_commission_reversal', ref: $earningRef, allowDebt: true);
    return (int) $row['amount'];
}
```

- The commission is paid on top, from the app's own margin. It is not taken from the referred user's earning.
- The reversal takes back the stored amount, never a value computed again from today's rate.
- Pay commission only on kinds that are verified earnings. Never on bonuses, promo credits, purchases of credits, or on commission itself: each of those lets two accounts pump value in a circle.
- The lock on the referral row makes the cap exact when two earnings of one referred account arrive together.
- If two sources can issue the same earning reference, scope it the way the ledger does (`<source>:<id>`).

## Caps and budget

| Cap | Where | Default |
| --- | --- | --- |
| One reward per referred account | the ledger's unique key | always |
| Rewards per referrer per 30 days | `payReward`, under the referrer's lock | 20, above that a person looks |
| Commission per referred account | `post_referral_commission` | a fixed amount |
| Commission duration | `created_at` of the referral | 12 months |
| Program budget | a counter row updated with a condition, or an alert on the daily total | owner's decision |

A reward for the invited user (a welcome bonus) follows the same rule: post it when the referral is rewarded, under its own kind with the referred account's id as reference, not at sign-up. A bonus on both sides paid at sign-up pays a farmer twice.

## Without a ledger

The status row is then the only guard, so the balance may change only inside a guarded move, in the same transaction:

```sql
BEGIN;
UPDATE referrals SET status = 'rewarded', rewarded_at = now()
 WHERE referred_id = :referred AND status = 'qualified' AND reward_at <= now();   -- 0 rows: stop, pay nothing
UPDATE users SET balance = balance + :bonus WHERE id = :referrer;
COMMIT;
```

The take-back mirrors it: `rewarded` to `reversed`, and only when that changed one row, subtract. This pays once and takes back once. It leaves no record of why a balance changed, and the threshold has to be computed from the orders or conversions table. Build the ledger first if the program is more than a small spend-only bonus.
