# Router와 Query 경계

> 패키징된 Tauri v2 프런트엔드에서 TanStack Router 파일 기반 라우팅과 TanStack Query를 도입하거나 검토할 때 이 규칙을 적용한다. 이 아키텍처는 브라우저 전용 Vite SPA다. API 사실은 날짜가 기록된 TanStack 참고 문서를 읽고, 이 문서는 아키텍처 결정을 정의한다.

## 실행 모델

Vite는 React SPA를 정적 자산으로 빌드하고, Tauri는 그 자산을 WebView에 패키징하고 로드한다. TanStack Router는 브라우저 탐색과 파일 기반 route 생성을 소유한다. 개발과 production build에서 route file로부터 `routeTree.gen.ts`를 생성하도록 React plugin보다 먼저 `@tanstack/router-plugin/vite`를 설정한다. TanStack Query는 비동기 데이터 cache와 freshness를 소유하며 파일 라우팅 시스템을 제공하지 않는다.
```ts
// vite.config.ts
import { tanstackRouter } from '@tanstack/router-plugin/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [tanstackRouter(), react()],
})
```

TanStack Start는 이 skill의 범위 밖이다. server function, server route, middleware, SSR을 포함한 요청은 이 패키징된 Vite SPA에 추가하지 말고 반드시 full-stack architecture workflow로 라우팅한다.

네이티브 기능은 검토된 desktop API/IPC 경계를 통과하고, 원격 서비스는 일반 브라우저 HTTP API를 사용한다. Tauri Rust command가 네이티브 authority를 유지한다. Vite module, route, WebView state를 네이티브 trust boundary로 취급하지 않는다.

## Router context는 composition root다

WebView runtime을 위해 module이 소유하는 `QueryClient` 하나와 module이 소유하는 router 하나를 만든다. route, component, loader, query factory, render function에서 만들지 않는다. Router context는 type이 지정되고, shared client와 raw Tauri bridge가 아닌 의도적으로 좁힌 desktop API를 담는다.

```ts
// src/router.tsx
import { QueryClient } from '@tanstack/react-query'
import { createRouter } from '@tanstack/react-router'
import { routeTree } from './routeTree.gen'
import { createDesktopApi } from './platform/desktop-api'

export interface RouterContext {
  queryClient: QueryClient
  desktop: ReturnType<typeof createDesktopApi>
}

export const queryClient = new QueryClient()
const desktop = createDesktopApi()

export const router = createRouter({
  routeTree,
  context: { queryClient, desktop },
  defaultPreloadStaleTime: 0,
})

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

```

```tsx
// src/main.tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider } from '@tanstack/react-router'
import { queryClient, router } from './router'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>,
)
```

Root route는 `createRootRouteWithContext<RouterContext>()`로 같은 type을 선언해야 한다. `createDesktopApi()`는 IPC command 선택, argument/result validation, 정규화된 client error를 소유한다. Tauri runtime authority, capability, scope, domain authorization은 Rust-side control로 유지한다. Route file은 feature에 필요한 최소 method만 사용한다. `invoke`, `window.__TAURI__`, 제한 없는 plugin object, ambient process state를 context에 전달하지 않는다.

`src/main.tsx`는 동일한 module-owned `QueryClient`와 router를 `QueryClientProvider` 및 `RouterProvider`에 제공해야 합니다. 두 번째 client는 loader-prefetch 재사용, invalidation, test 가정을 조용히 깨뜨립니다.

## Query만 freshness를 소유한다

Query factory는 각 원격 또는 네이티브 기반 resource의 key, fetcher, cache policy를 소유한다. Loader와 component가 정확히 같은 정의를 사용하도록 `queryOptions`를 쓴다.

```ts
// src/modules/preferences/queries/preferences.queries.ts
import { queryOptions } from '@tanstack/react-query'

export const preferencesOptions = (desktop: DesktopApi) =>
  queryOptions({
    queryKey: ['preferences'],
    queryFn: () => desktop.readPreferences(),
    staleTime: 30_000,
  })
```

```ts
// src/routes/preferences.tsx
export const Route = createFileRoute('/preferences')({
  loader: ({ context }) =>
    context.queryClient.ensureQueryData(preferencesOptions(context.desktop)),
  component: PreferencesPage,
})

function PreferencesPage() {
  const { desktop } = Route.useRouteContext()
  const { data } = useSuspenseQuery(preferencesOptions(desktop))
  return <PreferencesForm preferences={data} />
}
```

규칙:

- `loader`는 반드시 `ensureQueryData`로 cache를 예열하고, component는 같은 factory를 `useSuspenseQuery`로 읽는다(UX가 의도적으로 suspend하지 않을 때는 `useQuery`).
- freshness, retry, garbage collection, refetching, persistence policy는 Query option에 둔다. route 수준 timer, component effect, local mirror, 0이 아닌 Router preload cache로 중복하지 않는다.
- `defaultPreloadStaleTime: 0`을 router에 설정하여 Router가 preload 작업을 항상 다시 실행하고, data freshness 결정은 Query만 하게 한다.
- Query key에는 결과를 바꾸는 모든 입력을 포함한다. 그런 입력을 query function에 보이지 않게 capture하지 않는다.
- `validateSearch`는 route search input을 검증해야 한다. `loaderDeps`에는 loader 출력을 바꾸는 모든 검증된 search dependency를 넣어야 한다. 같은 dependency를 query factory/key에서 사용한다. route parameter dependency는 이미 route match가 식별한다.

아래 예시는 Zod v4를 전제하므로 schema를 `validateSearch`에 직접 넘깁니다. Zod v3 프로젝트는 `@tanstack/zod-adapter`의 `zodValidator`로 감싸야 하며, Zod v3에서 직접 형식을 쓰지 않고 한 route tree에 두 관례를 함께 두지 않습니다.

```ts
import { z } from 'zod'

const documentSearchSchema = z.object({
  revision: z.coerce.number().int().nonnegative().catch(0),
})

export const Route = createFileRoute('/documents/$documentId')({
  validateSearch: documentSearchSchema,
  loaderDeps: ({ search }) => ({ revision: search.revision }),
  loader: ({ context, params, deps }) =>
    context.queryClient.ensureQueryData(
      documentOptions(context.desktop, params.documentId, deps.revision),
    ),
  component: DocumentPage,
})
```

쓰기는 좁은 desktop API를 호출하는 mutation을 사용한다. 성공 시 같은 context `QueryClient`로 정확히 영향받은 query key만 invalidate하거나 갱신한다. 창을 다시 로드하거나 두 번째 source of truth를 만들지 않는다.

```ts
const mutation = useMutation({
  mutationFn: (input: PreferencesInput) => desktop.writePreferences(input),
  onSuccess: () => queryClient.invalidateQueries({ queryKey: ['preferences'] }),
})
```

## Route 상태와 guard

의미 있는 모든 route 계층은 pending, 실패, 없는 resource의 동작을 의도적으로 정해야 한다.

- loader에 묶인 navigation에는 `pendingComponent`(그리고 검토한 `pendingMs`)를 사용한다. 빈 화면을 남기지 않는다.
- 복구 가능한 route/query 실패에는 `errorComponent`를 사용한다. 안전한 retry path를 제공하고 native path, command 내부, token, raw Rust error를 노출하지 않는다.
- `notFoundComponent`를 사용하고, 없는 route resource에는 Router의 not-found 결과를 throw 또는 return 한다. 비어 있는 success payload는 없는 resource의 대체물이 아니다.
- 공통 state UI는 그것을 소유할 수 있는 가장 가까운 layout route에 두고, 사용자가 별도 recovery를 필요로 할 때만 특수화한다.

`beforeLoad`와 redirect는 탐색 흐름, 예를 들어 잠금 해제된 local workspace 또는 이미 선택된 profile을 guard할 수 있다. 그러나 **authorization이 아니다**. 사용자는 의도한 route 밖에서 IPC를 호출하거나, client state를 변경하거나, 오래된 route를 복원할 수 있다. 모든 privileged Tauri command와 remote service는 각자 input을 검증하고 동작을 authorize해야 한다.

## 검토 게이트

다음 조건 중 하나라도 있으면 제안한 구현을 거절하거나 수정한다.

1. 파일 기반 route가 `@tanstack/router-plugin/vite`로 생성되지 않거나 Router plugin이 React plugin 뒤에 배치된다.
2. `QueryClient` 또는 router가 둘 이상이거나, provider wiring이 다른 client/router를 사용하거나, route에서 raw Tauri bridge에 접근하거나, freshness logic이 중복된다.
3. Query loader/component 쌍이 다른 key 또는 fetcher를 쓰거나, loader가 출력을 바꾸는 검증된 search dependency를 빠뜨린다.
4. 의미 있는 route state의 pending, error, not-found 동작이 없다.
5. client-side guard를 native capability의 authorization control로 제시한다.

날짜가 기록된 API 근거는 [`../../references/official/tauri/tanstack-vite-react-2026-11-04.ko.md`](../../references/official/tauri/tanstack-vite-react-2026-11-04.ko.md)를, command-boundary 요구 사항은 [`tauri-ipc.ko.md`](tauri-ipc.ko.md)와 [`security.ko.md`](security.ko.md)를 읽는다.

## Sources

> 링크 확인 2026-11-04.

| 주장 | 출처 |
|---|---|
| Router plugin 순서와 file-route 생성, typed router context, `defaultPreloadStaleTime`, `validateSearch`/`loaderDeps`, pending/error/not-found component | [tanstack-vite-react-2026-11-04.ko.md](../../references/official/tauri/tanstack-vite-react-2026-11-04.ko.md); <https://tanstack.com/router/v1/docs/framework/react/guide/data-loading>; <https://tanstack.com/router/v1/docs/framework/react/guide/not-found-errors> |
| Zod v4가 schema를 `validateSearch`에 직접 넘기고 Zod v3는 `zodValidator`가 필요하다는 사실 | <https://tanstack.com/router/latest/docs/framework/react/guide/search-params> |
| `queryOptions`, `ensureQueryData`, `useSuspenseQuery`, query key 입력, staleness, invalidation 동작 | [tanstack-vite-react-2026-11-04.ko.md](../../references/official/tauri/tanstack-vite-react-2026-11-04.ko.md); <https://tanstack.com/query/v5/docs/reference/QueryClient>; <https://tanstack.com/query/latest/docs/framework/react/guides/query-keys> |
| 패키징된 정적 asset 경계와 native 작업의 Rust 측 권한 | [tauri-v2-2026-11-04.ko.md](../../references/official/tauri/tauri-v2-2026-11-04.ko.md); <https://v2.tauri.app/security/> |
| Route/page/module 소유권, 좁은 desktop adapter, client guard는 authorization이 아니라는 규칙 | 이 저장소의 규약과 안전 정책; 외부 출처 없음 |
