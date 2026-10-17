# Dodo Payments Usage-Based Billing: Instrumenting Your Application


### Track API Calls

Persist the event before reporting the operation as complete, then ingest it from a retrying worker. The outbox or queue implementation must durably store the payload before `persist` resolves.

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

async function completeApiOperation(
  outbox: UsageOutbox,
  operationId: string,
  customerId: string,
  occurredAt: string,
): Promise<void> {
  await outbox.persist({
    event_id: `api-call:${operationId}`,
    customer_id: customerId,
    event_name: 'api.call',
    timestamp: occurredAt,
    metadata: { endpoint: '/v1/users', method: 'GET', status: 200 },
  });
}

async function ingestUsageOutbox(outbox: UsageOutbox): Promise<void> {
  const events = await outbox.nextBatch(1000);
  if (events.length === 0) return;

  await client.usageEvents.ingest({ events });
  await outbox.markIngested(events.map((event) => event.event_id));
}
```

If the worker crashes after Dodo accepts the batch but before `markIngested`, retry the same persisted events with the same IDs. Dodo ignores the already-ingested IDs.

### Track AI Token Usage

```typescript
async function callAI(
  customerId: string,
  generationId: string,
  prompt: string,
  completedAt: string,
) {
  const response = await openai.chat.completions.create({
    model: 'gpt-4',
    messages: [{ role: 'user', content: prompt }],
  });

  // Track tokens after completion
  await client.usageEvents.ingest({
    events: [{
      event_id: `generation:${generationId}`,
      customer_id: customerId,
      event_name: 'ai.tokens',
      timestamp: completedAt,
      // Aggregated properties (Sum/Max/Last) must be numbers, not strings.
      metadata: {
        tokens: response.usage.total_tokens,
        prompt_tokens: response.usage.prompt_tokens,
        completion_tokens: response.usage.completion_tokens,
        model: 'gpt-4',
      }
    }]
  });

  return response;
}
```

### Track Storage Usage

For snapshot-based metrics (current state), use the `last` aggregation:

```typescript
async function updateStorageUsage(
  customerId: string,
  snapshotId: string,
  bytesUsed: number,
  capturedAt: string,
) {
  await client.usageEvents.ingest({
    events: [{
      event_id: `storage-snapshot:${snapshotId}`,
      customer_id: customerId,
      event_name: 'storage.snapshot',
      timestamp: capturedAt,
      // Numeric values: a string property does not aggregate.
      metadata: {
        bytes: bytesUsed,
        gb: Number((bytesUsed / 1024 / 1024 / 1024).toFixed(2)),
      }
    }]
  });
}

// Call periodically or after storage changes
await updateStorageUsage(
  'cus_abc',
  'snapshot_01K1M4D2K9',
  5368709120,
  '2026-08-01T10:30:00Z',
); // 5GB
```

---
