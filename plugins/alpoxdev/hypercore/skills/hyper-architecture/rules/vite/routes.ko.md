# 라우트 구조

> Vite + TanStack Router 파일 기반 라우팅

참고: TanStack Router는 flat file route와 folder route를 모두 지원합니다. 하지만 hypercore는 `-components/`나 `-hooks/`를 가진 페이지에서는 폴더형 route를 기본으로 사용합니다. 그래야 UI, 로직, 하위 페이지 자산을 한곳에 묶어 둘 수 있습니다.

---

## 라우트 폴더 구조

```
routes/
├── __root.tsx           # 루트 레이아웃
├── index.tsx            # / (홈)
├── users/
│   ├── route.tsx        # shared layout / beforeLoad / loader
│   ├── index.tsx        # /users (목록)
│   ├── -components/     # 페이지 전용 컴포넌트 (필수)
│   ├── -hooks/          # 페이지 전용 훅 (필수)
│   ├── $id/
│   │   ├── index.tsx    # /users/:id (상세)
│   │   ├── -components/ # 필수
│   │   └── -hooks/      # 필수
│   └── -sections/       # 섹션 분리 (선택, 복잡한 페이지만)
└── posts/
    ├── index.tsx
    ├── -components/     # 필수
    ├── -hooks/          # 필수
    └── $slug/
        ├── index.tsx
        ├── -components/
        └── -hooks/
```

| 접두사 | 용도 | 라우트 생성 |
|--------|---------|-----------------|
| `-` | 라우트 제외 폴더 | 제외됨 |
| `$` | 동적 파라미터 | 생성됨 |
| `_` | Pathless 레이아웃 | 생성됨 (경로 없음) |
| `(group)/` | Route group (괄호) | URL에는 영향 없음, 파일 정리용 |

**필수 규칙:**
- 모든 페이지는 `-components/`, `-hooks/` 폴더가 있어야 함
- `-functions/` 폴더 없음 (Vite에는 서버 함수 없음)
- 커스텀 훅은 **페이지 크기와 무관하게** 반드시 `-hooks/` 폴더로 분리
- `-sections/`는 선택사항, 복잡한 페이지(200줄 이상)만
- shared layout, `beforeLoad`, shared loader가 있으면 `route.tsx` 사용
- 저장소가 `routeToken`을 커스텀했다면 `tsr.config.json`에 그 규칙을 명시해 둠

---

## 라우트 파일명 규칙

| 경로 | 파일명 | 설명 |
|------|----------|-------------|
| `/` | `index.tsx` | 인덱스 라우트 |
| `/users` | `users/index.tsx` | 목록 페이지 |
| `/users/:id` | `users/$id/index.tsx` | 동적 파라미터 |
| `/dashboard/*` | `dashboard/$.tsx` | 캐치올 라우트 |
| 레이아웃 | `__root.tsx` | 루트 레이아웃 |
| 폴더 레이아웃 | `users/route.tsx` | `/users` 하위 공용 레이아웃 |
| Pathless | `_layout.tsx` | Pathless 레이아웃 |

---

## 기본 라우트 패턴

```tsx
// routes/users/index.tsx
import { createFileRoute } from '@tanstack/react-router'
import { UserListSection } from './-sections/user-list-section'

export const Route = createFileRoute('/users/')({
  component: UsersPage,
})

const UsersPage = (): JSX.Element => {
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Users</h1>
      <UserListSection />
    </div>
  )
}
```

## 로더 패턴 (클라이언트에서 도달 가능한 프리페치)

> route loader는 클라이언트에서 도달 가능한 코드로 취급합니다. SPA-only Vite 앱에서는 보통 브라우저 탐색 중 실행되지만, 저장소가 나중에 SSR/manual rendering을 추가하면 같은 loader가 서버 렌더에도 참여할 수 있습니다. 어떤 경우든 공개 가능한 로직만 loader에 둡니다.

최신 TanStack Router 문서의 조합은 loader의 `queryClient.query({ ...queryOptions, staleTime: 'static' })`와 컴포넌트의 `useSuspenseQuery`입니다. `query()`는 캐시 데이터가 아직 신선하면 그대로 반환하고 아니면 가져오며, `staleTime: 'static'`은 loader가 채운 캐시 항목을 절대 stale이 되지 않게 표시합니다. `useSuspenseQuery`가 그 캐시를 읽고 업데이트를 구독하므로 로딩 깜빡임이 없습니다.

`ensureQueryData`, `fetchQuery`, `prefetchQuery`는 TanStack Query 5.102+에서 deprecated이며 다음 메이저에서 제거됩니다.

```tsx
// routes/users/$id/index.tsx
import { createFileRoute } from '@tanstack/react-router'
import { useSuspenseQuery } from '@tanstack/react-query'
import { userQueryOptions } from '@/services/user/queries'

export const Route = createFileRoute('/users/$id')({
  loader: ({ params: { id }, context: { queryClient } }) =>
    queryClient.query({ ...userQueryOptions(id), staleTime: 'static' }),
  component: UserDetailPage,
})

const UserDetailPage = (): JSX.Element => {
  const { id } = Route.useParams()
  const { data: user } = useSuspenseQuery(userQueryOptions(id))
  return (
    <div>
      <h1>{user.name}</h1>
      <p>{user.email}</p>
    </div>
  )
}
```

`useQuery`는 옆에서 함께 가져오는 비-크리티컬 데이터(예: analytics 위젯)처럼 로딩 스켈레톤이 허용되는 경우에만 사용합니다.

## 지연 데이터 로딩

```tsx
import { createFileRoute, Await } from '@tanstack/react-router'
import { Suspense } from 'react'

export const Route = createFileRoute('/dashboard/')({
  loader: async ({ context: { queryClient } }) => {
    const slowDataPromise = queryClient.query(slowQueryOptions())
    const fastData = await queryClient.query({ ...fastQueryOptions(), staleTime: 'static' })
    return { fastData, deferredSlowData: slowDataPromise }
  },
  component: DashboardPage,
})

const DashboardPage = (): JSX.Element => {
  const { fastData, deferredSlowData } = Route.useLoaderData()
  return (
    <div>
      <div>{JSON.stringify(fastData)}</div>
      <Suspense fallback={<div>Loading...</div>}>
        <Await promise={deferredSlowData}>
          {(data) => <div>{JSON.stringify(data)}</div>}
        </Await>
      </Suspense>
    </div>
  )
}
```

---

## 검색 파라미터 검증

> 타입 안전한 검색 파라미터. Zod 4는 스키마를 `validateSearch`에 그대로 넘기고, `@tanstack/zod-adapter`는 Zod 3용 도구입니다.

```tsx
import { createFileRoute } from '@tanstack/react-router'
import { z } from 'zod'

const searchSchema = z.object({
  page: z.number().int().positive().catch(1),
  filter: z.string().optional(),
  sortBy: z.enum(['newest', 'oldest', 'price']).default('newest'),
})

export const Route = createFileRoute('/products/')({
  validateSearch: searchSchema,
  // 검증된 search params를 loader cache key로 연결
  loaderDeps: ({ search: { page, sortBy, filter } }) => ({ page, sortBy, filter }),
  loader: ({ deps, context: { queryClient } }) =>
    queryClient.query({ ...productsQueryOptions(deps), staleTime: 'static' }),
  component: ProductsPage,
})
```

| API | 출처 | 용도 |
|-----|--------|---------|
| `validateSearch: schema` | `@tanstack/react-router` + Zod 4 | 검색 파라미터 스키마 검증 (Zod 4 직접) |
| `zodValidator` | `@tanstack/zod-adapter` | 검색 파라미터 스키마 검증 (Zod v3 전용) |
| `fallback` | `@tanstack/zod-adapter` | Zod v3에서 잘못된 파라미터 기본값 (raw `.catch()`와 달리 타입 보존) |
| `loaderDeps` | route option | 검증된 search params를 loader cache key로 연결 |
| `Route.useSearch()` | `@tanstack/react-router` | 검증된 검색 파라미터 접근 |
| `Route.useNavigate()` | `@tanstack/react-router` | 검색 파라미터 업데이트로 탐색 |

> Zod 4에서는 스키마를 `validateSearch`에 직접 넘기고 `@tanstack/zod-adapter`를 쓰지 않습니다. 어댑터의 현재 peer dependency는 `zod: ^3.23.8`입니다. Zod 4의 `.catch()`는 타입 추론을 유지하므로, `fallback(...)`은 `zodValidator`와 함께 쓸 때 `.catch()`가 추론 타입을 `unknown`으로 떨어뜨리는 Zod 3의 보완책으로 남습니다.
>
> `search.strict: true`(라우터 옵션, 기본 `false`)는 `validateSearch`가 반환하지 않는 search param을 버려 엉뚱한 URL 파라미터가 앱 상태로 들어오지 않게 합니다.

### Route Group (괄호)

`(groupName)/` 안에 파일을 두면 URL에는 영향이 없고 파일만 묶을 수 있습니다. hypercore에서는 list 페이지를 `(main)/` 안에, create/edit 페이지를 그 바깥에 두어 URL을 공유하지 않게 정리합니다.

```text
routes/
├── (main)/
│   ├── users/
│   │   ├── route.tsx          # /users 레이아웃
│   │   └── index.tsx          # /users
│   └── posts/
│       └── index.tsx          # /posts
└── users/
    └── new/
        └── index.tsx          # /users/new (group 바깥)
```

---

## 라우트 옵션: 로딩 & 에러 상태

```tsx
export const Route = createFileRoute('/posts/')({
  loader: ({ context: { queryClient } }) =>
    queryClient.query({ ...postsQueryOptions(), staleTime: 'static' }),
  pendingComponent: () => <div>Loading posts...</div>,
  errorComponent: ({ error }) => (
    <div>
      <h2>에러</h2>
      <p>{error.message}</p>
    </div>
  ),
  component: PostsPage,
})
```

| 라우트 옵션 | 용도 | 필수 여부 |
|--------------|---------|----------|
| `pendingComponent` | 로더 실행 중 로딩 UI | 권장 |
| `errorComponent` | 로더/컴포넌트 실패 시 에러 UI | 필수 |
| `notFoundComponent` | 404 UI (루트 라우트) | `__root.tsx`에 필수 |
| `validateSearch` | 검색 파라미터 검증 | 검색 파라미터 사용 시 |

---

## 인증 가드 패턴 (beforeLoad)

```tsx
// routes/dashboard/route.tsx
import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/dashboard')({
  beforeLoad: ({ context, location }) => {
    if (!context.auth.isAuthenticated) {
      throw redirect({ to: '/login', search: { redirect: location.href } })
    }
  },
})
```

---

## 로더 실행 순서

| 단계 | 실행 | 설명 |
|------|-----------|-------------|
| 0. `validateSearch` | 탐색 전 | 검색 파라미터 검증 |
| 1. `beforeLoad` | 순차 (바깥 -> 안) | 인증 확인, 리다이렉트 |
| 2. `loader` | 병렬 (모든 로더 동시) | 쿼리 프리페치 |

---

## 라우터 로더 캐시와 Query 캐시

TanStack Router는 자체 loader 캐시를 두므로 loader는 단순한 프리페치 지점이 아닙니다. 현재 문서화된 기본값입니다.

| 설정 | 범위 | 기본값 |
|---------|-------|---------|
| `staleTime` | route option | `0`. 재사용되는 loader 데이터가 즉시 stale이 되어 백그라운드에서 재검증 |
| `defaultStaleTime` | router option | 미설정. 라우트 기본값을 한곳에서 지정 |
| preload 신선도 | router 캐시 | preload가 만든 loader 데이터는 30초 동안 신선 |
| `gcTime` / `preloadGcTime` | route / router | 각각 5분 |
| `staleReloadMode` / `defaultStaleReloadMode` | route / router | `'background'` |
| `shouldReload` | route option | 미설정. `false` 또는 탐색마다 판단하는 함수를 받음 |

- TanStack Query가 캐시를 소유하면 라우터에 `defaultPreloadStaleTime: 0`을 두어 라우터가 preload 데이터를 신선하게 붙들지 않고 Query가 fetch 여부를 정하게 합니다.
- 라우트가 한 번만 로드되어야 할 때만 `staleTime: Infinity`를 씁니다. 이 값은 stale이 되는 것을 막고, 재로드를 기다리는 `staleReloadMode: 'blocking'`과 다릅니다.
- `staleReloadMode` 같은 loader별 동작은 객체형 `loader: { handler, staleReloadMode: 'blocking' }`으로 설정합니다.

---

## 폴더 구조 규칙

| 페이지 크기 | 필수 | 선택 |
|-----------|----------|----------|
| ~100줄 | shared layout/loader가 있으면 `route.tsx`, 그리고 `-components/`, `-hooks/` | - |
| 100-200줄 | `-components/`, `-hooks/` | - |
| 200줄+ | `-components/`, `-hooks/` | `-sections/` |

---

## Sources

> `references/official/vite/current-docs-2026-11-04.ko.md`에 기록된 dated snapshot은 file-based routing, route tree 생성, `validateSearch`와 Zod 4 직접 스키마 방식을 사용한 search param validation, 라우터 loader 캐시 기본값, deprecated된 `<ScrollRestoration />` 컴포넌트, route loader가 client-reachable하다는 점을 기록하고 있고(그 스냅샷이 기록한 자체 검증일은 2026-11-04), 이 파일은 그 항목들을 그대로 서술합니다. 이 파일의 route 구조·route 파일 이름·route option·loader 실행 순서 서술은 이 패키지 자체의 guidance이며 외부 출처를 사용하지 않았습니다. folder route 선호, `-components/`/`-hooks/`/`-sections/` 요구사항, 페이지 크기 기준은 Hypercore/repo-local convention입니다. 이 파일을 위해 페이지를 다시 가져오지 않았습니다. 규칙 문장과 저장소 로컬 경로 확인 2026-11-04.
