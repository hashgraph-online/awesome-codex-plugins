# 아키텍처 규칙 참조

> Vite + TanStack Router hypercore 프로젝트를 위한 전체 규칙 세트

참고: 아래 일부 규칙은 TanStack Router 기본값보다 엄격합니다. 이는 보편적인 framework requirements가 아니라 hypercore team conventions입니다.

Drift에 민감한 Vite/TanStack Router 동작의 출처 우선순위는 `references/official/vite/current-docs-2026-11-04.ko.md`에서 시작합니다.

Brownfield 적용 규칙: 손대지 않은 legacy code는 문제가 stylistic 또는 hypercore-specific이면 즉시 실패가 아니라 migration work로 추적할 수 있습니다. Safety-boundary issues는 특히 touched code에서 즉시 차단합니다.

---

## 금지

| 범주 | 금지 사항 |
|----------|-----------|
| Routes | 자체 UI/logic folders를 소유하는 full page에 flat file routes 사용 (`routes/users.tsx`) |
| Route Export | `export const IndexRoute`, `const Route` (without export) |
| Server Functions | `createServerFn`, `useServerFn`, `createMiddleware` (server-side) |
| Route Folders | 어떤 route 안에도 `-functions/` folder 생성 |
| Layers | Routes 또는 hooks에서 직접 `fetch`/`axios` 호출 |
| Barrel Export | `services/index.ts` (Tree Shaking failure) |
| Folder Names | `lib/store` (`stores/` 사용); explicit exception 없는 `src/lib/foo.ts`, `src/services/foo.ts` 같은 direct shared leaves |
| Filenames | camelCase (`getUserById.ts`) |
| TypeScript | `any` type, `function` keyword declaration |
| Runtime Boundaries | Client-reachable route code에서 secrets, DB clients, non-`VITE_` env reads 사용 |
| Generated Files | `routeTree.gen.ts` 직접 수정 |
| Git | AI markers, multi-line commit messages, emojis |

---

## 레이어 아키텍처

```
Client (Browser)
  TanStack Router -> TanStack Query -> React UI
  State: TanStack Query (80%) + Zustand (20%)
       |
       v
  Services (API wrappers)
  schemas.ts, queries.ts, mutations.ts
       |
       v
  External API (REST / GraphQL / RPC)
```

**Data flow rules:**
- Query: Page -> useQuery -> service function -> fetch/axios -> External API
- Mutation: Form -> useMutation -> schema validation -> service function -> External API -> invalidateQueries

---

## Route Structure Rules

### 모든 page는 반드시 다음을 가집니다:
```
routes/<page>/
├── route.tsx          # Shared layout / beforeLoad / loader when needed
├── index.tsx          # UI only (no logic)
├── -components/       # REQUIRED always
├── -hooks/            # REQUIRED always (even 10-line pages)
├── $child/
│   ├── index.tsx
│   ├── -components/
│   └── -hooks/
└── -sections/         # Optional (200+ lines only)
```

TanStack Router가 `posts.$postId.tsx` 같은 flat file forms도 지원하지만, hypercore는 `-components/` 또는 `-hooks/`를 소유하는 모든 page에 directory routes를 선호합니다.

### Route Export (strict):
```typescript
// MUST be exactly this pattern
export const Route = createFileRoute('/path')({
  component: PageComponent,
})
```

### Route Group pattern:
- List pages -> `(main)/` route group
- Create/Edit pages -> outside group
- Shared layout에는 `route.tsx` 사용 (beforeLoad, loader)
- Repo가 `routeToken`을 customize한다면 folder convention을 explicit하게 document합니다.

### beforeLoad vs loader:
| | beforeLoad | loader |
|---|-----------|--------|
| Execution | Sequential (outer -> inner) | Parallel (after beforeLoad) |
| Use | Auth check, redirects | Query prefetching |
| Performance | HIGH impact (blocking) | LOW impact (parallel) |

### Loader pattern (client-reachable prefetch):
```typescript
// Use queryClient.query with a static staleTime for TanStack Query prefetching.
// ensureQueryData, fetchQuery, prefetchQuery는 TanStack Query 5.102+에서 deprecated입니다.
// Treat loaders as client-reachable. If the app later adds SSR/manual rendering,
// the same loader may also run during server render.
loader: ({ context: { queryClient } }) =>
  queryClient.query({ ...usersQueryOptions(), staleTime: 'static' }),
```

### Component separation:
- 100+ lines -> `-components/`로 extract
- 200+ lines -> `-sections/`로 extract
- Logic이 있는 component -> `-hooks/`를 가진 subfolder

```
-components/
├── user-card/
│   ├── index.tsx           # UI only
│   └── -hooks/
│       └── use-user-card.ts # Logic
```

---

## Shared Nested Folder Grouping

routes 밖의 shared code는 touched shared code를 추가하거나 재구성할 때 logical nested grouping을 사용합니다. 이는 Hypercore/repo-local convention이며 official Vite 또는 TanStack Router law가 아닙니다. explicit project exception이 없으면 `src/lib/foo.ts`, `src/services/foo.ts`, `lib/foo.ts`, `services/foo.ts` 같은 new direct leaf file을 만들지 않습니다. Ownership, runtime boundaries, provider integrations, dependency direction을 보여주기 위해 `src/lib/<domain>/...`, `src/services/<domain-or-provider>/...`를 선호합니다.

권장 shared shape:

```text
src/lib/<domain>/
src/services/<domain-or-provider>/
src/config/<area>/
src/server/<area>/
```

## Services Rules

### Folder structure:
```
services/<domain>/
├── schemas.ts      # Zod schemas + inferred types
├── queries.ts      # GET requests (read)
└── mutations.ts    # POST/PUT/DELETE (write)
```

Service functions는 `queries.ts` 또는 `mutations.ts`에서 직접 import합니다. `services/index.ts` barrel exports를 추가하지 않습니다.

### Query function pattern:
```typescript
// services/user/queries.ts
import type { User } from '@/types'

export const getUsers = async (): Promise<User[]> => {
  const response = await apiClient.get('/users')
  return response.data
}

export const getUserById = async (id: string): Promise<User> => {
  const response = await apiClient.get(`/users/${id}`)
  return response.data
}
```

### Mutation function pattern:
```typescript
// services/user/mutations.ts
import { createUserSchema } from './schemas'
import type { CreateUserInput, User } from '@/types'

export const createUser = async (input: CreateUserInput): Promise<User> => {
  createUserSchema.parse(input)  // validate before send
  const response = await apiClient.post('/users', input)
  return response.data
}
```

### TanStack Query options pattern:
```typescript
// services/user/queries.ts
import { queryOptions } from '@tanstack/react-query'

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

## Hook Rules

### Mandatory separation:
모든 page는 `-hooks/` folder에 hooks를 가져야 합니다. Page size와 관계없이 예외가 없습니다.

### Internal order (STRICT):
```typescript
export const usePageName = (): UsePageNameReturn => {
  // 1. State (useState, zustand)
  // 2. Global Hooks (useParams, useNavigate, useQueryClient)
  // 3. React Query (useQuery -> useMutation)
  // 4. Event Handlers (useCallback)
  // 5. useMemo (computed values)
  // 6. useEffect (side effects)

  return { /* ... */ }
}
```

### Requirements:
- Return type interface를 define/export합니다.
- 각 section에 Korean block comments를 사용합니다 (`━━━` separator 포함).
- Event handlers에는 `useCallback`을 사용합니다.
- File naming: `use-kebab-case.ts`

---

## Convention Rules

### Filenames:
| Type | Rule | Example |
|------|------|---------|
| General | kebab-case | `user-profile.tsx` |
| Route files | TanStack Router | `__root.tsx`, `index.tsx`, `$id.tsx` |
| Hook files | `use-` prefix | `use-user-filter.ts` |
| Service files | kebab-case | `get-users.ts` |

### TypeScript:
- `const` arrow functions (`function` keyword 금지)
- Explicit return types always
- Objects에는 `interface`, unions에는 `type`
- `any` 대신 `unknown`
- Type imports 분리: `import type { X } from '...'`

### Import order:
```typescript
// 1. External libraries
import { createFileRoute } from '@tanstack/react-router'
// 2. Internal (@/)
import { Button } from '@/components/ui/button'
// 3. Relative
import { UserCard } from './-components/user-card'
// 4. Type imports
import type { User } from '@/types'
```

### Korean block comments:
```typescript
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 섹션 설명
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Error handling:
- 각 route에 `errorComponent` 필요
- `__root.tsx`에 `notFoundComponent` 필요
- Custom error classes: `AppError`, `NotFoundError`, `ValidationError`, `UnauthorizedError`

---

## Execution Model Rules

- Route modules와 loaders는 기본적으로 client-reachable입니다.
- App이 SSR/manual server rendering을 추가하면 loaders는 server render 중에도 실행될 수 있습니다.
- Secrets, DB clients, filesystem access, privileged SDKs는 routes, loaders, shared client-reachable helpers에 두지 않습니다.
- Browser APIs는 module scope나 boundary 없는 shared route utilities가 아니라 components/hooks/effects에 둡니다.
- Client-reachable code에는 public `VITE_` env values만 둡니다.

---

## Platform Setup Rules

- `vite.config.ts`는 `tanstackRouter()`를 explicit하게 유지하고 `react()`보다 앞에 둡니다.
- `@vitejs/plugin-react` 6은 Vite 8에 두고(peer가 `vite: ^8.0.0`), `@tanstack/router-plugin`과 `@tanstack/react-router`는 같은 릴리스로 함께 올립니다.
- `routeTree.gen.ts`는 generated output이며 직접 수정하면 안 됩니다.
- 새 Vite 설정은 Oxc/Rolldown 이름(`oxc`, `build.rolldownOptions`, Rolldown `output.codeSplitting`)을 쓰고, `esbuild`, `build.rollupOptions`, 객체형 `manualChunks`를 새로 넣지 않습니다.
- `src/router.tsx`의 router wiring을 explicit하게 유지합니다.
- SSR/manual rendering이 있다면 process-global singleton보다 fresh router factory를 선호합니다.
- Vite와 TypeScript config 양쪽에서 path alias를 명시적으로 유지합니다.
- ad-hoc read에 의존하지 말고 env typing/runtime validation을 명시적으로 유지합니다.

---

## Auto-Remediation Policy

- 문제가 local, reversible, low-risk이면 직접 auto-fix합니다.
- 예시: `validateSearch` 추가, route/hook의 direct networking을 services로 이동, 누락된 `pendingComponent` 추가, 누락된 route folders 추가, 명시적인 router plugin/config wiring 복원.
- 광범위하거나 breaking 가능성이 있는 migration은 명확한 근거 없이 auto-apply하지 않습니다.
- 예시: 대량 route/file rename, 전면적인 route tree restructuring, SPA-only app에 SSR/manual rendering 도입, 큰 auth/api-client rewrite.

---

## Services Layer (API)

```
services/<domain>/
├── schemas.ts      # Zod schemas
├── queries.ts      # GET requests + queryOptions
└── mutations.ts    # POST/PUT/DELETE
```

---

## External Services Layer (Third-party SDKs)

```
services/<provider>/
├── client.ts       # SDK client initialization
├── types.ts        # Type definitions
└── utils.ts        # Helper functions
```

---

## State Management

| State Type | Tool | Usage |
|------------|------|-------|
| Server state | TanStack Query | API data, caching (80%) |
| Client state | Zustand | UI state, settings (20%) |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Bundler | Vite 8.x (Rolldown + Oxc; `build.rolldownOptions`, `oxc`) |
| Router | TanStack Router 1.170.x, `@tanstack/router-plugin` 1.168.x와 짝을 맞춤 |
| Data | TanStack Query 5.105.x (`queryClient.query`, `staleTime: 'static'`) |
| State | Zustand (latest) |
| Validation | Zod 4.6.x (`z.email()`, `z.url()`) |
| Zod Adapter | `@tanstack/zod-adapter`는 Zod 3 전용 (`zodValidator`, `fallback`) |
| UI | React 19.3+, Tailwind CSS 4.x |
| Auth | Client-side auth (Better Auth / Clerk / etc.) |
| Env | t3-env |
| Monitoring | Sentry |

---

## Context Management

```typescript
// 1. Root: context 정의
interface RouterContext {
  queryClient: QueryClient
  auth: AuthState
}
export const Route = createRootRouteWithContext<RouterContext>()({
  component: RootComponent,
})

// 2. route.tsx에서 확장
beforeLoad: async ({ context }) => {
  if (!context.auth.isAuthenticated) {
    throw redirect({ to: '/login' })
  }
}

// 3. component에서 사용
const { queryClient } = useRouteContext({ from: '__root__' })

// 4. Search params validation (Zod 4는 스키마를 직접 넘김)
export const Route = createFileRoute('/dashboard/')({
  validateSearch: dashboardSearchSchema,
  component: DashboardPage,
})

// Zod 3만: validateSearch: zodValidator(dashboardSearchSchema)
// @tanstack/zod-adapter를 쓰며, 이 패키지의 peer dependency는 zod ^3.23.8입니다.
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

apiClient.interceptors.request.use((config) => {
  const token = getAuthToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})
```
