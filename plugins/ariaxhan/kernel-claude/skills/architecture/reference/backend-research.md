# Backend Research

Deep reference for backend architecture patterns.

## Layered Architecture

```
┌─────────────────────────────────────┐
│          HTTP Handlers              │  Parse requests, return responses
├─────────────────────────────────────┤
│          Service Layer              │  Business logic, orchestration
├─────────────────────────────────────┤
│        Repository Layer             │  Data access abstraction
├─────────────────────────────────────┤
│      Database / External APIs       │  Actual storage/services
└─────────────────────────────────────┘
```

### Benefits
- Testability: Mock at boundaries
- Flexibility: Swap implementations
- Separation: Clear responsibilities

## Repository Pattern Deep Dive

### Interface Definition
```typescript
interface Repository<T, ID> {
  findById(id: ID): Promise<T | null>
  findAll(filters?: Filters): Promise<T[]>
  create(data: CreateDto): Promise<T>
  update(id: ID, data: UpdateDto): Promise<T>
  delete(id: ID): Promise<void>
  exists(id: ID): Promise<boolean>
}
```

### Concrete Implementation
```typescript
class PostgresUserRepository implements UserRepository {
  constructor(private pool: Pool) {}

  async findById(id: string): Promise<User | null> {
    const result = await this.pool.query(
      'SELECT * FROM users WHERE id = $1',
      [id]
    )
    return result.rows[0] || null
  }

  async findAll(filters?: UserFilters): Promise<User[]> {
    const conditions: string[] = []
    const params: unknown[] = []

    if (filters?.role) {
      params.push(filters.role)
      conditions.push(`role = $${params.length}`)
    }

    if (filters?.createdAfter) {
      params.push(filters.createdAfter)
      conditions.push(`created_at > $${params.length}`)
    }

    const where = conditions.length
      ? `WHERE ${conditions.join(' AND ')}`
      : ''

    const result = await this.pool.query(
      `SELECT * FROM users ${where} ORDER BY created_at DESC`,
      params
    )
    return result.rows
  }
}
```

### Testing with Repository
```typescript
// In-memory fake for tests
class InMemoryUserRepository implements UserRepository {
  private users: Map<string, User> = new Map()

  async findById(id: string): Promise<User | null> {
    return this.users.get(id) || null
  }

  async create(data: CreateUserDto): Promise<User> {
    const user = { id: uuid(), ...data, createdAt: new Date() }
    this.users.set(user.id, user)
    return user
  }
}

// Test with fake
test('create user sends welcome email', async () => {
  const userRepo = new InMemoryUserRepository()
  const emailService = new MockEmailService()
  const service = new UserService(userRepo, emailService)

  await service.createUser({ email: 'test@example.com', name: 'Test' })

  expect(emailService.sentTo).toContain('test@example.com')
})
```

## Service Layer Patterns

### Transaction Script
Simple operations, procedural:
```typescript
async function transferFunds(fromId: string, toId: string, amount: number) {
  const from = await accountRepo.findById(fromId)
  const to = await accountRepo.findById(toId)

  if (from.balance < amount) throw new InsufficientFundsError()

  from.balance -= amount
  to.balance += amount

  await accountRepo.update(fromId, from)
  await accountRepo.update(toId, to)
}
```

### Domain Service
Complex business logic:
```typescript
class PaymentService {
  constructor(
    private accountRepo: AccountRepository,
    private paymentGateway: PaymentGateway,
    private notificationService: NotificationService
  ) {}

  async processPayment(orderId: string, paymentDetails: PaymentDetails) {
    // Validate
    const order = await this.orderRepo.findById(orderId)
    if (!order) throw new NotFoundError('Order not found')
    if (order.status !== 'pending') throw new InvalidStateError('Order not pending')

    // Process
    const result = await this.paymentGateway.charge(paymentDetails)
    if (!result.success) throw new PaymentFailedError(result.error)

    // Update state
    order.status = 'paid'
    order.paymentId = result.transactionId
    await this.orderRepo.update(orderId, order)

    // Side effects
    await this.notificationService.sendReceipt(order.userId, order)

    return order
  }
}
```

## N+1 Query Solutions

### The Problem
```typescript
// BAD: N+1 queries
const orders = await orderRepo.findAll()  // 1 query
for (const order of orders) {
  order.customer = await customerRepo.findById(order.customerId)  // N queries
}
```

### Solution 1: Batch Loading
```typescript
const orders = await orderRepo.findAll()

// Collect unique IDs
const customerIds = [...new Set(orders.map(o => o.customerId))]

// Single batch query
const customers = await customerRepo.findByIds(customerIds)
const customerMap = new Map(customers.map(c => [c.id, c]))

// Attach
orders.forEach(order => {
  order.customer = customerMap.get(order.customerId)
})
```

### Solution 2: JOIN in Query
```sql
SELECT orders.*, customers.name as customer_name
FROM orders
JOIN customers ON orders.customer_id = customers.id
```

### Solution 3: DataLoader
```typescript
import DataLoader from 'dataloader'

const customerLoader = new DataLoader(async (ids: string[]) => {
  const customers = await customerRepo.findByIds(ids)
  const map = new Map(customers.map(c => [c.id, c]))
  return ids.map(id => map.get(id))
})

// Usage (batches automatically)
const orders = await orderRepo.findAll()
await Promise.all(orders.map(async order => {
  order.customer = await customerLoader.load(order.customerId)
}))
```

## Caching Strategies

### Cache-Aside (Lazy Loading)
```
Read:
1. Check cache
2. If miss, query DB
3. Write to cache
4. Return

Write:
1. Write to DB
2. Invalidate cache
```

```typescript
async function getUser(id: string): Promise<User> {
  // Check cache
  const cached = await cache.get(`user:${id}`)
  if (cached) return JSON.parse(cached)

  // Cache miss
  const user = await db.users.findById(id)
  if (!user) throw new NotFoundError()

  // Populate cache
  await cache.setex(`user:${id}`, 300, JSON.stringify(user))

  return user
}
```

### Write-Through
```
Write:
1. Write to cache
2. Write to DB (sync)
```

### Write-Behind (Write-Back)
```
Write:
1. Write to cache
2. Queue write to DB (async)
```

### Cache Invalidation Patterns

1. **Time-based (TTL)**
```typescript
await cache.setex(key, 300, value)  // Expires in 5 min
```

2. **Event-based**
```typescript
// On update
await db.users.update(id, data)
await cache.del(`user:${id}`)
```

3. **Version-based**
```typescript
const version = await cache.incr('users:version')
await cache.set(`user:${id}:v${version}`, data)
```

## Queue Patterns

### Simple Queue
```typescript
interface Job<T> {
  id: string
  payload: T
  attempts: number
  createdAt: Date
}

class Queue<T> {
  private items: Job<T>[] = []

  enqueue(payload: T): string {
    const job = {
      id: uuid(),
      payload,
      attempts: 0,
      createdAt: new Date()
    }
    this.items.push(job)
    return job.id
  }

  dequeue(): Job<T> | undefined {
    return this.items.shift()
  }
}
```

### Dead Letter Queue
Failed jobs go to separate queue for investigation:
```typescript
class QueueWithDLQ<T> {
  private main: Job<T>[] = []
  private dlq: Job<T>[] = []
  private maxAttempts = 3

  async process(handler: (payload: T) => Promise<void>) {
    const job = this.main.shift()
    if (!job) return

    try {
      await handler(job.payload)
    } catch (error) {
      job.attempts++
      if (job.attempts >= this.maxAttempts) {
        this.dlq.push(job)  // Move to DLQ
      } else {
        this.main.push(job)  // Retry
      }
    }
  }
}
```

### Priority Queue
```typescript
interface PriorityJob<T> extends Job<T> {
  priority: number  // Lower = higher priority
}

class PriorityQueue<T> {
  private items: PriorityJob<T>[] = []

  enqueue(payload: T, priority: number) {
    const job = { id: uuid(), payload, priority, attempts: 0, createdAt: new Date() }
    const index = this.items.findIndex(j => j.priority > priority)
    if (index === -1) {
      this.items.push(job)
    } else {
      this.items.splice(index, 0, job)
    }
  }
}
```

## Error Handling

### Error Hierarchy
```typescript
class AppError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number = 500
  ) {
    super(message)
  }
}

class NotFoundError extends AppError {
  constructor(resource: string) {
    super(`${resource} not found`, 'not_found', 404)
  }
}

class ValidationError extends AppError {
  constructor(public errors: FieldError[]) {
    super('Validation failed', 'validation_error', 400)
  }
}

class UnauthorizedError extends AppError {
  constructor() {
    super('Authentication required', 'unauthorized', 401)
  }
}
```

### Global Error Handler
```typescript
function errorHandler(error: unknown, req: Request, res: Response) {
  // Known errors
  if (error instanceof AppError) {
    return res.status(error.statusCode).json({
      error: { code: error.code, message: error.message }
    })
  }

  // Zod validation
  if (error instanceof z.ZodError) {
    return res.status(400).json({
      error: {
        code: 'validation_error',
        message: 'Validation failed',
        details: error.errors
      }
    })
  }

  // Unknown errors - log and hide details
  console.error('Unexpected error:', error)
  return res.status(500).json({
    error: { code: 'internal_error', message: 'Internal server error' }
  })
}
```

## Resources

- Martin Fowler, "Patterns of Enterprise Application Architecture"
- Redis docs on caching patterns
- AWS Well-Architected Framework

---

## Inline Examples Moved from SKILL.md (2026-05-28)

### Repository Pattern — Supabase Implementation
```typescript
interface UserRepository {
  findAll(filters?: UserFilters): Promise<User[]>
  findById(id: string): Promise<User | null>
  create(data: CreateUserDto): Promise<User>
  update(id: string, data: UpdateUserDto): Promise<User>
  delete(id: string): Promise<void>
}

class SupabaseUserRepository implements UserRepository {
  async findAll(filters?: UserFilters): Promise<User[]> {
    let query = supabase.from('users').select('id, name, email')

    if (filters?.role) {
      query = query.eq('role', filters.role)
    }

    const { data, error } = await query
    if (error) throw new Error(error.message)
    return data
  }
}
```

### Service Layer — Constructor Injection
```typescript
class UserService {
  constructor(
    private userRepo: UserRepository,
    private emailService: EmailService
  ) {}

  async createUser(data: CreateUserDto): Promise<User> {
    // Business logic: validate, transform, orchestrate
    const existing = await this.userRepo.findByEmail(data.email)
    if (existing) throw new ConflictError('Email already registered')

    const user = await this.userRepo.create(data)
    await this.emailService.sendWelcome(user.email)

    return user
  }
}
```

### N+1 Prevention — Batch Fetch Pattern
```typescript
// BAD: N+1 queries
const orders = await getOrders()
for (const order of orders) {
  order.customer = await getCustomer(order.customer_id)  // N queries!
}

// GOOD: Batch fetch
const orders = await getOrders()
const customerIds = [...new Set(orders.map(o => o.customer_id))]
const customers = await getCustomersByIds(customerIds)  // 1 query
const customerMap = new Map(customers.map(c => [c.id, c]))

orders.forEach(order => {
  order.customer = customerMap.get(order.customer_id)
})
```

```typescript
// GOOD: Select only needed columns
const { data } = await supabase
  .from('orders')
  .select('id, total, status, customer:customers(id, name)')
  .eq('status', 'active')
  .limit(10)
```

### Caching — Cache-Aside with Invalidation
```typescript
// Cache-aside pattern
class CachedUserRepository implements UserRepository {
  constructor(
    private baseRepo: UserRepository,
    private redis: RedisClient
  ) {}

  async findById(id: string): Promise<User | null> {
    const cacheKey = `user:${id}`

    // Check cache
    const cached = await this.redis.get(cacheKey)
    if (cached) return JSON.parse(cached)

    // Cache miss - fetch from DB
    const user = await this.baseRepo.findById(id)

    if (user) {
      // Cache for 5 minutes
      await this.redis.setex(cacheKey, 300, JSON.stringify(user))
    }

    return user
  }

  async update(id: string, data: UpdateUserDto): Promise<User> {
    const user = await this.baseRepo.update(id, data)
    // Invalidate cache on mutation
    await this.redis.del(`user:${id}`)
    return user
  }
}
```

### Transactions — Supabase RPC
```typescript
// Supabase RPC for atomic operations
async function transferFunds(fromId: string, toId: string, amount: number) {
  const { data, error } = await supabase.rpc('transfer_funds', {
    from_id: fromId,
    to_id: toId,
    amount: amount
  })

  if (error) throw new Error('Transfer failed')
  return data
}
```

```sql
-- SQL function with automatic rollback
CREATE OR REPLACE FUNCTION transfer_funds(
  from_id uuid,
  to_id uuid,
  amount decimal
)
RETURNS jsonb
LANGUAGE plpgsql
AS $$
BEGIN
  -- Deduct from sender
  UPDATE accounts SET balance = balance - amount WHERE id = from_id;
  -- Add to receiver
  UPDATE accounts SET balance = balance + amount WHERE id = to_id;
  RETURN jsonb_build_object('success', true);
EXCEPTION
  WHEN OTHERS THEN
    -- Automatic rollback
    RETURN jsonb_build_object('success', false, 'error', SQLERRM);
END;
$$;
```

### Error Handling — ApiError + Global Handler
```typescript
class ApiError extends Error {
  constructor(
    public statusCode: number,
    public message: string,
    public code: string
  ) {
    super(message)
  }
}

export function errorHandler(error: unknown): Response {
  if (error instanceof ApiError) {
    return NextResponse.json({
      error: { code: error.code, message: error.message }
    }, { status: error.statusCode })
  }

  if (error instanceof z.ZodError) {
    return NextResponse.json({
      error: {
        code: 'validation_error',
        message: 'Validation failed',
        details: error.errors
      }
    }, { status: 400 })
  }

  // Log unexpected errors, don't expose details
  console.error('Unexpected error:', error)
  return NextResponse.json({
    error: { code: 'internal_error', message: 'Internal server error' }
  }, { status: 500 })
}
```

### Retry Pattern — Exponential Backoff
```typescript
async function fetchWithRetry<T>(
  fn: () => Promise<T>,
  maxRetries = 3
): Promise<T> {
  let lastError: Error

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error as Error
      if (i < maxRetries - 1) {
        // Exponential backoff: 1s, 2s, 4s
        const delay = Math.pow(2, i) * 1000
        await new Promise(r => setTimeout(r, delay))
      }
    }
  }

  throw lastError!
}
```

### Queue Pattern — Basic Job Queue
```typescript
class JobQueue<T> {
  private queue: T[] = []
  private processing = false

  async add(job: T): Promise<void> {
    this.queue.push(job)
    if (!this.processing) this.process()
  }

  private async process(): Promise<void> {
    this.processing = true

    while (this.queue.length > 0) {
      const job = this.queue.shift()!
      try {
        await this.execute(job)
      } catch (error) {
        console.error('Job failed:', error)
        // Optionally: retry, dead-letter queue
      }
    }

    this.processing = false
  }

  private async execute(job: T): Promise<void> {
    // Implement job execution
  }
}
```
