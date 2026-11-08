# Server Routes

> TanStack Start server route는 공식 HTTP endpoint 기능입니다. hypercore는 실제 HTTP semantics가 있을 때 사용합니다.

## Rule Classifications

| Rule | Classification | Enforcement |
|---|---|---|
| `createFileRoute(... )({ server })`로 정의하는 server route | Official | 허용 |
| simple handlers는 `server.handlers`, composed handlers는 `createHandlers` function 사용 | Official | 현재 handler shape 사용 |
| Route-level middleware는 `server.middleware`로 선언 가능 | Official | 모든 handler가 request behavior를 공유할 때 적용 |
| webhook/file/health/auth/public machine endpoint | Official + Hypercore convention | justification 있으면 허용 |
| duplicate route path + HTTP method handlers | Official | collision 차단 |
| internal app RPC를 server route로 구현 | Hypercore convention | server function 선호 |
| 검증 없는 request body 신뢰 | Safety policy | trust 전 validation |
| 반환 response를 조용히 덮어쓰는 response helper | Official | 모순되는 status/cookie 처리 차단 |

## Current Server Route Shape

Server routes는 TanStack Router file-route convention을 따릅니다. `createFileRoute(...)(...)`에 `server` property가 있으면 API route가 됩니다.

Simple handlers는 `server.handlers` object를 사용합니다:

```ts
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/hello')({
  server: {
    handlers: {
      GET: async ({ request }) => {
        return new Response('Hello, World! from ' + request.url)
      },
    },
  },
})
```

Handlers에 middleware composition이 필요하면 current server-routes guide의 `createHandlers` function form을 사용합니다. 동일 route-level middleware가 모든 handlers에 적용되어야 하면 `server.middleware`를 사용합니다.

같은 resolved route path에 duplicate methods를 만들지 않습니다. `users.ts`와 `users.index.ts` 같은 file-route variants는 같은 API route로 resolve될 수 있으며 duplicate HTTP methods는 invalid입니다. wildcard/splat server routes는 `routes/file/$.ts`처럼 trailing `$` convention을 사용합니다.

## Response Helper 우선순위

`setResponseStatus`, `setResponseHeader`, `setCookie`, `appendResponseHeader` 같은 helper로 응답을 쓰면 반환하거나 throw한 `Response`와 조용히 어긋날 수 있습니다. 손댄 handler에서 다음은 차단 대상입니다 (Official):

| 패턴 | 결과 | 올바른 형태 |
|---|---|---|
| `setResponseStatus(401)` 뒤에 `return new Response(body, { status: 200 })` | `401`이 나감. helper가 이깁니다 | 한 채널만 씁니다. status를 helper로 정하고 body만 담은 response를 반환하거나, helper를 빼야 합니다 |
| `setResponseHeader('set-cookie', cookie)` | 나가는 **모든** cookie를 대체합니다. 다른 helper가 설정한 cookie도 사라집니다 | cookie 하나면 `setCookie(...)`, 추가하려면 `appendResponseHeader('set-cookie', cookie)` |
| serialized server-function 응답에 helper로 `setResponseStatus(204)` / `205` / `304` | 무시됩니다 | 해당 status의 `Response`를 반환합니다 |
| serialized server-function 응답에 helper `Location` | 직렬화되지 않습니다 | `redirect()`를 씁니다 |
| `setResponseStatus`에 `200`-`599` 밖의 code | 무시되고 production이 아닐 때 경고가 납니다 | 실제 HTTP status를 씁니다 |

handler를 일찍 걸러내는 request 수준 사실입니다 (Official):

- `getRequestHeader(name)`은 header가 존재하지만 비어 있으면 `''`, 없을 때만 `undefined`를 반환합니다. `if (!header)`로 판단하지 말고 `=== undefined`로 확인합니다.
- percent-encoding이 잘못된 path는 server entry와 middleware가 실행되기 전에 `400 Bad Request`가 되므로 handler까지 오지 않습니다.
- function middleware가 context를 보내지 않으면 `sendContext`는 `{}`가 아니라 `undefined`입니다.

Start handler에서 잡히지 않은 error는 이제 `400`-`599`(기본 `500`) status의 일반 JSON body가 되고 message나 stack을 그대로 드러내지 않습니다. 특정 error payload가 필요한 endpoint는 throw하지 말고 `Response`를 반환합니다. throw한 `Response`는 body와 metadata를 유지하지만 `HEAD` request와 status `204`, `205`, `304`에서는 body가 빠집니다.

## Typed Request Context

`@tanstack/react-router`의 `Register` interface에 `server.requestContext`를 등록하면 `handler.fetch(request, { context })`가 받는 per-request context에 type이 붙습니다. 등록은 type만 정하고 값을 만들지는 않습니다. context는 global middleware, request/function middleware, server route, server function, router 전체에서 보입니다.

```ts
declare module '@tanstack/react-router' {
  interface Register {
    server: {
      requestContext: { requestId: string }
    }
  }
}
```

## Allowed Uses

단순 app-internal RPC가 아니라 HTTP semantics가 있을 때 server route를 사용합니다:

- Third-party webhook.
- Auth provider callback 또는 required auth endpoint.
- Health/readiness endpoint.
- File upload/download 또는 wildcard HTTP handler.
- `robots.txt`, `sitemap.xml`, LLMO/metadata endpoint.
- Public machine-readable resource.

## Prefer Server Functions For

- React component 또는 route loader가 소비하는 app read/mutation.
- End-to-end typing과 server function middleware가 유리한 internal RPC.
- TanStack Query invalidation pattern을 공유해야 하는 operation.

## Validation Checklist

- [ ] 새 server route마다 HTTP justification이 있음.
- [ ] Simple server routes는 `server.handlers` object를 사용하고, composed handlers는 current `createHandlers` function form을 사용함.
- [ ] `server.middleware`는 모든 handler가 공유하는 route-level behavior에만 사용함.
- [ ] Duplicate route path + HTTP method collision을 확인함.
- [ ] Wildcard/splat routes는 필요할 때 trailing `$` file-route convention을 사용함.
- [ ] request body, params, headers, client-sent context를 trust 전에 검증함.
- [ ] user가 HTTP endpoint를 명시 요청하지 않았다면 internal app RPC는 server function을 사용함.
- [ ] 필요한 경우 route/handler level middleware가 적용됨.

## Sources

> 출처 확인 2026-11-04: <https://tanstack.com/start/latest/docs/framework/react/guide/server-routes.md>(`handlers`, `createHandlers`, route-level `middleware`), <https://tanstack.com/start/latest/docs/framework/react/guide/server-entry-point.md>(error 처리, `server.requestContext`), <https://tanstack.com/start/latest/docs/framework/react/migrate-from-release-candidate.md>(response helper 우선순위, `set-cookie` 대체, error status 범위). 그 밖의 공식 TanStack 동작은 이 패키지 자체의 snapshot(`references/official/tanstack-start/tanstack-start-2026-11-04.md`, `references/official/tanstack-start/tanstack-router-2026-11-04.md`, `references/official/tanstack-start/current-docs-2026-11-04.md`)에 위임합니다. 공식 사실 검증 2026-11-04. 저장소 로컬 링크 확인 2026-11-04.
