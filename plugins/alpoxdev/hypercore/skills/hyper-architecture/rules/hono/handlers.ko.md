# 핸들러

> 분리된 핸들러도 타입과 조합 가능성을 유지

---

## Stable Hono 4.13 기준

`createFactory<Env>()`, `factory.createApp()`, `factory.createHandlers()`, `createMiddleware()`는 공식 type-preserving helper입니다. 모든 파일에서 binding/variable을 반복하지 말고 호환되는 `Env` surface마다 factory 하나를 사용합니다.

- `createFactory()`는 `factory.createApp()`이 상속하는 `HonoOptions`를 `defaultAppOptions`로 받을 수 있고(`{ strict: false }` 등), `createApp()`이 만든 app을 초기화하는 `initApp`도 받습니다.
- `createHandlers()`는 handler tuple을 반환하므로 route call에 spread합니다.
- Handler가 `c.req.valid()`를 읽으면 validator middleware와 handler를 같은 typed chain에 둡니다.
- 모든 terminal branch에서 `Response`를 반환하고 RPC client가 status union을 필요로 하면 literal status argument를 사용합니다.
- Service에는 transport-neutral primitive를 전달하며 domain/repository layer로 `Context`를 넘기지 않습니다.
- Route input/output/variable inference를 지우는 넓은 `Context` annotation을 handler에 붙이지 않습니다.
## 핵심 규칙

- 작은 라우트는 inline handler 허용
- 핸들러를 분리할 때는 `createFactory()` / `factory.createHandlers()`로 타입 유지
- Feature module이 자체 typed sub-app 또는 shared factory options를 필요로 하면 `factory.createApp()`을 우선합니다.
- handler 파일은 transport orchestration까지만 담당하고, 도메인 persistence는 아래 레이어로 내립니다

## 권장 패턴

```ts
import { createFactory } from 'hono/factory'

import type { AppEnv } from '@/lib/types'

const factory = createFactory<AppEnv>()

const listUsers = factory.createHandlers(async (c) => {
  return c.json({ users: [] })
})

export const usersApp = factory.createApp().get('/', ...listUsers)
```

## 리뷰 체크리스트

- 분리된 handler가 context typing을 유지함
- 분리된 handler가 `c`, `c.req`, `c.var` typing을 보존함
- Handler module이 `Env` / `Bindings` / `Variables` 정의를 불필요하게 중복하지 않음
- `Variables`, `Bindings`가 암묵적이지 않음
- handler가 giant controller object로 비대해지지 않음
- business logic은 service가 소유

## Sources

> Checked 2026-11-04.

| Claim | Source |
|---|---|
| `createFactory()`, `createApp()`, `createHandlers()`, `defaultAppOptions`, `initApp` | [Factory Helper](https://hono.dev/docs/helpers/factory) |
