# Go Standards Catalog - Vibe Canonical Reference

**Version:** 1.0.0
**Last Updated:** 2026-01-20
**Purpose:** Canonical Go standards for vibe skill validation

---

## Table of Contents

1. [Error Handling Patterns](#error-handling-patterns)
2. [Interface Design](#interface-design)
3. [Concurrency Patterns](#concurrency-patterns)
4. [Security Practices](#security-practices)
5. [Package Organization](#package-organization)
6. [Testing Patterns](#testing-patterns)
7. [Documentation Standards](#documentation-standards)
8. [Code Quality Metrics](#code-quality-metrics)
9. [Anti-Patterns Avoided](#anti-patterns-avoided)

---

## Error Handling Patterns

### ✅ **Custom Error Types**

Production-grade error types follow these patterns:

```go
type AppError struct {
    Code     string        // Machine-readable error code
    Message  string        // Human-readable message
    Cause    error         // Wrapped error (optional)
    Metadata map[string]any // Additional context
}

// Implements error interface
func (e *AppError) Error() string {
    if e.Cause != nil {
        return fmt.Sprintf("[%s] %s: %v", e.Code, e.Message, e.Cause)
    }
    return fmt.Sprintf("[%s] %s", e.Code, e.Message)
}

// Supports errors.Unwrap()
func (e *AppError) Unwrap() error {
    return e.Cause
}

// Supports errors.Is() for sentinel comparison
func (e *AppError) Is(target error) bool {
    t, ok := target.(*AppError)
    if !ok {
        return false
    }
    return e.Code == t.Code
}
```

**Requirements:**
- ✅ Implements `error` interface
- ✅ Implements `Unwrap()` for error chain inspection
- ✅ Implements `Is()` for sentinel error comparison
- ✅ Structured error codes enable programmatic handling
- ✅ Preserves context with metadata
- ✅ Proper nil-safety in `Unwrap()` and `Is()`

### ✅ **Error Wrapping with %w**

Use `fmt.Errorf` with `%w` verb for error wrapping:

```go
// CORRECT
resp, err := client.Do(req)
if err != nil {
    return nil, fmt.Errorf("sending request: %w", err)
}

// INCORRECT - Breaks error chains
if err != nil {
    return nil, fmt.Errorf("sending request: %v", err)
}
```

**Why This Matters:**
- `%w` preserves error chain for `errors.Is()` and `errors.As()`
- `%v` breaks the chain - root cause is lost
- Error context adds debugging information

### ⚠️ **Intentional Error Ignores**

Document why errors are intentionally ignored:

```go
// CORRECT
defer func() {
    _ = conn.Close() // nolint:errcheck - best effort cleanup
}()

// INCORRECT - Silent ignore
defer func() {
    _ = conn.Close()
}()
```

**Validation:** Prescan pattern P13 detects undocumented ignores

---

## Interface Design

### ✅ **Accept Interfaces, Return Structs**

**Pattern:**
```go
// Define interface
type Agent interface {
    Initialize(ctx context.Context) error
    Invoke(ctx context.Context, req *Request) (*Response, error)
}

// Functions accept interface (flexible)
func ProcessAgent(ctx context.Context, agent Agent) error {
    if err := agent.Initialize(ctx); err != nil {
        return fmt.Errorf("initialization failed: %w", err)
    }
    // ...
}

// Constructors return struct (concrete)
func NewRegistry() *Registry {
    return &Registry{
        agents: make(map[string]Agent),
        mu:     sync.RWMutex{},
    }
}
```

**Why This Matters:**
- Callers can pass any implementation (testability)
- Return type can add methods without breaking callers
- Follows Go proverb: "Be conservative in what you send, liberal in what you accept"

### ✅ **Small, Focused Interfaces**

**Good Example:**
```go
type Initializer interface {
    Initialize(ctx context.Context) error
}

type Invoker interface {
    Invoke(ctx context.Context, req *Request) (*Response, error)
}

// Compose interfaces
type Agent interface {
    Initializer
    Invoker
}
```

**Anti-Pattern (God Interface):**
```go
type Agent interface {
    Initialize(ctx context.Context) error
    Invoke(ctx context.Context, req *Request) (*Response, error)
    Shutdown(ctx context.Context) error
    HealthCheck(ctx context.Context) error
    GetMetrics() *Metrics
    SetConfig(cfg *Config)
    // ... 20 more methods
}
```

---

## Concurrency Patterns

### ✅ **Context Propagation** (Required)

Every I/O or long-running operation accepts `context.Context`:

```go
// HTTP Requests
req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, body)

// Database Operations
rows, err := db.QueryContext(ctx, query)

// Custom Functions
func (c *Client) Invoke(ctx context.Context, req *Request) (*Response, error)
```

**Benefits:**
- Timeout propagation
- Cancellation support
- Request-scoped values (tracing)

### ✅ **Proper WaitGroup Usage**

```go
var wg sync.WaitGroup
for name, agent := range agents {
    wg.Add(1)

    // Capture loop variables
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

**Requirements:**
- ✅ Variables captured before goroutine (avoids closure bug)
- ✅ `defer wg.Done()` ensures decrement on panic
- ✅ Mutex protects shared data structures
- ✅ Context cancellation checked in each goroutine

### ✅ **Thread-Safe Data Structures**

```go
type Registry struct {
    items map[string]Item
    mu    sync.RWMutex // Read-write mutex
}

// Read operations use RLock
func (r *Registry) Get(key string) (Item, error) {
    r.mu.RLock()
    defer r.mu.RUnlock()
    // ...
}

// Write operations use Lock
func (r *Registry) Set(key string, item Item) error {
    r.mu.Lock()
    defer r.mu.Unlock()
    // ...
}
```

**Pattern Benefits:**
- Multiple concurrent reads
- Exclusive writes
- Zero race conditions

### ✅ **Backpressure in Streaming**

```go
select {
case eventChan <- event:
    // Event sent successfully
case <-time.After(30 * time.Second):
    return fmt.Errorf("event channel blocked - consumer too slow (backpressure triggered)")
case <-ctx.Done():
    return ctx.Err()
}
```

**Why This Matters:**
- Prevents unbounded memory growth
- Handles fast producer, slow consumer scenario
- Explicit timeout for debugging

---

## Security Practices

### ✅ **Constant-Time Comparison** (Timing Attack Prevention)

```go
import "crypto/subtle"

// CORRECT - Timing attack resistant
token := r.Header.Get("Authorization")
if subtle.ConstantTimeCompare([]byte(token), []byte(expectedToken)) != 1 {
    return ErrUnauthorized
}

// INCORRECT - Vulnerable to timing attacks
if token == expectedToken {
    // Attacker can brute-force byte-by-byte
}
```

**Why This Matters:**
- String comparison (`==`) leaks timing information
- Attacker can brute-force secrets byte-by-byte
- `subtle.ConstantTimeCompare()` runs in constant time
- Critical for API keys, tokens, passwords

### ✅ **HMAC Signature Validation**

```go
import (
    "crypto/hmac"
    "crypto/sha256"
    "encoding/hex"
)

func validateHMAC(payload []byte, signature, secret string) bool {
    if !strings.HasPrefix(signature, "sha256=") {
        return false
    }

    expectedMAC := hmac.New(sha256.New, []byte(secret))
    expectedMAC.Write(payload)
    expected := "sha256=" + hex.EncodeToString(expectedMAC.Sum(nil))

    return hmac.Equal([]byte(expected), []byte(signature))
}
```

**Security Features:**
- ✅ HMAC prevents payload tampering
- ✅ Uses `hmac.Equal()` (constant-time)
- ✅ Verifies signature format first
- ✅ SHA-256 (secure hash function)

### ✅ **Replay Attack Prevention**

```go
func validateTimestamp(timestamp string, maxAge time.Duration) error {
    ts, err := time.Parse(time.RFC3339, timestamp)
    if err != nil {
        return fmt.Errorf("invalid timestamp format")
    }

    age := time.Since(ts)
    if age > maxAge || age < -1*time.Minute {
        return fmt.Errorf("request too old or in future: age=%v max=%v", age, maxAge)
    }

    return nil
}
```

**Protection Against:**
- Replay attacks (old requests resubmitted)
- Clock skew (1 minute tolerance for future timestamps)
- DoS via timestamp manipulation

### ✅ **TLS Configuration**

```go
tlsConfig := &tls.Config{
    MinVersion: tls.VersionTLS13, // Only TLS 1.3+
    // No InsecureSkipVerify - validates certificates
}
```

---

## Package Organization

### ✅ **Layered Architecture**

```
project/
├── cmd/                    # Binaries (main packages)
│   ├── server/            # Server binary
│   ├── worker/            # Worker binary
│   └── cli/               # CLI tool
├── internal/              # Private packages (cannot be imported externally)
│   ├── domain/            # Business logic
│   ├── handlers/          # HTTP handlers
│   ├── repository/        # Data access
│   └── sdk/               # External SDK clients
├── pkg/                   # Public packages (can be imported)
│   ├── api/              # API types
│   └── client/           # Client library
└── tests/                # Test suites
    ├── e2e/              # End-to-end tests
    └── integration/      # Integration tests
```

**Principles:**
- ✅ `cmd/` for binaries (no importable code)
- ✅ `internal/` prevents external imports
- ✅ `pkg/` for public APIs
- ✅ Domain-driven structure
- ✅ Tests at package level, e2e/integration separate

### ✅ **Import Grouping** (Go Convention)

```go
import (
    // Standard library
    "context"
    "fmt"
    "time"

    // External dependencies
    "github.com/external/package"

    // Internal packages
    "myproject.com/internal/domain"
)
```

---

## Testing Patterns

### ✅ **Table-Driven Tests**

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

**Benefits:**
- Easy to add test cases
- Clear test names with `t.Run()`
- DRY (Don't Repeat Yourself)

### ✅ **Test Helpers with t.Helper()**

```go
func setupTestServer(t *testing.T) *httptest.Server {
    t.Helper() // Marks this as a helper function

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
    // ... test code
}
```

**Why t.Helper() Matters:**
- Test failures report the *calling* line, not helper line
- Makes test output more useful
- Standard Go testing pattern

### ✅ **Mock Interfaces**

```go
// Define mockable interface
type Invoker interface {
    Invoke(ctx context.Context, req *Request) (*Response, error)
}

// Create mock
type MockInvoker struct {
    InvokeFn func(ctx context.Context, req *Request) (*Response, error)
}

func (m *MockInvoker) Invoke(ctx context.Context, req *Request) (*Response, error) {
    if m.InvokeFn != nil {
        return m.InvokeFn(ctx, req)
    }
    return nil, nil
}

// Use in tests
func TestProcessor(t *testing.T) {
    mock := &MockInvoker{
        InvokeFn: func(ctx context.Context, req *Request) (*Response, error) {
            return &Response{Status: "success"}, nil
        },
    }

    processor := NewProcessor(mock)
    // ... test with mock
}
```

### Test Double Types

| Type | Purpose | When to Use |
|------|---------|-------------|
| **Stub** | Returns canned data | Simple happy path |
| **Mock** | Verifies interactions | Behavior verification |
| **Fake** | Working implementation | Integration-like tests |
| **Spy** | Records calls | Interaction counting |

---

## Documentation Standards

### ✅ **Godoc Format**

Document all exported symbols with a comment directly above the declaration:

```go
// Registry manages agent lifecycle and discovery.
// It is safe for concurrent use.
type Registry struct {
    agents map[string]Agent
    mu     sync.RWMutex
}

// Get returns the agent registered under the given key.
// It returns ErrNotFound if no agent is registered with that key.
func (r *Registry) Get(key string) (Agent, error) {
    // ...
}
```

**Rules:**
- Comment starts with the name of the symbol
- First sentence is a complete summary (used by `go doc -short`)
- Use `//` comments, not `/* */` blocks (except for package-level docs)

### ✅ **Package-Level Comments**

For packages with significant public API, use a `doc.go` file:

```go
// Package registry provides agent lifecycle management
// including registration, discovery, and health monitoring.
//
// Basic usage:
//
//	reg := registry.New()
//	reg.Register("my-agent", agent)
//	a, err := reg.Get("my-agent")
package registry
```

**When to use `doc.go`:**
- Package has 3+ exported symbols
- Package is part of a public API (`pkg/`)
- Package needs usage examples beyond a single line

### ✅ **Testable Examples**

Write `Example*` functions in `_test.go` files — they appear in generated docs and are compiled/run by `go test`:

```go
func ExampleRegistry_Get() {
    reg := registry.New()
    reg.Register("agent-1", &MyAgent{Name: "alpha"})

    agent, err := reg.Get("agent-1")
    if err != nil {
        log.Fatal(err)
    }
    fmt.Println(agent.Name)
    // Output: alpha
}
```

**Naming Convention:**
- `ExampleTypeName` — type-level example
- `ExampleTypeName_MethodName` — method-level example
- `Example` — package-level example

### ✅ **Doc Generation**

```bash
# View docs in terminal
go doc ./pkg/registry
go doc ./pkg/registry.Registry.Get

# Run local doc server (pkgsite)
go install golang.org/x/pkgsite/cmd/pkgsite@latest
pkgsite -open .
```

### ✅ **Interface Documentation**

Interfaces define contracts — document the behavioral expectations, not just the signature:

```go
// Store persists agent state across restarts.
//
// Implementations must be safe for concurrent use.
// All methods must respect context cancellation.
type Store interface {
    // Save persists the agent. It returns ErrConflict if the agent
    // was modified since it was last read (optimistic locking).
    Save(ctx context.Context, agent *Agent) error

    // Load retrieves an agent by ID. It returns ErrNotFound if
    // no agent exists with the given ID.
    Load(ctx context.Context, id string) (*Agent, error)
}
```

**Guidelines:**
- Document concurrency guarantees on the interface comment
- Document error contracts on each method (which sentinel errors are returned)
- Document preconditions and postconditions when non-obvious

### ✅ **Internal Package Documentation**

`internal/` packages cannot be imported outside the module, but still need documentation for team maintainability:

```go
// Package repository implements data access for agent storage.
//
// This is an internal package — it should not be imported outside
// the module. Use pkg/client for the public API.
package repository
```

**Guidelines:**
- Every `internal/` package needs a package comment explaining its role
- Note the public alternative if one exists (e.g., `pkg/client`)
- Document non-obvious design constraints (e.g., "not safe for concurrent use")

### ✅ **Package README Files**

For packages with significant scope, include a `README.md` alongside the Go source:

```
pkg/registry/
├── README.md          # Setup instructions, architecture notes
├── doc.go             # Godoc package comment
├── registry.go        # Implementation
└── registry_test.go   # Tests with examples
```

**When to include a README:**
- Package requires setup steps (config, env vars, migrations)
- Package has architecture or design decisions worth explaining
- Package is a top-level entry point (`cmd/`, major `pkg/` packages)

**README vs doc.go:**
- `doc.go` → API usage shown in `go doc` output
- `README.md` → Setup, architecture, diagrams, non-API context

### ✅ **Comment Style**

Follow Go's documentation conventions for consistent, tooling-friendly comments:

```go
// ProcessBatch sends all queued events to the remote collector.
// It returns the number of events successfully delivered and
// a non-nil error if the connection to the collector fails.
//
// ProcessBatch is safe for concurrent use. Each call acquires
// a connection from the pool and releases it on return.
func (c *Client) ProcessBatch(ctx context.Context) (int, error) {
    // ...
}

// ErrRateLimited is returned when the collector rejects a request
// due to rate limiting. Callers should back off and retry.
var ErrRateLimited = errors.New("rate limited")
```

**Rules:**
- Write complete sentences with proper punctuation
- First word is the name of the declared thing (`ProcessBatch sends...`, `ErrRateLimited is...`)
- First sentence stands alone as a summary — `go doc -short` shows only this
- Use third-person declarative ("ProcessBatch sends...") not imperative ("Send...")
- Separate paragraphs with a blank `//` line
- Use `[Registry.Get]` syntax (Go 1.19+) to link to other symbols in doc comments
- Keep line length under 80 characters for readability in terminals

**Anti-Patterns:**
```go
// BAD - Doesn't start with symbol name
// This function processes a batch of events.
func (c *Client) ProcessBatch(ctx context.Context) (int, error)

// BAD - Not a complete sentence
// process batch
func (c *Client) ProcessBatch(ctx context.Context) (int, error)

// BAD - Imperative instead of declarative
// Send all queued events to the remote collector.
func (c *Client) ProcessBatch(ctx context.Context) (int, error)
```

### ALWAYS / NEVER Rules

| Rule | Rationale |
|------|-----------|
| **ALWAYS** document exported types, functions, and methods | Required by `revive` linter, enables `go doc` |
| **ALWAYS** start doc comments with the symbol name | Standard godoc convention, enables tooling |
| **ALWAYS** write doc comments as complete sentences | Consistent style, readable in `go doc` output |
| **ALWAYS** include `// Output:` in Example functions | Makes examples testable by `go test` |
| **ALWAYS** document interface contracts (thread-safety, errors, lifecycle) | Callers depend on the contract, not the implementation |
| **NEVER** document unexported symbols unless logic is non-obvious | Noise — internal code changes frequently |
| **NEVER** use `@param` / `@return` javadoc-style annotations | Not idiomatic Go — godoc ignores them |
| **NEVER** duplicate the function signature in prose | Redundant — the signature is right below |
| **NEVER** use imperative voice in doc comments | Go convention is declarative third-person |

---

## Structured Logging (slog)

### ✅ **Use log/slog (Go 1.21+)**

```go
import "log/slog"

func main() {
    // Production: JSON handler for log aggregation
    logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
        Level: slog.LevelInfo,
    }))
    slog.SetDefault(logger)

    // Include correlation IDs for tracing
    slog.Info("request processed",
        "request_id", reqID,
        "user_id", userID,
        "duration_ms", duration.Milliseconds(),
    )
}
```

### Handler Selection

| Environment | Handler | Use Case |
|-------------|---------|----------|
| Production | `slog.JSONHandler` | Elasticsearch, Loki, CloudWatch |
| Development | `slog.TextHandler` | Human-readable console output |

### ❌ **Logging Anti-Patterns**

| Pattern | Problem | Instead |
|---------|---------|---------|
| `fmt.Println` in library | Not parseable, no levels | Use `slog.Info` |
| `log.Printf` | No structure | Use `slog` with attributes |
| Logging secrets | Security risk | Use `ReplaceAttr` to redact |
| Missing correlation ID | Can't trace requests | Always include request_id |

> **Talos check:** PRE-007 detects `fmt.Print*` debug statements in non-CLI code.

---

## Benchmarking and Profiling

### ✅ **Writing Benchmarks**

```go
func BenchmarkProcess(b *testing.B) {
    data := setupTestData()
    b.ResetTimer() // Exclude setup from timing

    for i := 0; i < b.N; i++ {
        Process(data)
    }
}

// Memory allocation benchmark
func BenchmarkProcessAllocs(b *testing.B) {
    data := setupTestData()
    b.ResetTimer()
    b.ReportAllocs()
    for i := 0; i < b.N; i++ {
        Process(data)
    }
}
```

### Running Benchmarks

```bash
# Run benchmarks
go test -bench=. -benchmem ./...

# Compare before/after
go test -bench=. -count=10 > old.txt
# make changes
go test -bench=. -count=10 > new.txt
benchstat old.txt new.txt
```

### ✅ **Profiling with pprof**

```go
import _ "net/http/pprof"

// Profiles available at:
// /debug/pprof/profile  - CPU profile
// /debug/pprof/heap     - Memory profile
// /debug/pprof/goroutine - Goroutine stacks
```

**Analyze Profiles:**
```bash
# CPU profile (30 seconds)
go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30

# Memory profile
go tool pprof http://localhost:6060/debug/pprof/heap

# Interactive commands
(pprof) top10      # Top 10 functions
(pprof) web        # Open flame graph in browser
```

---

## Configuration Management

### ✅ **Single Config Struct Pattern**

```go
type Config struct {
    Server   ServerConfig   `yaml:"server"`
    Database DatabaseConfig `yaml:"database"`
    Log      LogConfig      `yaml:"log"`
}

type ServerConfig struct {
    Port         int           `yaml:"port" env:"PORT"`
    ReadTimeout  time.Duration `yaml:"read_timeout"`
    WriteTimeout time.Duration `yaml:"write_timeout"`
}

// Load with precedence: flags > env > file > defaults
func Load() (*Config, error) {
    cfg := &Config{}
    setDefaults(cfg)
    if err := loadFromFile(cfg); err != nil {
        return nil, fmt.Errorf("load config file: %w", err)
    }
    loadFromEnv(cfg)
    if err := cfg.Validate(); err != nil {
        return nil, fmt.Errorf("validate config: %w", err)
    }
    return cfg, nil
}
```

### ❌ **Configuration Anti-Patterns**

| Pattern | Problem | Instead |
|---------|---------|---------|
| Global config var | Hard to test | Pass as dependency |
| Reading env in functions | Scattered config | Centralize in Load() |
| No validation | Runtime errors | Validate at startup |
| Secrets in config files | Security risk | Use env vars or vault |

---

## HTTP API Standards

### ✅ **API Versioning**

```go
mux := http.NewServeMux()

// Health endpoints (unversioned - K8s standard)
mux.HandleFunc("/health", healthHandler)
mux.HandleFunc("/healthz", healthHandler)   // K8s liveness
mux.HandleFunc("/readyz", readyHandler)     // K8s readiness

// API v1
mux.HandleFunc("/v1/webhook/gitlab", handler.ServeHTTP)

// API documentation
mux.HandleFunc("/openapi.json", openAPIHandler)
```

### ✅ **Health Endpoints**

```go
func healthHandler(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusOK)
    w.Write([]byte(`{"status":"healthy"}`))
}

func readyHandler(w http.ResponseWriter, r *http.Request) {
    if !dependenciesReady() {
        w.WriteHeader(http.StatusServiceUnavailable)
        w.Write([]byte(`{"status":"not ready"}`))
        return
    }
    w.WriteHeader(http.StatusOK)
    w.Write([]byte(`{"status":"ready"}`))
}
```

### ✅ **Server Configuration**

```go
server := &http.Server{
    Addr:         ":" + port,
    Handler:      loggingMiddleware(mux),
    ReadTimeout:  15 * time.Second,
    WriteTimeout: 15 * time.Second,
    IdleTimeout:  60 * time.Second,
}

// Graceful shutdown
quit := make(chan os.Signal, 1)
signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)

go func() {
    if err := server.ListenAndServe(); err != http.ErrServerClosed {
        log.Fatalf("Server failed: %v", err)
    }
}()

<-quit
ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
defer cancel()
server.Shutdown(ctx)
```

### ❌ **HTTP API Anti-Patterns**

| Pattern | Problem | Instead |
|---------|---------|---------|
| Unversioned API | Breaking changes affect all | `/v1/webhook/gitlab` |
| No Health Endpoint | K8s can't probe | Add `/health`, `/readyz` |
| No OpenAPI Spec | Undocumented API | Serve OpenAPI 3.0 |
| No Timeout Config | Slow clients block | Set Read/Write timeouts |
| No Graceful Shutdown | Dropped requests | Catch signals, drain |

---

## Kubernetes Operator Patterns

### ✅ **Controller Reconciliation**

```go
func (r *MyReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    var resource myv1.MyResource
    if err := r.Get(ctx, req.NamespacedName, &resource); err != nil {
        return ctrl.Result{}, client.IgnoreNotFound(err)
    }

    // Handle deletion with finalizer
    if !resource.DeletionTimestamp.IsZero() {
        return r.handleDeletion(ctx, &resource)
    }

    // Add finalizer if not present
    if !controllerutil.ContainsFinalizer(&resource, myFinalizer) {
        controllerutil.AddFinalizer(&resource, myFinalizer)
        if err := r.Update(ctx, &resource); err != nil {
            return ctrl.Result{}, err
        }
        return ctrl.Result{Requeue: true}, nil
    }

    // State machine based on desired state
    switch resource.Spec.DesiredState {
    case myv1.StateActive:
        return r.ensureActive(ctx, &resource)
    case myv1.StateIdle:
        return r.ensureIdle(ctx, &resource)
    }
    return ctrl.Result{}, nil
}
```

### Return Patterns

| Result | Meaning |
|--------|---------|
| `ctrl.Result{}, nil` | Success, no requeue |
| `ctrl.Result{Requeue: true}, nil` | Requeue immediately |
| `ctrl.Result{RequeueAfter: time.Minute}, nil` | Requeue after duration |
| `ctrl.Result{}, err` | Error, controller-runtime handles backoff |

### ❌ **Operator Anti-Patterns**

| Pattern | Problem | Instead |
|---------|---------|---------|
| Status as Spec | Status is observed, not desired | Use Spec for desired |
| Missing Finalizer | Orphaned external resources | Add finalizer first |
| No Context Timeout | Hung operations | `context.WithTimeout` |
| Condition Storms | Triggers unnecessary watches | Update only on change |
| Direct Status Update | Conflicts with spec updates | Use `r.Status().Update()` |

---

## Code Quality Metrics

> See `common-standards.md` for universal coverage targets and testing principles.

### ✅ **golangci-lint Configuration**

Minimum recommended linters:

```yaml
# .golangci.yml
linters:
  enable:
    - errcheck      # Check error returns
    - govet         # Go vet
    - staticcheck   # Advanced static analysis
    - unused        # Detect unused code
    - gosimple      # Simplification suggestions
    - gocritic      # Opinionated checks
    - misspell      # Spell checking
    - errorlint     # Error wrapping checks
    - goimports     # Auto-organize imports
    - revive        # Exported name checks

linters-settings:
  gocyclo:
    min-complexity: 10  # Cyclomatic complexity threshold
```

### 📊 **Complexity Thresholds**

| Complexity Range | Status | Action |
|-----------------|--------|--------|
| CC 1-5 (Simple) | ✅ Excellent | Maintain |
| CC 6-10 (OK) | ✅ Acceptable | Monitor |
| CC 11-15 (High) | ⚠️ Warning | Refactor recommended |
| CC 16+ (Very High) | ❌ Critical | Refactor required |

**Refactoring Strategies:**
- Strategy maps (replace switch statements)
- Guard clauses (early returns)
- Helper functions (extract validation)
- Interface composition

---

## Anti-Patterns Avoided

> See `common-standards.md` for universal anti-patterns across all languages.

### ❌ **No Naked Returns**
```go
// BAD
func bad() (err error) {
    err = doSomething()
    return // Naked return
}

// GOOD
func good() error {
    err := doSomething()
    return err // Explicit return
}
```

### ❌ **No init() Abuse**
- No `init()` functions with side effects
- Configuration via constructors
- Explicit initialization with error handling

### ❌ **No Panics in Library Code**
- All errors returned via `error` interface
- `panic` only used in tests for assertion failures
- No `panic` in production paths

### ❌ **No Global Mutable State**
```go
// BAD
var globalRegistry *Registry

// GOOD
type Server struct {
    registry *Registry // Instance field
}
```

### ❌ **No Pointer to Interface**
```go
// BAD
func bad(agent *Agent) // Interface is already a reference

// GOOD
func good(agent Agent)
```

### ❌ **No Goroutine Leaks**
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

## Compliance Assessment

**Use letter grades + evidence, NOT numeric scores.**

| Category | Assessment Criteria | Evidence Required |
|----------|-------------------|-------------------|
| Error Handling | Custom errors, %w wrapping, documented ignores | Count proper wrappings, undocumented ignores |
| Interface Design | Accept interfaces, return structs, small interfaces | Count interfaces, methods per interface |
| Concurrency | Context propagation, WaitGroups, mutexes | Activities with context, race condition count |
| Security | Constant-time comparison, HMAC, replay prevention | Prescan P2 findings, hardcoded secrets count |
| Code Organization | Layered architecture, import grouping | Package structure review, import violations |
| Testing | Table-driven, helpers, mocks | Test pattern count, coverage percentage |

**Grading Scale:**

| Grade | Finding Threshold | Description |
|-------|------------------|-------------|
| A+ | 0-2 minor findings | Exemplary - industry best practices |
| A | <5 HIGH findings | Excellent - strong practices |
| A- | 5-15 HIGH findings | Very Good - solid practices |
| B+ | 15-25 HIGH findings | Good - acceptable practices |
| B | 25-40 HIGH findings | Satisfactory - needs improvement |
| C+ | 40-60 HIGH findings | Needs Improvement - multiple issues |
| C | 60+ HIGH findings | Significant Issues - major refactoring |
| D | 1+ CRITICAL findings | Major Problems - not production-ready |
| F | Multiple CRITICAL | Critical Issues - complete rewrite |

**Example Assessment:**

| Category | Grade | Evidence |
|----------|-------|----------|
| Error Handling | A- | 131 proper %w wrappings, 5 undocumented ignores, 0 %v issues |
| Interface Design | A+ | 9 small interfaces (avg 4 methods), proper composition |
| Concurrency | A | 24/24 activities use context, 0 race conditions (go test -race) |
| Security | A | 0 CRITICAL, 2 HIGH (P2 findings), timing-safe comparisons |
| **OVERALL** | **A- (Excellent)** | **12 HIGH, 34 MEDIUM findings** |

---

## Vibe Integration

### Prescan Patterns

| Pattern | Severity | Detection |
|---------|----------|-----------|
| P13: Undocumented Error Ignores | HIGH | `_ =` without `nolint:errcheck` |
| P14: Error Wrapping with %v | MEDIUM | `fmt.Errorf.*%v` with error args |
| P15: golangci-lint Violations | HIGH | JSON output parsing |

### Semantic Analysis

Deep validation includes:
- Error chain inspection (`errors.Is`, `errors.As` usage)
- Interface segregation (ISP compliance)
- Goroutine lifecycle analysis
- Security vulnerability detection

### JIT Loading

**Tier 1 (Fast):** Load `~/.agents/skills/standards/references/go.md` (5KB)
**Tier 2 (Deep):** Load this document (16KB) for comprehensive audit
**Override:** Use `.agents/validation/GO_*.md` if project-specific standards exist

---

## Additional Resources

- [Effective Go](https://go.dev/doc/effective_go)
- [Go Code Review Comments](https://github.com/golang/go/wiki/CodeReviewComments)
- [Go Proverbs](https://go-proverbs.github.io/)
- [golangci-lint Linters](https://golangci-lint.run/usage/linters/)
- [OWASP Go Secure Coding](https://owasp.org/www-project-go-secure-coding-practices-guide/)

---

**Related:** `go-patterns.md` for quick reference examples
