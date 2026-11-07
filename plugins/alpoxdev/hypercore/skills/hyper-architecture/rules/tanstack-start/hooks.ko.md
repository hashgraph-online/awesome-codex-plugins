# Custom Hook Patterns

> logic이 있는 page/component의 interactive logic, server-function wrapper, query orchestration, handler, memo, effect를 모읍니다.

## Rule Classifications

| Rule | Classification | Enforcement |
|---|---|---|
| React hooks는 React rules/tanstack-start 준수 | Official | 위반 시 차단 |
| `useServerFn`은 `@tanstack/react-start`에서 import | Official | 잘못된 import 수정 |
| touched interactive page의 `-hooks/` 추출 | Hypercore convention | official default 요청이 없으면 적용 |
| publishing-only static page는 `-hooks/` 예외 | Hypercore convention | 빈 폴더 생성 금지 |
| hook internal order | Hypercore convention | touched hook에 적용 |

## Extraction Rule

Interactive logic이 있는 page/component는 orchestration을 `-hooks/`로 옮깁니다:

- `useState`, `useReducer`, Zustand/global state
- `useServerFn` wrapper
- TanStack Query `useQuery` / `useMutation`
- handler와 callback
- derived memoized value
- effect와 lifecycle code

logic/server integration이 없는 publishing-only static page는 `-hooks/`가 필요 없습니다.

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
| `useServerFn` wrapper | Client component 또는 hook | `@tanstack/react-start` |
| TanStack Query | Client cache, mutation, invalidation | `@tanstack/react-query` |

## Validation Checklist

- [ ] publishing-only static page에 hook file 생성을 강제하지 않음.
- [ ] logic이 있는 touched page/component가 orchestration을 hook으로 추출함.
- [ ] hook filename이 `use-users.ts` 같은 kebab-case임.
- [ ] hook에 explicit return type/interface가 있음.
- [ ] `useServerFn` wrapper가 `@tanstack/react-start`에서 import됨.
- [ ] hook order가 hypercore sequence를 따르거나 deviation 이유가 기록됨.

## Sources

> 출처 확인 2026-11-04. 이 파일은 이 패키지 자체의 snapshot(`references/official/tanstack-start/tanstack-start-2026-11-04.md`, `references/official/tanstack-start/tanstack-router-2026-11-04.md`, `references/official/tanstack-start/current-docs-2026-11-04.md`)에 담기지 않은 공식 사실을 주장하지 않습니다. 그 snapshot의 공식 사실은 거기 나열된 TanStack guide page에서 2026-11-04에 다시 검증했습니다. 저장소 로컬 링크 확인 2026-11-04.
