# Measuring the inputs from the project's own data

Every number in the economy file is the app's own. This file shows how to read each one from the database, and what to do when the data does not exist yet. Do not fill a gap with a figure from an article or from another app: a wrong input gives a confident wrong verdict.

The queries assume two tables. Adapt the names to the project.

- `ledger (account_id, amount, kind, ref, created_at)`: one row per balance change, with kinds such as `offer`, `offer_reversal`, `signup_bonus`, `daily_bonus`, `promo`, `referral`, `payout`, `payout_refund`. This is the table the `build-ledger` skill creates.
- `offer_conversions (network, tx_id, user_id, payout_micros, coins, status, created_at, reversed_at)`: one row per conversion, with the payout in micro-dollars and a status of `credited` or `reversed`. The `add-offerwall` skill creates it.

If the project has only a balance column and no history, nothing here can be measured. Say so, enter the owner's planning figures, and recommend the ledger first.

The SQL is PostgreSQL. Differences for MySQL and SQLite are at the end.

## Revenue and the reversal rate

Group by the month of the credit, not the month the reversal arrived. Otherwise a growing app always looks better than it is.

```sql
SELECT date_trunc('month', created_at) AS month,
       SUM(payout_micros) / 1000000.0 AS revenue_usd,
       100.0 * SUM(CASE WHEN status = 'reversed' THEN payout_micros ELSE 0 END)
             / NULLIF(SUM(payout_micros), 0) AS reversal_rate_pct
FROM offer_conversions
GROUP BY 1
ORDER BY 1;
```

Recent months are not finished: their reversals are still arriving. Use months that are older than the longest delay in the arrival curve below. `volume.monthlyRevenueUsd` is `revenue_usd` of a typical recent month, and `reversals.ratePct` is `reversal_rate_pct` of the finished months.

Compare the revenue with the networks' own reports for the same month. A difference means conversions the app never recorded, or recorded twice. Find it before designing anything on top.

## The arrival curve

Of all reversed revenue, the part that was reversed within N days of the credit:

```sql
SELECT d.days,
       100.0 * SUM(CASE WHEN c.reversed_at <= c.created_at + d.days * INTERVAL '1 day' THEN c.payout_micros ELSE 0 END)
             / NULLIF(SUM(c.payout_micros), 0) AS pct
FROM offer_conversions c
CROSS JOIN (VALUES (7), (14), (30), (45), (60), (90)) AS d(days)
WHERE c.status = 'reversed'
  AND c.created_at < now() - INTERVAL '120 days'
GROUP BY d.days
ORDER BY d.days;
```

The rows are the `reversals.arrival` list. Only credits old enough to have had their full reversal window are counted; with a shorter cutoff the curve looks faster than it is. If the networks differ much, run it per network and size the hold for the slowest one that matters.

No reversal data yet: ask each network for its reversal window in writing, or check the network's documentation. Until then leave `arrival` out. The check then counts every reversal as arriving after the hold, which is the safe direction.

`reversals.lateRecoveryPct` is the part of late reversals that was collected after all, because the account still had a balance or earned again. Read it as what accounts below zero still owe, against everything that was reversed after the hold:

```sql
SELECT 100.0 * (1 - 1.0 * (SELECT COALESCE(SUM(-balance), 0) FROM accounts WHERE balance < 0)
                          / NULLIF(SUM(-l.amount), 0)) AS late_recovery_pct
FROM ledger l
JOIN offer_conversions c ON l.ref = c.network || ':' || c.tx_id
WHERE l.kind = 'offer_reversal'
  AND c.reversed_at > c.created_at + 30 * INTERVAL '1 day';
```

Replace 30 with the hold, and the join condition with the way the project builds the ledger reference. A result below 0 means 0. With no data, use 0.

## Bonuses and take-up

What each kind of bonus cost, and how many accounts received it:

```sql
SELECT date_trunc('month', created_at) AS month,
       kind,
       SUM(amount) AS coins,
       COUNT(*) AS entries,
       COUNT(DISTINCT account_id) AS accounts
FROM ledger
WHERE amount > 0
  AND kind NOT IN ('offer', 'payout_refund', 'spend_refund')
GROUP BY 1, 2
ORDER BY 1, 2;
```

Take-up is what was claimed over what could have been claimed:

- Sign-up bonus: `accounts` over the new users of that month.
- Daily bonus: `entries` over active users times the days in the month.
- Streak or monthly bonus: `accounts` over active users.
- Boost coverage: offer coins credited while the boost ran, over all offer coins of the month.
- Referral coverage: offer coins earned by accounts that have a referrer, over all offer coins.

Active users are accounts with at least one earning entry in the month. New users come from the users table.

```sql
SELECT date_trunc('month', created_at) AS month, COUNT(DISTINCT account_id) AS active_users
FROM ledger
WHERE kind = 'offer'
GROUP BY 1
ORDER BY 1;
```

Then look at who takes the bonuses. If most of the bonus coins go to accounts that never earned anything, the bonus pays for sign-ups, not for users:

```sql
SELECT COUNT(*) AS accounts,
       SUM(bonus_coins) AS bonus_coins
FROM (
  SELECT account_id,
         SUM(CASE WHEN kind = 'offer' THEN amount ELSE 0 END) AS offer_coins,
         SUM(CASE WHEN kind IN ('signup_bonus', 'daily_bonus', 'promo') THEN amount ELSE 0 END) AS bonus_coins
  FROM ledger
  GROUP BY account_id
) per_account
WHERE offer_coins = 0 AND bonus_coins > 0;
```

## Payouts, fees and redemption

```sql
SELECT COUNT(*) AS payouts,
       AVG(amount_cents) / 100.0 AS average_payout_usd,
       100.0 * SUM(fee_cents) / NULLIF(SUM(amount_cents), 0) AS fee_pct_of_amount
FROM payouts
WHERE status = 'paid'
  AND created_at >= now() - INTERVAL '90 days';
```

Take `feePct` and `feeFixedUsd` from the provider's price list or invoices. The query is a cross-check: the measured fee should match the price list at the average payout.

Redemption is the part of all standing credits that has left as money. Measure it over credits that are old enough to have been redeemed:

```sql
SELECT 100.0 * -SUM(CASE WHEN kind IN ('payout', 'payout_refund') THEN amount ELSE 0 END)
             / NULLIF(SUM(CASE WHEN kind NOT IN ('payout', 'payout_refund') THEN amount ELSE 0 END), 0) AS redemption_pct
FROM ledger
WHERE account_id IN (SELECT id FROM accounts WHERE created_at < now() - INTERVAL '180 days');
```

On a young app this figure is low only because users have not reached the minimum yet. Use 100 until at least six months of history exist. Whatever the figure, the check also computes the margin with every coin redeemed, and that one must hold.

## The liability and cash

```sql
SELECT SUM(balance) AS outstanding_coins,
       COUNT(*) AS accounts
FROM accounts
WHERE balance > 0;
```

`cash.reserveUsd` and `cash.receivablesUsd` come from the owner's bank and from the networks' statements, not from the database. `cash.networkPaymentDelayDays` is in each network's payment terms: count from the day of the conversion to the day the money arrives, not from the end of the month.

Track the liability over time. A total that grows faster than revenue means coins are being created faster than they are earned.

## The smallest payout

```sql
SELECT MIN(payout_micros) / 1000000.0 AS smallest_payout_usd,
       percentile_cont(0.01) WITHIN GROUP (ORDER BY payout_micros) / 1000000.0 AS first_percentile_usd
FROM offer_conversions
WHERE payout_micros > 0
  AND created_at >= now() - INTERVAL '90 days';
```

Use the smaller of this and the smallest payout the app intends to show.

## Plan against actuals

The economy file is the plan. Once a month, compare it with what happened:

1. Run the queries for the last finished month and write the results into a copy of the economy file, for example `economy.actuals.json`.
2. Run `node scripts/economy-check.mjs economy.actuals.json --json`. A non-zero exit code means the app as it ran last month breaks a rule. Send that to a person.
3. Compare `share.effectivePct` and `perDollarOfRevenue.margin` of the actuals with the plan. A gap of more than a few points has a cause: a bonus with higher take-up than planned, a boost that ran longer, a network with more reversals.
4. When the plan is wrong, change the plan file in a commit, with the check passing. Do not adjust numbers in an admin panel and leave the file behind.

The effective share can also be read directly, as a cross-check on the model:

```sql
SELECT 100.0 * (SUM(l.amount) / 1000.0)
             / NULLIF((SELECT SUM(payout_micros) / 1000000.0
                       FROM offer_conversions
                       WHERE status = 'credited'
                         AND created_at >= DATE '2025-01-01' AND created_at < DATE '2025-02-01'), 0) AS effective_share_pct
FROM ledger l
WHERE l.kind NOT IN ('payout', 'payout_refund')
  AND l.created_at >= DATE '2025-01-01' AND l.created_at < DATE '2025-02-01';
```

Replace 1000.0 with the redeem rate and the dates with the month. Reversal entries are negative, so they reduce the sum as they should.

## MySQL and SQLite

| PostgreSQL | MySQL 8 | SQLite |
| --- | --- | --- |
| `date_trunc('month', created_at)` | `DATE_FORMAT(created_at, '%Y-%m-01')` | `strftime('%Y-%m-01', created_at)` |
| `created_at + d.days * INTERVAL '1 day'` | `created_at + INTERVAL d.days DAY` | `datetime(created_at, '+' || d.days || ' days')` |
| `now() - INTERVAL '120 days'` | `NOW() - INTERVAL 120 DAY` | `datetime('now', '-120 days')` |
| `(VALUES (7), (14)) AS d(days)` | `(VALUES ROW(7), ROW(14)) AS d(days)` | `(SELECT 7 AS days UNION ALL SELECT 14) AS d` |
| `percentile_cont(...) WITHIN GROUP` | not available: sort and pick the row with `LIMIT 1 OFFSET n` | the same as MySQL |
| `DATE '2025-01-01'` | `DATE '2025-01-01'` | `'2025-01-01'` |
| `c.network \|\| ':' \|\| c.tx_id` | `CONCAT(c.network, ':', c.tx_id)` | the same as PostgreSQL |

SQLite compares timestamps as text, so they must be stored in one format, such as `YYYY-MM-DD HH:MM:SS` in UTC.
