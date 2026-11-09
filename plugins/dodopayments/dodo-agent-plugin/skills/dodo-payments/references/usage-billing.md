# Usage-based billing

## Contents

- [How it works](#how-it-works)
- [Create a meter](#create-a-meter)
- [Attach the meter to a product](#attach-the-meter-to-a-product)
- [Send usage events](#send-usage-events)
- [Instrumentation patterns](#instrumentation-patterns)
- [Read usage](#read-usage)
- [Common mistakes](#common-mistakes)

## How it works

1. Your backend sends **usage events** (`client.usageEvents.ingest`), each with a customer and an `event_name`.
2. A **meter** matches events by `event_name` (case-sensitive) and aggregates them: `count`, `sum`, `max` or `last` of a metadata key.
3. A usage-based product prices the meter: `(usage - free_threshold) x price_per_unit`, billed each cycle. Example: 2,500 calls, 1,000 free, USD 0.02 each = USD 30.00.

To deduct usage from a prepaid credit balance instead of billing money, link the meter to a credit entitlement ([credits.md](credits.md)).

## Create a meter

```typescript
const calls = await client.meters.create({
  name: 'API Requests',
  event_name: 'api.call',
  aggregation: { type: 'count' },
  measurement_unit: 'calls',
});

const tokens = await client.meters.create({
  name: 'Token Usage',
  event_name: 'ai.tokens',
  aggregation: { type: 'sum', key: 'tokens' }, // sum, max and last need a numeric metadata key
  measurement_unit: 'tokens',
});
console.log(calls.id, tokens.id);
```

Meters are archived, not deleted: `client.meters.archive(id)` and `client.meters.unarchive(id)`. List with `client.meters.list()`.

## Attach the meter to a product

The product uses `price.type: 'usage_based_price'` with a `meters` array. The full request is in [products.md](products.md#usage-based-product). `price_per_unit` is a decimal string; `free_threshold` is an integer. Per-unit pricing with a free threshold is the supported model.

Customers subscribe through a normal checkout session for that product.

## Send usage events

Ingest from your backend only, never from client code.

```typescript
async function recordApiCall(customerId: string, requestId: string, occurredAt: string) {
  const response = await client.usageEvents.ingest({
    events: [
      {
        event_id: `api-call:${requestId}`, // stable across retries
        customer_id: customerId,
        event_name: 'api.call',
        timestamp: occurredAt,
        metadata: { endpoint: '/v1/users', method: 'GET' },
      },
    ],
  });
  return response.ingested_count;
}
```

| Field | Rules |
|---|---|
| `event_id` | Required. Derive it from the immutable operation (request, job, generation ID) and reuse it on every retry. A previously ingested ID is ignored, so retries are safe. A duplicate ID inside one request rejects the whole request |
| `customer_id` | Required. A Dodo `cus_` ID |
| `event_name` | Required. Must equal the meter's `event_name` exactly |
| `timestamp` | Optional ISO 8601, defaults to now. Must be within the last hour and no more than 5 minutes ahead |
| `metadata` | Optional flat object of strings, numbers and booleans. Max 50 keys. Aggregated keys must be numbers |

Send up to 1,000 events per request.

## Instrumentation patterns

**Durable outbox (default).** Persist the event in the same transaction as the work, then ingest from a retrying worker. Nothing is lost if the process dies after responding.

```typescript
type PersistedUsageEvent = {
  event_id: string;
  customer_id: string;
  event_name: string;
  timestamp: string;
  metadata: Record<string, string | number | boolean>;
};

interface UsageOutbox {
  persist(event: PersistedUsageEvent): Promise<void>;
  nextBatch(limit: number): Promise<PersistedUsageEvent[]>;
  markIngested(eventIds: string[]): Promise<void>;
}

async function flushUsage(outbox: UsageOutbox): Promise<void> {
  const events = await outbox.nextBatch(1000);
  if (events.length === 0) return;
  await client.usageEvents.ingest({ events });
  await outbox.markIngested(events.map((event) => event.event_id));
}
```

**AI tokens.** After the model call, record `{ tokens: usage.total_tokens, model }` in metadata with `event_name: 'ai.tokens'` and `event_id: 'generation:<generationId>'`; meter with `sum` on `tokens`.

**Storage and seats.** Send periodic snapshots (`event_name: 'storage.snapshot'`, metadata `{ bytes: 5368709120 }`) and meter with `last`.

## Read usage

```typescript
for await (const event of client.usageEvents.list({ customer_id: 'cus_abc123' })) {
  console.log(event.event_id, event.event_name);
}

// Per billing period, across the subscription's lifetime. Filter with start_date, end_date, meter_id.
for await (const period of client.subscriptions.retrieveUsageHistory('sub_abc123', {
  start_date: '2025-01-01T00:00:00Z',
})) {
  console.log(period);
}
```

## Common mistakes

- A new random or timestamp `event_id` on each retry bills the same operation twice. Reusing one ID for different operations drops usage.
- Fire-and-forget ingestion after responding. Persist first.
- `event_name` case mismatch (`API.CALL` vs `api.call`) silently matches no meter.
- Numeric values sent as strings for a `sum`, `max` or `last` key.
- Clock skew: events older than one hour are rejected.
- Expecting `free_threshold` to apply to a meter billed in credits. It applies only to meters billed in money.
