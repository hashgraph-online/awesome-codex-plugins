---
name: usage-based-billing
description: Dodo Payments usage-based billing that charges per measured unit, covering meters, usage event ingestion by event_name, aggregation, free thresholds, price_per_unit, and metered subscriptions. Use when billing per API call, AI token, storage, or bandwidth, sending usage events, or adding metered pricing to a plan; use credit-based-billing for prepaid credit pools.
---

# Dodo Payments Usage-Based Billing

**Reference: [docs.dodopayments.com/features/usage-based-billing](https://docs.dodopayments.com/features/usage-based-billing/introduction)**

Charge customers for what they actually use—API calls, storage, AI tokens, or any metric you define.

---

## When to use this skill

- You need to bill customers based on consumption (API calls, tokens, storage, bandwidth).
- You want to combine usage charges with subscriptions or one-time purchases.
- You need to track and aggregate events into billable quantities.
- You're building an AI service, SaaS platform, or infrastructure product with metered features.

---

## Core Concepts

### Events

Usage records sent from your application to Dodo. Each event is attributed to a customer and matched to a meter by its `event_name`.

```json
{
  "event_id": "evt_unique_123",
  "customer_id": "cus_abc123",
  "event_name": "api.call",
  "timestamp": "2025-01-21T10:30:00Z",
  "metadata": { "endpoint": "/v1/users", "tokens": 150 }
}
```

### Meters

Filters and aggregates events into billable quantities. A meter specifies:
- **Event name**: which events to match (case-sensitive)
- **Aggregation type**: how to combine events (count, sum, max, last)
- **Measurement unit**: the billing unit (calls, tokens, GB, etc.)
- **Optional filters**: conditions events must meet to be counted

### Aggregation Types

| Type | Use Case | Example |
|------|----------|---------|
| **Count** | Total events | API calls, image generations |
| **Sum** | Add values from a property | Tokens used, bytes transferred |
| **Max** | Highest value in a period | Peak concurrent users |
| **Last** | Most recent value | Current storage used |

For `sum`, `max`, and `last`, you specify which metadata property to aggregate.

### Pricing

Attach a meter to a product price to charge per unit:
- **Price per unit**: e.g., $0.001 per API call
- **Free threshold**: e.g., 1,000 free calls per month
- **Charge formula**: `(usage − threshold) × price_per_unit`

**Example**: 2,500 calls − 1,000 free = 1,500 × $0.02 = $30.00

---

## Meter Lifecycle

### Create a Meter

```typescript
import DodoPayments from 'dodopayments';

const client = new DodoPayments({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  environment: 'test_mode',
});

const meter = await client.meters.create({
  name: 'API Requests',
  event_name: 'api.call',
  aggregation: { type: 'count' },
  measurement_unit: 'calls',
  description: 'Track API calls per customer',
});

console.log(meter.id); // mtr_...
```

For a sum aggregation, specify the property to aggregate:

```typescript
const meter = await client.meters.create({
  name: 'Token Usage',
  event_name: 'ai.tokens',
  aggregation: { type: 'sum', key: 'tokens' },
  measurement_unit: 'tokens',
});
```

### List and Retrieve Meters

```typescript
// List all meters
const meters = await client.meters.list();

// Retrieve a specific meter
const meter = await client.meters.retrieve('mtr_abc123');
```

### Archive and Unarchive

Meters are archived, not deleted. Archived meters stop accepting new events but retain historical data.

```typescript
// Archive a meter
await client.meters.archive('mtr_abc123');

// Unarchive to resume
await client.meters.unarchive('mtr_abc123');
```

---

## Event Ingestion

### Send Events

```typescript
async function recordApiCall(
  customerId: string,
  requestId: string,
  occurredAt: string,
): Promise<number> {
  const response = await client.usageEvents.ingest({
    events: [{
      event_id: `api-call:${requestId}`,
      customer_id: customerId,
      event_name: 'api.call',
      timestamp: occurredAt,
      metadata: {
        endpoint: '/v1/users',
        method: 'GET',
      },
    }],
  });

  return response.ingested_count;
}
```

`requestId` must identify the underlying API operation and remain unchanged across retries. Do not generate it inside the ingestion attempt.

### Event Schema

| Field | Required | Notes |
|-------|----------|-------|
| `event_id` | Yes | Unique identifier for idempotency. Duplicate IDs in the same request reject the entire request. |
| `customer_id` | Yes | Dodo Payments customer ID. |
| `event_name` | Yes | Must match a meter's event name exactly (case-sensitive). |
| `timestamp` | No | ISO-8601 datetime. Defaults to current UTC time. Must be within one hour in the past or five minutes in the future. |
| `metadata` | No | Object with string, integer, number, or boolean values. Max 50 pairs; key length 100, value length 500. No nested objects or arrays. |

### Idempotency and Deduplication

- Each distinct operation gets one globally unique `event_id`.
- Derive the ID from an immutable request, job, generation, or snapshot ID and reuse it on every retry.
- Duplicate IDs in a single request reject the entire batch.
- An ID already ingested in an earlier request is silently ignored, making retries safe.

### Batch Ingestion

Send up to 1,000 events per request:

```typescript
async function trackBatchUsage(
  events: Array<{
    operationId: string;
    customerId: string;
    eventName: string;
    occurredAt: string;
    metadata: Record<string, string | number | boolean>;
  }>
) {
  const formattedEvents = events.map((event) => ({
    event_id: `usage:${event.operationId}`,
    customer_id: event.customerId,
    event_name: event.eventName,
    timestamp: event.occurredAt,
    metadata: event.metadata,
  }));

  await client.usageEvents.ingest({ events: formattedEvents });
}

// Batch track multiple API calls
await trackBatchUsage([
  { operationId: 'req_101', customerId: 'cus_abc', eventName: 'api.call', occurredAt: '2026-08-01T10:00:00Z', metadata: { endpoint: '/v1/users' } },
  { operationId: 'req_102', customerId: 'cus_abc', eventName: 'api.call', occurredAt: '2026-08-01T10:00:01Z', metadata: { endpoint: '/v1/orders' } },
  { operationId: 'req_103', customerId: 'cus_xyz', eventName: 'api.call', occurredAt: '2026-08-01T10:00:02Z', metadata: { endpoint: '/v1/products' } },
]);
```

### Query Events

```typescript
// List events for a customer
const events = await client.usageEvents.list({
  customer_id: 'cus_abc123',
});

// Retrieve a specific event
const event = await client.usageEvents.retrieve('evt_abc123');
```

---

## Pricing Models

### Per-Unit Pricing

The only currently documented and operable pricing model. A meter attachment uses:
- `price_per_unit`: decimal string (max 5 integer digits, 12 decimal places)
- `free_threshold`: optional integer (usage below this is not charged)

Charge formula: `(usage − threshold) × price_per_unit`

The `product-catalog-management` skill is the canonical source for the complete product creation request. It defines the singular `price` object with `type: 'usage_based_price'` and its nested `meters` array; do not define a parallel product schema here.

**Note:** Tiered, graduated, volume, and staircase pricing models are not currently documented in the Dodo Payments API. Use per-unit pricing with free thresholds for now.

---

## Instrumenting Your Application

Full guide: [references/instrumentation.md](references/instrumentation.md).

Covers:

- Track API Calls
- Track AI Token Usage
- Track Storage Usage

## Querying Usage for Display

### Retrieve Usage History

```typescript
// Auto-paginates across ALL billing periods; narrow with start_date/end_date/meter_id.
for await (const period of client.subscriptions.retrieveUsageHistory('sub_abc123', {
  start_date: '2025-01-01T00:00:00Z',
  page_size: 20,
})) {
  console.log(period); // one record per billing period, with per-meter usage
}
```

This is paginated usage history organized by billing period, across the subscription's lifetime - not just the current period. Filter with `start_date`, `end_date`, and `meter_id`, and iterate pages (or `for await`) rather than reading only the first page.

---

## Credit-Based Billing Integration

Usage events can deduct from a customer's credit balance instead of charging per-unit. See the `credit-based-billing` skill for full details on credit entitlements, balances, and ledger management.

To link a meter to credits:

1. Create a credit entitlement (e.g., "AI Credits").
2. Attach the credit entitlement to the same product.
3. On the meter, enable **Bill usage in Credits**.
4. Set `credit_entitlement_id` and `meter_units_per_credit` (e.g., 1,000 tokens = 1 credit).

The free threshold does **not** apply to credit-billed meters: every unit counts toward credit deduction (it only applies when the meter bills in money). Approximately every minute, a background worker aggregates new usage, converts it using the meter-to-credit ratio, and deducts from non-expired grants, earliest-expiring grants consumed first. When credits run out, configured overage behavior applies.

---

## Webhook Integration

Usage events trigger webhooks for monitoring and reconciliation. See the `webhook-integration` skill for webhook setup and verification.

---

## Common Mistakes

### 1. Using Unstable or Reused Event IDs

Generate one ID from the immutable business operation. Reusing an ID for a different operation drops usage, while generating a timestamp or random ID on every retry can bill the same operation twice.

```typescript
// WRONG — a retry creates a new billable event
await client.usageEvents.ingest({
  events: [{
    event_id: `api-call:${Date.now()}:${crypto.randomUUID()}`,
    customer_id: 'cus_abc',
    event_name: 'api.call',
  }],
});

// CORRECT — retry request req_123 with this same ID
await client.usageEvents.ingest({
  events: [{
    event_id: 'api-call:req_123',
    customer_id: 'cus_abc',
    event_name: 'api.call',
  }],
});
```

Do not reuse `api-call:req_123` for a distinct request. This matches credit ledger guidance: a timeout is not permission to generate a fresh idempotency key.

### 2. Using Fire-and-Forget Ingestion

Do not start ingestion after responding without first persisting the event. The process can crash after the user receives success but before usage reaches Dodo.

```typescript
// WRONG — an acknowledged operation can lose its usage event
app.post('/api/generate', async (req, res) => {
  const result = await generateAI(req.body);
  res.json(result);
  void client.usageEvents.ingest({ events: [result.usageEvent] });
});

// CORRECT — durable persistence completes before success is returned
app.post('/api/generate', async (req, res) => {
  const result = await generateAI(req.body);
  await usageOutbox.persist(result.usageEvent);
  res.json(result);
});
```

A retrying worker ingests the persisted payload with its original `event_id`, as shown in **Track API Calls**. If persistence fails, return an error so the operation can be retried rather than silently underbilling.

### 3. Clock Skew in Timestamps

Timestamps must be within one hour in the past or five minutes in the future. Ensure your server clock is synchronized.

```typescript
// WRONG — timestamp is 2 hours old
const oldTime = new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString();
await client.usageEvents.ingest({
  events: [{
    event_id: 'evt_123',
    customer_id: 'cus_abc',
    event_name: 'api.call',
    timestamp: oldTime, // Rejected
    metadata: {}
  }]
});

// CORRECT — use current time
await client.usageEvents.ingest({
  events: [{
    event_id: 'evt_123',
    customer_id: 'cus_abc',
    event_name: 'api.call',
    timestamp: new Date().toISOString(),
    metadata: {}
  }]
});
```

### 4. Ingesting on the Client Side

Never send events from client-side code. Always ingest from your backend to avoid exposing your API key.

```typescript
// WRONG — client-side
const trackUsage = async (eventName: string) => {
  await fetch('https://test.dodopayments.com/events/ingest', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.DODO_PAYMENTS_API_KEY}`, // Exposed!
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ events: [...] })
  });
};

// CORRECT — send the event from a backend worker using its persisted payload
await client.usageEvents.ingest({
  events: [{
    event_id: 'api-call:req_123',
    customer_id: 'cus_abc',
    event_name: 'api.call',
    timestamp: '2026-08-01T10:30:00Z',
    metadata: { endpoint: '/v1/users' },
  }],
});
```

### 5. Mismatched Event Names

Event names are case-sensitive and must match the meter's event name exactly.

```typescript
// WRONG — meter expects "api.call", event sends "API.CALL"
const meter = await client.meters.create({
  name: 'API Requests',
  event_name: 'api.call',
  aggregation: { type: 'count' },
  measurement_unit: 'calls',
});

await client.usageEvents.ingest({
  events: [{
    event_id: 'api-call:req_123',
    customer_id: 'cus_abc',
    event_name: 'API.CALL', // Won't match
  }]
});

// CORRECT
await client.usageEvents.ingest({
  events: [{
    event_id: 'api-call:req_123',
    customer_id: 'cus_abc',
    event_name: 'api.call', // Matches exactly
  }]
});
```

---

## Resources

- [Usage-Based Billing Guide](https://docs.dodopayments.com/features/usage-based-billing/introduction)
- [Meters Documentation](https://docs.dodopayments.com/features/usage-based-billing/meters)
- [Event Ingestion API](https://docs.dodopayments.com/api-reference/usage-events/ingest-events)
- [Create Meter API](https://docs.dodopayments.com/api-reference/meters/create-meter)
- [Usage-Based Billing Integration Guide](https://docs.dodopayments.com/developer-resources/usage-based-billing-guide)
- [Credit-Based Billing](https://docs.dodopayments.com/features/credit-based-billing)
- [Webhook Integration](https://docs.dodopayments.com/developer-resources/webhooks)
