# HTTP Client Resilience Knowledge

## Budget Model

The caller owns a total context deadline. Connection, TLS, response-header, and
per-attempt limits must fit inside it. Retries consume the same total budget,
including backoff and body processing. A client-wide timeout can provide a
backstop, but operation contexts express the real work boundary.

## Failure Classes

- **Transport**: DNS, connect, TLS, socket, or protocol failure.
- **Cancellation/timeout**: caller canceled or a deadline expired.
- **HTTP status**: server returned a complete response with application meaning.
- **Decode/protocol**: response shape, content type, or framing is invalid.
- **Local policy**: body too large, redirect rejected, or retry budget exhausted.

Preserve the underlying cause and include bounded context such as operation,
method, host, status, and request ID.

## Client Lifecycle

`http.Client` and `http.Transport` are safe for concurrent reuse and should
normally live for the application lifetime. Reusing them enables connection
pooling. Response bodies must be closed. Reading to EOF when reasonable can
allow reuse, but error bodies must still be size-limited.

Choose response consumption deliberately. Stream large success bodies when
callers can process incrementally; materialize only within a known size bound.
Draining to `io.Discard` is memory-efficient but still needs byte and time
bounds. Closing a body does not guarantee connection reuse.

Clone and review a baseline transport instead of constructing a sparse
`http.Transport` that silently loses default proxy, timeout, compression, or
protocol behavior. Bound pool-wide and per-host connections from measured load.

## Retry Safety

Safe retries require a transient failure plus an idempotent operation or a
server-supported idempotency key. Respect `Retry-After`, add jitter, cap attempts
and delays, and stop on context cancellation. A retry policy is part of the
operation contract, not generic middleware applied blindly.

## Pagination

Track next cursors explicitly, detect repeated cursors, cap pages or records,
and share the total context budget. Return partial results only when the public
contract states how callers can recognize and resume them.

Prefer opaque cursor parameters. Validate the scheme and origin of any absolute
next URL before reusing authentication. Close each page body before the next
request. Retrying a page must not append its records twice.

For a protocol promising one JSON document, validate the expected media type
when required, decode one value, and reject unexpected trailing data.
