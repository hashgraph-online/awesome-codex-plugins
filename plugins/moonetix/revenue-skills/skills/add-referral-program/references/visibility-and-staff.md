# What the referrer sees, what staff see

A referral program that pays late and takes rewards back needs to explain itself. The referrer must be able to see where each referral stands and why nothing was paid yet. Staff must be able to see which referrers are bringing people and which are bringing copies of themselves.

## The referrer's view

One endpoint returns the code, the totals and the list. Everything is read from the server's tables at request time.

```json
{
  "code": "7KQ2M9XA",
  "link": "https://app.example/?ref=7KQ2M9XA",
  "totals": { "waiting": 3, "on_the_way": 1, "rewarded": 4, "earned": 2000 },
  "referrals": [
    { "joined": "2026-03-02", "state": "on_the_way", "reward_on": "2026-03-21" },
    { "joined": "2026-02-18", "state": "rewarded", "reward": 500 },
    { "joined": "2026-02-11", "state": "waiting" },
    { "joined": "2026-01-30", "state": "taken_back", "reward": 0 }
  ]
}
```

```sql
SELECT r.status, r.created_at, r.reward_at, COALESCE(l.amount, 0) AS reward
  FROM referrals r
  LEFT JOIN ledger l ON l.kind = 'referral' AND l.ref = CAST(r.referred_id AS TEXT)
 WHERE r.referrer_id = $1
 ORDER BY r.created_at DESC
 LIMIT 50;

SELECT COALESCE(SUM(amount), 0) AS earned
  FROM ledger
 WHERE account_id = $1
   AND kind IN ('referral', 'referral_reversal', 'referral_commission', 'referral_commission_reversal');
```

On MySQL write `CAST(r.referred_id AS CHAR)`.

| Status in the database | Shown as | Text for the user |
| --- | --- | --- |
| `pending` | waiting | "Signed up. The reward comes after their first purchase." State the real condition. |
| `qualified` | on the way | "Qualified. Your reward arrives on March 21." The date is `reward_at`. |
| `rewarded` | rewarded | The amount and the date. |
| `reversed` | taken back | "The purchase was refunded, so the reward was taken back." |
| `blocked` | waiting, or not eligible | No reason. See below. |

- **State the rules where the code is shared:** what the friend has to do, how long the wait is, the cap, and that a refund takes the reward back. A reward that arrives late is fine when it was announced. A reward that silently never arrives is a support ticket.
- **Show the pending state.** Most complaints about referral programs are "my friend signed up and I got nothing". The list answers that before it is asked.
- **Protect the referred person.** Show the join date and the state. Do not show the email address, the full name, what was bought or how much was earned. A first name or a masked email is enough to recognize a friend.
- **Do not explain a block.** Showing "same device" tells a farmer what to change. A blocked referral is shown as waiting, or as not eligible, with a link to support.
- **The balance changes only through the ledger,** so the history page already shows the reward and a take-back as two lines. The take-back line says which referral it belongs to.
- **Debt after a take-back** (the reward was spent before the refund came): show the negative balance and the reason in words.

## The staff view

Start from the referrer, not from the single referral. Fraud in referral programs is a pattern across one person's invitations.

```sql
-- Referrers ordered by how much of what they bring ends up blocked or reversed.
SELECT r.referrer_id,
       COUNT(*) AS referred,
       SUM(CASE WHEN r.status = 'rewarded' THEN 1 ELSE 0 END) AS rewarded,
       SUM(CASE WHEN r.status = 'reversed' THEN 1 ELSE 0 END) AS reversed,
       SUM(CASE WHEN r.status = 'blocked' THEN 1 ELSE 0 END) AS blocked,
       SUM(CASE WHEN r.created_at > now() - interval '24 hours' THEN 1 ELSE 0 END) AS joined_last_day
  FROM referrals r
 GROUP BY r.referrer_id
HAVING COUNT(*) >= 5
 ORDER BY SUM(CASE WHEN r.status IN ('reversed', 'blocked') THEN 1 ELSE 0 END) * 1.0 / COUNT(*) DESC, COUNT(*) DESC
 LIMIT 100;

-- Inside one referrer's invitations: values that several referred accounts share.
SELECT s.kind, s.value, COUNT(DISTINCT s.account_id) AS accounts
  FROM referrals r
  JOIN account_signals s ON s.account_id = r.referred_id
 WHERE r.referrer_id = $1
 GROUP BY s.kind, s.value
HAVING COUNT(DISTINCT s.account_id) > 1
 ORDER BY accounts DESC;
```

What to put on the screen for one referrer:

- every referral with status, dates, block reason and the staff member who last decided on it,
- the referred accounts' verified activity next to the threshold. A row of accounts that each did exactly the minimum and then went silent is the classic farm,
- shared signals between the referrer and the referred accounts, and among the referred accounts,
- joins per day, to see bursts,
- what happened to the rewards: spent in the app, or withdrawn at once,
- the reversal rate of the referred accounts' purchases or conversions.

### Staff decisions

Each one is a guarded change of status with the staff member's identity from the session and a written reason. Node, with `settleReferral` and `takeBackReward` from [rewards-and-reversals.md](rewards-and-reversals.md):

```js
import { withTransaction } from './ledger.mjs';
import { settleReferral, takeBackReward } from './referral-rewards.mjs';

function decision(staff, reason) {
  if (typeof reason !== 'string' || reason.trim().length < 5) throw new TypeError('a reason is required');
  return [`staff:${staff.id}`, reason.trim()];
}

async function notOwn(tx, referredId, staff) {
  const own = await tx.query(
    'SELECT 1 FROM referrals WHERE referred_id = $1 AND (referred_id = $2 OR referrer_id = $2)',
    [referredId, staff.accountId],
  );
  if (own.rowCount > 0) throw new Error('staff cannot decide on a referral of their own account');
}

// Holds a referral that has not paid yet.
export async function blockReferral(pool, referredId, staff, reason) {
  const [actor, why] = decision(staff, reason);
  return withTransaction(pool, async (tx) => {
    await notOwn(tx, referredId, staff);
    const held = await tx.query(
      `UPDATE referrals SET status = 'blocked', blocked_reason = $2, decided_by = $3
        WHERE referred_id = $1 AND status IN ('pending', 'qualified')`,
      [referredId, why, actor],
    );
    return held.rowCount === 1;
  });
}

// Releases a held referral and evaluates it again. It still has to qualify and wait.
export async function releaseReferral(pool, referredId, staff, reason, program) {
  const [actor] = decision(staff, reason);
  return withTransaction(pool, async (tx) => {
    await notOwn(tx, referredId, staff);
    const freed = await tx.query(
      `UPDATE referrals SET status = 'pending', blocked_reason = NULL, decided_by = $2, qualified_at = NULL, reward_at = NULL
        WHERE referred_id = $1 AND status = 'blocked'`,
      [referredId, actor],
    );
    return freed.rowCount === 1 ? settleReferral(tx, referredId, program) : null;
  });
}

// Takes back a reward that was already paid, for example after a farm was found.
export async function revokeReward(pool, referredId, staff, reason) {
  const [actor, why] = decision(staff, reason);
  return withTransaction(pool, async (tx) => {
    await notOwn(tx, referredId, staff);
    const found = await tx.query('SELECT referrer_id FROM referrals WHERE referred_id = $1 FOR UPDATE', [referredId]);
    if (found.rowCount === 0) return null;
    const result = await takeBackReward(tx, referredId, found.rows[0].referrer_id, actor);
    if (result) await tx.query('UPDATE referrals SET blocked_reason = $2, decided_by = $3 WHERE referred_id = $1', [referredId, why, actor]);
    return result;
  });
}
```

- These are the only staff actions. There is no "grant referral bonus" button: a goodwill credit is a manual adjustment in the ledger, with its own kind, and does not pretend to be a referral.
- Removing a referrer from the program is a flag on the account that `payReward` reads (the `users.status` check). It does not delete referral rows.
- Staff permissions for these actions are named and separate from read access. Write each decision to the audit log.

## Reconcile

Run on a schedule. Any row is an alert. On MySQL write `CAST(... AS CHAR)` and `NOW() - INTERVAL 6 HOUR`.

```sql
-- Every rewarded or reversed referral has its entries, and no other referral has any.
SELECT r.referred_id, r.status
  FROM referrals r
  LEFT JOIN ledger l ON l.ref = CAST(r.referred_id AS TEXT) AND l.kind IN ('referral', 'referral_reversal')
 GROUP BY r.referred_id, r.status
HAVING SUM(CASE WHEN l.kind = 'referral' THEN 1 ELSE 0 END)
       <> CASE WHEN r.status IN ('rewarded', 'reversed') THEN 1 ELSE 0 END
    OR SUM(CASE WHEN l.kind = 'referral_reversal' THEN 1 ELSE 0 END)
       <> CASE WHEN r.status = 'reversed' THEN 1 ELSE 0 END;

-- A referral entry in the ledger with no referral row behind it.
SELECT l.id, l.kind, l.ref
  FROM ledger l
  LEFT JOIN referrals r ON CAST(r.referred_id AS TEXT) = l.ref
 WHERE l.kind IN ('referral', 'referral_reversal') AND r.referred_id IS NULL;

-- Qualified referrals long past their date: the job is not running.
SELECT referred_id, reward_at
  FROM referrals
 WHERE status = 'qualified' AND reward_at < now() - interval '6 hours';
```

Watch two numbers over time as well: rewards posted per day against the program budget, and the share of rewards that end up reversed. A rising reversal share means the hold is shorter than the real reversal window.
