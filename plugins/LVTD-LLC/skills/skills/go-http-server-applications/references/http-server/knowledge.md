# HTTP Server Knowledge

## Adapter Boundary

Handlers translate HTTP requests into application inputs and map application
results into HTTP responses. Domain services should not depend on
`http.ResponseWriter`, status codes, headers, or route variables.

## Routing

Modern `ServeMux` patterns are Go-version-sensitive. Go 1.22 added method
patterns, wildcards, `Request.PathValue`, precedence, and conflict detection.
Invalid or conflicting patterns may panic. The root pattern `/` is broad;
`/{$}` expresses an exact root on supporting versions.

## Response Commitment

The first body write implicitly commits status 200. Repeated `WriteHeader`
calls do not replace the first final status. Prepare JSON and headers before
commitment when feasible so encoding failures can still map cleanly.

Streaming commits early, so define framing, ordering, per-result limits,
partial-result semantics, and how terminal errors appear after status can no
longer change. Keep one goroutine responsible for `ResponseWriter`; workers
send bounded results to that coordinator.

## Writer Wrapping

Embedding `http.ResponseWriter` does not automatically preserve `Flusher`,
`Hijacker`, `Pusher`, or optimized transfer behavior. Prefer
`http.NewResponseController` for supported controls. If wrapping, define
`Unwrap` and test actual capabilities without advertising unsupported ones.

## Lifecycle

`Server.Shutdown` closes listeners, closes idle connections, and waits for
active connections until its context expires. Serve methods return
`ErrServerClosed` during shutdown. Hijacked or upgraded connections require
separate coordination.

`Shutdown` drains active handlers but does not itself cancel every active
request context. Define graceful drain, deadline expiry, and forced-cancellation
policy explicitly. Non-cooperative dependencies that ignore context require
their own timeout or isolation boundary.

## Health

Liveness says the process can respond. Readiness says it is willing and able to
serve according to an explicit dependency policy. Keep dependency checks
bounded and avoid turning health probes into expensive load.
