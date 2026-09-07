# Go Concurrency Pipelines Guidelines

| Situation | Load |
|---|---|
| New worker pool or pipeline | `workflows/design-cancellable-pipeline.md` |
| Blocked send or goroutine leak | `workflows/review-goroutine-lifecycle.md` |
| Flaky concurrency test | `workflows/test-concurrency-contract.md` |
| Public result API choice | `references/concurrency-pipelines/knowledge.md` |
| Buffer, close, fan-in, or ordering decision | `references/concurrency-pipelines/rules.md` |
| Mutex, WaitGroup, Cond, errgroup, map, or slice race | `references/concurrency-pipelines/rules.md`, `references/concurrency-pipelines/examples.md` |
| Detached background work | `workflows/review-goroutine-lifecycle.md` |

## Boundary

- Use `go-cli-process-control` for OS processes, pipes, signals, and descendants.
- Use `go-http-client-resilience` for HTTP retries and transport policy.
- Use `go-cli-terminal-experience` for rendering and terminal restoration.
- Use this skill for in-process goroutine, channel, iterator, and backpressure behavior.
- Use this skill for in-process shared-state synchronization and lifecycle behavior.
- Use `go-language-correctness` for non-concurrent slice, map, and range semantics.
