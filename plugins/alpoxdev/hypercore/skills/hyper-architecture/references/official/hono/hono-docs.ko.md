# Hono 공식 문서 요약

last_verified_at: 2026-11-07

## Contents

- Stable package snapshot
- 공식 문서로 확인한 핵심 포인트
- 이 스킬에 미치는 영향
- Sources

## Stable package snapshot

2026-11-07 npm registry metadata와 아래 인용한 release note를 확인한 기준입니다. 이는 근거 snapshot이며 자동 upgrade target이 아닙니다.

| Package | Stable | 확인된 compatibility |
|---|---:|---|
| `hono` | 4.13.17 | Core package의 Node engine `>=16.9.0`, registry `latest`는 4.13.17이고 4.13.16이 보안 최소 버전 |
| `@hono/node-server` | 2.1.6 | Node `>=20`, Hono `^4 || ^5.0.0-0` |
| `@hono/zod-validator` | 0.9.1 | Hono `>=4.11.2`, Zod `^3.25.0 || ^4.0.0` |
| `@hono/standard-validator` | 0.4.1 | Hono `>=4.11.2`, Standard Schema `^1.0.0` |
| `@hono/zod-openapi` | 1.6.3 | Hono `>=4.10.0`, Zod `^4.0.0`만 |
| `@hono/swagger-ui` | 0.6.2 | Hono `>=4.0.0` |
| `hono-openapi` | 1.5.0 | Third-party; Hono `^4.11.2`와 Standard Schema peer |

출처: [npm registry: hono](https://registry.npmjs.org/hono), [npm registry: `@hono/node-server`](https://registry.npmjs.org/@hono/node-server), [Hono middleware repository](https://github.com/honojs/middleware), [`@hono/node-server`](https://github.com/honojs/node-server), [`hono-openapi`](https://github.com/rhinobase/hono-openapi)

채택하지 않는 것: `hono` 5.0.0-rc.1은 `next` tag에 있고 `drizzle-orm` 1.0.0-rc.x는 release candidate입니다. 이 스킬이 v5 동작을 적을 때는 이미 v4 deprecation으로 존재하는 제거 항목만 적으며, release candidate API를 현재 API로 제시하지 않습니다.

구현 시 installed manifest와 lockfile이 우선합니다. 검증일 이후 dependency를 변경하기 전 registry metadata를 다시 확인합니다.

코어 스킬이나 규칙 파일에서 공식 문서 재확인이 필요할 때 이 참조를 사용합니다.

## 공식 문서로 확인한 핵심 포인트

1. Best practices는 작은 app과 `app.route()` 조합을 선호하며, 가능하면 controller를 만들지 말라고 명시합니다.
출처: [Best Practices](https://hono.dev/docs/guides/best-practices)

2. `createFactory()`, `createHandlers()`, `createApp()`는 핸들러와 미들웨어를 분리해도 타입을 유지하기 위한 공식 도구입니다. `createFactory()`는 `defaultAppOptions`와 `initApp`도 받습니다.
출처: [Factory Helper](https://hono.dev/docs/helpers/factory)

3. `Context`는 요청마다 새로 만들어집니다. 요청 범위 값, 헤더, 상태 코드를 담을 수 있고, `c.set()` / `c.get()`를 쓸 때는 app generics를 통해 `Variables` 타입을 주는 것이 맞습니다.
출처: [Context API](https://hono.dev/docs/api/context)

4. 미들웨어와 핸들러는 등록 순서대로 실행됩니다. 따라서 fallback이나 catch-all 위치가 중요합니다.
출처: [Routing API](https://hono.dev/docs/api/routing), [Middleware Guide](https://hono.dev/docs/guides/middleware)

5. Hono의 validation은 middleware 기반입니다. 공식 문서는 third-party validator 사용을 권장하고, `@hono/zod-validator`와 `@hono/standard-validator`를 공식 생태계 옵션으로 제공합니다.
출처: [Validation Guide](https://hono.dev/docs/guides/validation)

6. `HTTPException.getResponse()`는 `Context`를 모릅니다. 이미 `Context`에 세팅한 헤더가 있다면 새 응답에 명시적으로 보존해야 합니다.
출처: [HTTPException API](https://hono.dev/docs/api/exception)

7. `testClient()`는 route가 export한 `Hono` 인스턴스에 체이닝된 형태로 직접 정의되어야 타입 추론이 제대로 됩니다.
출처: [Testing Helper](https://hono.dev/docs/helpers/testing)

8. 큰 앱에서 RPC를 쓸 때는 type inference가 유지되도록 sub-app 조합을 조심해야 하고, typed client는 안정적인 `AppType` 또는 sub-app export에 의존합니다.
출처: [RPC Guide](https://hono.dev/docs/guides/rpc)

9. `app.request()`는 request/response 테스트를 지원하고, Hono는 route contract용 typed testing helper도 제공합니다.
출처: [Testing Guide](https://hono.dev/docs/guides/testing), [Testing Helper](https://hono.dev/docs/helpers/testing)

10. `@hono/zod-openapi`는 `OpenAPIHono`, `createRoute()`, `app.openapi()`, `app.doc()` / `app.doc31()`를 사용해 route schema에서 OpenAPI 문서를 생성합니다.
출처: [Zod OpenAPI Example](https://hono.dev/examples/zod-openapi), [`@hono/zod-openapi` README](https://github.com/honojs/middleware/tree/main/packages/zod-openapi)

11. `hono-openapi`는 `describeRoute()`, `validator()`, `resolver()`, `openAPIRouteHandler()`를 통한 middleware-driven OpenAPI 생성을 지원하며 여러 validator ecosystem에 맞습니다. 1.3.2부터 `validator()` route에 400 validation 응답이 자동으로 붙고, 1.4.0은 header의 `resolver()` schema를 해석합니다.
출처: [Hono OpenAPI Example](https://hono.dev/examples/hono-openapi), [`hono-openapi` releases](https://github.com/rhinobase/hono-openapi/releases)

12. `@hono/swagger-ui`는 Hono route에서 Swagger UI를 제공하고 generated spec endpoint를 가리켜야 합니다. 이 패키지 자체가 spec을 생성하지는 않습니다. 0.6.2는 생성 page에 삽입되는 title과 string option을 escape합니다.
출처: [Swagger UI Example](https://hono.dev/examples/swagger-ui), [`@hono/swagger-ui` README](https://github.com/honojs/middleware/tree/main/packages/swagger-ui)

13. OpenAPI operation은 responses와 reusable components를 명시해야 합니다. Security schemes는 `components.securitySchemes`에 두고, examples도 reusable components로 둘 수 있습니다.
출처: [OpenAPI Specification 3.1.0](https://spec.openapis.org/oas/v3.1.0.html), [Swagger Authentication Docs](https://swagger.io/docs/specification/v3_0/authentication/), [Swagger `$ref` Docs](https://swagger.io/docs/specification/v3_0/using-ref/), [Swagger Examples Docs](https://swagger.io/docs/specification/v3_0/adding-examples/)

14. Hono environment binding은 app generics로 type 지정하고 `c.env`로 접근합니다. Cloudflare Workers 문서는 D1 등 binding을 `Bindings` 모델로 다루고, Factory Helper 문서는 `initApp`에서 `c.env`로 Drizzle D1 database를 만들고 typed `Variables`에 저장하는 예시를 제공합니다.
출처: [Context API](https://hono.dev/docs/api/context), [Cloudflare Workers](https://hono.dev/docs/getting-started/cloudflare-workers), [Factory Helper](https://hono.dev/docs/helpers/factory)

15. Root app은 `use`, `route`, `basePath`, `notFound`, `onError`를 제공합니다. `notFound`는 top-level app에서만 호출되고, route-level `onError`는 parent handler보다 우선합니다.
출처: [App API](https://hono.dev/docs/api/hono)

16. Middleware는 등록 순서로 실행되고 typed variable은 chained middleware를 거치며 누적됩니다. 따라서 shared middleware 위치는 behavior와 inferred context 모두에 영향을 줍니다.
출처: [Middleware Guide](https://hono.dev/docs/guides/middleware)

17. Hono는 Web Standards 기반으로 여러 runtime을 지원하며 Node.js에서는 `@hono/node-server`를 사용합니다. Runtime-neutral app과 별도 adapter entrypoint는 이 사실에 근거한 Hypercore portability convention이지, 공식 필수 folder layout은 아닙니다.
출처: [Hono repository](https://github.com/honojs/hono), [Node.js Guide](https://hono.dev/docs/getting-started/nodejs), [`@hono/node-server`](https://github.com/honojs/node-server)

18. `hono` 4.13.16이 보안 최소 버전입니다. 이 release 하나에서 `mount()` / `app.mount()`가 mount prefix 안쪽 middleware를 우회하는 path를 넘기던 문제, `RegExpRouter`(따라서 기본 `SmartRouter`)가 일부 route pattern과 encoded line terminator가 있는 path에서 wildcard middleware를 건너뛰던 문제, `charset` 같은 추가 parameter가 붙은 `multipart/form-data`에서 `validator('form')`이 검증을 건너뛰던 문제, template part 사이에서 나뉜 닫는 tag를 통한 `css` HTML injection, `text/ping` 요청을 검사하지 않던 `csrf()`를 함께 고칩니다. 빈 문자열과 match되는 custom pattern(`{[0-9]*}` 등)은 이제 `UnsupportedPathError`를 던지므로 upgrade 시 build-time `PreparedRegExpRouter` data를 다시 생성해야 합니다.
출처: [`hono` v4.13.16 release](https://github.com/honojs/hono/releases/tag/v4.13.16)

19. Runtime adapter는 별도 package입니다: `@hono/bun`, `@hono/deno`, `@hono/cloudflare-workers`, `@hono/aws-lambda`, `@hono/lambda-edge`, `@hono/netlify`, `@hono/vercel`, `@hono/service-worker`. `hono/<adapter>`는 v4에서 동작하지만 deprecated이고 v5에서 제거됩니다. `hono/cloudflare-pages`는 대체 package 없이 deprecated이며, Cloudflare는 static assets를 쓰는 Workers를 권장합니다.
출처: [`hono` v4.13.10 release](https://github.com/honojs/hono/releases/tag/v4.13.10), [Cloudflare Pages guide](https://hono.dev/docs/getting-started/cloudflare-pages)

20. `app.mount()`는 v4에서 deprecated이고 v5에서 제거됩니다. 대체는 Mount middleware입니다. `import { mount } from 'hono/mount'`로 가져와 `app.all('/prefix/*', mount(handler))`로 등록합니다. Mount된 app은 `handler(request, c.env, c.executionCtx)`로 호출되고, 기본적으로 match된 path prefix가 제거된 `Request`를 받습니다. `optionHandler`와 `replaceRequest`가 그 인자와 request를 바꿉니다.
출처: [App API](https://hono.dev/docs/api/hono), [Mount Middleware](https://hono.dev/docs/middleware/builtin/mount), [`hono` v4.13.13 release](https://github.com/honojs/hono/releases/tag/v4.13.13)

21. `hono/method-not-allowed`의 `methodNotAllowed({ app })`는 path는 등록된 route와 맞지만 method가 다를 때 `Allow` header와 함께 `405 Method Not Allowed`를 반환합니다. 이 middleware가 없으면 Hono는 같은 경우에 `404 Not Found`를 반환합니다.
출처: [Method Not Allowed Middleware](https://hono.dev/docs/middleware/builtin/method-not-allowed)

22. HTTP QUERY method는 1급입니다. `app.query()`로 handler를 등록하고, Cache middleware는 body digest를 key에 넣어 QUERY 응답을 cache하며, ETag는 QUERY conditional request를 처리하고, CORS 기본값은 `GET, HEAD, PUT, POST, DELETE, PATCH, QUERY`입니다. GET을 포함한 전 method의 내부 cache key 형식이 바뀌어 entry가 `/.hono/cache?__hono_cache_key=...` 아래 저장되므로, 원본 URL로 purge하던 code는 수정해야 합니다.
출처: [`hono` v4.13.0 release](https://github.com/honojs/hono/releases/tag/v4.13.0), [Routing API](https://hono.dev/docs/api/routing)

23. `serveStatic`은 decoding 후에도 `%`가 남은 request path를 거부하고, `allowPercentInPath: true`가 이름에 literal `%`가 들어간 file 제공을 되살립니다. 또한 `GET`과 `HEAD`만 제공하고, precompressed file에 대해 `Accept-Encoding` q-value를 존중합니다.
출처: [`hono` v4.13.11 release](https://github.com/honojs/hono/releases/tag/v4.13.11), [`hono` v4.13.14 release](https://github.com/honojs/hono/releases/tag/v4.13.14)

24. `validator('form')`은 4.13.16부터 추가 parameter가 붙은 `multipart/form-data`를 처리합니다. `@hono/standard-validator` 0.4.0은 form/field error 정렬용 `flattenErrors`를 추가했고, 0.4.1은 `header` validation의 기본 400 body에서 `cookie` header를 제거합니다.
출처: [`hono` v4.13.16 release](https://github.com/honojs/hono/releases/tag/v4.13.16), [`@hono/standard-validator` releases](https://github.com/honojs/middleware/releases)

25. `getPath()`는 `strict: false`와 함께 쓸 수 없습니다. strict 기본값은 `true`입니다.
출처: [`hono` v4.13.14 release](https://github.com/honojs/hono/releases/tag/v4.13.14)

26. `@hono/zod-openapi` 1.6.x: JSON이나 form body의 `Content-Type`이 route에 선언한 media type과 하나도 맞지 않으면 빈 객체 검증 대신 `415 Unsupported Media Type`으로 거부합니다. `request.body.required` 기본값은 `false`여서 body 없는 요청이 `c.req.valid('json')`이 `{}`인 채로 handler에 도달하고, `required: true`면 `400`으로 실패합니다. `get()`, `post()`, `use()`는 `Hono` 타입을 반환하므로 `$()`나 `HonoToOpenAPIHono`로 `OpenAPIHono`를 되살립니다. `defineOpenAPIRoute()`와 `openapiRoutes([...] as const)`로 묶음 등록을 하고, `createRoute()`는 1.6.0부터 `method: 'query'`를 받습니다.
출처: [`@hono/zod-openapi` README](https://github.com/honojs/middleware/tree/main/packages/zod-openapi), [`@hono/zod-openapi` releases](https://github.com/honojs/middleware/releases)

27. RPC client 함정: path parameter와 query 값은 `string`으로 넘겨야 합니다. `.then()` chain을 그대로 반환하는 handler는 응답 타입을 잃어 client가 `unknown`을 추론합니다. `$path()`는 origin 없는 typed path 문자열을 반환합니다. `NotFoundResponse` module augmentation으로 `c.notFound()`가 typed 404를 실을 수 있습니다. server app과 함께 client module을 compile(`hcWithType`)하면 호출마다 type을 계산하지 않습니다.
출처: [RPC Guide](https://hono.dev/docs/guides/rpc)

28. `ContextVariableMap`은 해당 변수를 설정하는 middleware가 실제로 실행됐는지와 무관하게 모든 context에 type을 전역으로 추가합니다. 그래서 `c.get()`이 type-safe해 보여도 runtime에서는 `undefined`일 수 있습니다. Augmentation은 app-wide middleware가 설정하는 변수에만 맞습니다.
출처: [Context API](https://hono.dev/docs/api/context)

29. WebSocket은 `@hono/node-server`에 내장되어 있습니다. `ws`를 설치하고 `{ noServer: true }`로 `WebSocketServer`를 만든 뒤 `serve()`에 `websocket: { server: wss }`로 넘기고, route는 `@hono/node-server`의 `upgradeWebSocket`을 씁니다. `@hono/node-ws`는 deprecated입니다. 이 package는 Node `>=20`을 요구하며 Node.js guide page는 아직 더 낮은 최소 버전을 적고 있으므로 package manifest가 우선합니다.
출처: [Node.js Guide](https://hono.dev/docs/getting-started/nodejs), [`@hono/node-server` README](https://github.com/honojs/node-server)

## 이 스킬에 미치는 영향

- hypercore의 route composition 규칙은 공식 `app.route()` / factory 가이드를 근거로 삼아야 합니다.
- hypercore validation 규칙은 기존 저장소 표준을 먼저 보고, 새 검증 표면을 함부로 발명하면 안 되며, 4.13.16의 form 검증 하한을 함께 적용합니다.
- hypercore error handling 규칙은 `HTTPException.getResponse()`가 context-set header를 자동 보존한다고 가정하면 안 됩니다.
- hypercore testing/RPC 규칙은 detached registration을 가볍게 보지 말고 체이닝된 app typing을 보호해야 합니다.
- hypercore OpenAPI 규칙은 415와 `body.required` 결과를 포함해 runtime validation, typed RPC responses, generated OpenAPI responses가 서로 맞도록 보호해야 합니다.
- Swagger UI 노출은 spec generation과 별개의 platform/security 결정입니다.
- 큰 앱에서는 route modules, typed clients, OpenAPI metadata가 같은 app boundary에서 조합되도록 해야 drift를 줄일 수 있습니다.
- Database binding과 request-scoped database variable은 `Bindings` / `Variables`로 type 지정하고, route module은 provider-specific setup에서 독립적으로 유지해야 합니다.
- Adapter import는 `@hono/*` package에 두고 `app.mount()` 이관은 Mount middleware로 처리하므로, `hono/<adapter>`와 `app.mount()`를 새 code로 받아들이지 않습니다.

## Sources

> 확인 2026-11-07. `hono` 행을 npm registry 기준으로 갱신했고, 4.13.16은 문서화된 보안 최소 버전으로 남습니다.

| 주장 | 출처 |
|---|---|
| 위 snapshot 표의 package version과 compatibility 범위 | 그 표 옆에 적은 npm registry·repository URL |
| 18-26번 항목의 release별 동작 | 각 항목에 링크한 `honojs/hono`·`honojs/middleware` release page |
| 위 1-17번과 27-29번 항목에 기록한 공식 Hono·OpenAPI 동작 | 각 번호 항목에 붙은 inline `Source:` 링크 |
