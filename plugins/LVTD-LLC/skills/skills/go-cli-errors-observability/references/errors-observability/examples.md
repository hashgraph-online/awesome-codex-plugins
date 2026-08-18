# Errors and Observability Examples

## Joined Error Classification

```go
err := errors.Join(flushErr, closeErr)
if errors.Is(err, context.Canceled) {
	// Preserve cancellation policy even when cleanup also failed.
}
var pathErr *os.PathError
if errors.As(err, &pathErr) {
	// Add safe path-operation context without parsing prose.
}
```

Do not walk only `errors.Unwrap() error`; joined errors use a multi-error tree.

## Typed Classification

```go
type UsageError struct {
	Field string
	Err   error
}

func (e *UsageError) Error() string { return "invalid " + e.Field + ": " + e.Err.Error() }
func (e *UsageError) Unwrap() error { return e.Err }
```

The process boundary can classify with `errors.As` while the command returns the
underlying error normally.

## Structured Logging

```go
logger.ErrorContext(ctx, "request failed",
	"operation", "list_projects",
	"status_code", resp.StatusCode,
	"request_id", requestID,
)
```

Do not add the authorization header, response body, or raw URL query unless each
field is reviewed and sanitized.

## Safe Exit Mapping

```go
func exitCode(err error, interrupted bool) int {
	switch {
	case err == nil:
		return 0
	case interrupted && errors.Is(err, context.Canceled):
		return 130
	case errors.Is(err, context.Canceled):
		return 1
	case errors.Is(err, context.DeadlineExceeded):
		return 1
	default:
		var usage *UsageError
		if errors.As(err, &usage) {
			return 2
		}
		return 1
	}
}
```

Set `interrupted` only when the process boundary observed an OS interrupt.
Internal cancellation, remote cancellation, and declined prompts must retain
their own classification. Treat numeric choices as contractual once published.
