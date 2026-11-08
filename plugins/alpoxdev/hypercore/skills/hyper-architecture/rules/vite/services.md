# API Services

> Vite project data layer (public client-side API wrappers)

---

## Overview

In Vite projects there are no server functions. All data access goes through **service functions** that wrap `fetch`/`axios` calls and return typed data. Routes, hooks, and loaders stay thin and call service/query-option helpers instead of networking directly.

| Layer | Tool | Purpose |
|-------|------|---------|
| Validation | Zod schemas | Input/output validation |
| Query | service function + `useQuery` | GET requests |
| Mutation | service function + `useMutation` | POST/PUT/DELETE |
| Prefetch | `queryClient.query({ ...options, staleTime: 'static' })` | Loader prefetch |

---

## Service Folder Structure

Canonical ownership path: `services/<domain>/` or `src/services/<domain-or-provider>/`.

```
services/
├── user/
│   ├── schemas.ts       # Zod schemas + inferred types
│   ├── queries.ts       # GET requests + queryOptions
│   └── mutations.ts     # POST/PUT/DELETE
```

| File | Purpose |
|------|---------|
| `schemas.ts` | Zod validation schemas |
| `queries.ts` | GET requests (read) + queryOptions |
| `mutations.ts` | POST/PUT/DELETE (write) |

Import service functions directly from `queries.ts` or `mutations.ts`. Do not add `services/index.ts` barrel exports. Shared services are nested by domain or provider; do not add direct leaf files such as `src/services/foo.ts` or `services/foo.ts` unless an explicit project exception is recorded.

---

## Schema Pattern

```typescript
// services/user/schemas.ts
import { z } from 'zod'

export const createUserSchema = z.object({
  email: z.email(),
  name: z.string().min(1).max(100).trim(),
})

export type CreateUserInput = z.infer<typeof createUserSchema>

export const userSchema = z.object({
  id: z.string(),
  email: z.email(),
  name: z.string(),
  createdAt: z.string(),
})

export type User = z.infer<typeof userSchema>
```

---

## Query Pattern (GET)

```typescript
// services/user/queries.ts
import { queryOptions } from '@tanstack/react-query'
import { apiClient } from '@/config/api-client'
import type { User } from './schemas'

export const getUsers = async (): Promise<User[]> => {
  const response = await apiClient.get('/users')
  return response.data
}

export const getUserById = async (id: string): Promise<User> => {
  const response = await apiClient.get(`/users/${id}`)
  return response.data
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// TanStack Query options
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
export const usersQueryOptions = () =>
  queryOptions({
    queryKey: ['users'],
    queryFn: getUsers,
  })

export const userQueryOptions = (id: string) =>
  queryOptions({
    queryKey: ['users', id],
    queryFn: () => getUserById(id),
  })
```

---

## Mutation Pattern (POST/PUT/DELETE)

```typescript
// services/user/mutations.ts
import { apiClient } from '@/config/api-client'
import { createUserSchema } from './schemas'
import type { CreateUserInput, User } from './schemas'

export const createUser = async (input: CreateUserInput): Promise<User> => {
  createUserSchema.parse(input)
  const response = await apiClient.post('/users', input)
  return response.data
}

export const updateUser = async (
  id: string,
  input: Partial<CreateUserInput>
): Promise<User> => {
  const response = await apiClient.put(`/users/${id}`, input)
  return response.data
}

export const deleteUser = async (id: string): Promise<void> => {
  await apiClient.delete(`/users/${id}`)
}
```

---

## Loader Prefetch Pattern

> Use `queryClient.query({ ...options, staleTime: 'static' })` in route loaders for public-safe prefetching. The loader may run during client navigation and can also participate in SSR/manual rendering if the project adds it later.

The current TanStack Router doc-recommended pairing is `queryClient.query({ ...queryOptions, staleTime: 'static' })` in the loader and `useSuspenseQuery` in the component: the loader fills the cache and marks it non-stale, so the component reads it without a loading flash.

`ensureQueryData`, `fetchQuery`, and `prefetchQuery` are deprecated in TanStack Query 5.102+ and will be removed in the next major version. `query()` also differs from the old helpers: retries are off by default (`retry: false`) because no component re-renders to retry, it rejects with the fetch error, and it does not accept observer-only options such as `enabled`, `refetchOn*`, `throwOnError`, `suspense`, or `placeholderData`.

```typescript
// routes/users/index.tsx
import { useSuspenseQuery } from '@tanstack/react-query'

export const Route = createFileRoute('/users/')({
  loader: ({ context: { queryClient } }) =>
    queryClient.query({ ...usersQueryOptions(), staleTime: 'static' }),
  component: UsersPage,
})

const UsersPage = (): JSX.Element => {
  const { data: users } = useSuspenseQuery(usersQueryOptions())
  return <UserList users={users} />
}

// routes/users/$id/index.tsx
export const Route = createFileRoute('/users/$id')({
  loader: ({ params: { id }, context: { queryClient } }) =>
    queryClient.query({ ...userQueryOptions(id), staleTime: 'static' }),
  component: UserDetailPage,
})
```

`useQuery` is fine for non-critical secondary data the loader did not await (e.g. analytics widgets); `useSuspenseQuery` stays the default for anything the loader prefetched.

For mixed-priority pages, start a non-critical fetch without awaiting it so it streams during SSR while the loader awaits the critical query. `query()` rejects on failure, so swallow the error where the result is optional (`noop` is a local no-op such as `() => {}`):

```typescript
// routes/dashboard/index.tsx
export const Route = createFileRoute('/dashboard/')({
  loader: ({ context: { queryClient } }) => {
    // Critical: block navigation until ready
    const user = queryClient.query({ ...userQueryOptions(), staleTime: 'static' })

    // Non-critical: start the request, do not await, ignore failures
    queryClient.query(analyticsQueryOptions()).catch(noop)

    return user
  },
  component: DashboardPage,
})
```

---

## API Client Setup

```typescript
// config/api-client.ts
import axios from 'axios'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: { 'Content-Type': 'application/json' },
})

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Authentication token interceptor
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
apiClient.interceptors.request.use((config) => {
  const token = getAuthToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      redirectToLogin()
    }
    return Promise.reject(error)
  }
)
```

---

## External SDK Services

> Third-party integrations follow the same pattern

```
services/<domain-or-provider>/
├── client.ts       # SDK client initialization
├── types.ts        # Type definitions
└── utils.ts        # Helper functions
```

```typescript
// services/stripe/client.ts
import Stripe from 'stripe'

export const stripe = new Stripe(import.meta.env.VITE_STRIPE_PUBLIC_KEY)
```

Vite 8 changed how a `default` import resolves from CommonJS packages, so a CommonJS SDK wrapper that worked under Vite 7 can resolve differently. Fix the import or the package instead of pinning the old behavior; `legacy.inconsistentCjsInterop: true` is only a temporary escape hatch.

---

## Best Practices

| Principle | Description |
|-----------|-------------|
| **File separation** | Separate schemas, queries, mutations required |
| **Return types** | All service functions must have explicit return types |
| **Validation** | Validate input with Zod before POST/PUT/PATCH |
| **queryOptions** | Export `queryOptions` factories for reuse in loaders and hooks |
| **Loader prefetch** | Use `queryClient.query({ ...options, staleTime: 'static' })`; `ensureQueryData`/`fetchQuery`/`prefetchQuery` are deprecated |
| **No direct fetch** | Never call `fetch`/`axios` in routes or hooks - use service functions |
| **Public-safe loaders** | Loaders only call services/query options and do not read secrets or private env values |
| **Error handling** | Let errors propagate to `errorComponent`; handle 401/403 in interceptors |

---

## Sources

> The TanStack Query loader-prefetch facts stated here (`queryClient.query({ ...options, staleTime: 'static' })`, the deprecation of `ensureQueryData`/`fetchQuery`/`prefetchQuery`, and the `query()` option surface) come from the dated snapshot recorded in `references/official/vite/current-docs-2026-11-04.md`, whose own verification date is 2026-11-04. The query-option factory layout, the loader/component cache pairing guidance, and the error-handling advice are this package's own guidance. The `services/<domain>/` layout, the no-barrel-export rule, and the `src/services/<domain-or-provider>/` grouping are Hypercore/repo-local conventions. No page was re-fetched for this file. Rule text and repository-local paths checked 2026-11-04.
