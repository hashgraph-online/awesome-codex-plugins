# Spent balances, entitlements and dependent rewards

Taking back a number is the easy part. This file covers the three cases where the value is no longer where it was put: the balance was spent, the purchase granted access instead of a balance, or the purchase caused a reward for someone else.

## A balance that is already spent

The reversal arrives and the account holds less than it was granted. There are two wrong reflexes. Clamping at zero forgives the difference without a record, and buy, spend, refund becomes a loop that prints value. Refusing to go below zero makes the reversal fail, the provider retries it for days, and it never applies.

The default rule is debt:

- The reversal always applies in full, and the balance may go below zero. In the ledger this is the one case that passes the debt flag.
- While the balance is below zero, spending and payouts are refused. With a conditional debit (`WHERE balance >= :amount`) that needs no extra code: nothing can be covered by a negative balance.
- New credits repay the debt first, because they are added to a negative number.
- The account is marked for review, by whatever means the project has.
- The user can see the negative balance and the entry that caused it.

Check every way value leaves the account, not only the spend endpoint:

| Way out | What must hold |
| --- | --- |
| Spending | The debit is conditional on the balance. |
| Payouts | The amount is capped by the current balance, whatever maturity or hold rules also apply. Payouts that are requested but not yet sent are cancelled through the payout code, so their funds return and offset the debt. |
| Transfers and gifts | Same conditional debit as spending. |
| Features paid by a plan, not by the balance | Decide with the user whether debt also suspends them. By default it does not. |

Accounts in debt, for the review queue and the report:

```sql
SELECT a.id, a.balance, MAX(l.created_at) AS last_reversal
  FROM accounts a
  JOIN ledger l ON l.account_id = a.id AND l.reverses_id IS NOT NULL AND l.amount < 0
 WHERE a.balance < 0
 GROUP BY a.id, a.balance
 ORDER BY a.balance
 LIMIT 100;
```

**Writing debt off.** If the user wants small debts forgiven, forgiveness is an entry of its own, posted after the reversal, never a smaller reversal:

```js
// Staff or a scheduled job forgives a debt. The reversal entry stays as it is.
export async function writeOffDebt(tx, { accountId, reversalEntryId, actor, note }) {
  const { rows } = await tx.query('SELECT balance FROM accounts WHERE id = $1 FOR UPDATE', [accountId]);
  const debt = -Number(rows[0].balance);
  if (debt <= 0) return 0;
  await postEntry(tx, {
    accountId,
    amount: debt,
    kind: 'debt_writeoff',
    ref: String(reversalEntryId),
    actor,
    note,
  });
  return debt;
}
```

The loss is then a line in the report with a name and a reason, and the reconciliation check still passes.

**Prevention.** A hold period before earned value can be withdrawn is what makes most reversals collectable: the value is still there when the reversal comes. That belongs to the payout code, and the `add-payouts` skill covers it.

## Entitlements and items

Not every purchase grants a balance. A plan, a lifetime license, an item, a seat: these are rows, and a reversal must end them.

The `grants` table in the asset file records what each order granted besides a balance, with `revoked_at` and a reason. Two rules make it work.

- **Access is checked at the time of use,** against the row: `WHERE account_id = :id AND item = :item AND revoked_at IS NULL`. A plan name copied into a session, a long-lived token or a client-side cache keeps working after the row is revoked. Keep such copies short-lived or check the row.
- **The state follows the money,** computed from the stored facts and not toggled by single events:

```js
// An order keeps its grants while it is not fully refunded and no dispute stands against it.
export async function syncEntitlements(tx, order) {
  const money = await tx.query('SELECT COALESCE(SUM(amount_cents), 0) AS refunded FROM refunds WHERE order_id = $1', [order.id]);
  const contested = await tx.query("SELECT 1 FROM disputes WHERE order_id = $1 AND status IN ('open', 'lost') LIMIT 1", [order.id]);
  const refundedInFull = BigInt(money.rows[0].refunded) >= BigInt(order.price_cents);
  if (refundedInFull || contested.rows.length > 0) {
    await tx.query(
      `UPDATE grants SET revoked_at = COALESCE(revoked_at, now()), revoke_reason = $2
        WHERE order_id = $1 AND (revoked_at IS NULL OR revoke_reason <> $2)`,
      [order.id, refundedInFull ? 'refund' : 'dispute'],
    );
  } else {
    await tx.query(
      "UPDATE grants SET revoked_at = NULL, revoke_reason = NULL WHERE order_id = $1 AND revoke_reason = 'dispute'",
      [order.id],
    );
  }
}
```

A partial refund leaves the grant in place by default: it is usually a price adjustment, and access cannot be cut into parts. A full refund or a dispute revokes. A won dispute restores what the dispute revoked, and nothing a refund revoked.

**Subscriptions.** Access must follow every event that ends or shortens it, not only the one that started it. Map the provider's events to these cases, and check the provider's documentation for their names and for the grace period it applies:

| What happened | Access |
| --- | --- |
| Cancelled by the user, period already paid | Until the end of the paid period |
| Expired, not renewed | Ends at the period end |
| Renewal payment failed | The grace period the user decided on, then ends |
| Refunded | Ends now |
| Disputed | Suspended now, restored if the dispute is won |

Store the period end the provider reports, and let the access check compare it with the current time. A subscription that is "active" in the app with a period end in the past is the bug to look for.

**Items that are gone.** A consumable that was used, a gift code that was shown, goods that were shipped cannot be revoked.

- A consumed item cannot be revoked. Revoke what is left of the order's grants and mark the account for review. By default no debt is created for it, because an item has no balance to go negative. The user may decide to charge its value in the app's currency instead, as a debt entry tied to the order.
- If delivery cannot be undone, the protection is before delivery: a hold, a limit for new accounts, or delivery only after the dispute window for high-value goods. Say this to the user. No reversal code can fix it afterwards.

## Dependent rewards

A purchase or a conversion often pays someone else too: a referral commission, cashback, loyalty points on the order, progress toward a tier. When the original is reversed, these go back as well, in the same transaction.

The convention that makes them findable: **a dependent reward is posted with the reference of the entry that caused it.** A commission on order `ord_81` is `kind = 'referral_commission', ref = 'ord_81'`. One order then pays one commission, and the reversal can look it up.

```js
// Rewards paid because of `original` keep the proportion of what is left of it.
// They were posted with the reference of the original, which is how they are found.
export async function settleDependents(tx, original) {
  const left = await outstanding(tx, original);
  const rewards = await tx.query(
    "SELECT id, account_id, amount, kind FROM ledger WHERE kind = 'referral_commission' AND ref = $1",
    [original.ref],
  );
  for (const reward of rewards.rows) {
    const { rows } = await tx.query(
      'SELECT COALESCE(SUM(amount), 0) AS net, COUNT(*) AS n FROM ledger WHERE reverses_id = $1',
      [reward.id],
    );
    const remains = Number(reward.amount) + Number(rows[0].net);
    const shouldRemain = Number((BigInt(reward.amount) * BigInt(left)) / BigInt(original.amount));
    const delta = shouldRemain - remains;
    if (delta === 0) continue;
    await postEntry(tx, {
      accountId: reward.account_id,
      amount: delta,
      kind: delta < 0 ? `${reward.kind}_reversal` : `${reward.kind}_restored`,
      ref: `${reward.id}:${Number(rows[0].n) + 1}`,
      reversesId: reward.id,
      allowDebt: delta < 0,
    });
  }
}
```

- The function compares what should remain with what remains and posts the difference. Half the order refunded takes half the commission. A dispute takes the rest. A won dispute gives it back.
- It posts nothing when nothing changed, so running it again is harmless. The reference counts the adjustments of one reward, which is stable because the order row is locked.
- List every dependent kind the project has. The example handles one. Repeat the query per kind, or select with `kind IN (...)`.
- The referrer's balance may go below zero too. That is the default, and it is a decision: the referrer did nothing wrong, and the user may prefer to absorb commissions that were already paid out.

**Rewards paid at a threshold.** A bonus that was paid once because a total crossed a line ("the invited user spent 20 dollars") has no single original. After a reversal, compute the verified total again, net of reversals. If it is below the line and the bonus was paid, take the bonus back under its own key (`referral_bonus_reversal`, with the invited account as the reference). The `add-referral-program` skill covers how such rewards qualify.

**Counters and status.** Tier progress, streaks and leaderboard points that were raised by the purchase are computed values. Derive them from net entries, reversals included, instead of incrementing a counter that nothing decrements.

**Holding dependent rewards.** A commission that becomes spendable only after the refund window of the purchase rarely needs to be taken back from an empty account. Recommend it when commissions can be withdrawn.
