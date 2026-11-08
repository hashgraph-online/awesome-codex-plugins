# Route Handlers

> `route.ts`가 맞는 surface인지, 아닌지 판단하는 규칙.

---

## Use Route Handlers For

- webhooks
- feeds
- CORS-sensitive endpoints
- machine-readable public endpoints
- XML, JSON, streams 같은 non-UI content
- method-level handling, headers, status codes, raw body access가 필요한 HTTP-native integrations

## Do Not Default To Route Handlers For

- Server Actions로 충분한 일반 internal form mutations
- Server Components에서 가능한 internal UI data reads
- Proxy가 맡아야 하는 forwarding behavior

mutation이 app UI에서 시작된다면 Server Action을 먼저 가정하고, 실제 요구가 HTTP semantics일 때만 `route.ts`를 정당화합니다.

## Current Facts

- Route Handlers는 App Router에서 사용할 수 있습니다.
- `route.ts` file은 `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, `OPTIONS` 표준 HTTP method exports를 지원합니다.
- Route Handlers는 Web `Request` / `Response` APIs를 사용하며 Next.js helper가 필요할 때 `NextRequest` / `NextResponse`를 사용합니다.
- Dynamic segment `params`는 current App Router examples에서 promise-shaped입니다. 사용 전에 await하거나 typed params에는 global `RouteContext<'/route/[id]'>` helper를 사용합니다.
- Route Handlers는 route segment config를 공유하지만, `cacheComponents`가 활성화된 경우 v16에서 제거된 options(`dynamic`, `dynamicParams`, `revalidate`, `fetchCache`)를 사용하면 안 되고, `runtime` export도 제거해야 합니다.
- previous model에서 Route Handlers는 기본 cached가 아니며 `GET`만 caching opt-in이 가능합니다. 다른 methods는 cached `GET`과 같은 파일에 있어도 cached가 아닙니다.
- Cache Components 활성 상태에서는 `GET` Route Handlers가 UI routes와 같은 prerendering model을 따릅니다. 기본은 request-time이고, uncached/runtime data를 접근하지 않으면 prerender 가능하며, `use cache`가 붙은 helper functions로 cache할 수 있습니다.

## Hard Rules

| 확인 | 규칙 |
|---|---|
| 같은 segment에 `route.ts`와 `page.tsx` 배치 | 차단 |
| UI-only flow에 Route Handler를 default internal RPC로 사용 | HTTP semantics가 필요하지 않으면 차단 |
| Route Handler 안에서 `NextResponse.next()` 사용 | 차단. 해당 behavior는 Proxy 영역 |
| 현재 behavior 확인 없이 오래된 기본값으로 Route Handler caching 가정 | 차단 |
| `use cache`를 extracted helper 대신 Route Handler body 안에 직접 배치 | 차단 |
| current App Router Route Handler examples에서 `params`를 await하지 않고 synchronous하게 사용 | 차단 |
| sitemap, robots, icons, Open Graph images 같은 built-in metadata files를 필요 없이 custom Route Handler로 중복 | 위험도에 따라 경고/차단 |

## Cache and Freshness

- previous caching model에서는 `dynamic = 'force-static'` 같은 explicit route config 또는 문서화된 다른 strategy로만 `GET` handlers를 cache합니다.
- Cache Components 활성 상태에서는 `GET` handlers가 UI-route prerendering model을 따릅니다. `use cache`는 helper functions에 두고 필요하면 `cacheLife` / `cacheTag`를 사용합니다.
- freshness는 `cacheTag`, `revalidateTag(tag, 'max')`, webhook-like immediate expiry용 `revalidateTag(tag, { expire: 0 })`, `revalidatePath` 또는 다른 explicit strategy 중 무엇인지 명시합니다.
- `updateTag`와 `refresh`는 Server Action 전용이므로 webhook Route Handler에서는 쓸 수 없습니다. 즉시 무효화가 필요하면 `revalidateTag(tag, { expire: 0 })`을 씁니다.
- Proxy에서는 `revalidateTag`를 호출할 수 없으므로 webhook이 필요로 하는 cache 무효화는 handler 안에서 실행합니다.
- correctness-critical endpoints에서는 문서화되지 않은 `GET` caching defaults에 의존하지 않습니다.

## Decision Rule

선택 순서:

1. server-rendered UI reads는 Server Component
2. internal UI mutations와 forms는 Server Action
3. genuinely HTTP-native surface일 때만 Route Handler
4. pre-route request boundary behavior는 Proxy

## Review Checklist

- endpoint가 실제로 HTTP semantics를 필요로 함
- `page.tsx` conflict 없음
- method exports와 request/response handling이 명시적임
- 현재 caching behavior를 이해하고 문서화함
- Proxy-specific behavior가 Route Handler로 새지 않음

## Sources

> 확인 2026-11-04. `https://nextjs.org/docs/app/getting-started/route-handlers`, `https://nextjs.org/docs/app/api-reference/file-conventions/route`, `https://nextjs.org/docs/app/api-reference/functions/revalidateTag`, `https://nextjs.org/docs/app/api-reference/functions/updateTag`를 확인했습니다. 날짜가 붙은 스냅숏은 `references/official/nextjs/current-docs-2026-11-04.md`입니다.
