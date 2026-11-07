# Custom Hook Patterns

> Centralize interactive logic, server-function wrappers, query orchestration, handlers, memoization, and effects for pages/components that have logic.

## Rule Classifications

| Rule | Classification | Enforcement |
|---|---|---|
| React hooks follow React rules/tanstack-start | Official | Block violations |
| `useServerFn` imported from `@tanstack/react-start` | Official | Fix wrong imports |
| Logic extraction to `-hooks/` for touched interactive pages | Hypercore convention | Apply unless official defaults requested |
| Publishing-only static pages exempt from `-hooks/` | Hypercore convention | Do not create empty folders |
| Internal hook order | Hypercore convention | Apply to touched hooks |

## Extraction Rule

Pages/components with interactive logic must move orchestration into `-hooks/`:

- `useState`, `useReducer`, Zustand/global state
- `useServerFn` wrappers
- TanStack Query `useQuery` / `useMutation`
- Handlers and callbacks
- Derived memoized values
- Effects and lifecycle code

Publishing-only static pages with no logic and no server integration do not need `-hooks/`.

## Folder Pattern

```text
routes/users/
├── index.tsx
├── -hooks/
│   └── use-users.ts
├── -components/
└── -functions/
```

## Hook Internal Order

```typescript
export const useUsers = (): UseUsersReturn => {
  // 1. State
  // 2. Global stores / context
  // 3. Server function wrappers with useServerFn
  // 4. Queries and mutations
  // 5. Handlers / callbacks
  // 6. Memoized derived values
  // 7. Effects
  // 8. Return object
}
```

## `useServerFn` + TanStack Query Pattern

```typescript
import { useServerFn } from '@tanstack/react-start'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getUsers } from '../-functions/get-users'
import { createUser } from '../-functions/create-user'

export const useUsers = (): UseUsersReturn => {
  const queryClient = useQueryClient()
  const getServerUsers = useServerFn(getUsers)
  const createServerUser = useServerFn(createUser)

  const usersQuery = useQuery({
    queryKey: ['users'],
    queryFn: () => getServerUsers(),
  })

  const createMutation = useMutation({
    mutationFn: (data: CreateUserInput) => createServerUser({ data }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  })

  return { usersQuery, createMutation }
}
```

## Direct Calls vs Wrappers

| Pattern | When | Import/source |
|---|---|---|
| Direct server function call | `loader`, `beforeLoad`, server-only code | Direct import |
| `useServerFn` wrapper | Client component or hook | `@tanstack/react-start` |
| TanStack Query | Client cache, mutations, invalidation | `@tanstack/react-query` |

## Validation Checklist

- [ ] Publishing-only static pages were not forced to create hook files.
- [ ] Touched pages/components with logic extract orchestration to a hook.
- [ ] Hook files use kebab-case filenames such as `use-users.ts`.
- [ ] Hook has an explicit return type/interface.
- [ ] `useServerFn` wrappers are imported from `@tanstack/react-start`.
- [ ] Hook order follows the hypercore sequence or records a reason for deviation.

## Sources

> Sources checked 2026-11-04. This file states no official fact that is not carried in this package's own snapshots: `references/official/tanstack-start/tanstack-start-2026-11-04.md`, `references/official/tanstack-start/tanstack-router-2026-11-04.md`, and `references/official/tanstack-start/current-docs-2026-11-04.md`, whose official facts were re-verified on 2026-11-04 from the TanStack guide pages listed there. Repository-local links checked 2026-11-04.
