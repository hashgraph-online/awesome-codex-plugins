# Limits, holds, withdrawable balance and destinations

The state machine pays each payout once. These rules decide whether a payout may exist at all. They run inside the request transaction, under the lock on the account row, so parallel requests cannot each pass a limit that only one of them fits under.

## What can be withdrawn

Not every unit in a balance is the same. Value the user earned (a completed offer, a sale, a commission) may leave as money once it can no longer be reversed. Value the app gave away (sign-up and promo bonuses, referral bonuses, goodwill adjustments) and value the user bought are for spending inside the app. If bought or promotional value could be withdrawn, every promo code would be a cash machine and every stolen card a way to move money out.

The withdrawable amount is computed from the ledger at request time, never stored:

```text
withdrawable = max(0, min(balance, matured earnings + reversals of earnings + payouts and their refunds))
```

- **Matured earnings:** entries of the earned kinds that are older than the hold period.
- **Reversals of earnings:** negative entries, counted at once whatever their age. A reversal of an earning that is still in its hold lowers the amount early. That errs on the safe side and corrects itself when the hold ends.
- **Payouts and their refunds:** `payout` entries are negative and `payout_refund` entries positive, so the sum is what has left for good or is on its way out.
- **`min(balance, ...)`:** spending lowers the balance but not the earned total, so spends use up bought and promotional value first, and the result never exceeds what the account holds. A balance in debt gives zero.

```js
export const POLICY = {
  currency: 'USD',
  unitsPerMinor: 1, // ledger units per cent: 1 when the ledger is in cents, 10 when 1,000 coins are a dollar
  minAmount: 500,
  maxAmount: 20_000,
  dailyAmount: 20_000,
  dailyCount: 3,
  holdSeconds: 14 * 86_400,
  reviewAbove: 10_000,
  destinationCooldownSeconds: 48 * 3600,
  maxAttempts: 5,
  idempotencyKeyLifetimeSeconds: 12 * 3600,
};

// The server's list of ledger kinds that count as earned. Every other kind is spend-only.
const EARNED = ['offer', 'sale', 'commission'];
const TAKEN = ['offer_reversal', 'sale_refund', 'commission_reversal', 'payout', 'payout_refund'];

export async function withdrawable(tx, accountId, balance, holdSeconds) {
  const sums = await tx.query(
    `SELECT COALESCE(SUM(CASE WHEN kind = ANY($2) AND created_at <= now() - make_interval(secs => $4)
                              THEN amount ELSE 0 END), 0) AS matured,
            COALESCE(SUM(CASE WHEN kind = ANY($3) THEN amount ELSE 0 END), 0) AS taken
       FROM ledger WHERE account_id = $1`,
    [accountId, EARNED, TAKEN, holdSeconds],
  );
  const { matured, taken } = sums.rows[0];
  return Math.max(0, Math.min(balance, Number(matured) + Number(taken)));
}
```

- The values in `POLICY` are placeholders. Each one is a decision of the owner, listed in the skill.
- The kinds are constants in server code. A new way to credit an account is spend-only until someone adds it to `EARNED` on purpose.
- `idempotencyKeyLifetimeSeconds` must be shorter than the time the provider honors a key. Check the provider's documentation.
- MySQL and SQLite have no `ANY($2)`: build an `IN (?, ?, ?)` list from the constants. `now() - make_interval(secs => $4)` becomes `NOW() - INTERVAL ? SECOND` in MySQL.
- With many entries per account, add an index on `(account_id, kind, created_at)`, or keep running totals per kind in a table that the posting function updates in the same transaction.

### The hold period

The hold is at least as long as the longest time in which an earning can still be taken back: the advertiser's or network's reversal window for offers, the refund and dispute window for sales. If sources differ much, give each earned kind its own hold and sum them separately. A hold that is shorter than the reversal window means the app pays out money it will have to return to someone else.

Show the user both numbers and the date the next part matures: "1,200 available to withdraw, 800 more on March 14". A balance that cannot be withdrawn with no explanation produces support tickets.

## The checks for one request

```js
// Returns the reason for a refusal, or null. Runs inside the request transaction, after
// the account row was locked.
export async function payoutRefusal(tx, account, destination, amount, policy = POLICY) {
  if (!Number.isSafeInteger(amount) || amount < policy.minAmount || amount > policy.maxAmount) return 'invalid_amount';
  if (amount % policy.unitsPerMinor !== 0) return 'invalid_amount';
  if (!account) return 'account_not_eligible';

  const eligible = await tx.query(
    `SELECT 1 FROM users
      WHERE id = $1 AND status = 'active' AND (payouts_blocked_until IS NULL OR payouts_blocked_until <= now())`,
    [account.id],
  );
  if (eligible.rowCount === 0) return 'account_not_eligible';
  if (!destination) return 'no_usable_destination';

  const day = await tx.query(
    `SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS requests FROM payouts
      WHERE account_id = $1 AND status NOT IN ('failed', 'rejected', 'canceled')
        AND created_at > now() - interval '24 hours'`,
    [account.id],
  );
  if (Number(day.rows[0].requests) >= policy.dailyCount) return 'daily_limit_reached';
  if (Number(day.rows[0].total) + amount > policy.dailyAmount) return 'daily_limit_reached';

  const available = await withdrawable(tx, account.id, Number(account.balance), policy.holdSeconds);
  if (amount > available) return 'not_withdrawable_yet';
  return null;
}
```

| Check | Why |
| --- | --- |
| Whole number, minimum, maximum per request | Below the minimum the provider's fee eats the payout. The maximum bounds the damage of any other mistake. A string, a fraction or a negative number never reaches the arithmetic. |
| Converts to whole minor units | The provider is sent cents. An amount that is not a whole number of them is refused, not rounded. |
| Account state | Banned, under review, or paused after a security change: no payout. A balance in debt fails the last check by itself. |
| Usable destination | One exists, belongs to this account and is past its cool-down. |
| Amount and count per 24 hours | A rolling window, summed over every payout that was not ended without paying. A stolen session can take one day's cap, not the balance. |
| Withdrawable | Earned and matured only, as above. |

- The amount is a whole number in the JSON body. Do not parse it out of a string, and never multiply a decimal by 100 in floating point to get cents.
- Refusals answer 4xx with a machine-readable reason and, where it helps, the number that would pass: the minimum, the withdrawable amount, the time the destination becomes usable.
- Stricter caps for new accounts (a lower daily amount in the first 30 days) are one more comparison against the account's age.
- Count refused attempts per account and per address too, and slow down a client that keeps trying. That is a rate limit, and it belongs to the project's existing one.
- If the provider charges a fee per payout, decide who pays it. The default is that the app pays and the user receives the amount shown. If the user pays, show the fee before the request and store both numbers on the payout row.

## When a payout needs a person

```js
// Returns why this request goes to manual review, or null to send it without one.
export async function reviewReason(tx, account, destination, amount, policy = POLICY) {
  if (amount >= policy.reviewAbove) return 'large_amount';
  const paidBefore = await tx.query(`SELECT 1 FROM payouts WHERE account_id = $1 AND status = 'paid' LIMIT 1`, [account.id]);
  if (paidBefore.rowCount === 0) return 'first_payout';
  const shared = await tx.query(
    'SELECT 1 FROM payout_destinations WHERE fingerprint = $1 AND account_id <> $2 LIMIT 1',
    [destination.fingerprint, account.id],
  );
  if (shared.rowCount > 0) return 'destination_shared';
  return null;
}
```

Other signals worth a review, when the project has them: a high share of reversed earnings, all earnings from one source in a short time, a risk score from sign-up checks (the `guard-signups` skill produces one). The funds are taken in review too, so the user cannot spend what they asked to withdraw. The queue itself is in [review-and-reconciliation.md](review-and-reconciliation.md).

## Changing where the money goes

Someone who gets into an account changes the payout destination first. The defenses are friction, delay and a notice.

```js
export async function changeDestination(pool, { accountId, method, details, fingerprint }, policy = POLICY) {
  return withTransaction(pool, async (tx) => {
    await tx.query('SELECT id FROM accounts WHERE id = $1 FOR UPDATE', [accountId]);
    await tx.query('UPDATE payout_destinations SET removed_at = now() WHERE account_id = $1 AND removed_at IS NULL', [
      accountId,
    ]);
    const added = await tx.query(
      `INSERT INTO payout_destinations (account_id, method, details, fingerprint, usable_from)
       VALUES ($1, $2, $3, $4, now() + make_interval(secs => $5))
       RETURNING id, usable_from`,
      [accountId, method, details, fingerprint, policy.destinationCooldownSeconds],
    );
    return added.rows[0];
  });
}
```

`withTransaction` is the ledger's helper, imported as in the state machine reference.

- **Ask for the password or second factor again** in the handler, even inside a valid session. A session cookie alone must not be enough to redirect money.
- **Cool-down.** The new destination cannot be used until `usable_from`. The default is 48 hours. Apply it to the first destination too, unless the hold period already covers a new account.
- **Notify the owner** at the contact address that was on file before the change, with a way to stop it. If the email address itself changed, write to the old one.
- **Other security changes count.** A password reset, a new email address or a removed second factor set `users.payouts_blocked_until` to now plus the same cool-down.
- **Payouts that already exist keep their destination.** The payout row holds a copy, so a change affects new requests only. A user who entered a wrong destination cancels the open request and makes a new one.
- **The fingerprint** is the destination in normalized form (a lowercased email, an account number without spaces) or a keyed hash of it. It finds one destination used by many accounts, which is a common sign of a farm.
- **Validate the format** on the server before storing. Where the provider offers a way to verify that a destination exists or belongs to the user, use it. Check the provider's documentation.
- Store what the provider needs and nothing more. Where the provider hands out a token for a bank account or card, store the token, not the number.
