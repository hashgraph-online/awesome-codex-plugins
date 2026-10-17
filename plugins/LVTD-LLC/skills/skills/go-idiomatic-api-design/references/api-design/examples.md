# API Design Examples

## Consumer-Owned Interface

```go
// package report
type UserFinder interface {
    FindUser(context.Context, string) (User, error)
}

type Service struct {
    users UserFinder
}
```

The storage provider remains concrete. The report package owns only the
operation it consumes.

## Concrete Provider with Optional Capability

```go
type Store struct {
    // unexported state
}

func (s *Store) Load(ctx context.Context, key string) ([]byte, error) {
    // ...
}

type Flusher interface {
    Flush(context.Context) error
}
```

Callers that need flushing can test for the optional behavior without forcing
all stores to implement an oversized interface.

## Executable Documentation

```go
func ExampleParseMode() {
    mode, err := ParseMode("safe")
    fmt.Println(mode, err)
    // Output:
    // safe <nil>
}
```

Avoid network access, current time, random map order, and process exits in
examples.

## Named Field Instead of Accidental Embedding

```go
type Service struct {
    client *http.Client
}
```

Embedding `*http.Client` would promote its methods into `Service`'s public
surface. Use a named field unless that complete promoted contract is intended.

## Avoid a Typed-Nil Error

```go
func validate(input string) error {
    var problem *ValidationError
    if input == "" {
        problem = &ValidationError{Field: "input"}
    }
    if problem != nil {
        return problem
    }
    return nil
}
```

Returning `problem` unconditionally would convert a nil pointer into a non-nil
interface value.
