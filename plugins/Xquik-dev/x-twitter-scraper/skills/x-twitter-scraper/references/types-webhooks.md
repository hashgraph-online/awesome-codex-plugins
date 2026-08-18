# Xquik TypeScript Types: Webhooks

```typescript

interface WebhookCreated {
  id: string;
  url: string;
  eventTypes: EventType[];
  secret: string;
  createdAt: string;
}

interface Webhook {
  id: string;
  url: string;
  eventTypes: EventType[];
  isActive: boolean;
  consecutiveFailures: number;
  deliveryStatus: "active" | "paused" | "needs_attention";
  failureHardCap: number;
  createdAt: string;
}

interface Delivery {
  id: string;
  streamEventId: string;
  status: "pending" | "delivered" | "failed" | "exhausted";
  attempts: number;
  lastStatusCode?: number;
  lastError?: string;
  createdAt: string;
  deliveredAt?: string;
}

interface WebhookPayload {
  schemaVersion: 1;
  streamEventId: string;
  deliveryId: string;
  eventType: EventType;
  username?: string;
  query?: string;
  occurredAt: string;
  data: Record<string, unknown>;
}

```
