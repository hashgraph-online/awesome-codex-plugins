# TypeScript Patterns & Standards

This file contains the team's TypeScript-specific patterns, standards, and code examples. Referenced by the typescript-dev skill during Research and Implementation phases.

---

## Guiding Principles

### Simplicity First

```
Simplest working solution > Clever solution > Over-engineered solution
```

- Avoid complexity and over-engineering at ALL costs
- Self-critique: If a simpler path exists, take it
- Three similar lines > premature abstraction

### Modern TypeScript (5.x+)

```typescript
// CORRECT: Use const assertions for literal types
const STATUS = {
  ACTIVE: 'active',
  INACTIVE: 'inactive',
} as const;

type Status = typeof STATUS[keyof typeof STATUS];

// CORRECT: Satisfies operator for type checking without widening
const config = {
  port: 3000,
  host: 'localhost',
} satisfies ServerConfig;

// CORRECT: Template literal types
type EventName = `on${Capitalize<string>}`;

// CORRECT: Using 'using' for resource management (5.2+)
using file = await openFile('data.txt');
// file is automatically disposed when scope ends
```

### Type-First Design

```typescript
// GOOD: Interface for object shapes
interface User {
  readonly id: string;
  name: string;
  email: string;
  createdAt: Date;
}

// GOOD: Type alias for unions, intersections, mapped types
type Result<T> = { success: true; data: T } | { success: false; error: Error };
type Partial<T> = { [P in keyof T]?: T[P] };

// GOOD: Discriminated unions for state
type RequestState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: Error };

// BAD: Using 'any'
function process(data: any) { ... }

// BAD: Type assertions without validation
const user = response.data as User;
```

### Strict Mode Always

```json
// tsconfig.json - minimum strictness
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "exactOptionalPropertyTypes": true
  }
}
```

---

## Architecture Patterns

### Project Structure (Backend)

```
src/
├── api/
│   ├── routes/           # Route handlers
│   ├── middleware/       # Express/Fastify middleware
│   └── validation/       # Request validation schemas
├── config/
│   └── index.ts          # Configuration with env validation
├── domain/
│   ├── entities/         # Domain models
│   ├── errors/           # Domain-specific errors
│   └── types/            # Shared type definitions
├── services/             # Business logic layer
├── repositories/         # Data access layer
├── utils/                # Shared utilities
└── index.ts              # Entry point
```

**Flow:** Route Handler → Service → Repository → Database

### Project Structure (Frontend)

```
src/
├── components/
│   ├── ui/               # Reusable UI components
│   └── features/         # Feature-specific components
├── hooks/                # Custom React hooks
├── services/             # API clients and business logic
├── stores/               # State management (Zustand, Redux)
├── types/                # Shared type definitions
├── utils/                # Utility functions
└── App.tsx               # Root component
```

### Dependency Injection

```typescript
// GOOD: Constructor injection with interfaces
interface UserRepository {
  findById(id: string): Promise<User | null>;
  save(user: User): Promise<void>;
}

class UserService {
  constructor(
    private readonly userRepository: UserRepository,
    private readonly emailService: EmailService,
  ) {}

  async createUser(data: CreateUserDto): Promise<User> {
    const user = User.create(data);
    await this.userRepository.save(user);
    await this.emailService.sendWelcome(user.email);
    return user;
  }
}

// BAD: Hard-coded dependencies
class UserService {
  private userRepository = new PostgresUserRepository();
}
```

### Service Pattern

```typescript
// Service with clear interface
interface IUserService {
  getUser(id: string): Promise<User>;
  createUser(data: CreateUserDto): Promise<User>;
}

class UserService implements IUserService {
  constructor(private readonly repository: UserRepository) {}

  async getUser(id: string): Promise<User> {
    const user = await this.repository.findById(id);
    if (!user) throw new UserNotFoundError(id);
    return user;
  }

  async createUser(data: CreateUserDto): Promise<User> {
    const user: User = {
      id: crypto.randomUUID(),
      ...data,
      createdAt: new Date(),
    };
    await this.repository.save(user);
    return user;
  }
}
```

---

## Type System Patterns

### Generics

```typescript
// GOOD: Constrained generics
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

// GOOD: Generic with default
interface ApiResponse<T = unknown> {
  data: T;
  status: number;
}

// GOOD: Conditional types for inference
type Awaited<T> = T extends Promise<infer U> ? U : T;
```

### Utility Types

```typescript
// Built-in utility types - use them!
type PartialUser = Partial<User>;           // All props optional
type RequiredUser = Required<User>;          // All props required
type ReadonlyUser = Readonly<User>;          // All props readonly
type UserKeys = keyof User;                  // Union of keys
type UserName = Pick<User, 'name' | 'email'>; // Subset of props
type UserWithoutId = Omit<User, 'id'>;       // Exclude props

// Custom utility types
type NonNullableFields<T> = {
  [K in keyof T]: NonNullable<T[K]>;
};
```

### Type Guards

```typescript
// GOOD: Type predicates
function isUser(value: unknown): value is User {
  return (
    typeof value === 'object' &&
    value !== null &&
    'id' in value &&
    'name' in value
  );
}

// GOOD: Assertion functions
function assertUser(value: unknown): asserts value is User {
  if (!isUser(value)) {
    throw new Error('Invalid user');
  }
}

// Usage
if (isUser(data)) {
  console.log(data.name); // TypeScript knows data is User
}
```

### Branded Types

```typescript
// Prevent primitive type confusion
type UserId = string & { readonly brand: unique symbol };
type OrderId = string & { readonly brand: unique symbol };

function createUserId(id: string): UserId {
  return id as UserId;
}

function getUser(id: UserId): Promise<User> { ... }

// Won't compile: getUser(orderId) - type mismatch!
```

---

## Error Handling

### Custom Error Hierarchy

```typescript
// Base domain error
class DomainError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly cause?: Error,
  ) {
    super(message);
    this.name = this.constructor.name;
    Error.captureStackTrace(this, this.constructor);
  }
}

// Specific errors
class NotFoundError extends DomainError {
  constructor(resource: string, id: string) {
    super(`${resource} not found: ${id}`, 'NOT_FOUND');
  }
}

class ValidationError extends DomainError {
  constructor(message: string, public readonly field?: string) {
    super(message, 'VALIDATION_ERROR');
  }
}
```

### Result Type Pattern

```typescript
// For operations that can fail without throwing
type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };

function ok<T>(value: T): Result<T, never> {
  return { ok: true, value };
}

function err<E>(error: E): Result<never, E> {
  return { ok: false, error };
}

// Usage
async function parseConfig(path: string): Promise<Result<Config, ParseError>> {
  try {
    const content = await readFile(path, 'utf-8');
    return ok(JSON.parse(content));
  } catch (e) {
    return err(new ParseError(`Invalid config: ${path}`));
  }
}

const result = await parseConfig('./config.json');
if (result.ok) {
  console.log(result.value);
} else {
  console.error(result.error);
}
```

---

## Async Patterns

### Promise Handling

```typescript
// GOOD: Async/await with proper error handling
async function fetchUser(id: string): Promise<User> {
  const response = await fetch(`/api/users/${id}`);
  if (!response.ok) {
    throw new ApiError(`Failed to fetch user: ${response.status}`);
  }
  return response.json() as Promise<User>;
}

// GOOD: Parallel execution
const [user, orders] = await Promise.all([
  fetchUser(userId),
  fetchOrders(userId),
]);

// GOOD: Error handling in parallel
const results = await Promise.allSettled([
  fetchUser(userId),
  fetchOrders(userId),
]);
```

### Async Iterators

```typescript
// For streaming data
async function* readLines(path: string): AsyncGenerator<string> {
  const file = await open(path);
  for await (const line of file.readLines()) {
    yield line;
  }
}

// Usage
for await (const line of readLines('./data.txt')) {
  process(line);
}
```

---

## Validation

### Zod for Runtime Validation

```typescript
import { z } from 'zod';

// Schema definition
const UserSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(100),
  email: z.string().email(),
  age: z.number().int().positive().optional(),
});

// Infer TypeScript type from schema
type User = z.infer<typeof UserSchema>;

// Validation
function validateUser(data: unknown): User {
  return UserSchema.parse(data); // Throws on invalid
}

// Safe validation
const result = UserSchema.safeParse(data);
if (result.success) {
  console.log(result.data);
} else {
  console.error(result.error.issues);
}
```

---

## Testing

### Stack

- `vitest` or `jest` for unit/integration tests
- `@testing-library/react` for React components
- `playwright` or `cypress` for E2E tests
- `msw` for API mocking

### Unit Test Pattern

```typescript
import { describe, it, expect, vi } from 'vitest';

describe('UserService', () => {
  it('should create user with valid data', async () => {
    // Arrange
    const mockRepo: UserRepository = {
      findById: vi.fn(),
      save: vi.fn(),
    };
    const service = new UserService(mockRepo);

    // Act
    const user = await service.createUser({
      name: 'Test',
      email: 'test@example.com',
    });

    // Assert
    expect(user.name).toBe('Test');
    expect(mockRepo.save).toHaveBeenCalledWith(
      expect.objectContaining({ name: 'Test' })
    );
  });

  it('should throw NotFoundError for missing user', async () => {
    const mockRepo: UserRepository = {
      findById: vi.fn().mockResolvedValue(null),
      save: vi.fn(),
    };
    const service = new UserService(mockRepo);

    await expect(service.getUser('123')).rejects.toThrow(NotFoundError);
  });
});
```

### Coverage Target: 70-80%

---

## Code Quality

### ESLint + Prettier

```json
// .eslintrc.json
{
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/strict-type-checked",
    "plugin:@typescript-eslint/stylistic-type-checked",
    "prettier"
  ],
  "parser": "@typescript-eslint/parser",
  "parserOptions": {
    "project": "./tsconfig.json"
  },
  "rules": {
    "@typescript-eslint/no-explicit-any": "error",
    "@typescript-eslint/explicit-function-return-type": "warn",
    "@typescript-eslint/no-unused-vars": ["error", { "argsIgnorePattern": "^_" }]
  }
}
```

### Build Commands

```bash
# Type checking
tsc --noEmit

# Linting
eslint . --ext .ts,.tsx

# Testing
vitest run        # or: jest
vitest --coverage # or: jest --coverage

# Build
tsc               # or: esbuild, vite build, etc.
```

---

## Module System

### ESM by Default

```json
// package.json
{
  "type": "module"
}
```

```typescript
// GOOD: ESM imports
import { UserService } from './services/user.js';
import type { User } from './types/user.js';

// Note: .js extension required for Node.js ESM
// TypeScript resolves .ts files, but output uses .js
```

### Export Patterns

```typescript
// Named exports (preferred)
export interface User { ... }
export class UserService { ... }

// Barrel exports for public API
// src/index.ts
export { UserService } from './services/user.js';
export type { User } from './types/user.js';
```

---

## Quick Reference

| Need | Do This |
|------|---------|
| Object shape | `interface` |
| Union/intersection | `type` alias |
| Immutable data | `readonly` modifier, `as const` |
| Type narrowing | Type guard function |
| Runtime validation | Zod schema |
| Dependency | Constructor injection |
| Async operation | `async/await` |
| Multiple async | `Promise.all()` |
| Long function | Split into smaller functions |

## What NOT to Do

| Anti-Pattern | Instead |
|--------------|---------|
| `any` type | Proper type, `unknown`, or generic |
| Type assertions without validation | Type guards, Zod |
| `@ts-ignore` | Fix the type error |
| Implicit `any` in callbacks | Explicit types |
| `enum` (most cases) | `as const` objects |
| `namespace` | ES modules |
| Class for everything | Functions, plain objects |
| Barrel files in deep directories | Direct imports |
| `null` and `undefined` mixed | Pick one, use `strictNullChecks` |
| 100+ line functions | Break into focused units |
| Over-engineering "for the future" | Solve current problem only |
