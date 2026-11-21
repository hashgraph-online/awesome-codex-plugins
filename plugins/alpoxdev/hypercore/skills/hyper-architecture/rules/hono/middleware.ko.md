# 미들웨어

> 요청 경계와 공통 관심사에 대한 미들웨어 규칙

---

## Stable Hono 4.13 기준

Middleware는 등록 순서에 따라 onion 방식으로 실행됩니다. `await next()` 전 코드는 바깥에서 안쪽으로, 이후 코드는 안쪽에서 바깥으로 실행되며 middleware는 `Response`를 early return할 수 있습니다. Chained `.use()`는 뒤 handler가 사용하는 typed `Variables`를 누적합니다.

권장 순서는 명시적 project contract이며 보통 request ID/observability, CORS 또는 security header, authentication, authorization, validation, handler입니다. 모든 downstream response를 감쌀 의도가 있을 때만 `await next()` 뒤에서 response를 변경합니다.

- Middleware를 path 또는 sub-app으로 scope하며 feature-only authorization을 global로 만들지 않습니다.
- 보장된 request-scoped value에는 typed `Variables` 또는 `createMiddleware<Env>()`를 사용합니다.
- Global `ContextVariableMap` augmentation은 모든 consuming app에서 실제 보장되는 값에만 사용합니다. Local typed chaining이 더 안전합니다. 이는 Hypercore 취향이 아니라 공식 guide입니다. Context API는 `ContextVariableMap`이 해당 변수를 설정하는 middleware가 실제로 실행됐는지와 무관하게 모든 context에 type을 전역으로 추가한다고 적고 있습니다. 그래서 값이 `undefined`인 handler에서도 `c.get()`이 type-safe해 보입니다.
- Request state를 module global에 저장하거나 `Context`를 request 사이에서 재사용하지 않습니다.
- 특히 Deno 같은 URL-import runtime에서는 Hono core와 middleware package version compatibility를 유지합니다.
## 핵심 규칙

미들웨어는 auth, request ID, CORS, logging, context enrichment처럼 요청 전반의 관심사를 명시하는 경계입니다.

Middleware가 variables를 설정하거나 bindings에 의존하면 `createMiddleware()` 같은 typed helper로 reusable middleware를 추출합니다.

## 비타협 규칙

| 확인 항목 | 규칙 |
|------|------|
| 미들웨어 순서를 잘못 가정 | 차단 |
| 공통 요청 관심사를 handler마다 복붙 | 경고 |
| `c.set()` 값을 typed `Variables` 없이 사용 | 차단 |
| `Context`로 요청 간 상태를 유지한다고 가정 | 차단 |
| App-wide middleware가 보장하지 않는 값에 global `ContextVariableMap` 사용 | 차단 |

## Typed Middleware Pattern

```ts
import { createMiddleware } from 'hono/factory'

import type { AppEnv } from '@/lib/types'

export const authMiddleware = createMiddleware<AppEnv>(async (c, next) => {
  const user = await resolveUser(c.req)
  c.set('user', user)
  await next()
})
```

## 리뷰 체크리스트

- 등록 순서가 의도적임
- 공통 관심사가 중앙화됨
- context variable이 타입화됨
- middleware가 숨은 business-logic layer가 되지 않음
- request-scoped context value가 이를 읽는 handler보다 먼저 설정됨

## Sources

> Checked 2026-11-04.

| 주장 | 출처 |
|---|---|
| 등록 순서, onion 실행, typed variable 누적 | [Middleware Guide](https://hono.dev/docs/guides/middleware), [Routing API](https://hono.dev/docs/api/routing) |
| Middleware 실행 여부와 무관하게 `ContextVariableMap`이 type을 전역 적용함 | [Context API](https://hono.dev/docs/api/context) |
