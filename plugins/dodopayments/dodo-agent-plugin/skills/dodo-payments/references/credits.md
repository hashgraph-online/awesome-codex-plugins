# Credits

## Contents

- [When to use credits](#when-to-use-credits)
- [Concepts and SDK namespaces](#concepts-and-sdk-namespaces)
- [Create a credit entitlement](#create-a-credit-entitlement)
- [Attach credits to products](#attach-credits-to-products)
- [Deduct credits from metered usage](#deduct-credits-from-metered-usage)
- [Read balances and the ledger](#read-balances-and-the-ledger)
- [Grant or deduct credits manually](#grant-or-deduct-credits-manually)
- [Credit webhooks](#credit-webhooks)
- [Enforcing credits per request](#enforcing-credits-per-request)
- [Common mistakes](#common-mistakes)

## When to use credits

| Requirement | Use |
|---|---|
| Bill each measured unit in money | [usage-billing.md](usage-billing.md), no credits |
| Include an allowance in a plan, or sell top-up packs | Credits |
| Include an allowance, then charge beyond it | Credits with overage |

Credits are virtual units (tokens, calls, compute hours) or a fiat balance. They are not the real-money customer wallet in [customers.md](customers.md).

## Concepts and SDK namespaces

- A **credit entitlement** defines a credit: unit, precision, expiry, rollover and overage. A product can carry up to five.
- A **grant** issues credits to one customer: each subscription cycle, on a one-time purchase or add-on, through a manual ledger entry, or by rollover.
- Every change writes a **ledger entry** with `balance_before`, `balance_after`, `overage_before` and `overage_after`. The ledger is the audit trail.
- Credit amounts are **decimal strings**. Keep them as strings or use a decimal library, never JavaScript floats.

| Namespace | Holds |
|---|---|
| `client.creditEntitlements` | Credit definitions |
| `client.creditEntitlements.balances` | A customer's balance, ledger and grants |
| `client.customers.listCreditEntitlements(customerId)` | Every credit balance for one customer |
| `client.entitlements` | A different system: feature flags, files and license keys. Not credits |

## Create a credit entitlement

```typescript
const tokenCredits = await client.creditEntitlements.create({
  name: 'AI Token Credits',
  unit: 'token credit',
  precision: 0, // 0 to 10 decimal places, cannot change later
  expires_after_days: 30,
  rollover_enabled: true,
  rollover_percentage: 25,
  rollover_timeframe_count: 1, // count and interval go together
  rollover_timeframe_interval: 'Month', // Day, Week, Month or Year
  max_rollover_count: 2,
  overage_enabled: true,
  overage_behavior: 'invoice_at_billing',
  overage_limit: 100000,
  price_per_unit: '1', // decimal string in the smallest currency unit: 1 cent per credit
  currency: 'USD',
});
console.log(tokenCredits.id);
```

- Rollover runs before expiry; only the remainder expires.
- `overage_behavior` at the end of a cycle: `forgive_at_reset` (default, drop the deficit), `invoice_at_billing` (charge it), `carry_deficit` (keep the negative balance), `carry_deficit_auto_repay` (keep it and repay from new grants).
- `overage_enabled: true` requires `price_per_unit`, and a price requires `currency`. Without overage, deduction stops at zero.

## Attach credits to products

Attach the credit entitlement in the dashboard (**Products > Entitlements & Credits**) or with the current Create Product schema (use the MCP `search` tool; do not invent a payload).

- **Subscription product:** credits issued each billing period, with optional low-balance threshold, trial credits and proration on plan change.
- **One-time product or add-on:** one grant per purchase. This is how top-up packs work.

Checkout is a normal checkout session for that product; checkout never takes an ad hoc credit amount.

## Deduct credits from metered usage

1. Attach the credit entitlement and the meter to the same usage-based product.
2. On the meter, enable **Bill usage in Credits** and set `credit_entitlement_id` and `meter_units_per_credit` (usage units per one credit, for example 1000 tokens).
3. Ingest usage events as in [usage-billing.md](usage-billing.md).

A background worker deducts about once a minute, from the earliest-expiring grants first. `free_threshold` does not apply to credit-billed meters. Several meters can share one credit pool. A balance read right after ingesting may not include the deduction yet.

## Read balances and the ledger

```typescript
const balance = await client.creditEntitlements.balances.retrieve('cus_abc123', {
  credit_entitlement_id: 'cde_abc123',
});
console.log(balance.balance, balance.overage, balance.last_transaction_at);

for await (const entry of client.creditEntitlements.balances.listLedger('cus_abc123', {
  credit_entitlement_id: 'cde_abc123',
})) {
  console.log(entry.id, entry.amount, entry.balance_before, entry.balance_after);
}

const all = await client.customers.listCreditEntitlements('cus_abc123');
console.log(all.items);
```

## Grant or deduct credits manually

Use a ledger entry for promotions, support credits, migrations, or a fixed-cost debit. Derive `idempotency_key` from the business operation so a retry cannot apply it twice.

```typescript
const entry = await client.creditEntitlements.balances.createLedgerEntry('cus_abc123', {
  credit_entitlement_id: 'cde_abc123',
  amount: '500',
  entry_type: 'credit', // 'debit' to deduct
  idempotency_key: 'support-credit:case_42',
  reason: 'Support credit for case 42',
  metadata: { support_case_id: 'case_42' },
});
console.log(entry.balance_after);
```

- A repeated `idempotency_key` can return 409. Reconcile the original entry; do not retry with a new key.
- A debit can return 400 for an insufficient balance.
- Do not manually debit usage that a meter already deducts.

## Credit webhooks

Verify and deduplicate as in [webhooks.md](webhooks.md).

| Webhook | Action |
|---|---|
| `credit.added`, `credit.deducted`, `credit.manual_adjustment` | Refresh the cached balance; reconcile with the source purchase, job or support case |
| `credit.expired`, `credit.rolled_over`, `credit.rollover_forfeited` | Refresh the balance and account history |
| `credit.overage_charged`, `credit.overage_reset` | Reconcile overage with billing |
| `credit.balance_low` | Re-read the balance, notify the customer once, offer a top-up checkout session |

`credit.balance_low` has its own payload: `customer_id`, `subscription_id`, `credit_entitlement_id`, `credit_entitlement_name`, `available_balance`, `subscription_credits_amount`, `threshold_percent`, `threshold_amount`. The other credit webhooks carry the ledger entry.

## Enforcing credits per request

The balance is eventually consistent, so it is not a lock.

- **Fixed cost per request:** create an idempotent `debit` ledger entry before serving; a 400 means deny. On failure after the debit, issue a compensating `credit` with its own key.
- **Variable cost (AI tokens):** reserve an estimate in your own database, ingest the actual usage afterwards, and reconcile with webhooks.
- **Precision 0:** a coarse pre-check is `BigInt(balance.balance) >= required`. It is not a reservation.

## Common mistakes

- Using `client.entitlements.grants` for credits. Credits live under `client.creditEntitlements`.
- Wrong argument order: `balances.retrieve`, `listLedger`, `listGrants` and `createLedgerEntry` take the customer ID first and `credit_entitlement_id` in the params.
- `type` or `description` on a ledger entry. The fields are `entry_type` and `reason`.
- Reading `available_balance` from the balance API. It exists only on the `credit.balance_low` payload; the API returns `balance`.
- Choosing precision casually. It cannot change after creation.
- New idempotency keys on retry, or debiting usage that a meter also deducts.
