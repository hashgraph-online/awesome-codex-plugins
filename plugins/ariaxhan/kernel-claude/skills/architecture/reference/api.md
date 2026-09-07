
<skill id="api">

<purpose>
APIs are contracts. Breaking changes break consumers.
Resources are nouns, not verbs. HTTP methods define actions.
Status codes are not decorative. 200 for errors is a lie.
</purpose>

<prerequisite>
AgentDB read-start has run. Check existing API patterns in codebase.
Identify API versioning strategy in use (URL path, header, none).
</prerequisite>

<reference>
Skill-specific: skills/architecture/reference/api-research.md
</reference>

<methodology>

1. **RESOURCE NAMING**
   - URLs are nouns, plural, kebab-case: `/api/v1/users`, `/api/v1/team-members`
   - HTTP methods are the verbs: GET/POST/PUT/PATCH/DELETE
   - Sub-resources for relationships: `/api/v1/users/:id/orders`
   - Actions (sparingly): `POST /api/v1/orders/:id/cancel`
   - (gate: no verb in URL path, no singular resource names, no snake_case in URL)

2. **STATUS CODES** — use semantically, never 200 for errors
   ```
   200 OK · 201 Created (+ Location header) · 204 No Content
   400 Bad Request · 401 Unauthorized · 403 Forbidden · 404 Not Found
   409 Conflict · 422 Unprocessable Entity · 429 Too Many Requests
   500 Internal Server Error · 502 Bad Gateway · 503 Service Unavailable (+ Retry-After)
   ```
   (gate: POST returns 201, DELETE returns 204, errors never return 200)

3. **VALIDATE ALL INPUT** before any processing
   - Schema validation with Zod (TS) or Pydantic (Python) on every endpoint
   - Return 422 with structured field errors on validation failure
   - (gate: no endpoint processes input without schema.safeParse / model.validate)

4. **RESPONSE SHAPE** — consistent envelope
   - Single resource: `{ "data": { ... } }`
   - Collection: `{ "data": [...], "meta": { total, page, per_page }, "links": { self, next, last } }`
   - Error: `{ "error": { "code": "snake_case_code", "message": "...", "details": [...] } }`
   - (gate: all responses use envelope; no bare objects; error.code is machine-readable)

5. **PAGINATION** — mandatory for all list endpoints
   - Cursor (`?cursor=...&limit=20`): use for feeds, infinite scroll, >10K rows
   - Offset (`?page=N&per_page=20`): use for admin dashboards, search with page jumps
   - Return `next_cursor` as opaque string — agents must not compute it from math
   - (gate: no list endpoint returns unbounded results)

6. **VERSIONING**
   - URL path versioning: `/api/v1/`, `/api/v2/` (recommended)
   - Max 2 active versions; add `Sunset` header before removal
   - Non-breaking (no new version): add fields, add optional params, add endpoints
   - Breaking (new version required): remove/rename fields, change types, change URL structure
   - (gate: breaking change without version bump = blocked)

7. **RATE LIMITING** — expose via headers on every response
   ```
   X-RateLimit-Limit: 100
   X-RateLimit-Remaining: 95
   X-RateLimit-Reset: <unix-timestamp>
   Retry-After: 60   # on 429 only
   ```
   (gate: 429 response always includes Retry-After)

8. **IDEMPOTENCY** — mandatory for state-changing ops in distributed/agentic contexts
   - Accept `Idempotency-Key` header on POST/PATCH
   - Cache result keyed by `idem:<key>` with 24h TTL; return cached on repeat
   - Required for: payments, orders, bulk imports, any agent-called endpoint
   - (gate: agent-facing POST endpoints either are idempotent by design OR support Idempotency-Key)

9. **HEALTH ENDPOINTS**
   ```
   GET /health          # Liveness: 200 if process alive
   GET /health/ready    # Readiness: 200 if all dependencies up
   GET /health/startup  # Startup: 200 once init complete
   ```
   - Response: `{ "status": "ok|degraded", "version": "...", "dependencies": { "db": "ok" } }`
   - 503 if critical dependency down; 200 + "degraded" if non-critical
   - (gate: every new service exposes /health and /health/ready)

10. **AGENTIC CLIENT DESIGN** — when API is called by AI agents
    - Every state-changing endpoint: idempotent OR requires `Idempotency-Key` (document which)
    - Distinct error codes per failure mode — agents parse codes to decide retry vs abort vs escalate
    - Batch endpoints for high-frequency reads: `GET /api/v1/users/batch?ids=a,b,c`
    - Return `next_cursor` as direct string, never derivable by offset math
    - (gate: agent-facing APIs documented with retry-safety posture per endpoint)

11. **SCHEMA-FIRST FOR AI CONSUMERS** — when the API will be called by AI agents or code-generated clients, define the OpenAPI spec before the implementation.
    - Generate TypeScript types from the spec (`openapi-typescript`), not from the implementation; AI clients hallucinate field names from training data — a machine-readable spec is the authoritative correction mechanism
    - Every breaking change shows as a spec diff before it hits a consumer
    - AI agents parse error codes (step 10) more reliably when they are documented in the spec alongside the schema
    - (gate: AI-facing endpoints have an OpenAPI spec entry before the route handler is written) <!-- Updated 2026-06-18: https://code.claude.com/docs/en/best-practices -->

</methodology>

<anti_patterns>
<block id="verbs_in_urls">/getUsers, /createOrder. Use HTTP methods for actions.</block>
<block id="200_for_errors">{ "status": 200, "success": false }. Use HTTP status codes.</block>
<block id="no_validation">Trusting user input. Validate everything with schemas.</block>
<block id="leaking_details">Stack traces in error responses. Generic messages for users.</block>
<block id="no_pagination">Returning all records. Pagination is mandatory for lists.</block>
</anti_patterns>

<on_complete>
agentdb write-end '{"skill":"api","endpoints_created":<N>,"validation":"zod|pydantic|none","pagination":"cursor|offset|none","versioning":"v1|none"}'

Record endpoints added and patterns used.
</on_complete>

</skill>
