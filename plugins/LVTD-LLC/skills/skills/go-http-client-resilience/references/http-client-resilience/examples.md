# HTTP Client Resilience Examples

## Clone a Baseline Transport

```go
transport := http.DefaultTransport.(*http.Transport).Clone()
transport.MaxIdleConns = 100
transport.MaxIdleConnsPerHost = 10
transport.MaxConnsPerHost = 20
```

Treat these values as workload-specific examples. Own the client and transport
for the application lifetime and close idle connections during cleanup when
appropriate.

## Testable Client

```go
type Doer interface {
	Do(*http.Request) (*http.Response, error)
}

type Client struct {
	http    Doer
	baseURL *url.URL
	token   string
}
```

The interface sits at the consumer and contains only the operation needed.

## Function-Backed Transport

```go
type roundTripFunc func(*http.Request) (*http.Response, error)

func (f roundTripFunc) RoundTrip(r *http.Request) (*http.Response, error) {
	return f(r)
}

httpClient := &http.Client{Transport: roundTripFunc(func(r *http.Request) (*http.Response, error) {
	return &http.Response{
		StatusCode: http.StatusOK,
		Header:     make(http.Header),
		Body:       io.NopCloser(strings.NewReader(`{"id":"p1"}`)),
		Request:    r,
	}, nil
})}
```

## Bounded Error Body

```go
const maxErrorBody = 64 << 10
body, err := io.ReadAll(io.LimitReader(resp.Body, maxErrorBody+1))
if err != nil {
	return fmt.Errorf("read error response: %w", err)
}
if len(body) > maxErrorBody {
	return fmt.Errorf("remote error body exceeds %d bytes", maxErrorBody)
}
```

Sanitize before including any body fragment in an error or log.

## Retry Skeleton

```go
type waitFunc func(context.Context, time.Duration) error

for attempt := 1; attempt <= maxAttempts; attempt++ {
	req, err := newRequest(ctx) // recreates any replayable body
	if err != nil {
		return err
	}
	resp, err := c.http.Do(req)
	if !retryable(req, resp, err) {
		return classifyAndClose(resp, err)
	}
	closeBounded(resp) // drain within a limit, then close
	if attempt == maxAttempts {
		return &RetryExhaustedError{Attempts: attempt, Err: err}
	}
	if err := wait(ctx, delay(attempt, resp)); err != nil {
		return err
	}
}
```

Inject the waiter, clock, and jitter source so schedule tests use no wall-clock
sleep. `RetryExhaustedError` should preserve the final classified cause and safe
status context. Keep one total operation context.
