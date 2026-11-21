# Route Structure

> route 조직, file-route lifecycle, search validation, hypercore page folder convention.

## Rule Classifications

| Rule | Classification | Enforcement |
|---|---|---|
| file route instance를 `Route`로 export | Official | 없으면 차단 |
| search params를 사용할 때 validation | Official + Safety policy | 사용자 입력이 동작에 영향 주면 차단 |
| Zod 버전에 맞는 validation 경로 선택 | Official | Zod 4와 `@tanstack/zod-adapter` 동시 사용 차단 |
| `beforeLoad`가 `loader`보다 먼저 실행되는 lifecycle | Official | auth/context/redirect에 사용 |
| Router는 flat/directory 혼용 지원 | Official | flat route를 TanStack invalid라고 말하지 않음 |
| 앱 페이지 route-directory 선호 | Hypercore convention | official default 요청이 없으면 touched page에 적용 |
| interactive logic 또는 커지는 UI가 있는 페이지의 `-hooks/`, `-components/` | Hypercore convention | route-local orchestration 또는 UI extraction이 있으면 적용 |
| route-local server function exception용 `-functions/` | Hypercore convention + Safety policy | 기본은 domain module; route-only action만 local 유지 |

## Publishing-Only Exception

Publishing-only page는 interactive logic과 server integration이 없는 static display page입니다.
예: terms, privacy, about, 단순 marketing content.

- `-components/`, `-hooks/`, `-functions/`가 필요 없습니다.
- interactive logic을 추가하면 필요에 따라 `-hooks/`와 route-local component를 만듭니다.
- server integration을 추가할 때도 기본은 `src/modules/<domain>/<feature>/`의 server function을 route-local hook에서 호출하는 것입니다. 진짜 단일 route 전용 action만 `-functions/`에 둡니다.

## Hypercore Route Folder Shape

Global Start project structure, actual route-root discovery, generated `routeTree.gen.ts`, shared nested folder policy는 `rules/tanstack-start/project-structure.ko.md`를 읽습니다.

```text
routes/<page>/
├── index.tsx          # page UI
├── route.tsx          # layout/beforeLoad/loader when needed
├── -components/       # route-local UI
├── -hooks/            # route-local state/query orchestration
└── -sections/         # large page sections when needed
```

Route-local server function exception:

```text
routes/<page>/
└── -functions/
    ├── <resource>.functions.ts
    ├── <resource>.server.ts
    └── <resource>.schemas.ts
```

공식 TanStack Router는 flat route file도 지원합니다. 위 구조들은 hypercore maintainability convention입니다. `-components/`, `-hooks/`, `-functions/` 같은 `-` prefix folder는 Router의 default ignore-prefix와 맞아 route file generation에 포함되지 않는 co-location folder로 사용합니다.

## File Route Export

```typescript
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/users/')({
  component: UsersPage,
})
```

- route instance는 `Route`로 export해야 합니다.
- `createFileRoute` path string은 router plugin 또는 CLI가 생성/갱신합니다.

## Route Tokens and Code Splitting

- `routeToken`(기본값 `route`)은 layout route file을, `indexToken`(기본값 `index`)은 index route file을 식별합니다 (Official).
- 두 token 모두 regex를 받습니다. `tsr.config.json`에서는 `{ "regex": "...", "flags": "..." }` 형태이고 inline config에서는 native `RegExp`를 씁니다. regex는 route path의 마지막 segment 전체에 대해 매칭됩니다 (Official).
- segment를 대괄호로 감싸면 token으로 해석되지 않고 literal로 남습니다. `indexToken: { "regex": "[a-z]+-page" }`일 때 literal `home-page` segment는 `[home-page].tsx`로 이름 짓습니다 (Official).
- `autoCodeSplitting`은 TanStack Router bundler plugin option입니다. opt-in이고 기본값은 `false`입니다(다음 major release에서는 기본값이 `true`가 됩니다) (Official).
- `tanstackStart()`로는 전달할 수 없습니다. Start plugin이 받는 router config에서 `autoCodeSplitting`과 `target`을 제외하기 때문입니다 (Official).

## Route Lifecycle

| Step | Official behavior | Use for |
|---|---|---|
| `validateSearch` | matching/search validation 중 실행 | URL search state 파싱/검증 |
| `beforeLoad` | route loading 전 serial 실행 | Auth, redirects, context extension |
| `loader` | route loading phase에서 실행, cache/preload 가능 | Data loading; server-only로 취급 금지 |
| `pendingComponent` | threshold 기반 optional pending UI | 느린 critical loader UX |
| `errorComponent` | route lifecycle/render error 처리 | Recoverable route errors |

## Search Transform

현재 검색 변환 API는 route option의 `search.middlewares`입니다. 이 route와 하위 route의 새 link를 만들 때 search params를 변환하는 함수들입니다 (Official).

```typescript
import { createFileRoute, retainSearchParams } from '@tanstack/react-router'

export const Route = createFileRoute('/')({
  search: {
    middlewares: [retainSearchParams(['rootValue'])],
  },
})
```

- Router는 흔한 두 경우를 위해 `retainSearchParams`(하위 link에 부모 params 유지)와 `stripSearchParams`(기본값을 가진 params 제거)를 제공합니다 (Official).
- `preSearchFilters` / `postSearchFilters`는 폐기 예정이고 현재 search-params guide에는 없습니다. API reference에는 아직 `⚠️ deprecated, use search.middlewares instead`로 남아 있습니다 (Official). 삭제된 것이 아니라 폐기 예정으로 취급합니다.

## Search Validation

search params를 사용하면 검증합니다.

`validateSearch`는 planning callback입니다. 같은 입력에 대해 결정적이고 부수효과가 없어야 하며, 그 안에서 navigate하거나 application/router state를 변경하지 않습니다 (Official).

Zod v4 official path:

```typescript
import { z } from 'zod'

const searchSchema = z.object({ page: z.number().default(1) })

export const Route = createFileRoute('/products/')({
  validateSearch: searchSchema,
  component: ProductsPage,
})
```

Zod v3 official path:

```typescript
import { zodValidator, fallback } from '@tanstack/zod-adapter'
import { z } from 'zod'

const searchSchema = z.object({ page: fallback(z.number(), 1).default(1) })

export const Route = createFileRoute('/products/')({
  validateSearch: zodValidator(searchSchema),
  component: ProductsPage,
})
```

`@tanstack/zod-adapter`는 Zod v3 전용입니다. `peerDependencies`가 `zod: ^3.23.8`을 고정하고 있어 Zod 4와 충돌합니다. Zod 4 프로젝트에서는 import 방식을 통일하려는 목적이더라도 adapter를 설치하지 않고 schema를 직접 전달합니다. Zod 3에서는 adapter가 여전히 공식 경로입니다. 프로젝트가 `zodValidator`로 표준화하는 경우에도 Zod 3에 머무는 동안만 성립하며 project note에 hypercore convention으로 표시해야 합니다.

## Loader Boundary Rule

- TanStack Start loader는 isomorphic입니다.
- loader code에서 secret, database client, filesystem, privileged SDK에 직접 접근하지 않습니다.
- privileged work는 route-local exception인 `-functions/<resource>.functions.ts` 또는 기본 shared 위치인 `src/modules/<domain>/<feature>/<resource>.functions.ts`의 `createServerFn` 뒤로 옮깁니다.
- `*.functions.ts` handler 내부에서만 `*.server.ts` helper를 import하고, route/component/hook은 server function wrapper를 static import합니다.

## Validation Checklist

- [ ] touched file route가 `Route`를 export함.
- [ ] search params가 설치된 Zod version에 맞게 검증됨.
- [ ] auth/context/redirect는 필요한 경우 `beforeLoad`에 있음.
- [ ] loader code에 direct secret/DB/filesystem access가 없음.
- [ ] publishing-only page에 빈 route-local folder를 강제하지 않음.
- [ ] interactive logic이 있는 page는 route-local hooks/components를 갖거나 이유가 기록됨.
- [ ] route-local server functions가 `.functions.ts` / `.server.ts` / schema split을 따르거나 `src/modules/<domain>/<feature>/`로 승격됨.

## Sources

> 출처 확인 2026-11-04: <https://tanstack.com/router/latest/docs/guide/search-params.md>(Zod v4 direct schema, `search.middlewares`), <https://tanstack.com/router/latest/docs/how-to/validate-search-params.md>(Zod v4에서 adapter 불필요), <https://registry.npmjs.org/@tanstack/zod-adapter/latest>(Zod v3 peer 범위). 그 밖의 공식 TanStack 동작은 이 패키지 자체의 snapshot(`references/official/tanstack-start/tanstack-start-2026-11-04.md`, `references/official/tanstack-start/tanstack-router-2026-11-04.md`, `references/official/tanstack-start/current-docs-2026-11-04.md`)에 위임합니다. 공식 사실 검증 2026-11-04. 저장소 로컬 링크 확인 2026-11-04.
