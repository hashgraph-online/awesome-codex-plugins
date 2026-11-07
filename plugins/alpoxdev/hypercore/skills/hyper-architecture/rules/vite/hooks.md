# Custom Hook Patterns

> Centralize all logic, state, and lifecycle for pages/sections

---

## Required Rule: Custom Hook Separation

**Every page MUST separate Custom Hooks into the `-hooks/` folder.**

- MUST separate regardless of page size (line count)
- Even a 10-line simple page requires Hook separation
- Page components handle ONLY UI rendering

```
routes/users/
├── index.tsx              // UI only
├── -hooks/
│   └── use-users.ts       // All logic
├── -components/
```

---

## Hook Internal Order (Required)

| Order | Hook Type | Example |
|-------|-----------|---------|
| 1 | State | `useState`, zustand store |
| 2 | Global Hooks | `useParams`, `useNavigate`, `useQueryClient` |
| 3 | React Query | `useQuery` -> `useMutation` |
| 4 | Event Handlers | `handleCreate`, `handleDelete` (useCallback) |
| 5 | useMemo | Computed values |
| 6 | useEffect | Side effects |

---

## Page Hook Pattern

```typescript
// routes/users/-hooks/use-users.ts
import { useState, useMemo, useEffect, useCallback } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { usersQueryOptions } from '@/services/user/queries'
import { createUser, deleteUser } from '@/services/user/mutations'
import type { User } from '@/types'

interface UseUsersReturn {
  users: User[] | undefined
  filteredUsers: User[]
  isLoading: boolean
  search: string
  setSearch: (value: string) => void
  handleCreate: (data: { email: string; name: string }) => void
  handleDelete: (id: string) => void
}

export const useUsers = (): UseUsersReturn => {
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // 1. State
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  const [search, setSearch] = useState('')

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // 2. Global Hooks
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // 3. React Query
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  const { data: users, isLoading } = useQuery(usersQueryOptions())

  const createMutation = useMutation({
    mutationFn: createUser,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  })

  const deleteMutation = useMutation({
    mutationFn: deleteUser,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  })

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // 4. Event Handlers
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  const handleCreate = useCallback(
    (data: { email: string; name: string }) => {
      createMutation.mutate(data)
    },
    [createMutation]
  )

  const handleDelete = useCallback(
    (id: string) => {
      deleteMutation.mutate(id)
    },
    [deleteMutation]
  )

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // 5. useMemo
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  const filteredUsers = useMemo(() => {
    if (!users) return []
    if (!search) return users
    return users.filter((user) =>
      user.name.toLowerCase().includes(search.toLowerCase())
    )
  }, [users, search])

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // 6. useEffect
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  useEffect(() => {
    // Side effects here
  }, [])

  return {
    users,
    filteredUsers,
    isLoading,
    search,
    setSearch,
    handleCreate,
    handleDelete,
  }
}
```

---

## Wrong Order (Forbidden)

```typescript
export const useBadHook = () => {
  const queryClient = useQueryClient()  // Global Hook first - WRONG
  useEffect(() => { /* ... */ }, [])    // useEffect in the middle - WRONG
  const [state, setState] = useState()  // State after - WRONG
  const { data } = useQuery({})         // Query after Effect - WRONG
}
```

---

## TanStack Router Hooks

| Hook | Purpose | Example |
|------|---------|---------|
| `useParams` | URL parameters | `const { id } = useParams({ from: '/users/$id' })` |
| `useNavigate` | Navigation | `navigate({ to: '/users' })` |
| `useSearch` | Search params | `const { page } = useSearch({ from: '/users' })` |
| `useLoaderData` | Loader data | `const user = Route.useLoaderData()` |
| `useRouteContext` | Route context | `const { auth } = useRouteContext({ from: '__root__' })` |

> `useServerFn` does NOT exist in Vite projects. Use `useQuery`/`useMutation` directly.

---

## React Query Pattern (Standard)

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { usersQueryOptions } from '@/services/user/queries'
import { createUser } from '@/services/user/mutations'

export const useUsers = (): UseUsersReturn => {
  const queryClient = useQueryClient()

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // React Query
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  const { data: users, isLoading } = useQuery(usersQueryOptions())

  const createMutation = useMutation({
    mutationFn: (data: { email: string; name: string }) => createUser(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  })

  return { users, isLoading, createMutation }
}
```

---

## Requirements

| Principle | Description |
|-----------|-------------|
| **Order compliance** | State -> Global -> Query -> Handlers -> Memo -> Effect |
| **Type definition** | Explicit return type (interface) |
| **Single responsibility** | One Hook handles one concern |
| **useCallback** | Memoize event handlers with useCallback |
| **Clear naming** | `use-users.ts`, `use-user-filter.ts` |
| **No server functions** | Never use `useServerFn` - call services directly |

---

## Sources

> No external source was used for this file. The mandatory `-hooks/` separation, the State -> Global -> Query -> Handlers -> Memo -> Effect order, the exported return-type interface requirement, and the `use-kebab-case.ts` naming rule are Hypercore/repo-local conventions; the React and TanStack Query API names used in the examples are library identifiers, not claims taken from a dated source. Rule text and repository-local paths checked 2026-09-21.
