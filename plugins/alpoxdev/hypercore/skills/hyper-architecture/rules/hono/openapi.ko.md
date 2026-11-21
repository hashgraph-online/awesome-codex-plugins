# OpenAPI와 Swagger

> 생성된 API 문서를 typed contract boundary로 취급

---

## Stable package 기준

2026-11-04 확인 기준 `@hono/zod-openapi` 1.6.3은 Hono `>=4.10.0`과 Zod `^4.0.0`만 요구하고, `@hono/swagger-ui` 0.6.2는 Hono `>=4`를 요구합니다. Third-party `hono-openapi` 1.5.0은 Hono `^4.11.2`와 Standard Schema ecosystem peer를 요구합니다. 경로 선택 전 lockfile과 peer compatibility를 확인합니다.

- Zod 4 route-first API에는 `@hono/zod-openapi`를 우선합니다. `@hono/zod-validator`와 달리 Zod 3를 받지 않습니다.
- 기존 `hono-openapi` surface를 incidental하게 migration하지 않고 보존합니다. 이 package는 official HonoJS package가 아닙니다. 1.3.2부터 `validator()` route에 400 validation 응답이 자동으로 붙으므로 같은 응답을 두 번 문서화하지 않습니다.
- Undocumented plain `Hono` child를 섞고 `OpenAPIHono`가 metadata를 발견할 것이라 기대하지 않습니다.
- 실제 success/error status를 모두 schema화합니다. Central error envelope를 runtime 및 RPC global response type과 동기화합니다.
- Deterministic check에서 document를 생성하고 reference와 unique `operationId`를 검증하며 committed artifact라면 diff를 확인합니다.
- Spec/UI 노출을 별도로 gate합니다. UI를 숨겨도 public JSON spec이 private이 되지 않으며 Swagger UI는 spec을 생성하지 않습니다.
## 핵심 규칙

Hono API가 OpenAPI/Swagger docs를 발행한다면, route 변경은 같은 변경 안에서 generated contract도 갱신해야 합니다. Contract는 runtime route가 실제로 지원하는 request, response, status code, security, example과 일치해야 합니다.

Database row는 자동으로 public API DTO가 아닙니다. Persistence 변경이 문서화된 response에 영향을 주면 publish 또는 codegen 전에 ORM row를 public response schema로 매핑합니다.

## 승인된 생성 경로

| Repo 형태 | 우선 경로 |
|------|------|
| Zod-first routes | `@hono/zod-openapi`의 `OpenAPIHono`, `createRoute()`, `app.openapi()`, `app.doc()` |
| Mixed validator 또는 Standard Schema repos | `hono-openapi`의 `describeRoute()`, `resolver()`, `validator()`, `openAPIRouteHandler()` |
| UI only | Generated spec endpoint에 연결한 `@hono/swagger-ui` |

사용자가 명시적으로 migration을 요청하지 않았다면 앱 전체의 generator를 바꾸지 않습니다.

## 폴더 구조

```text
src/
├── app.ts
├── openapi/
│   ├── components.ts
│   ├── errors.ts
│   └── registry.ts
└── routes/
    └── users/
        ├── index.ts
        ├── routes.ts
        ├── schemas.ts
        └── handlers.ts
```

- Shared components, security schemes, examples, error envelopes는 두 개 이상 feature가 재사용할 때 `src/openapi/`에 둡니다.
- Feature operation metadata는 설명하는 feature route 근처에 둡니다.
- Canonical spec은 app boundary에서 조합하고, generated fragment를 손으로 복붙하지 않습니다.
- `/doc` 또는 `/openapi.json` 같은 안정적인 spec path를 사용합니다.
- Swagger UI는 `/ui`, `/docs`, admin route 같은 별도 path에서 제공합니다.

## Operation Metadata Checklist

문서화된 모든 operation은 아래를 정의해야 합니다:

- 안정적인 `operationId`
- 일관된 `tags`
- Path params, query params, headers, request body schemas
- Status별 JSON schema가 있는 success responses
- 필요한 경우 400, 401, 403, 404, 409, 422, 500 같은 expected error responses
- Reusable `components.securitySchemes`를 통한 auth requirements
- Schema와 일치하는 request/response examples
- Public으로 노출하면 안 되는 endpoint의 deprecation 또는 hide metadata

## Contract Drift Rules

| Drift | 규칙 |
|------|------|
| Handler가 OpenAPI에 없는 validated data를 읽음 | 차단. Request schema를 추가하거나 route 문서화를 중단합니다. |
| OpenAPI가 handler가 반환하지 않는 response status를 나열함 | 경고. Codegen/client publish 전에 handler 또는 docs를 고칩니다. |
| Handler는 status-specific payload를 반환하지만 docs는 generic response만 보여줌 | 경고. 명시적 response schema를 추가합니다. |
| OpenAPI response schema가 internal/sensitive field를 포함한 raw ORM row를 노출함 | 차단. DTO mapping을 추가하고 public response contract를 문서화합니다. |
| Shared auth middleware가 있는데 OpenAPI에 security requirements가 없음 | Public/partner-facing docs에서는 차단. |
| Swagger UI가 실수로 public 노출됨 | 차단. Auth/admin/dev gating을 추가하거나 public-docs 결정을 문서화합니다. |
| Generated spec lint 실패 또는 깨진 `$ref`가 있음 | Publish 전에 차단. |
| 문서화된 JSON·form body에 `415`가 없는데 client가 선언되지 않은 `Content-Type`을 보낼 수 있음 | 경고. 415 결과를 문서화하거나 허용 media type을 좁힙니다. |
| Body를 optional로 선언했는데 handler가 모든 field 존재를 가정함 | 차단. `body.required: true`로 바꾸거나 body 없는 경우를 명시적으로 검증합니다. |

## Request Body Contract

`@hono/zod-openapi` 1.6.x는 JSON과 form media type만 검증합니다. 두 동작을 계약에 반영해야 합니다.

- Request body의 `Content-Type`이 route에 선언한 media type과 하나도 맞지 않으면 `415 Unsupported Media Type`으로 거부합니다. 이전 version은 빈 객체를 검증했기 때문에 잘못된 header를 보낸 client가 handler까지 도달했습니다.
- `request.body.required` 기본값은 `false`입니다. Body 없는 요청이 handler에 도달하고 `c.req.valid('json')`은 `{}`입니다. Body가 필수라면 `required: true`로 두며, 그때 body가 없으면 `400`으로 실패합니다.

`createRoute({ request: { body: { content: { ... } } } })`에 허용하는 media type을 모두 선언하고, client가 의존한다면 두 결과를 operation response 목록에도 반영합니다.

## Large-App Pattern

`@hono/zod-openapi`에서는 feature-local route definition과 app-level registration을 선호합니다. `openapiRoutes()`는 `route`와 `handler`를 짝지은 `defineOpenAPIRoute()` 결과를 받으며, `createRoute()` 객체만으로는 이 방식으로 등록할 수 없습니다.

```ts
// routes/users/routes.ts
import { createRoute, defineOpenAPIRoute } from '@hono/zod-openapi'

export const listUsersRoute = defineOpenAPIRoute({
  route: createRoute({
    method: 'get',
    path: '/',
    operationId: 'listUsers',
    tags: ['Users'],
    responses: {
      200: {
        description: 'Users returned',
        content: {
          'application/json': {
            schema: usersResponseSchema,
          },
        },
      },
    },
  }),
  handler: async (c) => {
    return c.json({ users: await listUsers() }, 200)
  },
})

export const userRoutes = [listUsersRoute] as const
```

```ts
// app.ts
const app = new OpenAPIHono()

app.openapiRoutes([...userRoutes, ...billingRoutes] as const)
app.doc('/doc', { openapi: '3.0.0', info: { title: 'API', version: '1.0.0' } })
app.get('/ui', swaggerUI({ url: '/doc' }))
```

RPC app이 수십 개 route를 넘어가면 작은 `OpenAPIHono` instance로 나누고 `.route()`로 mount합니다. `.openapi()` chain이 길어지면 link마다 schema type이 누적되어 하나의 큰 app이 `hc` type 검사를 느리게 만듭니다. Routing과 OpenAPI output은 그대로이고 누적되는 type 연산만 줄어듭니다.

```ts
const users = new OpenAPIHono().openapi(getUserRoute, getUserHandler)
const posts = new OpenAPIHono().openapi(getPostRoute, getPostHandler)

export const appRoutes = new OpenAPIHono().route('/', users).route('/', posts)
```

`get()`, `post()`, `use()`는 `OpenAPIHono`가 아니라 `Hono` 타입을 반환하므로, 이들을 섞은 chain은 `.openapi()`를 잃습니다. 결과를 `$()`로 감싸거나 `HonoToOpenAPIHono`로 타입을 변환합니다.

```ts
import { $, OpenAPIHono } from '@hono/zod-openapi'

const app = $(new OpenAPIHono().use(requestIdMiddleware))
app.openapi(route, handler)
```

`hono-openapi`에서는 route-local `describeRoute()` metadata와 단일 app-level `openAPIRouteHandler()` endpoint를 선호합니다.

## Version and Package Caveats

- `@hono/zod-openapi`의 일반 예시는 `app.doc()`와 OpenAPI 3.0을 보여주지만, 3.1 output이 필요하면 `app.doc31()` / `getOpenAPI31Document()` 지원 여부를 확인합니다. `getOpenAPI31Document()`는 두 번째 인자로 `unionPreferredType: 'oneOf'` 같은 generator option을 받습니다.
- `@hono/zod-openapi`는 Zod `^4.0.0`만 peer로 받습니다. Zod 3을 쓰는 저장소는 `hono-openapi`를 유지하거나 Zod를 먼저 올립니다. 두 validator는 Zod major를 공유하지 않습니다.
- `@hono/swagger-ui`는 spec을 생성하지 않고 UI를 제공합니다. `url`은 단일 spec, `urls`는 여러 spec에 사용합니다. 0.6.2는 page에 삽입하는 title과 string option을 escape합니다.
- `persistAuthorization`, `remoteAssets.baseUrl`, UI `version`, custom HTML은 deployment/UI knobs이며 spec contract knobs가 아닙니다.
- Plain `Hono` sub-app을 `OpenAPIHono` 아래에 섞으면 OpenAPI metadata가 spec에 합쳐지지 않을 수 있습니다.
- Nested OpenAPI sub-app을 mount할 때 parent `.route()` path parameter는 Hono `:param` syntax를 사용합니다.
- Header schema key는 Hono validator와 OpenAPI generator 모두에서 lowercase로 맞춥니다.
- `createRoute({ method: 'query' })`는 1.6.0부터 쓸 수 있습니다. Publish 전에 generated document 소비자가 QUERY operation을 받아들이는지 확인합니다.

## 리뷰 체크리스트

- 하나의 generator strategy를 일관되게 사용함
- Spec endpoint와 Swagger UI endpoint가 분리되어 있고 의도적임
- Route validators와 documented schemas가 source 또는 synchronization rule을 공유함
- JSON·form body가 media type을 선언하고, client가 trigger할 수 있는 곳에 415를 문서화함
- `body.required`가 handler의 가정과 일치함
- Plain `Hono`를 반환하는 middleware chain은 `.openapi()` 전에 `$()`나 `HonoToOpenAPIHono`로 감쌈
- Database row shape가 publication 전에 public DTO schema로 매핑됨
- Reusable schemas, errors, security schemes, parameters, examples가 `components`를 사용함
- Operation ID가 안정적이고 unique함
- Error responses가 중앙 error handling과 일치함
- RPC `AppType`/typed client shape와 generated OpenAPI shape가 충돌하지 않음
- 단일 chain이 type 검사를 느리게 만들면 큰 RPC surface를 mount한 `OpenAPIHono` instance로 나눔
- Publish 전에 CI 또는 local verification이 generated spec을 lint, bundle, validate함

## Sources

> Checked 2026-11-04.

| 주장 | 출처 |
|---|---|
| `@hono/zod-openapi` 1.6.3, `@hono/swagger-ui` 0.6.2, `hono-openapi` 1.5.0 version과 peer 범위 | [npm registry: `@hono/zod-openapi`](https://registry.npmjs.org/@hono/zod-openapi), [npm registry: `@hono/swagger-ui`](https://registry.npmjs.org/@hono/swagger-ui), [npm registry: hono-openapi](https://registry.npmjs.org/hono-openapi) |
| 선언되지 않은 media type의 415, `body.required` 기본값, `$()` / `HonoToOpenAPIHono`, `defineOpenAPIRoute` / `openapiRoutes`, mount instance type 성능, 3.1 generator option | [`@hono/zod-openapi` README](https://github.com/honojs/middleware/tree/main/packages/zod-openapi) |
| `createRoute()`의 QUERY 지원, 1.6.3의 415 수정, 1.6.1·1.6.2의 type 비용 감소 | [`@hono/zod-openapi` releases](https://github.com/honojs/middleware/releases) |
| `hono-openapi` 400 자동 포함과 header `resolver()` 지원 | [`hono-openapi` releases](https://github.com/rhinobase/hono-openapi/releases) |
| 0.6.2의 Swagger UI escaping | [`@hono/swagger-ui` releases](https://github.com/honojs/middleware/releases) |
