# Security, Reliability, and Performance Checklist

主 `SKILL.md` 只在 diff 命中风险触发条件时加载本文件。把问题映射回既有轴线:多数风险属于 `功能`;只有纯 unused/dead code 才归 `废码`。

## Security

### Trust boundaries

- User/network/disk input must be validated before use.
- AuthN/AuthZ/tenant/ownership checks must stay server-side and must not trust client-provided roles, flags, or IDs.
- New endpoints, handlers, jobs, or commands must preserve the same guard pattern as neighboring code.

### Injection and unsafe IO

- No SQL/NoSQL/GraphQL/command injection via string concatenation or template interpolation.
- User-controlled URLs must not reach internal services without an allowlist or equivalent SSRF guard.
- User-controlled file paths must be normalized and constrained to an expected root; reject `..` traversal.
- Avoid unsafe deserialization of untrusted payloads.

### Secrets and sensitive data

- No API keys, tokens, credentials, private local paths, or production secrets in code/config/tests/logs.
- Logs and errors must not expose PII, tokens, internal stack traces, or raw sensitive payloads.
- Client-side bundles must not receive server-only env vars or credentials.

### Crypto and dependency changes

- Do not introduce weak crypto for security purposes (MD5/SHA1, hardcoded IV/salt, unauthenticated encryption, disabled certificate checks).
- Dependency/source changes should not loosen pinning, add untrusted registries/CDNs, or shadow private package names.

## Reliability and Data Integrity

### Errors and async

- Fallible IO/network/parse/db calls must either handle errors at the boundary or propagate them deliberately.
- No empty catch, log-and-forget, unhandled promise/Future, or fire-and-forget operation unless explicitly intentional.
- Retryable writes need idempotency or duplicate-safe semantics.

### Concurrency and state

- Check-then-act sequences must be atomic when concurrent calls are possible.
- Read-modify-write database updates need transactions, locks, optimistic version checks, or atomic update expressions.
- Shared mutable state, lazy initialization, caches, and singleton updates need synchronization or a single-threaded guarantee.

### Resource lifecycle

- Streams, files, sockets, DB connections, controllers, timers, and subscriptions must be closed/disposed.
- Background jobs and goroutines/tasks need cancellation or a bounded lifetime.
- Partial writes/migrations need rollback or a clearly safe recovery path.

## Performance

### Data access

- No new N+1 query or request loop on list/detail screens, API handlers, jobs, or hot paths.
- Large lists need pagination, batching, streaming, or explicit limits.
- Queries should not add obvious index-hostile predicates on large tables.

### CPU, memory, and cache

- Avoid expensive parsing, regex compilation, crypto, image/PDF processing, or sync IO in request/UI hot paths.
- Collections, buffers, logs, and in-memory caches must be bounded.
- Cache keys must include tenant/user/scope when data is scoped; caches need TTL or invalidation when stale data matters.

## Deletion Planning

- Safe delete now only when references are searched, dynamic/reflection/external consumers are considered, and deletion is in scope.
- Defer removal when active consumers, feature-flag telemetry, docs/API compatibility, migration, owner sign-off, or rollback evidence is missing.
- Defer findings should name the missing precondition and the verification command/metric needed before deletion.
