# TypeScript Fundamentals for Frontend

Shared TypeScript patterns loaded for ALL frontend projects regardless of framework. Referenced by the frontend-dev skill alongside framework-specific pattern files.

---

## Review Standards

Enforce these during Staff Engineer Review (Phase 4) — **applies to every frontend framework**:

- TypeScript strict mode enabled (`strict: true` in tsconfig.json)
- No `any` types — use proper types, `unknown`, or generics
- Type inference leveraged where obvious — annotate when not inferrable
- Proper type guards for runtime type narrowing
- Validate data at trust boundaries — not just "somewhere," but at every point where untyped data enters the app
- Imports organized: external → internal aliases → relative
- `as const` over enums for literal unions
- No `@ts-ignore` — fix the type error

---

## Configuration

```json
// tsconfig.json — minimum strictness for frontend projects
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

**Note:** Framework-specific options (e.g., `"jsx": "react-jsx"`, `"module": "esnext"`) are covered in each framework's pattern file.

---

## Type Inference

```typescript
// GOOD: Let TypeScript infer when obvious
const users = await fetchUsers();       // Type inferred from return
const [count, setCount] = useState(0);  // Inferred as number
const name = "hello";                   // Inferred as string

// GOOD: Annotate when not inferrable or for clarity
const users: User[] = [];
function getUser(id: string): Promise<User | null> { ... }

// BAD: Redundant annotations
const count: number = 0;
const name: string = "hello";
```

---

## Utility Types

```typescript
// Partial — all properties optional
type UpdateUser = Partial<User>;

// Pick — select specific properties
type UserPreview = Pick<User, "id" | "name">;

// Omit — exclude specific properties
type CreateUser = Omit<User, "id" | "createdAt">;

// Record — typed object with string keys
type UserRoles = Record<string, "admin" | "user" | "guest">;

// satisfies — type check without widening
const config = {
  apiUrl: "https://api.example.com",
  timeout: 5000,
} satisfies Record<string, string | number>;

// Readonly — immutable objects
type ImmutableUser = Readonly<User>;
```

---

## Discriminated Unions

```typescript
// Model state machines with discriminated unions
type AsyncState<T> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: T }
  | { status: "error"; error: Error };

// TypeScript narrows the type inside each branch
function handleState<T>(state: AsyncState<T>) {
  switch (state.status) {
    case "idle": return null;
    case "loading": return "Loading...";
    case "success": return state.data;  // TS knows `data` exists here
    case "error": return state.error;   // TS knows `error` exists here
  }
}
```

---

## Generics

```typescript
// Constrained generics
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

// Generic with default
interface ApiResponse<T = unknown> {
  data: T;
  status: number;
}

// Conditional types
type Awaited<T> = T extends Promise<infer U> ? U : T;
```

---

## Type Guards

```typescript
// Type predicates
function isUser(value: unknown): value is User {
  return (
    typeof value === "object" &&
    value !== null &&
    "id" in value &&
    "name" in value
  );
}

// Assertion functions
function assertUser(value: unknown): asserts value is User {
  if (!isUser(value)) {
    throw new Error("Invalid user");
  }
}

// Usage
if (isUser(data)) {
  console.log(data.name); // TypeScript knows data is User
}
```

---

## Const Assertions

```typescript
// GOOD: Use const assertions for literal types (instead of enums)
const STATUS = {
  ACTIVE: "active",
  INACTIVE: "inactive",
} as const;

type Status = typeof STATUS[keyof typeof STATUS]; // "active" | "inactive"

// BAD: Using enums
enum Status { ACTIVE = "active", INACTIVE = "inactive" }
```

---

## Import Organization

```typescript
// 1. External packages
import { useState } from "react";
import { z } from "zod";

// 2. Internal aliases
import { Button } from "@/components/Button";
import { useAuth } from "@/hooks/useAuth";
import type { User } from "@/types";

// 3. Relative imports
import { helper } from "./utils";
```

**Rule:** `type` imports use `import type` to ensure they're erased at compile time.

---

## Validation with Zod

```typescript
import { z } from "zod";

// Schema definition
const UserSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(100),
  email: z.string().email(),
  age: z.number().int().positive().optional(),
});

// Infer TypeScript type from schema
type User = z.infer<typeof UserSchema>;

// Safe validation
const result = UserSchema.safeParse(data);
if (result.success) {
  console.log(result.data); // typed as User
} else {
  console.error(result.error.issues);
}
```

---

## Trust Boundary Validation

External data enters the app untyped at these specific points — validate at each one:

- **API responses** — in fetch wrappers, before the data reaches components
- **`JSON.parse()` results** — localStorage reads, message payloads, serialized state
- **URL / query parameters** — route params, search params, hash fragments
- **Persist rehydration** — state management persist layers (Zustand persist, Redux persist, etc.)

The validation tool (Zod, Valibot, ArkType, io-ts) is a project choice. The discipline of validating at these four boundaries is not.

---

## Quick Reference

| Need | Do This |
|------|---------|
| Object shape | `interface` |
| Union/intersection | `type` alias |
| Immutable data | `Readonly<T>`, `as const` |
| Type narrowing | Type guard function |
| Runtime validation | Zod schema |
| Literal union | `as const` object (not enum) |
| Optional subset | `Partial<T>`, `Pick<T, K>` |

## What NOT to Do

| Anti-Pattern | Instead |
|--------------|---------|
| `any` type | Proper type, `unknown`, or generic |
| Type assertions without validation | Type guards, Zod |
| `@ts-ignore` | Fix the type error |
| Implicit `any` in callbacks | Explicit parameter types |
| `enum` (most cases) | `as const` objects |
| Redundant type annotations | Let TypeScript infer |
| `null` and `undefined` mixed | Pick one, use `strictNullChecks` |
