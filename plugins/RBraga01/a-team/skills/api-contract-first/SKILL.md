---
name: api-contract-first
description: Hard gate before implementing any API endpoint or service interface. Requires a written, reviewed contract (OpenAPI 3.x, protobuf, or GraphQL schema) before any implementation code is written. Prevents breaking changes, misaligned clients, and undocumented behaviour.
---

# API Contract First

## The Law

```
NO API IMPLEMENTATION WITHOUT A REVIEWED CONTRACT.
Writing endpoints before the contract is building to a spec that doesn't exist.
The contract IS the spec. Code that matches it is correct. Code that doesn't is wrong.
```

## When to Use

Use this skill before writing ANY of these:
- A new REST endpoint
- A new gRPC/protobuf service method
- A new GraphQL query, mutation, or subscription
- A new event schema (Kafka, SQS, webhooks)
- A new inter-service interface

## The Contract Process

### Step 1: Write the Contract

Choose the format that matches the project's stack:

**REST → OpenAPI 3.x**
```yaml
# docs/api/openapi.yaml
paths:
  /orders:
    post:
      summary: Create a new order
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateOrderRequest'
      responses:
        '201':
          description: Order created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Order'
        '400':
          $ref: '#/components/responses/ValidationError'
        '401':
          $ref: '#/components/responses/Unauthorized'
components:
  schemas:
    CreateOrderRequest:
      type: object
      required: [userId, items]
      properties:
        userId:
          type: string
          format: uuid
        items:
          type: array
          minItems: 1
          items:
            $ref: '#/components/schemas/OrderItem'
```

**Events / Async → AsyncAPI or JSON Schema**
```yaml
# docs/events/order-created.yaml
name: order.created
version: 1.0.0
payload:
  type: object
  required: [orderId, userId, createdAt]
  properties:
    orderId: { type: string, format: uuid }
    userId: { type: string, format: uuid }
    createdAt: { type: string, format: date-time }
```

### Step 2: Contract Review Checklist

Before implementation begins, verify the contract satisfies all of these:

**Naming & Consistency**
- [ ] Resource names are nouns, plural (`/orders` not `/createOrder`)
- [ ] Consistent casing throughout (snake_case for JSON fields, kebab-case for URL segments)
- [ ] New names consistent with existing API vocabulary (don't introduce synonyms for existing concepts)

**Completeness**
- [ ] All error responses documented (at minimum: 400, 401, 403, 404, 422, 500)
- [ ] All required vs optional fields explicitly marked
- [ ] Field types, formats, and constraints defined (min/max, pattern, enum values)
- [ ] Pagination documented if the endpoint returns a collection

**Versioning**
- [ ] Breaking changes introduce a new version (`/v2/`) — never modify `/v1/` in a breaking way
- [ ] A change is breaking if it: removes a field, changes a field type, makes an optional field required, changes status code semantics

**Security**
- [ ] Authentication requirement stated (which scheme: Bearer, API Key, session)
- [ ] Authorisation scope documented (who can call this: any user, admin only, service-to-service)
- [ ] Rate limits noted if applicable

**Consumer Perspective**
- [ ] The contract was designed for how clients need to use it — not how it's easiest to implement
- [ ] A new team member could implement a client from this contract alone

### Step 3: Get Contract Approved

Save the contract file to `docs/api/` or `docs/events/`. The contract is reviewed before implementation begins — not after.

**Approval gate:** the `planner` agent must reference the approved contract file in the implementation plan. If no contract file is referenced, the plan is not complete.

### Step 4: Implement Against the Contract

Implementation is correct when it matches the contract exactly. The contract is the source of truth — not the implementation.

If the implementation reveals that the contract needs to change:
1. Update the contract first
2. Re-review the changed section
3. Then update the implementation

Never silently diverge from the contract. Every divergence is a breaking change waiting to happen.

### Step 5: Contract Tests

Write at least one contract test per endpoint that validates the actual response against the OpenAPI schema:

```typescript
// [VALID] — tests the real implementation against the contract
import { validate } from 'openapi-validator'
import { spec } from '../docs/api/openapi.yaml'

test('POST /orders response matches contract', async () => {
  const response = await request(app).post('/orders').send(validPayload)
  const errors = validate(spec, '/orders', 'post', response)
  expect(errors).toHaveLength(0)
})
```

## Rationalization Red Flags

These mean you are about to skip the contract step:
- "The endpoint is simple, I'll document it after"
- "The client team knows what they're getting"
- "We'll sort out the contract in the PR description"
- "It's an internal API, nobody will break"

All of these precede the same outcome: a client built on undocumented assumptions, followed by a breaking change that neither team sees coming.
