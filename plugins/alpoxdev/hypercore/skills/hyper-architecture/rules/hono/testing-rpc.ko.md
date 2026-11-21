# Testing과 RPC

> typed client와 테스트를 route-shape 회귀로부터 보호

---

## Stable Hono 4.13 기준

Hono RPC는 server와 client 모두 TypeScript `strict`를 요구합니다. Producer/consumer Hono version은 일치해야 하며 version skew는 excessively deep type instantiation을 일으킬 수 있습니다. 큰 contract는 editor performance도 저하시킬 수 있습니다.

- 최종 chained route value에서 `AppType`을 export하며 나중에 mutate된 app이나 partial child에서 export하지 않습니다.
- Package boundary에서는 declaration을 compile/consume하거나 project reference를 사용하고 server implementation을 deep import하지 않습니다.
- Shared global error response typing에는 `ApplyGlobalResponse`를 사용합니다.
- Client contract를 관찰 가능하게 만들 때 `parseResponse()`, `DetailedError`, `InferRequestType`, `InferResponseType`을 사용합니다.
- Path parameter와 query 값은 `string`으로 넘깁니다. Server schema가 number로 coerce하더라도 `hc`는 string으로 type을 잡으므로 `id: 1` literal은 type check에서 실패합니다.
- Handler는 `await`한 값이나 평범한 promise를 반환하고 `.then()` chain을 반환하지 않습니다. `.then()` chain을 그대로 반환하면 응답 type이 사라져 client가 `unknown`을 추론합니다.
- `hc`는 path parameter value를 자동 URL-encode하지 않습니다. Slash를 허용하면 value를 encode하거나 명시적으로 test한 regexp route를 사용합니다.
- 문자열을 직접 조립하지 않고 `$path()`나 `$url()`로 client에서 request path를 만듭니다. 둘 다 app에 대해 typed로 유지됩니다.
- Client contract에 typed 404가 포함되면 route-local `c.json(..., 404)`를 반환하거나, `NotFoundResponse`를 augment해 `c.notFound()`가 응답 type을 싣게 합니다.
- Behavior에는 `app.request()`, server-side typed ergonomics에는 `testClient()`, serialization/base URL behavior가 중요할 때만 실제 `hc` boundary test를 사용합니다.
- `testClient()`와 route typing은 `Hono` instance에 직접 chaining한 route definition을 요구합니다. Detached registration은 inference를 지웁니다.
- Runtime binding은 `app.request()`의 세 번째 argument로 전달하고 adapter-specific behavior는 별도로 test합니다.
## 핵심 규칙

- 앱이 `testClient()` 또는 `hc`를 쓰면 route type inference를 보호
- `hc` 또는 shared RPC/client contract가 앱에 의존하면 `AppType` export
- 큰 앱에서는 sub-app composition 타입이 exported surface까지 유지되어야 함
- Typed RPC와 generated OpenAPI docs가 일치하도록 explicit response status를 유지

## 예시

```ts
export const app = new Hono()
  .get('/search', (c) => {
    const query = c.req.query('q')
    return c.json({ query })
  })

export type AppType = typeof app
```

## Large-App Contract Pattern

```ts
// app.ts
export const app = createApp()
  .route('/users', usersApp)
  .route('/billing', billingApp)

export type AppType = typeof app
```

```ts
// client.ts
import { hc } from 'hono/client'

import type { AppType } from './app'

export const client = hc<AppType>('/api')
```

Client compile 시간이나 editor 지연이 문제가 되면 호출 지점마다 type을 계산하지 않고 compile 시점에 한 번만 계산합니다.

```ts
// client.ts
import { hc } from 'hono/client'

import type { AppType } from './app'

const client = hc<AppType>('')
export type Client = typeof client

export const hcWithType = (...args: Parameters<typeof hc>): Client =>
  hc<AppType>(...args)
```

Route behavior test에는 `app.request()`, typed server-side ergonomics에는 `testClient()`, shared client-contract check에는 `hc<AppType>()`를 사용합니다.

## 비준수 시그널

- Route registration이 chained route type을 지우는 detached mutation을 사용함
- Consumer가 전체 API를 기대하는데 `AppType`이 partial sub-app에서 export됨
- 여러 success/error variant가 있는 route에서 response helper가 explicit status를 빠뜨림
- Handler가 `.then()` chain을 반환해 client의 응답 type이 `unknown`이 됨
- Client 호출 지점이 path parameter와 query 값에 number나 객체를 넘김
- Frontend typed client가 exported app type 대신 route internals를 import함
- Generated OpenAPI response schema가 RPC-inferred response variants와 다름
- Public client가 404 shape에 의존하지만 `app.notFound()` 또는 explicit JSON response contract가 테스트되지 않음

## 리뷰 체크리스트

- route type이 exported app까지 흐름
- 리팩터링 후에도 `testClient()`가 계속 유용함
- `hc<AppType>` 또는 sub-app client 추론이 유지됨
- Handler가 `.then()` chain이 아니라 `await`한 값을 반환함
- 호출 지점에서 path와 query 인자가 string임
- test가 있다는 이유만이 아니라 RPC/client consumer가 있을 때 `AppType`이 export됨
- detached registration이 조용히 타입을 지우지 않음
- 변경된 동작을 `app.request()` 또는 runtime adapter의 동등한 방식으로 request-level test가 검증함
- Public route shape가 바뀌면 typed client 또는 OpenAPI contract check도 갱신됨

## Sources

> Checked 2026-11-04. 아래 RPC·testing 동작은 공식 guide page에서 확인했으며, Hono 4.13 line 밖의 package version은 주장하지 않습니다.

| 주장 | 출처 |
|---|---|
| `testClient()`가 instance에 chaining한 route definition을 요구함 | [Testing Helper](https://hono.dev/docs/helpers/testing) |
| `string` path/query 인자, `.then()` chain의 type 소실, `$path()` / `$url()`, typed `NotFoundResponse`, `hcWithType`, `DetailedError`, version 일치 | [RPC Guide](https://hono.dev/docs/guides/rpc) |
