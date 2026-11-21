# 라우트 구조

> Hono route composition 규칙

---

## Stable Hono 4.13 기준

Hono 공식 routing은 등록 순서를 따릅니다. `route()`는 호출 시점에 child app의 registered route를 parent에 복사하므로 grouping order가 behavior를 바꿀 수 있습니다. `basePath()`는 app 하나에 prefix를 적용하고, Mount middleware는 다른 framework를 연결하는 수단이므로 typed Hono sub-app composition의 대체물이 아닙니다. `app.mount()`는 v4에서 deprecated이고 v5에서 제거됩니다.

- Inferred type이 `AppType`, `testClient`, `hc`에 쓰이면 route definition과 `route()` call을 chaining합니다.
- 넓은 parameter, wildcard, fallback, not-found behavior는 specific route 뒤에 등록합니다.
- Hono strict mode 기본값은 `true`이고 `getPath()`는 `strict: false`와 함께 쓸 수 없으므로 trailing-slash behavior를 명시적으로 결정합니다.
- Host-based routing과 custom `getPath()`는 app/platform boundary에 둡니다.
- `app.mount('/prefix', handler)`는 `hono/mount`의 `mount`를 써서 `app.all('/prefix/*', mount(handler))`로 옮깁니다. Mount된 app은 `handler(request, c.env, c.executionCtx)`로 호출되고, `optionHandler`나 `replaceRequest`가 바꾸지 않는 한 match된 prefix가 제거된 request를 받습니다.
- `QUERY`는 1급 method입니다. `app.query()`로 등록하고, `@hono/zod-openapi` 1.6.0부터 `createRoute({ method: 'query' })`를 쓸 수 있습니다. Cache 응답을 반환하는 QUERY route는 바뀐 cache key를 고려해야 합니다.
- `methodNotAllowed({ app })`를 켜면 계약이 바뀝니다. path는 맞고 method가 지원되지 않는 요청이 `404` 대신 `Allow`와 함께 `405`를 받습니다. 같은 변경에서 RPC status union과 OpenAPI response를 함께 고칩니다.
- Sub-app 이동 후 mount prefix와 order를 test합니다. 파일 배치만으로 동일 dispatch를 증명할 수 없습니다.
## 작은 구조

```text
src/
├── app.ts
├── index.ts
├── routes/
│   ├── index.ts
│   ├── health.ts
│   └── users/
│       ├── index.ts
│       ├── handlers.ts
│       ├── schemas.ts
│       └── service.ts
```

## 큰 구조

```text
src/routes/
├── index.ts
├── health.ts
├── users/
│   ├── index.ts
│   ├── routes.ts
│   ├── handlers.ts
│   ├── schemas.ts
│   ├── service.ts
│   └── tests/
└── billing/
    ├── index.ts
    ├── routes.ts
    ├── handlers.ts
    ├── schemas.ts
    ├── middleware.ts
    └── service.ts
```

`routes/index.ts` 또는 `app.ts`는 유일한 mount table로 남깁니다. Feature folder는 local route definition, handler, schema, feature-only middleware를 소유합니다.

## 규칙

- `app.ts`가 루트 app composition을 소유
- `routes/index.ts` 또는 `app.ts`가 mount table의 단일 진입점
- `app.route('/users', usersApp)` 같은 sub-app mount를 우선
- 기능이 두 파일 이상이면 route folder 사용
- health 같은 작은 운영 endpoint만 single-file route 허용
- handler가 두 개 이상이거나 request schema, feature middleware, OpenAPI metadata, service orchestration이 있으면 folder로 분리합니다.
- `basePath()`와 API version prefix는 composition boundary에 둡니다.
- Hono sub-app에는 `app.route()`를 쓰고 다른 framework에는 Mount middleware를 씁니다. 새 code에 `app.mount()`를 추가하지 않습니다.
- App이 의도적으로 405를 답할 때만 `methodNotAllowed({ app })` middleware를 넣고, 그때 documented·typed 404 계약을 모두 고칩니다.
- Route module에서 database client, Drizzle schema table, ORM driver, migration helper를 import하지 않습니다. Service/repository를 사용합니다.
- 한 feature route module이 다른 feature route module을 import하지 않습니다.
- Hono dispatch는 registration order를 따르므로 fallback과 catch-all route는 마지막에 둡니다.

## 마운트 패턴

```ts
import { createApp } from '@/lib/create-app'
import { healthApp } from '@/routes/health'
import { usersApp } from '@/routes/users'

export const app = createApp()
  .route('/health', healthApp)
  .route('/users', usersApp)
```

## Scale-Up Pattern

```ts
// routes/users/index.ts
import { createApp } from '@/lib/create-app'

import { createUserHandlers, listUserHandlers } from './handlers'

export const usersApp = createApp()
  .get('/', ...listUserHandlers)
  .post('/', ...createUserHandlers)
```

```ts
// routes/index.ts
import { usersApp } from './users'
import { billingApp } from './billing'

export const routesApp = createApp()
  .route('/users', usersApp)
  .route('/billing', billingApp)
```

## 비준수 시그널

- Route registration이 단일 mount table 없이 관련 없는 파일들에 흩어져 있음
- Multi-feature app인데 `app.route()`가 없음
- Feature route folder가 service 대신 database/SDK client를 직접 import함
- Route handler가 DB connection, Drizzle client, pool, migration을 직접 생성함
- 한 route file에 schemas, 긴 handlers, feature middleware, business logic이 모두 섞여 있음
- fallback, `*`, `/:id` route가 더 구체적인 route보다 앞에 있음
- Version prefix가 한 곳에서 정의되지 않고 모든 feature 안에서 반복됨
- 새 code에 `app.mount()`가 나타나거나, typed Hono sub-app 자리에 foreign app이 mount됨
- `methodNotAllowed()`를 켰는데 RPC status union이나 OpenAPI response가 아직 404를 전제함

## 리뷰 체크리스트

- composition 진입점이 하나로 명확함
- route mount 순서가 의도적임
- fallback route가 마지막에 위치
- Non-Hono mount는 `app.mount()`가 아니라 `/*` path를 쓰는 Mount middleware를 사용함
- 405 동작은 의도적으로 없거나, typed·documented response에 반영됨
- 큰 기능은 flat giant file 대신 sub-app folder 사용
- 새 route가 들어갈 위치가 명확할 만큼 feature boundary가 분명함
- Persistence 작업이 사소하지 않다면 service/repository boundary를 거침
- Route structure가 tests, RPC, OpenAPI generation을 위한 typed app inference를 보존함

## Sources

> Checked 2026-11-04.

| 주장 | 출처 |
|---|---|
| 등록 순서, `route()`의 child route 복사, strict mode 기본값 | [Routing API](https://hono.dev/docs/api/routing), [App API](https://hono.dev/docs/api/hono) |
| `app.mount()` deprecation과 Mount middleware 대체 | [App API](https://hono.dev/docs/api/hono), [Mount Middleware](https://hono.dev/docs/middleware/builtin/mount), [`hono` v4.13.13 release](https://github.com/honojs/hono/releases/tag/v4.13.13) |
| `strict: false`에서 `getPath()` 금지 | [`hono` v4.13.14 release](https://github.com/honojs/hono/releases/tag/v4.13.14) |
| QUERY method, cache key 변경, `methodNotAllowed` | [`hono` v4.13.0 release](https://github.com/honojs/hono/releases/tag/v4.13.0), [Method Not Allowed Middleware](https://hono.dev/docs/middleware/builtin/method-not-allowed) |
