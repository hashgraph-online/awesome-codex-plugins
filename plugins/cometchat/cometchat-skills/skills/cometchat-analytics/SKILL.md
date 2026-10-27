---
name: cometchat-analytics
description: "See what your chat is doing — pull usage & message metrics via REST, stream real-time events to your data/observability stack via webhooks, monitor client-side errors & the init/login path, and read push/call logs. Cross-family: metrics/webhooks are server-side; client error monitoring wires per family. Triggers: 'chat analytics', 'usage metrics', 'message volume', 'monitor cometchat', 'observability', 'send chat events to datadog/segment/bigquery', 'track delivery', 'error monitoring for chat', 'dashboards for chat'."
license: "MIT"
compatibility: "CometChat Metrics REST API (usage · message) · Webhooks · Notification/Call logs · on-prem Prometheus/Grafana/Loki. Client error monitoring via each family's error boundary / listeners."
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat analytics observability metrics webhooks monitoring datadog sentry dashboards"
---

> **Ground truth:** shapes are FETCHED from the live docs — `{DOCS_BASE}/rest-api/metrics/usage-metrics`, `/rest-api/metrics/message-metrics`, `/fundamentals/webhooks` (+ `/rest-api/management-apis/webhooks/overview`), `/notifications/logs`, `/rest-api/calls-apis/get-call`, and on-prem `/on-premise-deployment/docker/monitoring`. `DOCS_BASE = https://www.cometchat.com/docs`; append `.md`. Verify each metric field / event name against the docs before charting it; don't invent a metric.

## Use this skill when
You need visibility into chat: product analytics (DAU, messages, retention), an ops/observability signal (delivery, errors, latency), or feeding chat events into an existing warehouse/monitoring stack.

## Three layers of visibility
| Layer | Source | Use it for |
| --- | --- | --- |
| **Aggregate metrics** | Metrics REST API (usage + message) | dashboards, MAU/DAU, message volume, growth |
| **Real-time events** | Webhooks | stream every message/user/group/call event to your pipeline |
| **Client health** | your error monitor + the kit's error boundary/listeners | init/login failures, render errors, UX latency |

## 1. Aggregate metrics (REST, server-side)
- **Usage metrics** (`{DOCS_BASE}/rest-api/metrics/usage-metrics`) — active users and usage over time.
- **Message metrics** (`{DOCS_BASE}/rest-api/metrics/message-metrics`) — message volume/counts.
- **Call metrics** — per-call detail incl. participant metrics via `{DOCS_BASE}/rest-api/calls-apis/get-call`.
Call these from a server job with the **REST API Key** (never client-side), on a schedule, into your BI tool. Fetch the exact query params + response fields from each page before building the report.

## 2. Real-time events → your stack (webhooks)
Webhooks POST an HTTPS notification to your server on message / user / group / call events (`{DOCS_BASE}/fundamentals/webhooks`; configure via `/rest-api/management-apis/webhooks/overview`). This is how you get chat into **Segment / BigQuery / Snowflake / Datadog / a data lake** in real time:
1. Stand up an HTTPS endpoint (returns 200 to ack). Secure it with the **Basic Auth** credentials CometChat sends on every webhook request (`{DOCS_BASE}/fundamentals/webhooks` — the docs describe Basic Auth only, with no payload-signature scheme, so validate the `Authorization` header rather than looking for an HMAC signature).
2. Subscribe to the events you need (don't fan out everything if you only need message.sent).
3. Transform + forward to your warehouse/observability sink; make the handler idempotent and fast (queue heavy work).
The same webhook stream doubles as a **tamper-evident audit log** for `cometchat-compliance`.

## 3. Client-side error & performance monitoring (per family)
The metrics API won't tell you a user's chat failed to load — instrument the client:
- **Capture kit render errors** — on the React families via the error boundary's hook (React v7: `CometChatErrorBoundary` `onError`; Angular/RN have the equivalent); on iOS/Android/Flutter (no error-boundary construct) via the SDK error listeners / the kit's error-state views. Forward to Sentry/Datadog with context.
- **Instrument the critical path** — wrap init, the token fetch, and login in spans/breadcrumbs; a spike in login failures is your earliest incident signal (often Region or token issues).
- **Listen for connection state** — the SDK's connection/websocket listeners tell you when clients drop; count reconnects.
- **Don't log secrets or message bodies** to your monitor — log UIDs/event types/latencies, not content (privacy + `cometchat-compliance`).
Wire these through the resolved family's `-core`/`-production`/`-troubleshooting` skills.

## 4. Delivery & call logs
- **Push delivery logs** (`{DOCS_BASE}/notifications/logs`) — FCM/APNs/email/SMS delivery, ~14-day retention; enable when diagnosing "notifications not arriving" and export before they age out.
- **Call logs** — the Calls REST APIs for per-call quality/participant metrics.

## 5. Self-host observability
On-prem ships **Prometheus + Grafana + Loki + Promtail** (`{DOCS_BASE}/on-premise-deployment/docker/monitoring`): service metrics, dashboards, alerts, and centralized logs — wire alerts (P95 latency, error rate, WS capacity) to your on-call. SaaS customers use the Metrics API + webhooks instead.

## Common pitfalls
1. **Metrics API called client-side** — it needs the REST API Key; server only.
2. **Webhook handler slow or non-idempotent** — retries pile up; ack fast, queue the work, dedupe.
3. **Charting an invented metric** — fetch the real fields from the metrics pages.
4. **Logging message content to your monitor** — privacy/compliance risk; log metadata, not bodies.
5. **No client error monitoring** — you'll hear about outages from users, not dashboards; wire the error boundary + login-path spans.
6. **Relying on push logs after they age out** — export within the retention window.

## Verify it works
Usage/message metrics return real numbers into your dashboard · a test message triggers your webhook and lands in your warehouse/monitor · a forced init/login failure shows up in your error monitor with context · push/call logs are readable when needed · (on-prem) Grafana shows the services and alerts fire.
