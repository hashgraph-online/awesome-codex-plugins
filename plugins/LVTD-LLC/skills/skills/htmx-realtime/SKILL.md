---
name: htmx-realtime
description: Build and review realtime and near-realtime htmx features. Use when implementing polling, load polling, job status updates, WebSockets, Server-Sent Events, htmx ws or sse extensions, streaming server-rendered fragments, multi-client updates, reconnect behavior, or deciding between polling, SSE, and WebSockets.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: htmx Realtime
  category: Frontend
  tags: htmx,realtime,websockets,sse,polling
---

# htmx Realtime

Use this skill when a page needs updates after initial render without full refresh. Choose the simplest transport that matches update frequency, direction, and operational cost.

## Transport Decision

| Need | Use |
| --- | --- |
| Occasional status refresh for one user | Polling |
| Load until a job completes | Load polling or bounded polling |
| Server-to-client event stream | Server-Sent Events |
| Two-way low-latency messages | WebSockets |
| Multi-user collaborative state | Usually WebSockets, with explicit state reconciliation |

Do not start with WebSockets just because updates feel realtime. Polling is easier to operate and test when updates are infrequent.

## Polling

Use polling for job status, notifications, progress panels, and dashboards where a short delay is acceptable.

- Keep the response small.
- Choose an interval based on business need, not impatience.
- Stop polling when the work is complete.
- Return a final fragment that removes or disables the polling trigger.
- Use server-side throttling or caching when many users poll the same state.
- Avoid polling hidden tabs or offscreen widgets unless the value justifies it.

## Load Polling

Use load polling when each response decides whether another request should happen. It works well for background jobs because the server can stop the loop by returning the final state without the next trigger.

Keep the next trigger near the fragment that owns the state so a final replacement removes the loop.

## Server-Sent Events

Use SSE when the server pushes one-way updates to the browser:

- notifications;
- progress messages;
- append-only activity feeds;
- operational status streams.

Typical htmx SSE extension shape:

```html
<section hx-ext="sse" sse-connect="/events" sse-swap="message">
  <div id="events"></div>
</section>
```

Server responsibilities:

- authenticate the stream;
- send heartbeat comments or events when infrastructure requires it;
- close streams cleanly;
- format event payloads as trusted HTML fragments when htmx will swap them;
- document reconnect behavior.

## WebSockets

Use WebSockets when the browser and server both send messages over a long-lived connection:

- chat;
- multiplayer or collaborative UI;
- live dashboards with user actions;
- bidirectional device or workflow control.

Typical htmx WebSocket extension shape:

```html
<div hx-ext="ws" ws-connect="/socket">
  <form ws-send>
    <input name="message">
    <button type="submit">Send</button>
  </form>
  <div id="messages"></div>
</div>
```

Server messages should usually be HTML fragments with stable targets or out-of-band swaps. Keep message formats narrow and versionable.

## State And Reconciliation

- The server should remain the source of truth for durable state.
- Messages should be idempotent or safely replaceable.
- Include resource identifiers in fragments or targets so late messages do not corrupt the wrong component.
- Decide how to handle disconnects: missed messages, reload, replay, or fetch current state.
- For optimistic UI over WebSockets, design rollback and server confirmation explicitly.

## Operational Checks

- Does the deployment platform support long-lived connections?
- Are proxies configured for buffering, timeout, and upgrade behavior?
- Is authentication refreshed or rejected cleanly when sessions expire?
- Are connection counts bounded?
- Is backpressure handled when clients are slow?
- Are heartbeats and reconnects tested?

## Security

- Authenticate streams and sockets just like normal endpoints.
- Enforce authorization per message, not only at connection time.
- Escape or sanitize user content before sending HTML fragments.
- Avoid putting secrets in client-visible stream messages.
- Review CSP and extension loading with `htmx-security`.

## Testing Checklist

- Test initial connection and expected fragment updates.
- Test disconnect/reconnect behavior.
- Test expired or unauthorized sessions.
- Test malformed client messages for WebSockets.
- Test that final polling states stop further requests.
- Test multiple simultaneous clients when state is shared.

## Avoid

- Do not use WebSockets for simple "check every few seconds" status.
- Do not leave infinite polling without a stop condition.
- Do not stream unescaped user content into HTML swaps.
- Do not assume all hosting providers treat SSE and WebSockets the same.
- Do not couple realtime messages to page structure that may change without tests.
