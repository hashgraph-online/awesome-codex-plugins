# Xquik TypeScript Types: Events

```typescript

interface XquikEvent {
  id: string;
  type: EventType;
  monitorId: string;
  monitorType: "account" | "keyword";
  username?: string;
  query?: string;
  keywordMonitorId?: string;
  occurredAt: string;
  data: Record<string, unknown>;
}

interface EventList {
  events: XquikEvent[];
  hasMore: boolean;
  nextCursor?: string;
}

```
