# Code Conventions

> TanStack Start project coding rules/tanstack-start

---

## Rule Classifications

| Rule | Classification | Enforcement |
|---|---|---|
| Route file names follow TanStack Router conventions | Official | Keep official route names |
| Kebab-case non-route filenames | Hypercore convention | Apply to touched files |
| No `any`, explicit return types, const arrow functions | Hypercore convention | Apply to touched code |
| Korean block comments for meaningful code groups | Hypercore convention | Apply to touched implementation files |

---

## File Naming

> camelCase filenames are FORBIDDEN - all filenames must use kebab-case

| Type | Rule | Example |
|------|------|---------|
| **General files** | kebab-case | `user-profile.tsx`, `auth-service.ts` |
| **Route files** | TanStack Router rules/tanstack-start | `__root.tsx`, `index.tsx`, `$id.tsx` |
| **Hook files** | `use-` prefix + kebab-case | `use-user-filter.ts`, `use-auth.ts` |
| **Components** | PascalCase component, kebab-case file | `UserCard` in `user-card.tsx` |
| **Server Functions** | kebab-case | `get-users.ts`, `create-post.ts` |

```
FORBIDDEN camelCase: getUserById.ts, authService.ts, useUserFilter.ts
REQUIRED kebab-case: get-user-by-id.ts, auth-service.ts, use-user-filter.ts
```

Folder shape and placement (route roots, shared folders, and co-located `-hooks/` / `-components/` / `-functions/` directories) are owned by [`rules/tanstack-start/project-structure.md`](project-structure.md); this file owns file naming. Apply both when adding files.

---

## TypeScript Rules

| Rule | Description | Example |
|------|-------------|---------|
| **Function declaration** | const arrow function, explicit return type (framework entrypoint exemption below) | `const fn = (): ReturnType => {}` |
| **Type definition** | interface (objects), type (unions) | `interface User {}`, `type Status = 'a' \| 'b'` |
| **No any** | Use unknown | `const data: unknown = JSON.parse(str)` |
| **Type imports** | Separate type imports | `import type { User } from '@/types'` |

```typescript
// const arrow function, explicit types
const getUserById = async (id: string): Promise<User> => {
  return prisma.user.findUnique({ where: { id } })
}

// No any -> use unknown
const parseJSON = (data: string): unknown => {
  return JSON.parse(data)
}

// function keyword FORBIDDEN, except at a framework entrypoint whose official example is a declaration
// function badFunction() {} -> use const arrow function
```

**Framework entrypoint exemption (Official).** The ban on function declarations has exactly one exception: a framework-mandated entrypoint whose official example uses a declaration. `src/router.tsx` must `export function getRouter()` (Official), so that single file keeps its declaration. The exemption covers the declaration FORM only - explicit return types, `no any`, kebab-case filenames, and Korean block comments still apply there, and the const arrow function rule still applies to every other file (route files, hooks, components, server functions, and libs).

---

## Import Order

```typescript
// 1. External libraries
import { createFileRoute } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { z } from 'zod'

// 2. Internal packages (@/)
import { Button } from '@/components/ui/button'
import { prisma } from '@/database/prisma'
import { getUsers } from '@/modules/users/list/users.functions'

// 3. Relative imports (route-specific)
import { UserCard } from './-components/user-card'
import { useUsers } from './-hooks/use-users'

// 4. Type imports
import type { User } from '@/types'
import type { UseUsersReturn } from './-hooks/use-users'
```

---

## Korean Block Comments (per group)

```typescript
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// User-related state
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const [user, setUser] = useState<User | null>(null)
const [isLoading, setIsLoading] = useState(false)

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Data fetching
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const { data: users } = useQuery({
  queryKey: ['users'],
  queryFn: () => getUsers(),
})
```

Line-by-line comments are FORBIDDEN. Comments only per code group/block.

---

## Error Handling Pattern

```typescript
// lib/errors.ts
export class AppError extends Error {
  constructor(
    message: string,
    public statusCode: number = 500,
    public code: string = 'INTERNAL_ERROR'
  ) {
    super(message)
    this.name = 'AppError'
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string) {
    super(`${resource} not found`, 404, 'NOT_FOUND')
  }
}

export class ValidationError extends AppError {
  constructor(message: string) {
    super(message, 400, 'VALIDATION_ERROR')
  }
}

export class UnauthorizedError extends AppError {
  constructor() {
    super('Unauthorized', 401, 'UNAUTHORIZED')
  }
}
```

## Sources

> Sources checked 2026-11-04. This file states no official fact that is not carried in this package's own snapshots: `references/official/tanstack-start/tanstack-start-2026-11-04.md`, `references/official/tanstack-start/tanstack-router-2026-11-04.md`, and `references/official/tanstack-start/current-docs-2026-11-04.md`, whose official facts were re-verified on 2026-11-04 from the TanStack guide pages listed there. Repository-local links checked 2026-11-04.
