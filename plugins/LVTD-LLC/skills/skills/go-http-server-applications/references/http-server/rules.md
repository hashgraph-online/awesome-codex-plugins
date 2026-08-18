# HTTP Server Rules

## Routing and Handlers

- Construct a dedicated mux and inject handler dependencies.
- Validate methods, route values, media types, and request semantics explicitly.
- Map stable domain errors at the HTTP edge.
- Return immediately after `http.Error` or any other terminal response helper;
  do not continue into mutation or a success response.
- Keep middleware ordering documented in request and response directions.

## Input and Output

- Wrap inbound bodies with `http.MaxBytesReader`.
- Detect `*http.MaxBytesError` and choose the public status deliberately.
- Decode one expected JSON value and reject trailing non-whitespace data.
- Bound collection cardinality and per-item size in addition to total bytes.
- Use `DisallowUnknownFields` only when strict compatibility policy warrants it.
- Close request bodies and avoid logging secrets, headers, or raw bodies by default.

## Server Lifecycle

- Configure `ReadHeaderTimeout`, idle behavior, header limits, and shutdown budget.
- Choose response and upload limits from the workload; streaming needs separate policy.
- Observe serving errors and distinguish `http.ErrServerClosed`.
- Wait for `Shutdown` to complete before returning from `main`.
- Coordinate hijacked, upgraded, and background connections separately.
- For streaming responses, use one writer goroutine, bounded result buffering,
  explicit framing, and `ResponseController` deadlines or flushing where supported.
- Define how a committed stream reports terminal errors and partial success.
- Use `http.TimeoutHandler` only when buffered response semantics are acceptable;
  it is unsuitable for streaming. Distinguish handler deadlines from server
  header, read, write, and idle timeouts.

## Testing

- Use `httptest.NewRequest` for inbound handler requests.
- Prefer `ResponseRecorder.Result()` for final status and headers.
- Test exact routes, method mismatches, implicit status, middleware order, and limits.
- Test that terminal error responses return before downstream mutation or success output.
- Use `httptest.Server` when wire-level client/server behavior matters.
- Test client disconnect, slow readers, flush failure, partial streams, and
  shutdown before and after response commitment.
- Exercise shared services concurrently and run the race detector.
