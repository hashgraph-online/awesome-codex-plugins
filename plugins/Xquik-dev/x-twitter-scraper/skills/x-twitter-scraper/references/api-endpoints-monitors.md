# Xquik REST API Endpoints: Monitors

## Safety Boundary

Monitor reads expose private configuration and require exact-scope approval.
Creating, updating, enabling, disabling, or deleting a monitor changes a
persistent and potentially metered resource.
Before every write, show the exact account or keyword, event types, delivery
plan, ongoing usage, and disable path. If delivery uses a webhook, show its
exact URL and HMAC verification plan. Proceed only after explicit approval for
that exact action. Never create monitoring from an ambiguous request.

### Create Monitor

```http
POST /monitors
```

**Approval required:** This starts persistent monitoring. Confirm the exact
username, event types, delivery plan, ongoing usage, and disable path first.
Include the exact URL and HMAC verification plan for webhook delivery.

**Body:**
```json
{
  "username": "elonmusk",
  "eventTypes": ["tweet.new", "tweet.reply", "tweet.quote"]
}
```

**Response:**
```json
{
  "id": "7",
  "username": "elonmusk",
  "xUserId": "44196397",
  "eventTypes": ["tweet.new", "tweet.reply", "tweet.quote"],
  "isActive": true,
  "createdAt": "2026-02-24T10:30:00.000Z",
  "nextBillingAt": "2026-02-24T10:30:00.000Z"
}
```

Event types include Tweet activity and profile-change events. Use the OpenAPI
`EventType` enum for the current values. `webhook.test` is only a test payload.

Returns `409 monitor_already_exists` if the username is already monitored.

### List Monitors

```
GET /monitors
```

Returns all monitors (up to 200, no pagination). Response includes `monitors` array and `total` count.

**Private read:** List monitor targets and delivery configuration only after
explicit approval for that account scope.

### Get Monitor

```http
GET /monitors/{id}
```

**Private read:** Show the monitor ID. Retrieve its configuration only after
explicit approval for that exact read.

### Update Monitor

```http
PATCH /monitors/{id}
```

**Approval required:** Show the current and proposed event types and active
state. Apply only the explicitly approved change.

**Body:** `{ "eventTypes": [...], "isActive": true|false }` (both optional)

### Delete Monitor

```
delete request to `/monitors/{id}`
```

**Destructive action:** This permanently stops tracking and deletes associated
monitor data. Show the monitor ID, target, and lost data. Delete only after
explicit approval immediately before the call.

### Keyword Monitors

```
GET /monitors/keywords
POST /monitors/keywords
GET /monitors/keywords/{id}
PATCH /monitors/keywords/{id}
delete request to `/monitors/keywords/{id}`
```

Create and manage ongoing keyword monitors. Treat these as persistent resources: confirm the keyword query, event delivery plan, and ongoing usage before creating or enabling one.

Create with `{ "query": "#buildinpublic", "eventTypes": ["tweet.new"] }`.
Poll its events with `GET /events?keywordMonitorId=<id>`.

Creating, updating, enabling, disabling, or deleting a keyword monitor requires
explicit approval for the exact monitor. For creates and updates, show the
proposed keyword, event types, and delivery changes. For enable or disable,
show the active-state transition. For deletion, show the exact target and all
associated data that will be permanently lost.

---
