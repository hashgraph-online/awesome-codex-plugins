# 커스텀 훅 패턴

> 페이지/섹션의 모든 로직, 상태, 생명주기를 중앙화

---

## 필수 규칙: 커스텀 훅 분리

**모든 페이지는 커스텀 훅을 `-hooks/` 폴더로 분리해야 합니다.**

- 페이지 크기(줄 수)에 무관하게 반드시 분리
- 10줄짜리 단순 페이지도 훅 분리 필요
- 페이지 컴포넌트는 UI 렌더링만 처리

```
routes/users/
├── index.tsx              // UI만
├── -hooks/
│   └── use-users.ts       // 모든 로직
├── -components/
```

---

## 훅 내부 순서 (필수)

| 순서 | 훅 타입 | 예시 |
|-------|-----------|---------|
| 1 | State | `useState`, zustand 스토어 |
| 2 | Global Hooks | `useParams`, `useNavigate`, `useQueryClient` |
| 3 | React Query | `useQuery` -> `useMutation` |
| 4 | Event Handlers | `handleCreate`, `handleDelete` (useCallback) |
| 5 | useMemo | 계산된 값 |
| 6 | useEffect | 사이드 이펙트 |

---

## 페이지 훅 패턴

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
    // 사이드 이펙트
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

## 잘못된 순서 (금지)

```typescript
export const useBadHook = () => {
  const queryClient = useQueryClient()  // Global Hook 먼저 - 잘못됨
  useEffect(() => { /* ... */ }, [])    // 중간에 useEffect - 잘못됨
  const [state, setState] = useState()  // State가 나중에 - 잘못됨
  const { data } = useQuery({})         // Effect 뒤에 Query - 잘못됨
}
```

---

## TanStack Router 훅

| 훅 | 용도 | 예시 |
|------|---------|---------|
| `useParams` | URL 파라미터 | `const { id } = useParams({ from: '/users/$id' })` |
| `useNavigate` | 탐색 | `navigate({ to: '/users' })` |
| `useSearch` | 검색 파라미터 | `const { page } = useSearch({ from: '/users' })` |
| `useLoaderData` | 로더 데이터 | `const user = Route.useLoaderData()` |
| `useRouteContext` | 라우트 컨텍스트 | `const { auth } = useRouteContext({ from: '__root__' })` |

> `useServerFn`은 Vite 프로젝트에 존재하지 않습니다. `useQuery`/`useMutation`을 직접 사용하세요.

---

## 요구사항

| 원칙 | 설명 |
|-----------|-------------|
| **순서 준수** | State -> Global -> Query -> Handlers -> Memo -> Effect |
| **타입 정의** | 명시적 반환 타입 (인터페이스) |
| **단일 책임** | 하나의 훅이 하나의 관심사만 처리 |
| **useCallback** | 이벤트 핸들러를 useCallback으로 메모이제이션 |
| **명확한 네이밍** | `use-users.ts`, `use-user-filter.ts` |
| **서버 함수 없음** | `useServerFn` 절대 사용 금지 - 서비스 직접 호출 |

---

## Sources

> 이 파일에는 외부 출처를 사용하지 않았습니다. `-hooks/` 분리 의무, State -> Global -> Query -> Handlers -> Memo -> Effect 순서, exported return-type interface 요구, `use-kebab-case.ts` 네이밍 규칙은 Hypercore/repo-local convention이고, 예시에 나오는 React/TanStack Query API 이름은 dated source에서 가져온 주장이 아니라 라이브러리 식별자입니다. 규칙 문장과 저장소 로컬 경로 확인 2026-09-21.
