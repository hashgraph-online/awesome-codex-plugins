# Data Fetching and Caching

> 서버 우선 읽기, 스트리밍, Cache Components, cache intent, freshness 규칙입니다.

---

## Preferred Read Path

- 가능하면 초기 페이지 데이터는 Server Components에서 가져옵니다.
- 데이터를 쓰는 컴포넌트 가까이에서 읽습니다.
- 독립적인 reads는 병렬화합니다.
- 전체 route를 불필요하게 막지 말고 `loading.tsx` 또는 `<Suspense>`로 스트리밍합니다.
- 반복되는 privileged reads는 server-only helper 또는 DAL에 둡니다.

## Current Runtime Facts

- 현재 App Router docs 기준 `fetch` requests는 기본 cached가 아닙니다. caching은 `cache: 'force-cache'`나 `use cache` scope로 직접 켭니다.
- `fetch`가 있는 route도 여전히 prerender되고 HTML이 cached될 수 있으므로 dynamic/static intent를 명시해야 합니다.
- `cookies()`, `headers()`, `searchParams`, `params`, `connection()` 및 request-time APIs는 해당 work를 runtime-dependent하게 만듭니다.
- Cache Components가 켜진 상태에서는 uncached runtime data를 `<Suspense>` 경계 뒤에 두거나, `io()`로 static shell에서 빼거나, 안전할 때 `use cache`로 명시적으로 cache해야 합니다.
- `io()`는 `new Date()`, `Math.random()`, 동기 드라이버 읽기 같은 동기 값을 static shell에서 빼는 표준 수단입니다. prerendering 중 suspend하고, 실제 요청, cached scope 내부, 브라우저, Cache Components를 쓰지 않는 앱에서는 즉시 resolve하며, 뒤쪽 코드는 cache와 prefetch 대상으로 남습니다.
- `connection()`은 실제 사용자 요청을 기다리므로 prefetch까지 막습니다. 렌더링이 그 요청을 기다려야 할 때만 쓰고 그 외에는 `io()`를 씁니다. `unstable_noStore`는 레거시 전용입니다.
- 동일 read는 request tree 안에서 memoized될 수 있지만 request memoization은 persistent cache policy가 아닙니다.

## Cache Components and `use cache`

Cache Components는 Next.js 16.4부터 App Router 작업의 권장 기본값이고 새 `create-next-app` 앱은 이미 켜져 있습니다. 기존 앱에서 켜는 일은 지나가며 처리할 변경이 아니라 의도적인 마이그레이션입니다.

1. `next.config.*`에서 `cacheComponents: true`와 `partialPrefetching: true` 두 플래그를 켭니다. `partialPrefetching`을 두면 경고가 남고, `cacheComponents` 없이 두면 설정 검증에서 실패합니다.
2. route 파일에서 `runtime` export를 제거합니다. `runtime = 'nodejs'`도 포함합니다.
3. cache 가능한 pages, components, async functions에 `use cache`를 표시합니다.
4. `use cache` input과 return value는 관련 React/Next.js serialization 규칙에 맞게 serializable해야 합니다.
5. normal cached scope 안에서 `cookies()`, `headers()`, `searchParams` 또는 다른 request-time APIs를 읽지 않습니다. 밖에서 읽어 serializable value로 넘깁니다.
6. 모든 `use cache` scope에 `cacheLife`를 짝지어 씁니다. 없으면 암묵 `default` 프로필이 적용되어 call site에서 수명이 보이지 않습니다.
7. invalidation groups에는 `cacheTag`를 씁니다.
8. storage, latency, platform cost를 감수할 가치가 있는 durable shared cache일 때만 `use cache: remote`를 씁니다. cache key에 build identity가 들어가므로 remote 항목은 deploy를 넘기지 못합니다.
9. cached function이 runtime APIs를 읽어야 하고 그 읽기를 밖으로 빼기 어려우면 `use cache: private`을 씁니다. 한 요청 안에서 같은 호출을 중복 제거하고, `stale` 구간 동안 client 메모리 사본을 두며, 요청 사이 server 캐시에는 아무것도 저장하지 않습니다. `use cache: remote`과는 중첩할 수 없습니다.

## Prerendering Thresholds

`cacheLife` 값이 cached 결과를 어디까지 전달할 수 있는지 정합니다:

| 수명 | 전달 지점 |
|---|---|
| `revalidate: 0` 또는 `expire` 5분 미만 | 요청 시점만. dynamic hole로 prerender에서 제외됩니다 |
| `stale` 30초 미만 | prerender에서 제외됩니다. prefetch가 클릭 전에 만료되기 때문입니다 |
| `stale` 30초 이상 5분 미만 | prerender에는 포함되지만 App Shell에서는 제외됩니다 |
| `stale` 5분 이상 | static shell과 per-link prefetch 대상이 됩니다 |

client는 `stale`에 30초 최소값을 강제합니다. Server Action에서 `revalidateTag`, `revalidatePath`, `updateTag`, `refresh`를 호출하면 그 구간을 건너뛰고 client cache 전체가 즉시 비워집니다.

## Navigation Stages

Partial Prefetching에서는 route의 server 출력이 단계로 나뉩니다. 기본 `<Link>`에는 App Shell, `<Link prefetch={true}>`에는 선택적 per-link prefetch, 그리고 navigation 자체입니다.

| 도구 | 무엇에서 빼는가 | 요구 사항 |
|---|---|---|
| `io()` | static shell. 여전히 cache와 prefetch 대상입니다 | suspend하는 subtree 둘레의 `<Suspense>` |
| `prefetch()` | App Shell | Cache Components. 효과를 보려면 Partial Prefetching |
| `navigation()` | App Shell과 per-link prefetch | Cache Components. 효과를 보려면 Partial Prefetching |
| `connection()` | prerendering과 prefetch 전부 | resolve하려면 실제 요청 |
| `ensureStatic = 'shell' / 'prefetch' / 'navigation'` | 해당 단계가 static이도록 build에서 강제 | Cache Components. dynamic route의 `'navigation'`에는 `generateStaticParams` |

`prefetch()`와 `navigation()`은 `use cache`, `use cache: private`, `after()`, `generateStaticParams`, Client Component 안에서 예외를 던집니다. page나 layout이 `prefetch` 세그먼트 설정도 export하면 함수는 다른 이름으로 import해야 합니다.

## Cache and Freshness Rules

| 확인 | 규칙 |
|---|---|
| 캐시 동작을 이해하지 못했거나 변경에 문서화되지 않음 | 차단 |
| request-time APIs 때문에 dynamic rendering이 우발적으로 발생 | 차단 |
| `fetch` caching이 pre-Next.js-16 기본값을 가정 | 차단 |
| `cacheComponents`가 켜졌는데 uncached data에 `use cache`, `io()`, `loading.tsx`, `<Suspense>` 의도가 없음 | 차단 |
| `cacheComponents`를 `partialPrefetching` 없이 켬 | 차단 |
| `use cache` scope에 `cacheLife`가 없고 호출자가 실제 수명을 말할 수 없음 | 차단 |
| `io()`면 cache와 prefetch 가능 상태로 남길 수 있는데 `connection()`을 씀 | 경고. `connection()`은 prefetch를 막습니다 |
| `use cache: remote`를 cost, durability, hit rate 정당화 없이 사용 | 차단 |
| `use cache: private`을 runtime 읽기 이유 없이 쓰거나 `use cache: remote`과 중첩 | 차단 |
| 새 code가 `io()` 또는 `connection()` 대신 `unstable_noStore` 사용 | legacy code 유지보수가 아니면 차단 |
| 반복 privileged logic에 속한 server read가 page code에 직접 존재 | 경고. DAL 또는 server-only helper 권장 |

## Freshness After Mutations

mutation 후 UI에는 명시적 freshness path가 있어야 합니다:

- Server Action read-your-own-writes 시나리오는 `updateTag`. 다음 읽기와 action 응답의 재렌더가 fresh data를 기다립니다
- Server Functions 또는 Route Handlers에서 stale-while-revalidate tag refresh는 `revalidateTag(tag, 'max')`. deprecated single-argument form은 피하고, `updateTag`를 쓸 수 없는 webhook이나 Route Handler에서는 `{ expire: 0 }`을 씁니다
- path-based invalidation은 `revalidatePath`
- tag invalidation 없이 current client router를 refetch해야 할 때는 Server Action 안에서 `next/cache`의 `refresh`
- freshness 작업 뒤 redirect, 또는 명확히 설명된 다른 전략

`updateTag`, `revalidatePath`, `refresh`, cookie 변경, `redirect`는 같은 응답에서 현재 route를 다시 렌더링합니다. stale-while-revalidate 프로필의 `revalidateTag`는 다시 렌더링하지 않으므로 페이지는 이후 읽기에서 변경을 반영합니다.

`redirect()`를 사용하면 이후 code가 실행되지 않으므로 필요한 cache invalidation을 먼저 수행합니다.

## Streaming Guidance

사용 기준:

- segment-level loading state는 `loading.tsx`
- 느리거나 dynamic한 subtree 가까이는 `<Suspense>`
- 동기 읽기를 static shell에서 빼면서 cache 가능 상태로 남겨야 할 때는 `io()`
- incoming request를 의도적으로 기다리는 subtree는 `connection()`
- promise passing + React `use()`는 구조가 더 명확하고 boundary가 유지될 때만

## Official-First Decision Rule

권장 우선순위:

1. 초기 데이터는 Server Component reads
2. 안전하게 재사용 가능한 data/UI는 `use cache` / `cacheTag` / `cacheLife`
3. privileged reads는 server-only helper 또는 DAL
4. Client-side fetching은 client-driven refresh, polling, browser-only state일 때만

## Review Checklist

- 초기 reads가 진짜 client-only 이유 없이 client로 내려가지 않음
- Cache Components, `fetch`, route prerendering 가정이 current docs와 호환됨
- `cacheComponents`와 `partialPrefetching`이 함께 켜져 있음
- 모든 `use cache` scope가 수명을 밝힘
- 고른 navigation 단계가 작업 비용과 맞음
- dynamic rendering triggers가 의도적임
- Suspense 또는 `loading.tsx`가 blocking work 가까이에 있음
- mutation freshness가 명시적이고 재렌더 동작과 맞음

## Sources

> 확인 2026-11-04. `https://nextjs.org/docs/app/getting-started/caching`, `https://nextjs.org/docs/app/api-reference/functions/cacheLife`, `https://nextjs.org/docs/app/api-reference/functions/io`, `https://nextjs.org/docs/app/api-reference/functions/connection`, `https://nextjs.org/docs/app/api-reference/functions/prefetch`, `https://nextjs.org/docs/app/api-reference/functions/navigation`, `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/ensureStatic`, `https://nextjs.org/docs/app/api-reference/directives/use-cache-private`, `https://nextjs.org/docs/app/api-reference/directives/use-cache-remote`를 확인했습니다. 날짜가 붙은 스냅숏은 `references/official/nextjs/current-docs-2026-11-04.md`입니다.
