# Code Conventions

> Vite + TanStack Router project coding rules/vite

---

## File Naming

> camelCase filenames are FORBIDDEN - all filenames must use kebab-case

| Type | Rule | Example |
|------|------|---------|
| **General files** | kebab-case | `user-profile.tsx`, `auth-service.ts` |
| **Route files** | TanStack Router rules/vite | `__root.tsx`, `index.tsx`, `$id.tsx` |
| **Hook files** | `use-` prefix + kebab-case | `use-user-filter.ts`, `use-auth.ts` |
| **Components** | PascalCase component, kebab-case file | `UserCard` in `user-card.tsx` |
| **Service files** | kebab-case | `get-users.ts`, `create-post.ts` |

```
FORBIDDEN camelCase: getUserById.ts, authService.ts, useUserFilter.ts
REQUIRED kebab-case: get-user-by-id.ts, auth-service.ts, use-user-filter.ts
```

---

## TypeScript Rules

| Rule | Description | Example |
|------|-------------|---------|
| **Function declaration** | const arrow function, explicit return type | `const fn = (): ReturnType => {}` |
| **Type definition** | interface (objects), type (unions) | `interface User {}`, `type Status = 'a' \| 'b'` |
| **No any** | Use unknown | `const data: unknown = JSON.parse(str)` |
| **Type imports** | Separate type imports | `import type { User } from '@/types'` |

```typescript
// const arrow function, explicit types
const getUserById = async (id: string): Promise<User> => {
  const response = await apiClient.get(`/users/${id}`)
  return response.data
}

// No any -> use unknown
const parseJSON = (data: string): unknown => {
  return JSON.parse(data)
}

// function keyword FORBIDDEN
// function badFunction() {} -> use const arrow function
```

---

## Import Order

```typescript
// 1. External libraries
import { createFileRoute } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { z } from 'zod'

// 2. Internal packages (@/)
import { Button } from '@/components/ui/button'
import { apiClient } from '@/config/api-client'
import { usersQueryOptions } from '@/services/user/queries'

// 3. Relative imports (route-specific)
import { UserCard } from './-components/user-card'
import { useUsers } from './-hooks/use-users'

// 4. Type imports
import type { User } from '@/types'
import type { UseUsersReturn } from './-hooks/use-users'
```

---

## Korean Block Comments (per group)

Use Korean descriptions in real project code. The example below uses English placeholder text so this canonical documentation remains English-only.

```typescript
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// User-related state
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const [user, setUser] = useState<User | null>(null)
const [isLoading, setIsLoading] = useState(false)

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Data fetching
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const { data: users } = useQuery(usersQueryOptions())
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

---

## Sources

> This file's naming, TypeScript, import-order, comment, and error-handling rules/vite are Hypercore/repo-local conventions, not official Vite or TanStack Router requirements. Its TanStack Router route-filename entries are this package's own guidance and are not facts taken from the dated snapshot recorded in `references/official/vite/current-docs-2026-11-04.md` (that snapshot's own verification date is 2026-11-04); no external source was used for them. No page was re-fetched for this file, and no other external source is cited. Rule text and repository-local paths checked 2026-11-04.
