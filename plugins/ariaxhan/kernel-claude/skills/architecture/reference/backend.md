
<skill id="backend">

<purpose>
Separate concerns: repositories for data, services for logic, handlers for HTTP.
N+1 queries kill performance. Batch fetch, don't loop.
Cache reads, not writes. Invalidate on mutation.
</purpose>

<prerequisite>
AgentDB read-start has run. Check existing patterns in codebase.
Identify ORM (Prisma, Drizzle, TypeORM) and cache (Redis, in-memory).
</prerequisite>

<reference>
Skill-specific: skills/architecture/reference/backend-research.md
</reference>

<steps>

1. **Identify layer** — determine which layer the change touches: handler / service / repository / DB.
   (gate: layer is named; no logic crosses two layers in a single function)

2. **Repository pattern** — abstract all data access behind an interface.
   - Interface defines: findById, findAll, create, update, delete.
   - Implementation depends on ORM/DB; swap without touching service.
   - (gate: no raw DB calls outside repository files)
   - Reference: backend-research.md §Repository Pattern Deep Dive

3. **Service layer** — business logic only; no HTTP, no DB calls.
   - Constructor-inject repositories and external services.
   - Validate, transform, orchestrate; throw typed errors on failure.
   - (gate: no `req`/`res` objects; no supabase/prisma/drizzle imports)
   - Reference: backend-research.md §Service Layer Patterns

4. **N+1 prevention** — before any loop over a result set, check for nested queries.
   - Collect IDs → single batch fetch → build Map → attach in-memory.
   - Alternative: JOIN in query or DataLoader for GraphQL.
   - (gate: zero `await repo.findById` calls inside a `for`/`forEach`/`.map`)
   - Reference: backend-research.md §N+1 Query Solutions

5. **Cache-aside** — for read-heavy data: check cache → miss → fetch DB → populate cache.
   - Invalidate on every mutation (`redis.del(key)` after update/delete).
   - TTL: 5 min default; shorter for volatile data.
   - (gate: no cache writes on mutation paths; only invalidation)
   - Reference: backend-research.md §Caching Strategies

6. **Transactions** — multi-step mutations must be atomic.
   - Use DB transaction block or Supabase RPC for cross-table ops.
   - Rollback must be automatic on any error.
   - (gate: no two-step mutations without wrapping transaction)
   - Reference: backend-research.md §Transactions

7. **Error handling** — typed error hierarchy; never expose stack traces.
   - AppError → NotFoundError / ValidationError / UnauthorizedError.
   - Global handler: map known errors to HTTP status; log + return generic 500 for unknown.
   - (gate: no raw `Error` thrown from service; no stack trace in response body)
   - Reference: backend-research.md §Error Handling

8. **Retry with backoff** — transient failures (network, lock contention) get exponential backoff.
   - Max 3 retries; delays: 1 s, 2 s, 4 s.
   - (gate: idempotent operations only; never retry mutations without idempotency key)
   - Reference: backend-research.md §Retry Pattern

9. **Queue pattern** — fire-and-forget or deferred work uses a job queue.
   - Failed jobs: retry up to maxAttempts, then dead-letter queue.
   - (gate: queue is not blocking the HTTP response)
   - Reference: backend-research.md §Queue Patterns

</steps>

<anti_patterns>
<block id="n_plus_one">Querying in loops. Batch fetch with IN clauses or joins.</block>
<block id="select_star">SELECT * is wasteful. Select only needed columns.</block>
<block id="no_transactions">Multi-step mutations without transactions. All or nothing.</block>
<block id="cache_writes">Caching write-heavy data. Cache reads, invalidate on writes.</block>
<block id="business_in_handlers">Business logic in HTTP handlers. Use service layer.</block>
<block id="expose_errors">Stack traces to users. Log details, return generic message.</block>
</anti_patterns>

<on_complete>
agentdb write-end '{"skill":"backend","patterns_used":["repository","service","cache-aside"],"n_plus_one_fixed":<N>,"cache_keys":["<list>"]}'

Record patterns applied and performance improvements.
</on_complete>

</skill>
