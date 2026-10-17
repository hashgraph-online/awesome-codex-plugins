# Concurrency Pipeline Examples

## Cancellation-Aware Stage

```go
func mapStage[A, B any](
    ctx context.Context,
    in <-chan A,
    fn func(context.Context, A) (B, error),
) <-chan result[B] {
    out := make(chan result[B])
    go func() {
        defer close(out)
        for v := range in {
            mapped, err := fn(ctx, v)
            select {
            case out <- result[B]{value: mapped, err: err}:
            case <-ctx.Done():
                return
            }
            if err != nil {
                return
            }
        }
    }()
    return out
}
```

The operation owning this stage must also cancel and join the complete topology.

## Bounded Errgroup

```go
group, ctx := errgroup.WithContext(ctx)
group.SetLimit(limit)
for _, item := range items {
    item := item // retain only for modules with pre-Go-1.22 loop semantics
    group.Go(func() error {
        return process(ctx, item)
    })
}
return group.Wait()
```

Check the module language version before adding a loop-variable rebind. Every
task must observe `ctx`; cancellation does not forcibly stop a goroutine.

## Parallel Fixed-Index Results

```go
results := make([]Result, len(items))
var group errgroup.Group
group.SetLimit(limit)
for i := range items {
    i := i // legacy language versions only
    group.Go(func() error {
        results[i] = transform(items[i])
        return nil
    })
}
if err := group.Wait(); err != nil {
    return nil, err
}
return results, nil
```

This is safe only because each goroutine writes a distinct element, no one
mutates the slice header, and `Wait` completes before results are read.

## Deterministic Concurrency Check

Inject a work function that blocks on a release channel. Count admitted workers,
wait until the expected limit is reached, assert that no additional worker
starts, then release them. This proves the bound without guessing a duration.
