# Middleware

> validation, context 전파, client-to-server 데이터 전달을 위한 middleware 규칙

---

## Rule Classifications

| Rule | Classification | Enforcement |
|---|---|---|
| Request middleware는 default로 `createMiddleware()` 사용 | Official | request middleware에 function-only syntax를 강제하지 않음 |
| Server function middleware는 `createMiddleware({ type: 'function' })` 사용 | Official | `.client(...)`, `.validator(...)`, server-function-only behavior가 쓰이면 잘못된 middleware type 차단 |
| Server function middleware validation은 `.validator(...)` 사용 | Official | `.inputValidator(...)` 차단. 1.169.0에서 제거됐고, middleware와 server-function validation chain은 개념적으로 분리 |
| `sendContext`는 명시적이며 자동 전송 아님 | Official | trust 전 validation |
| client-provided context를 server-side 검증 | Safety policy | unvalidated trust 차단 |
| session 주체는 서버가 신뢰하는 출처에서 얻고 `sendContext`에서는 얻지 않음 | Safety policy | 클라이언트가 보낸 값으로 권한을 판단하지 않음 |
| shared auth/logging/tenant logic 중앙화 | Hypercore convention | touched code에서 warn/fix |

---

## 핵심 규칙

Middleware는 단순 auth 용도가 아닙니다. request context, validation, logging, server-safe 데이터 전파를 명시적으로 처리하는 경계입니다.

TanStack Start에는 두 middleware type이 있습니다:

- Request middleware: `createMiddleware()` 또는 `createMiddleware({ type: 'request' })`. Server requests, server routes, SSR, server functions에 적용되며 `.server(...)`만 가집니다.
- Server function middleware: `createMiddleware({ type: 'function' })`. `createServerFn` middleware chain용이며 `.client(...)`, `.server(...)`, `.validator(...)`를 사용할 수 있습니다.

---

## 비타협 규칙

| 확인 항목 | 규칙 |
|------|------|
| Request middleware가 function-only behavior를 사용함? | 차단. `createMiddleware({ type: 'function' })` 사용 |
| Server function middleware validation을 `.inputValidator(...)`로 작성함? | BLOCKED. 별칭은 1.169.0에서 `createMiddleware`에서 제거됐고 `.validator(...)`가 유일한 표기입니다 |
| 클라이언트에서 `sendContext`로 보낸 동적 데이터를 서버에서 검증 없이 사용함? | 차단 |
| shape validation을 통과했다는 이유로 `sendContext` 값을 권한 판단으로 사용함? | 차단. 파싱된 식별자는 형식이 맞을 뿐 권한이 증명된 것이 아니므로 session 주체의 접근 권한을 별도로 확인합니다 |
| `next({ context: ... })` 대신 암묵적으로 context를 변형함? | 차단 |
| 공통 auth/logging/tenant 로직을 middleware 대신 각 handler에 중복함? | 경고. middleware 우선 |

---

## 허용 패턴

- server function middleware가 데이터 변환 또는 검증을 책임질 때 `.validator(...)`를 사용합니다
- Middleware `.validator(...)`와 server-function `.validator(...)`를 혼동하지 않습니다. method name은 같지만 서로 다른 chain 객체입니다.
- `next({ context: { ... } })`로 context를 확장합니다
- client middleware의 `sendContext`는 서버에 정말 필요한 데이터만 전송합니다
- 클라이언트가 보낸 `sendContext`는 서버에서 반드시 검증 후 신뢰합니다
- global request middleware는 `src/start.ts`에서 `createStart(() => ({ requestMiddleware: [...] }))`로 설정합니다
- global request middleware 배열에 CSRF 보호를 넣을 때는 `filter: (ctx) => ctx.handlerType === 'serverFn'`으로 server function에 한정합니다. filter 없는 기본값은 middleware가 처리하는 모든 request(SSR page request, server route 포함)를 검증합니다
- route guard는 data authorization 경계가 아닙니다. `beforeLoad`와 middleware가 page 접근을 막을 수는 있지만, server function이나 server route가 돌려주는 값은 session 주체에 대한 자체 검사를 거쳐야 합니다

---

## `sendContext` 보안 규칙

클라이언트 context는 자동으로 신뢰할 수 없습니다. 클라이언트가 보낼 수 있는 값은 클라이언트가 거짓으로 보낼 수도 있으므로, `sendContext`로 도착한 값은 type이 아무리 잘 맞아도 클라이언트가 통제하는 데이터입니다.

> **Shape validation is not authorization.** 파싱된 UUID나 숫자는 형식이 맞는 식별자일 뿐 권한이 증명된 식별자가 아닙니다. (Official)

Safety policy: 그 값이 어떤 행을 읽거나 쓸지 선택할 때(쿼리 키, 필터, path parameter)는 session 주체가 그 값에 접근할 권한이 있는지 별도로 확인합니다. 그러지 않으면 로그인한 사용자가 자기 요청에서 값을 바꿔 다른 tenant의 데이터에 도달합니다. session 자체는 항상 서버가 신뢰하는 출처(`authMiddleware`의 cookie + DB 조회)에서 얻고 `sendContext`에서는 얻지 않습니다.

잘못된 예:

```ts
const requestLogger = createMiddleware({ type: 'function' })
  .client(async ({ next, context }) => {
    return next({
      sendContext: {
        workspaceId: context.workspaceId,
      },
    })
  })
  .server(async ({ next, context }) => {
    // 클라이언트 통제 값: 호출자가 이 workspace를 써도 된다는 증명이 없습니다.
    useWorkspace(context.workspaceId)
    return next()
  })
```

올바른 예:

```ts
const authMiddleware = createMiddleware({ type: 'function' }).server(
  async ({ next }) => {
    // session은 서버가 신뢰하는 출처에서 얻고 sendContext에서는 얻지 않습니다.
    const session = await db.session.findByToken(getCookie('session'))
    if (!session) throw new Error('Unauthorized')
    return next({ context: { session } })
  },
)

const workspaceGuard = createMiddleware({ type: 'function' })
  .middleware([authMiddleware])
  .client(async ({ next, context }) => {
    return next({
      sendContext: {
        // 클라이언트가 보낼 수 있지만 이는 힌트이며 권한이 아닙니다.
        workspaceId: context.workspaceId,
      },
    })
  })
  .server(async ({ next, context }) => {
    const workspaceId = zodValidator(z.string()).parse(context.workspaceId)
    // 형식이 맞는 것과 접근이 허용되는 것은 다릅니다: session의 권한을 확인합니다.
    await assertWorkspaceAccess(context.session, workspaceId)
    useWorkspace(workspaceId)
    return next()
  })
```

---

## 리뷰 체크리스트

- Request middleware는 function-only feature가 필요하지 않으면 `createMiddleware()`를 사용
- Server function middleware는 `createMiddleware({ type: 'function' })`를 사용
- Server function middleware는 middleware-owned data validation에 `.validator(...)`를 사용
- 공통 request 로직이 middleware에 중앙화됨
- `sendContext`가 최소화되어 있고 서버에서 검증됨
- session 주체는 서버가 신뢰하는 출처에서 얻고 `sendContext`에서는 얻지 않음
- Context 확장이 명시적이고 typed 되어 있음

## Sources

> 출처 확인 2026-11-04: <https://tanstack.com/start/latest/docs/framework/react/guide/middleware.md>(middleware 종류, `sendContext`, "shape validation is not authorization", CSRF `filter`, middleware `handlerType`), <https://tanstack.com/start/latest/docs/framework/react/guide/authentication-server-primitives.md>("A route guard is not a data authorization boundary."), <https://tanstack.com/start/latest/docs/framework/react/migrate-from-release-candidate.md>(`.inputValidator()` 제거). 그 밖의 공식 TanStack 동작은 이 패키지 자체의 snapshot(`references/official/tanstack-start/tanstack-start-2026-11-04.md`, `references/official/tanstack-start/tanstack-router-2026-11-04.md`, `references/official/tanstack-start/current-docs-2026-11-04.md`, 공식 사실 검증일 2026-11-04)에 위임합니다. 저장소 로컬 링크 확인 2026-11-04.
