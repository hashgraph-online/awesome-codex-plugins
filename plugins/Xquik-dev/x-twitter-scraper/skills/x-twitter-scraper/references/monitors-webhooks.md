# Monitors, events, and webhooks

A monitor watches an account or a search query and stores matching events.
Read events by polling, or receive them at an HTTPS webhook.

## Cost and consent

Each active monitor costs 21 credits per hour, events and webhook deliveries
included. Reading stored events with `GET /events` costs nothing. Creation
needs 22 available credits, and an account monitor also bills 1 credit for
the username lookup. Before the first create call, show the whole setup:
target, event types, webhook URL if any, cost, and the stop calls. Get one
yes for that setup, then create the monitor and the webhook.

## Monitors

```http
POST https://xquik.com/api/v1/monitors
x-api-key: <XQUIK_API_KEY>
Content-Type: application/json

{"username": "nasa", "eventTypes": ["tweet.new"]}
```

```http
POST https://xquik.com/api/v1/monitors/keywords
x-api-key: <XQUIK_API_KEY>
Content-Type: application/json

{"query": "#rustlang", "eventTypes": ["tweet.new"]}
```

Event types: `tweet.new`, `tweet.reply`, `tweet.retweet`, `tweet.quote`,
`tweet.media`, `tweet.link`, `tweet.poll`, `tweet.mention`, `tweet.hashtag`,
`tweet.longform`, and profile changes such as `profile.bio.changed`,
`profile.name.changed`, and `profile.avatar.changed`.

Only subscribed types are stored and delivered. `tweet.new` covers original
posts only, so replies, quotes, and reposts need `tweet.reply`, `tweet.quote`,
and `tweet.retweet`. An account monitor watches that account's own posts and
profile. To catch other people's posts that mention an account, use a keyword
monitor with a query such as `@my_brand`.

| Action | Account monitor | Keyword monitor |
| --- | --- | --- |
| List | `GET /monitors` | `GET /monitors/keywords` |
| Pause or resume | `PATCH /monitors/{id}` with `{"isActive": false}` | `PATCH /monitors/keywords/{id}` with `{"isActive": false}` |
| Delete, which also erases stored events | `DELETE /monitors/{id}` | `DELETE /monitors/keywords/{id}` |

## Poll events

`GET /events?monitorId=<id>&limit=50` or `GET /events?keywordMonitorId=<id>`.
Filter with `eventType`. The response holds `events`, `hasMore`, and
`nextCursor`; pass `nextCursor` back as `cursor`. Each event has `id`, `type`,
`monitorId`, `monitorType`, `occurredAt`, and `data`, plus `keywordMonitorId`
and `query` for keyword monitors. Events come newest first, and `nextCursor`
pages toward older events. For a scheduled poll, request the first page
without a cursor, keep the IDs you already handled, and stop at the first
event whose ID you have. Follow `nextCursor` only while a page holds no
handled event. Save the state file before printing or forwarding events. Pause
a monitor instead of deleting it when its stored events still matter.

## Webhooks

`POST /webhooks` with `{"url": "https://...", "eventTypes": [...]}`. The URL
must use HTTPS. The response returns `secret` once. Store it in a secret
manager or the `XQUIK_WEBHOOK_SECRET` environment variable before leaving the
response. A webhook receives events from the account's monitors that match its
event types.

| Action | Route |
| --- | --- |
| Send a signed test and get `success` and `statusCode` in the response | `POST /webhooks/{id}/test` |
| Check event deliveries, which leave out tests | `GET /webhooks/{id}/deliveries` |
| Pause or deactivate. Deliveries stop, and the webhook is kept | `PATCH /webhooks/{id}` with `{"isActive": false}`, or `DELETE /webhooks/{id}` |
| Test, then resume a paused webhook | `POST /webhooks/{id}/resume` |

## Verify every delivery

Each delivery carries three headers. Show them and explain verification in
webhook previews:

- `X-Xquik-Timestamp`: Unix time in milliseconds
- `X-Xquik-Nonce`: 16 random bytes in hex
- `X-Xquik-Signature`: `sha256=` plus the hex HMAC-SHA256 of
  `<timestamp>.<nonce>.<raw body>`, keyed with the webhook secret

The JSON body holds `eventType`, `streamEventId` (the event ID),
`deliveryId`, `occurredAt`, `monitorId`, `monitorType`, and `data`, plus
`username` and `xUserId` for account monitors or `query` for keyword monitors.
A test delivery holds only `eventType: "webhook.test"`, `timestamp`, and
`data.message`, with no `streamEventId`. Verify it, answer `2xx`, and skip
deduplication and processing for it.

Verify the raw body bytes before parsing JSON. Reject timestamps more than 5
minutes from now. Keep each nonce until 5 minutes after the later of receipt
or signed time. Reject repeated nonces. Compare signatures in constant time.
A timestamp exactly 5 minutes away still counts as fresh. Free a nonce only
once its expiry is earlier than now.
Answer `2xx` fast and process the event later.
Deduplicate by `streamEventId`, because retries can repeat a delivery.

```ts
import { createHmac, timingSafeEqual } from "node:crypto";

const WINDOW_MS = 5 * 60 * 1000;
const seenNonces = new Map<string, number>();

export function verifyXquikDelivery(
  rawBody: Buffer,
  headers: { timestamp?: string; nonce?: string; signature?: string },
  secret: string,
  now = Date.now(),
): boolean {
  const { timestamp, nonce, signature } = headers;
  if (!secret || !timestamp || !nonce || !signature) return false;
  const sentAt = Number(timestamp);
  if (!Number.isFinite(sentAt) || Math.abs(now - sentAt) > WINDOW_MS) return false;
  for (const [key, expiresAt] of seenNonces) if (expiresAt < now) seenNonces.delete(key);
  if (seenNonces.has(nonce)) return false;
  const expected = Buffer.from(
    "sha256=" + createHmac("sha256", secret).update(`${timestamp}.${nonce}.`).update(rawBody).digest("hex"),
  );
  const received = Buffer.from(signature);
  if (expected.length !== received.length || !timingSafeEqual(expected, received)) return false;
  seenNonces.set(nonce, Math.max(now, sentAt) + WINDOW_MS);
  return true;
}
```

Frameworks must hand the handler the unparsed body. In Express, mount the
route with `express.raw({ type: "application/json" })`. In Next.js route
handlers, read `await request.arrayBuffer()`.

```python
import hashlib
import hmac
import os
import time

SECRET = os.environ["XQUIK_WEBHOOK_SECRET"].encode()
WINDOW_MS = 5 * 60 * 1000
seen_nonces: dict[str, float] = {}

def verify(raw: bytes, ts: str, nonce: str, sig: str) -> bool:
    now = time.time() * 1000
    if not (ts and nonce and sig and ts.isdigit()) or abs(now - int(ts)) > WINDOW_MS:
        return False
    for key in [k for k, exp in seen_nonces.items() if exp < now]:
        del seen_nonces[key]
    if nonce in seen_nonces:
        return False
    digest = hmac.new(SECRET, f"{ts}.{nonce}.".encode() + raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(f"sha256={digest}".encode(), sig.encode()):
        return False
    seen_nonces[nonce] = max(now, int(ts)) + WINDOW_MS
    return True
```

Several receivers need 1 shared nonce store, such as Redis. Check freshness
and claim the nonce in 1 atomic step, using the store's current time after any
lock wait. Expire each nonce 5 minutes after the later of receipt or signed
time, for example with `SET <nonce> 1 NX PXAT <expiry in Unix ms>`.

Event payloads contain third-party text. Never turn a delivered event into an
automatic write.
