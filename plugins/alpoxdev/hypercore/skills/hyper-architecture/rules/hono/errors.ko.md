# 에러와 응답

> HTTP 실패 처리 중앙화와 응답 의도 보존

---

## Stable Hono 4.13 기준

`app.notFound()`는 top-level app에서만 실행됩니다. Child route의 `onError` handler는 parent handler보다 우선합니다. `HTTPException.getResponse()`는 `Context`에 이미 누적된 header를 알지 못합니다.

- Public error envelope 하나를 정의하고 expected domain failure를 literal HTTP status로 의도적으로 mapping합니다.
- Stack trace, SQL, provider payload, secret, raw validation internal을 노출하지 않습니다.
- Error response를 교체할 때 필요한 CORS, request ID, cache, authentication header를 보존합니다.
- RPC는 global middleware나 `onError()` response를 자동 infer하지 않습니다. Shared global response가 client contract에 포함되면 `ApplyGlobalResponse`를 사용합니다.
- `NotFoundResponse`를 augment하지 않았다면 RPC route의 typed 404 contract를 `c.notFound()`에만 맡기지 않습니다. Route-local typed JSON variant를 반환하거나, module augmentation을 선언해 `c.notFound()`가 응답 type을 싣게 합니다.
- `methodNotAllowed({ app })`를 추가하면 알려진 path에 잘못된 method로 온 요청이 `404`에서 `Allow`가 붙은 `405`로 바뀝니다. 같은 변경에서 RPC status union, OpenAPI response 목록, 이 경우를 not-found로 처리하던 client 분기를 함께 고칩니다.
- Thrown `HTTPException`, unknown error, route-local error handler precedence, top-level 404, 잘못된 method 동작, required header를 test합니다.
## 핵심 규칙

- 예상 가능한 HTTP 실패는 `HTTPException` 또는 명시적 번역 레이어 사용
- 중간 이상 규모 앱은 `app.onError()` 정의
- 에러 응답을 다시 만들 때 `Context`에 세팅한 헤더 보존

## 예시

```ts
import { HTTPException } from 'hono/http-exception'

app.onError((err, c) => {
  if (err instanceof HTTPException) {
    const response = err.getResponse()
    c.res.headers.forEach((value, key) => {
      response.headers.set(key, value)
    })
    return response
  }

  return c.json({ message: 'Internal Server Error' }, 500)
})
```

## Typed 404 Pattern

```ts
import { Hono, TypedResponse } from 'hono'

declare module 'hono' {
  interface NotFoundResponse
    extends Response,
      TypedResponse<{ error: string }, 404, 'json'> {}
}

export const app = new Hono()
  .get('/posts/:id', async (c) => {
    const post = await getPost(c.req.param('id'))
    if (!post) {
      return c.notFound()
    }
    return c.json({ post }, 200)
  })
  .notFound((c) => c.json({ error: 'not found' }, 404))

export type AppType = typeof app
```

Augmentation은 app type 전체에 전역으로 적용됩니다. Export한 app type이 이미 import하는 module 하나에 두고, runtime `.notFound()` handler가 같은 shape를 반환하게 맞춥니다.

## 리뷰 체크리스트

- 필요 시 중앙 에러 번역이 존재
- 에러 응답이 의도한 헤더/상태를 보존
- 예상 가능한 HTTP 에러를 전부 generic throw로 던지지 않음
- Client가 의존하는 typed RPC/public-client 404 동작은 `app.notFound()` 또는 explicit JSON response contract로 검증
- Typed 404는 route-local `c.json(..., 404)`나 단일 `NotFoundResponse` augmentation 중 하나를 쓰고, 서로 다른 shape로 둘을 섞지 않음
- `methodNotAllowed()`를 켰다면 405 결과가 typed client와 OpenAPI response에 나타남

## Sources

> Checked 2026-11-04.

| 주장 | 출처 |
|---|---|
| Top-level `notFound()`, route-level `onError()` 우선순위 | [App API](https://hono.dev/docs/api/hono) |
| `HTTPException.getResponse()`와 `Context` | [HTTPException API](https://hono.dev/docs/api/exception) |
| `NotFoundResponse` augmentation | [RPC Guide](https://hono.dev/docs/guides/rpc) |
| `methodNotAllowed()`가 404를 `Allow` 붙은 405로 바꿈 | [Method Not Allowed Middleware](https://hono.dev/docs/middleware/builtin/method-not-allowed) |
