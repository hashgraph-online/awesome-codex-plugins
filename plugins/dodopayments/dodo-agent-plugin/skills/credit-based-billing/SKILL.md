---
name: credit-based-billing
description: Complete guide for giving customers included, free, prepaid, promotional, or top-up credits using grants, balances, ledger deductions, rollover, expiry, alerts, and overage.
---

# Dodo Payments Credit-Based Billing

Use this skill to build prepaid or included-credit billing for tokens, API calls, compute, storage, or currency-denominated value, with auditable grants and deductions.

## When to use this skill

- Include a recurring credit allowance in a subscription.
- Sell one-time top-up packs or prepaid usage.
- Deduct credits from metered AI, API, or compute consumption.
- Grant promotional or support credits and record a reason.
- Configure expiry, rollover, low-balance alerts, or overage.
- Reconcile a customer's balance against an immutable ledger trail.

## Choose the billing model

| Requirement | Choose | Why |
|---|---|---|
| A fixed product with no tracked consumption | Plain subscription or one-time payment | No balance or usage pipeline is needed. |
| Bill each measured unit directly in money | Pure usage-based billing | A meter rates usage with `price_per_unit`; no prepaid pool is needed. |
| Include or pre-sell a consumable allowance | Credit-based billing | Grants create a balance that usage can consume. |
| Include credits, then charge beyond the allowance | Credits with overage | The credit pool is consumed first; configured overage handles the deficit. |
| Combine a base fee, included credits, and metered use | Usage-based product linked to a credit entitlement | The meter converts usage units into credit deductions. |

Credit-based and usage-based billing are complementary. Define and test meters with the `usage-based-billing` skill; this skill covers the credit side and the meter-to-credit link.

## Core concepts

### Credit entitlements and grants

A **credit entitlement** is the reusable definition of a credit unit and its lifecycle: name, unit, precision, expiry, rollover, and overage. A **grant** is an issuance of that credit to one customer. Grants can originate from:

- a subscription, reissued each billing cycle;
- a one-time product or add-on;
- a direct API ledger credit;
- rollover from an earlier grant.

Credits gate **how much** a customer can consume. The separate `entitlements` resource gates fulfillment such as feature access, files, or license delivery. Do not confuse these SDK namespaces:

```text
client.creditEntitlements             credit definitions and balances
client.creditEntitlements.balances    customer credit balances and ledger
client.entitlements                   feature/file/license entitlements
client.entitlements.files             entitlement files
client.entitlements.grants            fulfillment grants
```

Use `client.customers.listCreditEntitlements(customerID)` for the customer-level credit-entitlement view. Do not substitute `client.customers.listEntitlements(...)`, which reads the other entitlement system.

### Custom-unit and fiat credits

| Credit model | Representation | Example |
|---|---|---|
| Custom unit | Application-defined units | tokens, calls, compute hours, GB-hours |
| Fiat | Currency value | USD or EUR prepaid balance |

Custom-unit precision is configurable from `0` through `10`; the dashboard default is `2`. Precision cannot be changed after creation, so choose it before issuing grants. Use `0` for indivisible units such as whole requests. Use decimal precision only when fractional credits are meaningful.

Fiat examples use currency minor units: `5,000` credits represents USD 50 in the documented OpenAI example. Do not infer a universal fiat precision rule beyond the documented minor-unit model. All monetary amounts are in the currency's smallest unit (for example, cents for USD).

A product can carry up to **five** credit entitlements. Each can have independent issuance and lifecycle settings.

### Balance and ledger

The balance response includes `balance`, `overage`, `last_transaction_at`, identifiers, and timestamps. Treat credit amounts as decimal strings; do not pass them through binary floating-point arithmetic.

Every transaction has a ledger record with:

- `balance_before` and `balance_after`;
- `overage_before` and `overage_after`;
- amount and transaction type;
- source references and grant ID;
- description, metadata, and timestamp.

This ledger is the audit trail and provides transaction-level balance snapshots. There is no separately documented historical balance-snapshots endpoint.

## Initialize the TypeScript SDK

Keep API keys server-side. Dodo Payments keys use `dodo_test_...` and `dodo_live_...` prefixes.

```typescript
import DodoPayments from 'dodopayments';

const client = new DodoPayments({
  bearerToken: process.env['DODO_PAYMENTS_API_KEY'],
  environment: 'test_mode',
});
```

The SDK defaults to `live_mode` when `environment` is omitted. Use `test_mode` explicitly during development.

## Create and configure a credit entitlement

The confirmed TypeScript method is `client.creditEntitlements.create(...)`.

```typescript
import DodoPayments from 'dodopayments';

const client = new DodoPayments({
  bearerToken: process.env['DODO_PAYMENTS_API_KEY'],
  environment: 'test_mode',
});

const tokenCredits = await client.creditEntitlements.create({
  name: 'AI Token Credits',
  description: 'Credits consumed by model token usage',
  unit: 'token credit',
  precision: 0,
  expires_after_days: 30,
  rollover_enabled: true,
  rollover_percentage: 25,
  rollover_timeframe_count: 1,
  rollover_timeframe_interval: 'Month',
  max_rollover_count: 2,
  overage_enabled: true,
  overage_behavior: 'invoice_at_billing',
  overage_limit: 100000,
  price_per_unit: '1',
  currency: 'USD',
});

console.log(tokenCredits.id);
```

`price_per_unit` is a decimal string in the configured currency; monetary values use the currency's smallest unit. In this example, `'1'` is one cent per overage credit for USD.

### Confirmed create options

| Field | Required | Meaning and constraints |
|---|---:|---|
| `name` | Yes | Display name for the credit entitlement. |
| `unit` | Yes | Unit label such as `API Calls`, `Tokens`, or `Credits`. |
| `precision` | Yes | Decimal places, `0–10`; immutable after creation. |
| `description` | No | Optional description. |
| `expires_after_days` | No | Nullable number of days after issuance before expiry. |
| `rollover_enabled` | Yes | Enables or disables carry-forward. |
| `rollover_percentage` | No | Percentage carried forward, `0–100`. |
| `rollover_timeframe_count` | No | Number of rollover-validity intervals. |
| `rollover_timeframe_interval` | No | `Day`, `Week`, `Month`, or `Year`. |
| `max_rollover_count` | No | Maximum consecutive rollovers before forfeiture. |
| `overage_enabled` | Yes | Allows deficit handling after credits are exhausted. |
| `overage_behavior` | No | End-of-cycle behavior from the exact enum below. |
| `overage_limit` | No | Maximum allowed overage units. |
| `price_per_unit` | Conditional | Decimal string; required when overage is enabled. |
| `currency` | Conditional | Required when a price is present. Monetary values use the smallest currency unit. |

### Configure rollover

Rollover carries eligible unused credits into a new grant. Configure:

1. `rollover_enabled: true`.
2. `rollover_percentage` as the carry-forward cap from `0` through `100`.
3. Both `rollover_timeframe_count` and `rollover_timeframe_interval`; neither should be supplied alone.
4. `max_rollover_count` if credits may roll only a limited number of consecutive times.

Rollover is applied before expiry; only the remainder expires.

### Configure expiry

The API represents expiry as nullable `expires_after_days`. The dashboard offers 7, 30, 60, 90, custom days, or never; its default is 30 days, and custom expiry has a one-day minimum. Use `null` for no API-configured expiry only where the current API form permits it.

### Configure overage

| Exact `overage_behavior` value | Result at billing-cycle end |
|---|---|
| `forgive_at_reset` | Do not charge and do not preserve the deficit. This is the default. |
| `invoice_at_billing` | Charge the overage at billing, then reset it. |
| `carry_deficit` | Preserve the negative balance. |
| `carry_deficit_auto_repay` | Preserve the deficit and repay it from newly issued credits. |

When `overage_enabled` is true, `price_per_unit` is required; when a price is present, `currency` is required. Use `overage_limit` to cap allowed overage units.

When overage is disabled, Dodo stops deducting after the balance reaches zero. Meter processing is asynchronous, so this is not synchronous authorization for your application requests. Implement application-side enforcement when requests must be rejected immediately.

## Attach credits to products and subscriptions

Credits are attached to products as credit entitlements in the product creation or edit flow. Do not use `client.entitlements.grants` to attach or issue credit balances.

### Subscription product

In **Products → Create Product** or an existing product:

1. Choose subscription pricing.
2. Open **Entitlements & Credits** and attach an existing credit entitlement.
3. Set the credits issued each billing period.
4. Optionally set a low-balance notification amount, trial-credit amount, whether unused trial credits expire after trial, and credit proration for plan changes.
5. Keep the entitlement's default rollover, overage, and expiry rules or customize them for this product.

The customer receives a fresh grant each billing cycle.

### One-time product or add-on

Attach the credit entitlement to a single-payment product or add-on and configure the one-time amount. The purchase issues one grant. This is the supported shape for prepaid packs, top-ups, and promotional bundles.

### Usage-based product

Attach the credit entitlement to the same usage-based product as the meter. The confirmed meter attachment fields are:

| Field | Purpose |
|---|---|
| `meter_id` | Meter to aggregate usage. |
| `free_threshold` | Optional usage excluded before rating. |
| `credit_entitlement_id` | Credit pool consumed by this meter. |
| `meter_units_per_credit` | Usage units required to deduct one credit; required when `credit_entitlement_id` is set. |
| `price_per_unit` | Direct per-unit monetary price when using pure usage pricing; decimal string. |

Product attachment request shapes can evolve. Configure them in the dashboard or copy the current schema from the [Create Product API](https://docs.dodopayments.com/api-reference/products/post-products); do not invent an `entitlements`, `credits`, or `grants` payload.

### Start checkout for an attached product

Product purchase creates the customer grant; checkout does not accept an ad hoc credit amount.

```typescript
const session = await client.checkoutSessions.create({
  product_cart: [
    {
      product_id: 'pdt_ai_pro_plan',
      quantity: 1,
    },
  ],
  customer: { email: 'customer@example.com' },
  return_url: 'https://app.example.com/billing/success',
});

console.log(session);
```

Use `checkoutSessions.create`, not the deprecated `payments.create` or `subscriptions.create` methods.

## Discover a customer's credit entitlements

Use the customer resource when the application needs to discover all credit entitlements associated with a customer:

```typescript
const customerCredits = await client.customers.listCreditEntitlements(
  'cus_TV52uJWWXt2yIoBBxpjaa',
);

console.log(customerCredits);
```

Use the balance resource below when the credit entitlement ID is already known and an exact balance is required.

## Read a customer's balance

The confirmed method takes the customer ID first and the credit entitlement ID inside the options object:

```typescript
const customerCreditBalance = await client.creditEntitlements.balances.retrieve(
  'cus_TV52uJWWXt2yIoBBxpjaa',
  { credit_entitlement_id: 'cde_ztxm5XJsKxWucRWA3rjdM' },
);

console.log({
  balance: customerCreditBalance.balance,
  overage: customerCreditBalance.overage,
  lastTransactionAt: customerCreditBalance.last_transaction_at,
});
```

`balance` and `overage` are decimal strings in the entitlement's credit unit. They are not currency amounts unless the entitlement itself represents fiat value.

## Grant credits manually

Manual credits are appropriate for promotions, migrations, refunds implemented as credit, and support gestures. Use a stable idempotency key derived from the business operation so a retry cannot grant twice.

```typescript
async function grantSupportCredits(
  customerId: string,
  creditEntitlementId: string,
  supportCaseId: string,
): Promise<string> {
  const entry = await client.creditEntitlements.balances.createLedgerEntry(
    customerId,
    {
      credit_entitlement_id: creditEntitlementId,
      amount: '500',
      entry_type: 'credit',
      expires_at: '2027-01-31T23:59:59Z',
      idempotency_key: `support-credit:${supportCaseId}`,
      reason: `Support gesture for case ${supportCaseId}`,
      metadata: { support_case_id: supportCaseId },
    },
  );

  return entry.id;
}
```

`amount` is a decimal string backed by `NUMERIC(38,28)`; its integer part must be below `10^10`. `expires_at` applies to credits. Keep the amount within the entitlement's configured precision.

If the same `idempotency_key` already exists, the API can return `409`. Treat that as a signal to reconcile the original operation, not as permission to generate a new key and retry the grant.

## Deduct credits manually

Use the same method with `entry_type: 'debit'`. Debits consume the oldest grants first (FIFO) and can return `400` when the balance is insufficient.

```typescript
async function deductJobCredits(
  customerId: string,
  creditEntitlementId: string,
  jobId: string,
  amount: string,
): Promise<{ balanceAfter: string; overageAfter: string }> {
  const entry = await client.creditEntitlements.balances.createLedgerEntry(
    customerId,
    {
      credit_entitlement_id: creditEntitlementId,
      amount,
      entry_type: 'debit',
      idempotency_key: `job-debit:${jobId}`,
      reason: `Credit deduction for job ${jobId}`,
      metadata: { job_id: jobId },
    },
  );

  return {
    balanceAfter: entry.balance_after,
    overageAfter: entry.overage_after,
  };
}
```

Do not manually debit usage that is also connected to automatic meter-to-credit deduction; that charges the same consumption twice.

## Read the ledger for an audit trail

The SDK returns an auto-paginating iterable:

```typescript
for await (const entry of client.creditEntitlements.balances.listLedger(
  'cus_TV52uJWWXt2yIoBBxpjaa',
  { credit_entitlement_id: 'cde_ztxm5XJsKxWucRWA3rjdM' },
)) {
  console.log({
    id: entry.id,
    amount: entry.amount,
    balanceBefore: entry.balance_before,
    balanceAfter: entry.balance_after,
    overageBefore: entry.overage_before,
    overageAfter: entry.overage_after,
    createdAt: entry.created_at,
  });
}
```

Persist the Dodo ledger entry ID with internal order, support-case, or job IDs. Reconciliation should compare ledger entries and source references rather than overwrite history from a cached balance.

## Configure automatic meter-to-credit deduction

1. Attach a credit entitlement to the usage-based product.
2. Add the meter to the same product.
3. Enable **Bill usage in Credits** for that meter.
4. Set `credit_entitlement_id` and `meter_units_per_credit`.
5. Optionally set `free_threshold`; usage under it is excluded.
6. Ingest events whose case-sensitive `event_name` matches the meter.

A background worker processes new usage approximately every minute, aggregates it according to the meter, converts meter units using `meter_units_per_credit`, and consumes the oldest non-expired grants first (FIFO). Multiple meters can consume one shared credit pool at different conversion rates.

This delay is material: an accepted usage event does not imply that a balance read immediately afterward includes its deduction.

Use the `usage-based-billing` skill to create the meter, choose `count`, `sum`, `max`, or `last`, define its filter, and validate event batching and metadata.

## End-to-end AI token example

Assume the dashboard/API configuration already has:

- a custom-unit entitlement named `AI Token Credits`, precision `0`;
- a subscription product that issues credits each cycle;
- a `sum` meter whose case-sensitive event name is `ai.tokens` and key is `tokens`;
- that meter linked through `credit_entitlement_id` and `meter_units_per_credit`;
- a one-time product `pdt_ai_token_topup` with credits attached.

The following server-side script records actual model usage, reads the credit balance, and creates a top-up checkout when your verified low-balance webhook flow prompts the customer:

```typescript
import DodoPayments from 'dodopayments';

const client = new DodoPayments({
  bearerToken: process.env['DODO_PAYMENTS_API_KEY'],
  environment: 'test_mode',
});

async function recordTokenUsage(
  customerId: string,
  generationId: string,
  model: string,
  promptTokens: number,
  completionTokens: number,
): Promise<number> {
  const tokens = promptTokens + completionTokens;
  const response = await client.usageEvents.ingest({
    events: [
      {
        event_id: `generation:${generationId}`,
        customer_id: customerId,
        event_name: 'ai.tokens',
        timestamp: new Date().toISOString(),
        metadata: {
          tokens,
          prompt_tokens: promptTokens,
          completion_tokens: completionTokens,
          model,
        },
      },
    ],
  });

  return response.ingested_count;
}

async function readTokenBalance(
  customerId: string,
  creditEntitlementId: string,
): Promise<string> {
  const response = await client.creditEntitlements.balances.retrieve(
    customerId,
    { credit_entitlement_id: creditEntitlementId },
  );
  return response.balance;
}

async function createTopUpCheckout(customerEmail: string) {
  return client.checkoutSessions.create({
    product_cart: [
      { product_id: 'pdt_ai_token_topup', quantity: 1 },
    ],
    customer: { email: customerEmail },
    return_url: 'https://app.example.com/credits',
  });
}

async function main(): Promise<void> {
  const customerId = 'cus_8VbC6JDZzPEqfBPUdpj0K';
  const creditEntitlementId = 'cde_ztxm5XJsKxWucRWA3rjdM';

  const ingested = await recordTokenUsage(
    customerId,
    'gen_01JZAIEXAMPLE',
    'example-model',
    1800,
    700,
  );
  console.log({ ingested });

  // Meter deduction is asynchronous; this read may still show the prior balance.
  const balance = await readTokenBalance(customerId, creditEntitlementId);
  console.log({ balance });

  // Call this after a verified credit.balance_low event and customer action.
  const topUp = await createTopUpCheckout('customer@example.com');
  console.log(topUp);
}

main().catch((error: unknown) => {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
});
```

The lifecycle is:

1. The model returns actual prompt and completion token counts.
2. The app ingests one uniquely identified `ai.tokens` event.
3. The meter aggregates the `tokens` metadata value.
4. The worker converts units into credits and deducts FIFO from non-expired grants.
5. Dodo emits `credit.deducted`; when configured threshold conditions are met, it emits `credit.balance_low`.
6. The app notifies the customer and offers checkout for the attached top-up product.

Do not poll every minute to synthesize your own threshold event. Use the verified webhook and keep polling only for user-interface freshness.

## Handle credit webhooks

Webhook signature verification, raw-body handling, retries, and event deduplication are covered in the `webhook-integration` skill. Verify with `client.webhooks.unwrap()` before dispatching any event; never trust a parsed, unverified body.

All credit events except `credit.balance_low` use the full ledger payload.

| Exact event | Application action |
|---|---|
| `credit.added` | Refresh cached balance; correlate the grant or purchase and ledger entry. |
| `credit.deducted` | Refresh cached balance and usage display; reconcile the source usage/job. |
| `credit.expired` | Refresh balance; notify only if your product policy promises expiry notices. |
| `credit.rolled_over` | Refresh balance and expose the new rollover grant in account history. |
| `credit.rollover_forfeited` | Refresh balance and explain forfeiture according to the configured rollover limit. |
| `credit.overage_charged` | Reconcile the overage charge with billing and customer-visible history. |
| `credit.overage_reset` | Clear cached overage state after confirming the ledger payload. |
| `credit.manual_adjustment` | Reconcile the adjustment with its internal support/admin operation. |
| `credit.balance_low` | Deduplicate, refresh the authoritative balance, notify the customer, and offer upgrade or top-up. |

### Low-balance payload

`credit.balance_low` has a dedicated payload:

```json
{
  "business_id": "bus_H4ekzPSlcg",
  "type": "credit.balance_low",
  "timestamp": "2025-08-04T06:15:00.000000Z",
  "data": {
    "payload_type": "CreditBalanceLow",
    "customer_id": "cus_8VbC6JDZzPEqfBPUdpj0K",
    "subscription_id": "sub_7EeHq2ewQuadropD2ra",
    "credit_entitlement_id": "cent_9xY2bKwQn5MjRpL8d",
    "credit_entitlement_name": "API Credits",
    "available_balance": "15",
    "subscription_credits_amount": "100",
    "threshold_percent": 20,
    "threshold_amount": "20"
  }
}
```

### Low-balance notification flow

1. Verify the raw webhook and deduplicate by `webhook-id` as described in `webhook-integration`.
2. Confirm `type === 'credit.balance_low'` and validate the dedicated payload.
3. Map `customer_id` to the authenticated application account; do not accept a customer ID supplied by a browser.
4. Read the current balance with `balances.retrieve(...)` because another grant or deduction may have occurred since emission.
5. If the balance is still below your customer-notification policy, enqueue one notification keyed by webhook ID or threshold occurrence.
6. Link to a one-time top-up checkout or plan-upgrade flow.
7. Record notification delivery separately from the Dodo ledger; never manufacture a ledger entry for an email.

## Enforce credits safely

### Best-effort balance gate

For a precision-`0` entitlement, a server can perform a coarse pre-check with integer-safe parsing:

```typescript
async function hasAtLeastWholeCredits(
  customerId: string,
  creditEntitlementId: string,
  required: bigint,
): Promise<boolean> {
  const response = await client.creditEntitlements.balances.retrieve(
    customerId,
    { credit_entitlement_id: creditEntitlementId },
  );

  return BigInt(response.balance) >= required;
}
```

Use this only for precision `0`. For fractional credits, use an arbitrary-precision decimal implementation that preserves the entitlement's configured precision.

This read is not a reservation. Two concurrent requests can both observe enough balance, and automatic meter deductions may not yet be reflected.

### Strict request enforcement

Choose one of these patterns:

- **Predictable fixed cost:** create an idempotent manual debit before serving. Treat an insufficient-balance `400` as denial. If work fails after debit, issue a separately idempotent compensating credit with a linked reason. Do not also meter the same usage.
- **Variable cost such as AI tokens:** reserve estimated capacity atomically in your own datastore, enforce per-customer concurrency, ingest actual usage afterward, and reconcile local reservations with Dodo webhooks and ledger entries.
- **Overage product:** authorize against the product's overage policy and your own risk limit, not merely `balance > 0`.

Return an application-level payment/credit-required response with a top-up or upgrade path when authorization fails. Do not expose Dodo API errors or secrets to the client.

### Race conditions to avoid

- **Check then act:** a remote balance read followed by work is not atomic.
- **Immediate post-event read:** the meter worker may not have processed the event.
- **Parallel workers:** multiple jobs can consume the same apparent balance without a local reservation or atomic debit.
- **Retry with new IDs:** changing `event_id` or `idempotency_key` after a timeout can duplicate usage or adjustments.
- **Cache as authority:** webhook-maintained balances are useful for display, not strict authorization.
- **Mixed deduction paths:** automatic meter deduction plus manual debit double-counts consumption.

## Common mistakes

1. **Confusing two resources.** `creditEntitlements` and `entitlements` are different. Credit balances do not live under `client.entitlements.grants`.
2. **Calling invented balance methods.** Use `balances.retrieve(customerId, { credit_entitlement_id })`, not `balances.get(creditId, customerId)`.
3. **Using the wrong ledger argument order.** `createLedgerEntry` receives `customerId` first; `credit_entitlement_id` belongs in the request object.
4. **Using `type` or `description` for adjustments.** Confirmed fields are `entry_type` and `reason`.
5. **Getting the grants argument order wrong.** `creditEntitlements.balances.listGrants(customerID, params)` does exist and takes the customer id first, with the entitlement supplied in the params object. It returns a paginated page, so read `.items` rather than treating the result as an array. Use `customers.listCreditEntitlements(customerID)` when you want the customer-level summary instead.
6. **Treating `available_balance` as the balance API field.** The confirmed balance response uses `balance` and `overage`; `available_balance` belongs to the dedicated low-balance webhook payload.
7. **Choosing precision casually.** It supports `0–10` for custom units and cannot be changed after creation.
8. **Using JavaScript floating point for credits.** API amounts are decimal strings. Preserve them as strings or use decimal arithmetic.
9. **Exceeding adjustment bounds.** Ledger amounts map to `NUMERIC(38,28)`, and the integer part must be below `10^10`.
10. **Misstating monetary units.** Currency amounts use the smallest currency unit. Do not label cents as dollars.
11. **Using unstable idempotency keys.** A timestamp or random key on every retry defeats deduplication. Derive the key from the immutable business operation.
12. **Retrying an insufficient debit blindly.** Manual debits can return `400` for insufficient balance; route the customer to top-up or your overage policy.
13. **Assuming event ingestion is synchronous deduction.** Meter-to-credit processing occurs approximately every minute.
14. **Using Dodo's balance as a per-request lock.** The docs explicitly warn against strict authorization from asynchronously reported meter balances.
15. **Mismatching meter names.** Usage `event_name` matching is case-sensitive.
16. **Sending duplicate IDs within one batch.** Duplicate `event_id` values in the same ingestion request reject the entire request. Previously ingested IDs are ignored on retry.
17. **Inventing a deduplication window.** Current docs require unique event IDs but do not publish a retention duration.
18. **Getting conversion backward.** `meter_units_per_credit` is usage units required for one credit, and is required when `credit_entitlement_id` is set.
19. **Ignoring the free threshold.** Usage under `free_threshold` is excluded before credit deduction.
20. **Supplying one rollover timeframe field.** `rollover_timeframe_count` and `rollover_timeframe_interval` must be supplied together.
21. **Using the wrong rollover enum case.** Confirmed values are `Day`, `Week`, `Month`, and `Year`.
22. **Assuming expiry happens before rollover.** Rollover is applied first; only the remainder expires.
23. **Inventing overage enum values.** Use only `forgive_at_reset`, `invoice_at_billing`, `carry_deficit`, or `carry_deficit_auto_repay`.
24. **Omitting overage pricing dependencies.** Enabled overage requires `price_per_unit`; a price requires `currency`.
25. **Attaching too many credits.** The current product limit is five credit entitlements.
26. **Assuming checkout grants arbitrary credits.** Credits must already be attached to the purchased product or add-on.
27. **Handling only the common webhooks.** Include `credit.overage_reset` and `credit.rollover_forfeited`, not only added, deducted, and low-balance events.
28. **Parsing an unverified webhook.** Verify the raw body with `client.webhooks.unwrap()` as covered in `webhook-integration`; never hand-roll HMAC or trust re-serialized JSON.
29. **Inventing historical snapshot APIs.** Use ledger `balance_before` and `balance_after` for transaction-level history.
30. **Using deprecated purchase methods.** New checkout flows use `client.checkoutSessions.create(...)`, not `payments.create(...)` or `subscriptions.create(...)`.
31. **Using the wrong host or key format.** Valid hosts are `https://test.dodopayments.com` and `https://live.dodopayments.com`; keys start with `dodo_test_` or `dodo_live_`.

## Resources

- [Credit-Based Billing Guide](https://docs.dodopayments.com/features/credit-based-billing)
- [Create Credit Entitlement API](https://docs.dodopayments.com/api-reference/credit-entitlements/create-credit-entitlement)
- [Get Customer Balance API](https://docs.dodopayments.com/api-reference/credit-entitlements/get-customer-balance)
- [Create Ledger Entry API](https://docs.dodopayments.com/api-reference/credit-entitlements/create-ledger-entry)
- [List Customer Ledger API](https://docs.dodopayments.com/api-reference/credit-entitlements/list-customer-ledger)
- [Credit Webhook Reference](https://docs.dodopayments.com/developer-resources/webhooks/intents/credit)
- [Meter Guide](https://docs.dodopayments.com/features/usage-based-billing/meters)
- [Usage Event Ingestion API](https://docs.dodopayments.com/api-reference/usage-events/ingest-events)
- [Create Product API](https://docs.dodopayments.com/api-reference/products/post-products)
