# Current Official Next.js Docs Snapshot (2026-11-04)

> cache, prerendering, Proxy, route handler, Server Action 동작이 중요한 Next.js 아키텍처 판단에서 오래된 문서 지도보다 먼저 쓰는 공식 문서 스냅숏입니다. 문서 인덱스로 확인한 사실만 담습니다.

checked_at: 2026-11-04
last_verified_at: 2026-11-04
library_id: `/vercel/next.js` at `v16.4.5`
source_priority: 마크다운으로 읽은 official Next.js docs, `https://github.com/vercel/next.js/releases` 릴리스 피드, canonical `https://nextjs.org/docs/...` 페이지.

## Contents

- [Release Baseline](#release-baseline)
- [Current Official Facts](#current-official-facts)
- [Architecture Implications](#architecture-implications)
- [Source URLs Checked](#source-urls-checked)
- [Sources](#sources)

## Release Baseline

| 버전 | 날짜 | 상태 |
|---|---|---|
| 16.4.5 | 2026-11-03 | 최신 stable 패치이며 보안 수정을 포함합니다 |
| 16.4.0 | 2026-10-06 | 모든 앱에 Cache Components를 권장하기 시작한 minor 릴리스입니다 |
| 16.3.0 | 2026-08-03 | Instant Navigations, `io`, `catchError`를 도입한 minor 릴리스입니다 |
| 16.5.0-canary.40 | canary | 채택하지 않습니다. canary 채널에만 있습니다 |

## Current Official Facts

- App Router는 React Server Components 위에서 동작하며 layouts, nested routes, loading 상태, error handling, `page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx`, `not-found.tsx`, `route.ts` 같은 special files를 쓰는 파일 시스템 라우팅입니다.
- App Router에서 pages와 layouts는 기본이 Server Components입니다. interactivity, browser APIs, client hooks가 필요한 client entry point에만 `'use client'`를 붙입니다.
- `src/` 디렉터리는 선택적인 프로젝트 구성이고 `app/`, `pages/`, `public/`은 프레임워크가 정한 의미를 갖습니다. `src/lib`나 `src/services` 같은 공유 폴더는 공식 Next.js 요구 사항이 아니라 저장소 로컬 관례입니다.
- Route groups는 URL 경로를 바꾸지 않고 routes를 묶습니다. `_components`, `_lib` 같은 private folders는 구현 코드를 라우팅에서 빼며 세그먼트 내부 전용 코드에 씁니다.
- Next.js 16.4부터 공식 문서는 Cache Components를 모든 App Router 앱의 최선 선택으로 권장하며, 권장 `create-next-app` 기본값으로 만든 새 앱은 Cache Components와 Partial Prefetching이 이미 켜져 있습니다.
- Cache Components는 `cacheComponents: true`와 `partialPrefetching: true` 두 플래그로 켭니다. `partialPrefetching`을 두면 `false`처럼 동작하고 경고가 남으며, `cacheComponents` 없이 `partialPrefetching`만 두면 설정 검증에서 예외가 납니다. 두 기능은 다음 major 릴리스에서 항상 켜지고 플래그는 제거됩니다.
- Cache Components가 켜지면 `dynamic`, `dynamicParams`, `revalidate`, `fetchCache` route segment 옵션이 제거됩니다. 남는 옵션은 `dynamicParams`(Cache Components를 쓰지 않을 때만), `runtime`(`'edge'` deprecated), `preferredRegion`(deprecated), `maxDuration`이고, pages와 layouts에는 `ensureStatic`(기본 `'auto'`)이 추가됩니다.
- `ensureStatic`은 `'auto' | 'shell' | 'prefetch' | 'navigation' | false`를 받습니다. layout에 걸면 하위 모든 route에 적용되고, 하위 세그먼트는 더 엄격한 값만 쓸 수 있으며, 함께 렌더링되는 parallel slot은 같은 값을 써야 합니다.
- `instant`(`v16.3` stable)는 Instant Navigation 검증을, `prefetch`(`v16.3` stable)는 세그먼트별 prefetch 방식을 `'partial'`과 `'force-disabled'`로 설정합니다. 둘 다 Cache Components가 필요하고 Client Component에서는 export할 수 없습니다.
- `use cache`, `use cache: remote`, `use cache: private`은 서로 다른 캐시 지시자입니다. `use cache`는 `cookies()`, `headers()`, `searchParams`를 읽을 수 없습니다. `use cache: private`은 이것들을 읽을 수 있고, 한 요청 안에서 같은 호출을 중복 제거하며, 결과를 `stale` 구간 동안 client 메모리에 두고, 요청 사이 server 캐시에는 저장하지 않습니다. `use cache: remote`는 remote handler를 쓰고 deploy 사이에 유지되지 않으며 `use cache: private`과 중첩할 수 없습니다.
- 모든 cache 지시자에 `cacheLife`를 짝지어 씁니다. 없으면 암묵 `default` 프로필이 적용됩니다. `revalidate`가 `0`이거나 `expire`가 5분 미만이면 prerender에서 제외되고, `stale`이 30초 미만이면 제외되며, `stale`이 30초에서 5분 사이면 prerender에는 포함되고 App Shell에서는 제외됩니다.
- Cache Components에서는 `connection()`보다 `io()`를 먼저 씁니다. `io()`는 prerendering 중에 suspend하므로 뒤쪽 코드가 static shell에서 빠지면서도 cache와 prefetch 대상이 될 수 있습니다. `connection()`은 실제 사용자 요청을 기다립니다. `unstable_noStore`는 레거시 유지보수용입니다.
- `navigation()`과 `prefetch()`(`v16.4`)는 비용이 큰 작업을 뒤 단계로 미룹니다. `navigation()`은 App Shell과 per-link prefetch에서 모두 빼고, `prefetch()`는 App Shell에서만 뺍니다. 둘 다 `use cache`, `use cache: private`, `after()`, `generateStaticParams`, Client Component 안에서는 예외를 던집니다.
- Edge Runtime은 deprecated입니다. route 파일에서 `runtime` export를 제거합니다. Cache Components에서는 `runtime = 'nodejs'`까지 제거합니다. Cache Components는 Node.js runtime을 요구하고 `runtime` 세그먼트 설정을 받지 않습니다.
- Server Actions는 외부에서 닿는 POST 표면입니다. Next.js는 client마다 한 번에 하나씩 dispatch하므로 client의 `Promise.all`로 병렬화되지 않습니다. `updateTag`, `revalidatePath`, `refresh`, cookie 변경, `redirect`는 같은 응답에서 현재 route를 다시 렌더링하고, stale-while-revalidate 프로필의 `revalidateTag`는 다시 렌더링하지 않습니다.
- `updateTag`와 `refresh`는 Server Action 전용입니다. `revalidateTag`는 Server Functions와 Route Handlers에서 동작하고 Client Components와 Proxy에서는 호출할 수 없으며 `'max'` 같은 두 번째 인자를 받습니다. 단일 인자 형식은 deprecated이고 `{ expire: 0 }`처럼 동작합니다.
- `experimental.serverActions` 아래에 `allowedOrigins`와 `bodySizeLimit`(기본 1MB)이 있습니다. origin은 `x-forwarded-host` 또는 `host`와 비교하고, `*`는 한 라벨, `**`는 한 개 이상 라벨과 맞으며, `Origin` 헤더가 없는 요청은 경고와 함께 통과합니다.
- action ID는 최대 14일마다 회전하므로 이전 build의 client는 "Failed to find Server Action"을 만날 수 있습니다. 인스턴스 사이에서 `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY`를 고정하고 rolling deploy를 씁니다.
- `next/error`의 `catchError`는 `v16.3`에서 stable이 되었고 `redirect()`와 `notFound()`를 방해하지 않는 컴포넌트 단위 error boundary를 제공합니다. `error.tsx`도 `retry()`를 받습니다.
- Route Handlers는 `GET`, `POST`, `PUT`, `PATCH`, `DELETE` 같은 HTTP 메서드 export를 씁니다. Cache Components에서 `GET` handler는 UI route와 같은 prerendering 모델을 따르고, `use cache`는 handler body가 아니라 도우미 함수에 둡니다.
- `NextResponse.next()`는 Route Handler 안에서 유효하지 않고 Proxy식 요청 이어가기에 속합니다.
- Next.js 16은 기존 `middleware` 파일 관례를 deprecated로 두고 `proxy.ts` / `proxy.js`를 씁니다. Proxy는 project root 또는 `src/` root에 둘 수 있고 Node.js runtime이 기본이며 `runtime` 설정을 받지 않고, static하고 좁은 matcher를 써야 하며, negative matcher로 제외해도 `_next/data`에는 실행되고 `revalidateTag`를 호출할 수 없습니다.
- 환경 변수는 project root의 `.env*` 파일에서 읽고 `src/`에서는 읽지 않습니다. browser 코드에는 `NEXT_PUBLIC_` 변수만 포함되고 공개 값은 build 시점에 inline됩니다.
- `next/root-params`(`v16.3`)는 `[lang]` 같은 루트 파라미터를 어떤 Server Component에서도 읽게 하고, `use cache` key에는 실제로 읽은 root param만 반영됩니다. 현재는 Server Components로 제한됩니다.
- `next upgrade --agent`는 에이전트에 버전별 업그레이드 지침을 주고, `next dev`는 버전에 맞는 `AGENTS.md` 블록을 유지하며, `experimental.agentUpgrade` 기본값은 `'security'`입니다.
- `next build`는 TypeScript 7 CLI(`useTypeScriptCli`)로 타입 검사를 할 수 있고, 프로젝트의 `typescript` 의존성을 `^7`로 올리면 켜집니다.
- React 19.3은 View Transitions를 stable로 두고, `react-dom`의 `browser()`와 Context 직접 렌더링을 제공합니다. Server Component가 `'use client'` 모듈에서 Context 객체를 import해 별도 provider 컴포넌트 없이 렌더링할 수 있습니다.
- Cache Components에서 navigation은 React `<Activity mode="hidden">`으로 상태를 유지합니다. 컴포넌트 상태는 남고, route가 숨겨질 때 effect가 정리되며 다시 보일 때 재생성됩니다.

## Architecture Implications

- `src/lib/<domain>/`과 `src/services/<domain-or-provider>/`는 Hypercore/저장소 로컬 관례로 취급합니다. ownership과 runtime 경계를 드러내는 데는 유용하지만 공식 Next.js 법칙은 아닙니다.
- 손댄 공유 root에 `src/lib/foo.ts`나 `src/services/foo.ts` 같은 direct leaf file을 새로 만들지 않습니다. 프로젝트가 명시적 예외를 기록한 경우만 다릅니다.
- 초기 읽기는 Server Components, 내부 UI 쓰기는 Server Actions, HTTP-native endpoint는 Route Handlers, render 전 가로채기는 마지막 수단으로만 Proxy를 고릅니다.
- Cache Components는 새 작업의 권장 기본값입니다. 기존 앱 도입에는 명시적 마이그레이션 이유와 두 플래그 설정을 같은 변경에 담아야 합니다.
- Server Action 병렬 dispatch를 전제로 client 흐름을 설계하지 않고, navigation 사이 상태 보존을 unmount 기준으로 가정하지 않습니다.

## Source URLs Checked

- `https://nextjs.org/docs/llms.txt`
- `https://nextjs.org/blog/next-16-4`
- `https://nextjs.org/blog/next-16-3`
- `https://nextjs.org/docs/app/getting-started/caching`
- `https://nextjs.org/docs/app/api-reference/config/next-config-js/cacheComponents`
- `https://nextjs.org/docs/app/api-reference/config/next-config-js/partialPrefetching`
- `https://nextjs.org/docs/app/api-reference/config/next-config-js/serverActions`
- `https://nextjs.org/docs/app/api-reference/directives/use-cache`
- `https://nextjs.org/docs/app/api-reference/directives/use-cache-remote`
- `https://nextjs.org/docs/app/api-reference/directives/use-cache-private`
- `https://nextjs.org/docs/app/api-reference/functions/cacheLife`
- `https://nextjs.org/docs/app/api-reference/functions/io`
- `https://nextjs.org/docs/app/api-reference/functions/connection`
- `https://nextjs.org/docs/app/api-reference/functions/navigation`
- `https://nextjs.org/docs/app/api-reference/functions/prefetch`
- `https://nextjs.org/docs/app/api-reference/functions/revalidateTag`
- `https://nextjs.org/docs/app/api-reference/functions/updateTag`
- `https://nextjs.org/docs/app/api-reference/functions/refresh`
- `https://nextjs.org/docs/app/api-reference/functions/catchError`
- `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config`
- `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/ensureStatic`
- `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/instant`
- `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/prefetch`
- `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/runtime`
- `https://nextjs.org/docs/app/api-reference/file-conventions/route`
- `https://nextjs.org/docs/app/api-reference/file-conventions/proxy`
- `https://nextjs.org/docs/app/guides/server-actions`
- `https://nextjs.org/docs/app/guides/environment-variables`
- `https://nextjs.org/docs/app/guides/data-security`
- `https://nextjs.org/docs/app/api-reference/functions/next-root-params`
- `https://nextjs.org/docs/app/guides/upgrading/agent-upgrade`
- `https://nextjs.org/docs/app/api-reference/config/next-config-js/useTypeScriptCli`
- `https://react.dev/blog/2026/09/09/react-19-3`

## Sources

> 확인 2026-11-04. 확인했습니다. 위 사실은 "Source URLs Checked"에 적은 `nextjs.org/docs` 마크다운, 릴리스 글, React 19.3 글에서 읽었고, 버전 기준선은 `next`의 npm `latest` 태그로 확인했습니다.

| 주장 | 출처 |
|---|---|
| 위 "Release Baseline"의 버전 기준선 | `https://github.com/vercel/next.js/releases`와 `https://nextjs.org/docs/llms.txt`(`@doc-version: 16.4.5`) |
| 위 "Current Official Facts"의 프레임워크 사실 | "Source URLs Checked"에 나열한 `https://nextjs.org/docs/...` 페이지 |
| 마지막 두 사실의 React 동작 | `https://react.dev/blog/2026/09/09/react-19-3` |
| 위 "Architecture Implications"의 아키텍처 함의 | 같은 공식 페이지. `src/lib` / `src/services` 명명은 공식 요구 사항이 아니라 Hypercore/저장소 로컬 관례입니다 |
