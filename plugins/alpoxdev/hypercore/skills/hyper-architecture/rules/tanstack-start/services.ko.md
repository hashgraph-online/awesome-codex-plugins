# Server Functions and Domain Modules

> Server function API 사용, runtime validation, route/modules/lib/database layering 규칙.

## Rule Classifications

| Rule | Classification | Enforcement |
|---|---|---|
| client-callable server RPC는 `createServerFn` 사용 | Official | server RPC에 필요 |
| validation API는 `.validator(...)` 하나 | Official | `.inputValidator(...)` 차단. 1.169.0에서 제거됨 |
| mutation input runtime validation | Safety policy | POST/PUT/PATCH validation 없으면 차단 |
| chain에서 handler는 마지막 | Official/API shape | malformed chain 차단 |
| non-trivial logic은 domain module/lib layer | Hypercore convention | touched non-trivial logic에 적용 |
| server function wrapper와 server-only helper 분리 | Official + Safety policy | `.functions.ts`와 `.server.ts` 역할 분리 |
| `functions/index.ts` barrel 금지 | Hypercore convention + Safety policy | import-protection/tree-shaking ambiguity 방지 |
| server functions는 same-origin app RPC | Official + Safety policy | public/cross-origin HTTP endpoint는 server route 사용 |

`.validator()` 규칙과 1.169.0에서 `.inputValidator()`가 제거된 경위는 `references/official/tanstack-start/tanstack-start-2026-11-04.md`를 봅니다.

## Canonical Server Function Pattern

```typescript
import { createServerFn } from '@tanstack/react-start'
import { z } from 'zod'

const createUserSchema = z.object({
  email: z.email(),
  name: z.string().min(1),
})

export const createUser = createServerFn({ method: 'POST' })
  .validator(createUserSchema)
  .middleware([authMiddleware])
  .handler(async ({ data, context }) => {
    return createUserMutation({ data, user: context.user })
  })
```

Notes:

- `.validator(...)`가 유일한 표기입니다. `.inputValidator(...)`는 1.169.0에서 `createServerFn`과 `createMiddleware`에서 제거됐습니다. 더 이상 해석되지 않으므로 남아 있는 호출은 legacy 부채가 아니라 깨진 코드이고 마이그레이션 대상입니다. (Official)
- `.validator(...)`는 Zod schema를 직접 받을 수 있고, builder는 validator를 하나만 가집니다(나중 `.validator(...)` 호출이 앞선 설정을 대체). `.middleware([...])`는 반복 가능하며 이전 middleware와 병합됩니다. (Official)
- `Method`는 정확히 `'GET' | 'POST'`이며 다른 verb는 없습니다. (Official)
- `strict` 옵션이 있고 기본값은 `strict: true`입니다. TypeScript 수준 serialization 검사만 다루며, `strict: false`는 타입 검사만 완화하고 runtime serialization layer는 값을 그대로 처리해야 합니다. (Official)
- middleware와 input validation 순서는 바뀔 수 있지만 `handler`는 chain 마지막입니다. (Official/API shape)
- project-local installed version이 다르면 typecheck로 확인하고 예외를 기록합니다.
- Server function은 app same-origin RPC입니다. public API, webhook, cross-origin endpoint, raw HTTP semantics가 필요하면 `rules/tanstack-start/server-routes.ko.md`에 따라 server route를 사용합니다.

## Server Function File Organization

TanStack Start 공식 guidance는 `*.functions.ts`(server function wrapper) / `*.server.ts`(server-only helper) 분리를 "one approach"로 소개하며 강제하지 않습니다 (Official). Hypercore는 이 패턴을 route-local `-functions/` exception과 shared `src/modules/<domain>/<feature>/` nested folder에 적용합니다 (Hypercore convention).

Route-local exception 예시:

```text
src/routes/billing/
├── route.tsx
├── index.tsx
├── -hooks/
│   └── use-invoices.ts
└── -functions/
    ├── invoices.functions.ts
    ├── invoices.server.ts
    └── invoices.schemas.ts
```

Default domain module 예시:

```text
src/modules/billing/invoices/
├── invoices.functions.ts
├── invoices.server.ts
├── invoices.schemas.ts
├── invoices-query-keys.ts
├── hooks/
└── components/
```

역할:

| File | Import 가능 위치 | 허용 내용 |
|---|---|---|
| `*.functions.ts` | loader, component, hook, 다른 server function에서 static import | `createServerFn` wrapper, middleware/validator/handler chain |
| `*.server.ts` | `*.functions.ts` handler 내부 또는 server-only module | DB, secrets, filesystem, privileged SDK, internal business logic |
| `*.schemas.ts` / `schemas.ts` | client/server 모두 | Zod schemas, serializable DTOs, constants |
| `*-query-keys.ts` | client/server 모두 | TanStack Query key builders, cache tags |

규칙:

- `*.functions.ts`는 강제 경계가 아니라 명명 관례입니다. import protection이 강제하는 파일 패턴은 `*.server.*`와 `*.client.*`뿐입니다. (Official)
- server function은 dynamic import하지 않습니다. Client bundle rewrite와 import protection 추적을 위해 direct static import를 사용합니다.
- `*.functions.ts`는 server-only helper를 handler 밖 surviving export에서 참조하지 않습니다.
- safe exports와 `.server.ts` exports를 같은 `index.ts` barrel에서 re-export하지 않습니다.
- route-local `-functions/`가 cross-route reuse, domain noun, cache/auth/permission 책임을 얻으면 `src/modules/<domain>/<feature>/`로 승격합니다.
- shared domain code는 domain/feature 단위 nested folder를 사용합니다. `src/modules/foo.ts` direct leaf를 새로 만들지 않습니다.
- external provider client는 domain module에 섞지 않고 `src/integrations/<provider>/` 또는 server-only module로 분리합니다.

## Layering

```text
Route / hook / query
  -> routes/<page>/-functions/<resource>.functions.ts
     또는 src/modules/<domain>/<feature>/<resource>.functions.ts
  -> src/modules/<domain>/<feature>/<resource>.server.ts
  -> src/lib/<domain>/shared helpers, src/db/<domain>/repositories,
     또는 src/integrations/<provider>/server-only clients
  -> database/ORM client 또는 external SDK
```

- **Safety policy:** route는 database/ORM client를 직접 import하지 않습니다.
- **Safety policy:** `*.server.ts` 또는 DB/repository imports는 client-reachable file에 살아남지 않게 합니다.
- **Hypercore convention:** non-trivial business logic은 route file이 아니라 `modules/<domain>/<feature>/` 또는 domain-specific `lib/<domain>/` folders에 둡니다.
- **Hypercore convention:** extraction이 noise라면 simple CRUD는 server function에 남길 수 있습니다.

## Query and Mutation Pattern

- Reads: 안전하고 cache semantic이 맞으면 GET server function 사용.
- Mutations: POST/PUT/PATCH + runtime `.validator(...)`. (Safety policy)
- Client hook은 보통 `useServerFn`과 TanStack Query로 server function/cache invalidation을 감쌉니다.
- Loader는 React component가 아니므로 server function을 직접 호출할 수 있습니다.
- Auth-required server function은 route `beforeLoad`만 믿지 않습니다. Server function 자체에 middleware 또는 handler-level auth check를 둡니다.
- CSRF: `src/start.ts`가 없으면 Start가 server function용 `createCsrfMiddleware()`를 자동 설치합니다. `src/start.ts`를 만들면 이 자동 설치가 조용히 빠지므로, 그 파일에 `requestMiddleware: [createCsrfMiddleware()]`를 명시하고 server function으로 filter해야 합니다. (Official + Safety policy)

```ts
// src/start.ts
import { createStart, createCsrfMiddleware } from '@tanstack/react-start'

const csrfMiddleware = createCsrfMiddleware({
  filter: (ctx) => ctx.handlerType === 'serverFn',
})

export const startInstance = createStart(() => ({
  requestMiddleware: [csrfMiddleware],
}))
```

- `filter`는 선택적 장식이 아닙니다. 기본 `createCsrfMiddleware()`는 middleware가 처리하는 모든 request를 검증하므로, filter 없이 전역 설치하면 SSR page request와 server route까지 검사합니다. 공식 type에는 `filter`, `origin`, `secFetchSite`(기본 `'same-origin'`), `referer`(기본 `true`), `allowRequestsWithoutOriginCheck`(기본 `false`), `failureResponse`(기본 `403 Forbidden`)가 있습니다. 뒤 세 개는 guide가 문서화하지 않은 type 수준 사실입니다. (Official)
- User/session/tenant에 의존하는 GET server function은 public cache header를 쓰지 않습니다. `public`은 사용자와 origin 사이의 모든 CDN과 proxy에 그 응답을 누구에게나 줘도 된다고 알리는 값이라, 한 사용자의 인증 응답이 다음 사용자에게 재생됩니다. `private`로 두고 identity로 vary하거나 caching을 아예 피합니다. `Cache-Control: private, max-age=60`에 `Vary: Cookie, Authorization`을 붙이거나, 캐시되면 안 되는 응답에는 `no-store`를 씁니다. (Official)
- production에서 server function ID는 함수의 SHA256 hash이고, 중복되면 `_1`/`_2` 접미사가 붙습니다. `tanstackStart({ serverFns: { generateFunctionId } })`로 바꿀 수 있습니다(experimental). log나 cache key가 ID에 의존하면 내부 세부로 취급합니다. (Official)
- `createStart`의 `serverFns.fetch`는 test나 custom runtime에서 server function 호출의 fetch 구현을 정합니다. call site와 middleware가 이를 덮어쓸 수 있습니다. production routing 규칙이 아니라 test seam입니다.

## Validation Checklist

- [ ] 새 mutation server function에 `.validator(...)`가 있음.
- [ ] `.inputValidator(`가 어디에도 없음. 1.169.0에서 제거됐으므로 발견되면 깨진 코드입니다.
- [ ] `handler`가 chain 마지막임.
- [ ] auth-required server function이 middleware 또는 equivalent checked boundary를 사용함.
- [ ] `*.functions.ts`와 `*.server.ts`가 분리되어 있고(import protection 규칙이 아니라 명명 관례), server-only import가 recognized boundary 밖에 살아남지 않음.
- [ ] server functions가 direct static import되며 dynamic import나 mixed barrel을 통하지 않음.
- [ ] public/cross-origin/raw HTTP endpoint는 server function이 아니라 server route로 구현됨.
- [ ] custom `src/start.ts`가 있으면 `requestMiddleware: [createCsrfMiddleware({ filter: (ctx) => ctx.handlerType === 'serverFn' })]`를 명시함.
- [ ] route가 ORM/database client에 직접 접근하지 않음.
- [ ] non-trivial logic이 `modules/<domain>/<feature>/` 또는 domain-specific `lib/<domain>/` folders로 분리됨.
- [ ] `functions/index.ts` barrel export를 만들지 않음.

## Sources

> 출처 확인 2026-11-04: <https://tanstack.com/start/latest/docs/framework/react/guide/server-functions.md>(same-origin RPC, `Cache-Control` 안전), <https://tanstack.com/start/latest/docs/framework/react/guide/middleware.md>(CSRF `filter`와 기본 전체 검증 동작), <https://tanstack.com/start/latest/docs/framework/react/migrate-from-release-candidate.md>(`.inputValidator()` 제거). 그 밖의 공식 TanStack 동작은 이 패키지 자체의 snapshot(`references/official/tanstack-start/tanstack-start-2026-11-04.md`, `references/official/tanstack-start/tanstack-router-2026-11-04.md`, `references/official/tanstack-start/current-docs-2026-11-04.md`)에 위임합니다. 공식 사실 검증 2026-11-04. 저장소 로컬 링크 확인 2026-11-04.
