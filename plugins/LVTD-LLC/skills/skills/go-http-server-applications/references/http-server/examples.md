# HTTP Server Examples

## Bounded Single-Document JSON

```go
func decodeJSON(w http.ResponseWriter, r *http.Request, dst any, limit int64) error {
    r.Body = http.MaxBytesReader(w, r.Body, limit)
    defer r.Body.Close()

    dec := json.NewDecoder(r.Body)
    dec.DisallowUnknownFields()
    if err := dec.Decode(dst); err != nil {
        return err
    }
    if err := dec.Decode(&struct{}{}); err != io.EOF {
        return errors.New("request body must contain one JSON value")
    }
    return nil
}
```

Strict unknown-field rejection is an endpoint compatibility decision, not a
universal default.

## Explicit Server

```go
srv := &http.Server{
    Addr:              addr,
    Handler:           handler,
    ReadHeaderTimeout: 5 * time.Second,
    IdleTimeout:       60 * time.Second,
    MaxHeaderBytes:    1 << 20,
}
```

Choose values from deployment and workload requirements. Add a bounded shutdown
path and wait for it before process exit.
