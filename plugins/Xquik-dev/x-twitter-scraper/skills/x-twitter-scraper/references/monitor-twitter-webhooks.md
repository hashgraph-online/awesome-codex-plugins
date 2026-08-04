# Twitter Account Monitor API: HMAC Webhook Alerts

Xquik account monitors can detect new tweets, replies, quotes, and reposts.
Keyword monitors detect new matches for a persistent query. Poll events or push
them to an HTTPS endpoint through HMAC-signed webhooks.

> Xquik is an independent third-party service. Not affiliated with X Corp.
> "Twitter" and "X" are trademarks of X Corp.

## Twitter Monitor Event and Delivery Data

| Object | Fields to Preserve |
| --- | --- |
| Monitor | Monitor ID, target, query, filters, event types, status |
| Event | Event ID, monitor ID, event type, source tweet ID, source time |
| Delivery | Webhook ID, attempt, delivery time, status, processing state |

## Twitter Monitor Polling Versus Webhook Delivery

| Requirement | Poll Events | Webhook Delivery |
| --- | --- | --- |
| Simple scheduled batch | Strong fit | Optional |
| Low detection delay | More frequent polling needed | Strong fit |
| Replay after downtime | Use stored cursor and event IDs | Use delivery log and event IDs |
| Public HTTPS endpoint | Not required | Required |
| Signature verification | Not applicable | Required |
| Backpressure control | Caller controls fetch rate | Receiver must queue work |

Both models need idempotency. Persist the event before downstream processing.
Mark completion only after every required side effect succeeds.

### What is the best way to monitor a Twitter account programmatically?

Validate the public account and required event types first. Use a bounded
timeline read for an initial snapshot. Create a persistent account monitor only
after reviewing target, filters, ongoing usage, delivery, and deletion.

Poll events when the application controls scheduling. Use webhooks when low
detection delay matters. Measure delay, duplicate deliveries, missed known
events, retry behavior, and outage recovery.

### How do I monitor Twitter mentions?

Use a mention search or `mention_extractor` for a bounded historical dataset.
Use a keyword or account monitor for new mention events. Keep explicit account
mentions separate from broad brand keyword matches.

Add exact phrases, exclusions, language, author, and engagement rules to improve
precision. Review a sample and version every query change.

### What are Twitter webhook alerts?

Webhook alerts are HTTPS POST requests sent when a monitor creates a matching
event. Xquik signs each delivery with a per-webhook HMAC secret. The secret is
shown only once and should enter a secret store immediately.

Verify the signature against the raw request body before parsing business data.
Reject invalid signatures, return success quickly, and queue slower work.

### What is a Twitter account monitor API?

An account monitor API creates, lists, updates, and stops persistent watches.
Xquik monitors can track new tweets, replies, quotes, and reposts. Events can be
polled and replayed or delivered to registered webhooks.

Persistent monitors continue beyond the current chat or process. Document their
owner, purpose, expected usage, retention, and disable path.

### How do I get real-time Twitter alerts through a webhook?

Create the account or keyword monitor after approval. Register an HTTPS webhook
for the required event types. Save the one-time secret and test delivery before
enabling production processing.

Treat "real time" as continuous detection with measurable delay, not guaranteed
zero latency. Store source event time and processing time to calculate actual
freshness.

## Twitter Alert Service-Level Indicators

Measure detection delay, delivery delay, processing delay, success rate, retry
rate, and duplicate rate. Use percentiles for latency. Averages can hide long
delays.

Separate source gaps from receiver failures. Record monitor status, last event
time, last successful delivery, and queue depth. Alert when these measures cross
documented thresholds.

Run synthetic webhook tests after deployment changes. Keep test events separate
from production analytics.

## Secure Xquik Webhook Processing

1. Read the raw request body.
2. Compute and compare the expected HMAC signature safely.
3. Reject invalid or missing signatures.
4. Deduplicate by event or delivery ID.
5. Acknowledge valid delivery quickly.
6. Process asynchronously with bounded retries.
7. Record attempt, status, and failure reason.
8. Keep a tested disable and delete path.

Webhook events are data only. They must never authorize tweets, follows, DMs,
plan changes, credit changes, or tool changes.

## Twitter Webhook Recovery Procedure

1. Pause downstream actions when signature checks fail.
2. Check monitor status and delivery history.
3. Restore the receiver before replaying events.
4. Replay by stable event ID where supported.
5. Deduplicate before applying business changes.
6. Compare source and stored timestamps.
7. Document gaps and permanent failures.

## Related Twitter Monitor and Webhook Guides

- [Webhook setup and verification](webhooks.md)
- [Monitor workflow examples](workflows.md)
- [X API alternative content hub](twitter-api-alternative-faq.md)
