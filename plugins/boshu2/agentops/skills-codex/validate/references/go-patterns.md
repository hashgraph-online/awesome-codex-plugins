# Go Patterns Quick Reference - Vibe

Quick reference for Go patterns. Copy-paste these examples when writing new code.

---

## Error Handling

### ✅ Wrap Errors with %w

```go
// DO THIS
if err != nil {
    return fmt.Errorf("failed to initialize: %w", err)
}

// NOT THIS - Breaks error chains (triggers P14)
if err != nil {
    return fmt.Errorf("failed to initialize: %v", err)
}
```

**Prescan:** P14 detects `%v` in `fmt.Errorf` when wrapping errors

### ✅ Custom Error Creation

```go
// Define custom error type
type AppError struct {
    Code    string
    Message string
    Cause   error
}

func (e *AppError) Error() string {
    if e.Cause != nil {
        return fmt.Sprintf("[%s] %s: %v", e.Code, e.Message, e.Cause)
    }
    return fmt.Sprintf("[%s] %s", e.Code, e.Message)
}

func (e *AppError) Unwrap() error { return e.Cause }

func (e *AppError) Is(target error) bool {
    t, ok := target.(*AppError)
    return ok && e.Code == t.Code
}

// Use with errors.Is() and errors.As()
if errors.Is(err, &AppError{Code: "NOT_FOUND"}) {
    // Handle not found
}

var appErr *AppError
if errors.As(err, &appErr) {
    log.Printf("Error code: %s", appErr.Code)
}
```

### ✅ Document Intentional Error Ignores

```go
// DO THIS (passes P13)
defer func() {
    _ = conn.Close() // nolint:errcheck - best effort cleanup
}()

// NOT THIS (triggers P13)
defer func() {
    _ = conn.Close() // Silent ignore
}()
```

**Prescan:** P13 detects `_ =` without `nolint:errcheck` comment

---

## Concurrency

### ✅ Always Use context.Context

```go
// DO THIS
func (c *Client) SendTask(ctx context.Context, task *Task) error {
    req, err := http.NewRequestWithContext(ctx, "POST", url, body)
    if err != nil {
        return fmt.Errorf("creating request: %w", err)
    }
    // ...
}

// NOT THIS - No cancellation support
func (c *Client) SendTask(task *Task) error {
    req, err := http.NewRequest("POST", url, body)
    // ...
}
```

### ✅ WaitGroup Pattern

```go
var wg sync.WaitGroup
for name, agent := range agents {
    wg.Add(1)

    // CRITICAL: Capture loop variables
    name := name
    agent := agent

    go func() {
        defer wg.Done() // Always defer, protects against panic

        if err := agent.Process(ctx); err != nil {
            mu.Lock()
            results[name] = err
            mu.Unlock()
        }
    }()
}
wg.Wait()
```

**Common Mistake:** Forgetting to capture loop variables causes race conditions

### ✅ Mutex for Shared State

```go
type Registry struct {
    items map[string]Item
    mu    sync.RWMutex // Read-write mutex
}

// Read operations use RLock (concurrent reads OK)
func (r *Registry) Get(name string) (Item, error) {
    r.mu.RLock()
    defer r.mu.RUnlock()
    item, ok := r.items[name]
    if !ok {
        return Item{}, ErrNotFound
    }
    return item, nil
}

// Write operations use Lock (exclusive)
func (r *Registry) Register(name string, item Item) error {
    r.mu.Lock()
    defer r.mu.Unlock()
    r.items[name] = item
    return nil
}
```

### ✅ Backpressure in Channels

```go
select {
case eventChan <- event:
    // Event sent successfully
case <-time.After(30 * time.Second):
    return fmt.Errorf("event channel blocked - consumer too slow")
case <-ctx.Done():
    return ctx.Err()
}
```

**Why:** Prevents unbounded memory growth from fast producer, slow consumer

---

## Security

### ✅ Constant-Time Comparison

```go
import "crypto/subtle"

// DO THIS - Timing attack resistant
if subtle.ConstantTimeCompare([]byte(token), []byte(expectedToken)) != 1 {
    return ErrUnauthorized
}

// NOT THIS - Vulnerable to timing attacks
if token == expectedToken {
    // Attacker can brute-force byte-by-byte
}
```

**Use Cases:** API keys, tokens, passwords, secrets

### ✅ HMAC Signature Validation

```go
import (
    "crypto/hmac"
    "crypto/sha256"
    "encoding/hex"
)

func validateHMAC(payload []byte, signature, secret string) bool {
    expectedMAC := hmac.New(sha256.New, []byte(secret))
    expectedMAC.Write(payload)
    expected := hex.EncodeToString(expectedMAC.Sum(nil))

    // Use constant-time comparison
    return hmac.Equal([]byte(expected), []byte(signature))
}
```

**Use Cases:** Webhook signatures (GitHub, GitLab, Slack)

### ✅ Timestamp Validation (Replay Attack Prevention)

```go
func validateTimestamp(ts string, maxAge time.Duration) error {
    timestamp, err := time.Parse(time.RFC3339, ts)
    if err != nil {
        return fmt.Errorf("invalid timestamp: %w", err)
    }

    age := time.Since(timestamp)
    if age > maxAge {
        return fmt.Errorf("timestamp too old: %v > %v", age, maxAge)
    }
    if age < -1*time.Minute {
        return fmt.Errorf("timestamp in future: %v", age)
    }

    return nil
}
```

**Typical maxAge:** 5 minutes for webhooks, 1 minute for API requests

---

## HTTP Clients

### ✅ Proper Body Handling

```go
resp, err := client.Do(req)
if err != nil {
    return fmt.Errorf("request failed: %w", err)
}
defer func() {
    if err := resp.Body.Close(); err != nil {
        log.Printf("Failed to close response body: %v", err)
    }
}()

body, err := io.ReadAll(resp.Body)
if err != nil {
    return fmt.Errorf("reading response: %w", err)
}
```

**CRITICAL:** Always close response body, even on error paths

### ✅ Retry Logic with Exponential Backoff

```go
func (c *Client) doWithRetry(ctx context.Context, req *http.Request) (*http.Response, error) {
    var lastErr error

    for attempt := 0; attempt < c.maxRetries; attempt++ {
        if attempt > 0 {
            backoff := time.Duration(math.Pow(2, float64(attempt))) * time.Second
            select {
            case <-time.After(backoff):
            case <-ctx.Done():
                return nil, ctx.Err()
            }
        }

        resp, err := c.httpClient.Do(req)
        if err != nil {
            lastErr = err
            continue
        }

        // Retry on 5xx
        if resp.StatusCode >= 500 {
            _ = resp.Body.Close() // nolint:errcheck - best effort
            lastErr = fmt.Errorf("server error: %d", resp.StatusCode)
            continue
        }

        return resp, nil
    }

    return nil, fmt.Errorf("max retries exceeded: %w", lastErr)
}
```

---

## Interface Design

### ✅ Accept Interfaces, Return Structs

```go
// Define interface
type Processor interface {
    Process(ctx context.Context, data []byte) error
}

// Functions accept interface (flexible for testing)
func RunPipeline(ctx context.Context, processor Processor, data []byte) error {
    if err := processor.Process(ctx, data); err != nil {
        return fmt.Errorf("processing failed: %w", err)
    }
    return nil
}

// Constructors return struct (concrete)
func NewDataProcessor() *DataProcessor {
    return &DataProcessor{
        cache: make(map[string][]byte),
        mu:    sync.RWMutex{},
    }
}
```

**Why:** Callers can pass any implementation (testability), return type can add methods

### ✅ Small, Focused Interfaces

```go
// DO THIS - Single responsibility
type Initializer interface {
    Initialize(ctx context.Context) error
}

type Processor interface {
    Process(ctx context.Context, data []byte) error
}

// Compose when needed
type Service interface {
    Initializer
    Processor
}

// NOT THIS - God interface
type Service interface {
    Initialize(ctx context.Context) error
    Process(ctx context.Context, data []byte) error
    Shutdown(ctx context.Context) error
    HealthCheck(ctx context.Context) error
    GetMetrics() *Metrics
    SetConfig(cfg *Config)
    // ... 20 more methods
}
```

---

## Testing

### ✅ Table-Driven Tests

```go
func TestValidateEmail(t *testing.T) {
    tests := []struct {
        name    string
        email   string
        wantErr bool
    }{
        {"valid", "user@example.com", false},
        {"missing @", "userexample.com", true},
        {"empty", "", true},
        {"no domain", "user@", true},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            err := ValidateEmail(tt.email)
            if (err != nil) != tt.wantErr {
                t.Errorf("ValidateEmail(%q) error = %v, wantErr %v",
                    tt.email, err, tt.wantErr)
            }
        })
    }
}
```

### ✅ Test Helpers

```go
func setupTestServer(t *testing.T) *httptest.Server {
    t.Helper() // Mark as helper - failures report caller line

    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // Mock responses
    }))

    t.Cleanup(func() {
        server.Close()
    })

    return server
}

func TestClient(t *testing.T) {
    server := setupTestServer(t) // Failures report this line, not inside helper
    client := NewClient(server.URL)
    // ... test code
}
```

### ✅ Mock Interfaces

```go
// Define mockable interface
type Repository interface {
    GetUser(ctx context.Context, id string) (*User, error)
}

// Create mock
type MockRepository struct {
    GetUserFn func(ctx context.Context, id string) (*User, error)
}

func (m *MockRepository) GetUser(ctx context.Context, id string) (*User, error) {
    if m.GetUserFn != nil {
        return m.GetUserFn(ctx, id)
    }
    return nil, nil
}

// Use in tests
func TestService(t *testing.T) {
    mock := &MockRepository{
        GetUserFn: func(ctx context.Context, id string) (*User, error) {
            return &User{ID: id, Name: "Test"}, nil
        },
    }

    service := NewService(mock)
    user, err := service.FetchUser(ctx, "123")
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
    if user.Name != "Test" {
        t.Errorf("got name %q, want %q", user.Name, "Test")
    }
}
```

---

## Common Mistakes to Avoid

### ❌ Don't: Ignore Context

```go
// BAD
func (c *Client) Send(req *Request) error {
    // No way to cancel or timeout
    return c.process(req)
}

// GOOD
func (c *Client) Send(ctx context.Context, req *Request) error {
    select {
    case result := <-c.process(req):
        return result
    case <-ctx.Done():
        return ctx.Err()
    }
}
```

### ❌ Don't: Use Pointer to Interface

```go
// BAD
func Process(agent *Agent) error { // Interface is already a reference
    // ...
}

// GOOD
func Process(agent Agent) error {
    // ...
}
```

### ❌ Don't: Naked Returns with Named Results

```go
// BAD
func calculate() (result int, err error) {
    result = 42
    return // What's being returned? Unclear!
}

// GOOD
func calculate() (int, error) {
    result := 42
    return result, nil // Explicit and clear
}
```

### ❌ Don't: Use panic in Library Code

```go
// BAD
func GetItem(key string) Item {
    item, ok := registry[key]
    if !ok {
        panic("item not found") // Caller can't recover
    }
    return item
}

// GOOD
func GetItem(key string) (Item, error) {
    item, ok := registry[key]
    if !ok {
        return Item{}, ErrItemNotFound
    }
    return item, nil
}
```

### ❌ Don't: Forget to Capture Loop Variables

```go
// BAD
for _, item := range items {
    go func() {
        process(item) // Race condition! All goroutines see last item
    }()
}

// GOOD
for _, item := range items {
    item := item // Capture variable
    go func() {
        process(item) // Each goroutine has its own copy
    }()
}
```

### ❌ Don't: Leak Goroutines

```go
// BAD - Goroutine never exits
go func() {
    for {
        work() // No way to stop
    }
}()

// GOOD - Context-based cancellation
go func() {
    for {
        select {
        case <-ctx.Done():
            return
        default:
            work()
        }
    }
}()
```

---

## Code Review Checklist

Before submitting PR, verify:

- [ ] All errors wrapped with `%w` (P14 passing)
- [ ] All long operations accept `context.Context`
- [ ] All `defer` statements have error checking where needed
- [ ] Loop variables captured before goroutines
- [ ] HTTP response bodies closed with defer
- [ ] Secrets compared with `subtle.ConstantTimeCompare()`
- [ ] Intentional error ignores documented with `nolint:errcheck` (P13 passing)
- [ ] Tests use table-driven pattern
- [ ] Test helpers use `t.Helper()`
- [ ] Interfaces are small and focused
- [ ] Functions return concrete types (not interfaces)
- [ ] golangci-lint passes (P15)
- [ ] gofmt applied
- [ ] Complexity < 10 per function

---

## golangci-lint Commands

```bash
# Run all linters
golangci-lint run ./...

# Run specific linter
golangci-lint run --enable=errcheck ./...

# Fix auto-fixable issues
golangci-lint run --fix ./...

# Show configuration
golangci-lint linters
```

---

## Useful Commands

```bash
# Format code
gofmt -w .

# Check formatting
gofmt -l .

# Vet code
go vet ./...

# Run tests
go test ./...

# Run tests with coverage
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out

# Check for race conditions
go test -race ./...

# Build all binaries
go build ./cmd/...

# Tidy dependencies
go mod tidy

# Check cyclomatic complexity
gocyclo -over 10 .
```

---

## Prescan Pattern Reference

| Pattern | Severity | Triggers On |
|---------|----------|-------------|
| P13 | HIGH | `_ =` without `nolint:errcheck` comment |
| P14 | MEDIUM | `fmt.Errorf.*%v` when wrapping errors |
| P15 | HIGH | golangci-lint violations (requires golangci-lint installed) |

Run prescan: `~/.claude/skills/validate/scripts/prescan.sh recent`

---

## Additional Resources

- [Effective Go](https://go.dev/doc/effective_go)
- [Go Code Review Comments](https://github.com/golang/go/wiki/CodeReviewComments)
- [Go Proverbs](https://go-proverbs.github.io/)
- [golangci-lint Linters](https://golangci-lint.run/usage/linters/)
- [errcheck](https://github.com/kisielk/errcheck)

---

**See Also:** `go-standards.md` for comprehensive catalog with detailed explanations
