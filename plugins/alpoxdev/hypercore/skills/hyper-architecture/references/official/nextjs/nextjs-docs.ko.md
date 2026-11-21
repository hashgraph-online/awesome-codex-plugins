# Official Next.js Docs Map

> 이 스킬이 의존하는 공식 문서 표면입니다. 동작이 달라졌거나 규칙이 모호해지면 이 목록을 다시 확인합니다.

Last verified: 2026-11-04 against latest stable Next.js 16.4.5 (`npm dist-tag latest`). 16.4.0은 2026-10-06, 16.3.0은 2026-08-03에 나왔고 16.5는 canary에만 있습니다.

last_verified_at: 2026-11-04

Reader access rule: 공식 문서를 다시 볼 때는 마크다운 대체 경로(`https://nextjs.org/docs/...md`)나 Jina Reader 마크다운(`https://r.jina.ai/https://nextjs.org/docs/...`)을 써서 브라우저 렌더링에 기대지 않고 현재 페이지 텍스트를 읽습니다. 아래에 적은 canonical URL은 원본 출처로 유지합니다.

## Contents

- [Core Sources](#core-sources)
- [Drift Watchlist](#drift-watchlist)
- [Interpretation Rules](#interpretation-rules)
- [Sources](#sources)

## Core Sources

- App Router index
  URL: `https://nextjs.org/docs/app`
  Use for: 현재 App Router 학습 경로와 공식 내비게이션.

- Docs index
  URL: `https://nextjs.org/docs/llms.txt`
  Use for: 권위 있는 페이지 목록과 설치된 문서의 `@doc-version` 표지.

- Project Structure
  URL: `https://nextjs.org/docs/app/getting-started/project-structure`
  Use for: 최상위 폴더, `app` / `pages` / `public` / `src`, route groups, private folders, metadata 관례, 구성 전략.

- File-system Conventions
  URL: `https://nextjs.org/docs/app/api-reference/file-conventions`
  Use for: `page`, `layout`, `loading`, `error`, `not-found`, `forbidden`, `unauthorized`, `route`, `proxy`, metadata 파일, route segment config 같은 special files.

- Server and Client Components
  URL: `https://nextjs.org/docs/app/getting-started/server-and-client-components`
  Use for: Server Component 기본값, `'use client'` 경계, 직렬화 가능한 props, provider 깊이, RSC payload, `server-only` / `client-only` 지침.

- Server and Client Boundary guide
  URL: `https://nextjs.org/docs/app/guides/server-and-client-boundary`
  Use for: Server와 Client Component가 실행되는 위치와 그 경계의 동작.

- Fetching Data
  URL: `https://nextjs.org/docs/app/getting-started/fetching-data`
  Use for: 서버 우선 fetch, 스트리밍, `<Suspense>`, preloading, 클라이언트 fetch 경계.

- Caching
  URL: `https://nextjs.org/docs/app/getting-started/caching`
  Use for: Cache Components, static shell, runtime API 처리, `use cache`, `use cache: private`, `cacheLife`, prerender 임계값, prefetch 동작.

- Revalidating
  URL: `https://nextjs.org/docs/app/getting-started/revalidating`
  Use for: 시간 기반과 on-demand 재검증 진입점.

- Caching and Revalidating (Previous Model)
  URL: `https://nextjs.org/docs/app/guides/caching-without-cache-components`
  Use for: Cache Components를 도입하지 않은 프로젝트의 `fetch` 캐시 옵션, `unstable_cache`, route segment config.

- How Revalidation Works
  URL: `https://nextjs.org/docs/app/guides/how-revalidation-works`
  Use for: 태그 시스템, 캐시 일관성, 다중 인스턴스 조정.

- `use cache`
  URL: `https://nextjs.org/docs/app/api-reference/directives/use-cache`
  Use for: `cacheComponents` 요구, cached scope, cache key, 직렬화 제약, request-time API 제한.

- `use cache: private`
  URL: `https://nextjs.org/docs/app/api-reference/directives/use-cache-private`
  Use for: cached scope 안의 runtime API 접근, 요청 스코프 중복 제거, client 메모리 stale 구간, static shell 제외.

- `use cache: remote`
  URL: `https://nextjs.org/docs/app/api-reference/directives/use-cache-remote`
  Use for: durable shared cache의 tradeoff, `cacheHandlers`, cache key 선택, 중첩 규칙, deploy 사이 유지 한계.

- `cacheComponents`
  URL: `https://nextjs.org/docs/app/api-reference/config/next-config-js/cacheComponents`
  Use for: 두 플래그 활성화, `runtime` export 제한, PPR 기본 동작, `<Activity>` navigation 모델.

- `partialPrefetching`
  URL: `https://nextjs.org/docs/app/api-reference/config/next-config-js/partialPrefetching`
  Use for: App Shell prefetch, `cacheComponents` 의존, 세그먼트별 `prefetch` 재정의.

- Mutating Data
  URL: `https://nextjs.org/docs/app/getting-started/mutating-data`
  Use for: Server Function mutation 흐름과 mutation 진입점.

- Forms
  URL: `https://nextjs.org/docs/app/guides/forms`
  Use for: form에서의 Server Actions, `FormData`, 검증, pending 상태, optimistic update, `useActionState`.

- Server Actions guide
  URL: `https://nextjs.org/docs/app/guides/server-actions`
  Use for: client 순차 dispatch, 단일 응답의 데이터와 UI 모델, 캐시 갱신 선택, CSRF와 body 크기 보호, 배포 시 회전 동작.

- `use server`
  URL: `https://nextjs.org/docs/app/api-reference/directives/use-server`
  Use for: 전용 action 파일, inline Server Functions, auth/authz 기대값.

- `serverActions` config
  URL: `https://nextjs.org/docs/app/api-reference/config/next-config-js/serverActions`
  Use for: `experimental.serverActions.allowedOrigins`, wildcard와 포트 매칭, `Origin` 없는 요청의 경고 경로, `bodySizeLimit`.

- Route Handlers guide
  URL: `https://nextjs.org/docs/app/getting-started/route-handlers`
  Use for: 기본 캐시 동작, Cache Components의 `GET` prerendering 모델, `use cache` 도우미 배치, 특수 metadata handler, route 해석.

- Route Handlers API
  URL: `https://nextjs.org/docs/app/api-reference/file-conventions/route`
  Use for: `route.ts`, HTTP 메서드 export, Web Request/Response API, cookies/headers, promise 형태 dynamic params, `RouteContext`, CORS, webhook, 스트리밍, non-UI 응답.

- Route Segment Config
  URL: `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config`
  Use for: 현재 옵션 표, `runtime`과 `preferredRegion` deprecation, `ensureStatic` 추가, Cache Components에서 v16이 제거한 `dynamic`, `dynamicParams`, `revalidate`, `fetchCache`.

- `ensureStatic`
  URL: `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/ensureStatic`
  Use for: `'auto' | 'shell' | 'prefetch' | 'navigation' | false`, layout 상속, 하위 세그먼트의 엄격한 값만 허용 규칙, parallel slot 일치, `generateStaticParams` 요구.

- `instant`
  URL: `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/instant`
  Use for: Instant Navigation 검증 레벨, `instant = false` opt-out, Navigation Inspector.

- `prefetch` segment config
  URL: `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/prefetch`
  Use for: 세그먼트별 `'partial'`과 `'force-disabled'` 재정의.

- `runtime`
  URL: `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/runtime`
  Use for: Edge Runtime deprecation과 Cache Components의 `runtime` export 금지.

- Proxy
  URL: `https://nextjs.org/docs/app/api-reference/file-conventions/proxy`
  Use for: `proxy.ts`, static matcher 배치, `_next/static` / `_next/image` / public assets negative matching, `_next/data` 예외, Node.js runtime 기본값, `runtime` 옵션 부재, Middleware에서 Proxy로의 이전.

- Environment Variables
  URL: `https://nextjs.org/docs/app/guides/environment-variables`
  Use for: `.env*` 로딩, `NEXT_PUBLIC_`, runtime과 build-time env 동작, `@next/env`.

- Redirecting
  URL: `https://nextjs.org/docs/app/guides/redirecting`
  Use for: redirect 표면, Server Action redirect, `next.config.*` redirect, render 전 redirect 전략.

- Data Security
  URL: `https://nextjs.org/docs/app/guides/data-security`
  Use for: DAL 지침, `server-only`, Server Action 보안, action 내부 auth/authz, 반환값 최소화.

- Authentication
  URL: `https://nextjs.org/docs/app/guides/authentication`
  Use for: 여러 진입점 인증 주의점, Server Action 접근, Proxy의 낙관적 확인, route 보호 패턴.

- Authentication with Cache Components
  URL: `https://nextjs.org/docs/app/guides/authentication-with-cache-components`
  Use for: Cache Components에서 세션 읽기와 세션 파생 데이터 캐시.

- Keeping pages static
  URL: `https://nextjs.org/docs/app/guides/keeping-pages-static`
  Use for: 단계별 `ensureStatic` 예제.

- Optimizing prefetching
  URL: `https://nextjs.org/docs/app/guides/optimizing-prefetching`
  Use for: App Shell과 per-link prefetch 구분, 뒤 단계로 작업 미루기.

- Adopting Partial Prefetching
  URL: `https://nextjs.org/docs/app/guides/adopting-partial-prefetching`
  Use for: `prefetch = 'partial'` 점진 도입과 이전 순서.

- Instant navigation
  URL: `https://nextjs.org/docs/app/guides/instant-navigation`
  Use for: Navigation Inspector 워크플로와 `@next/playwright` 회귀 테스트.

- Preserving UI state
  URL: `https://nextjs.org/docs/app/guides/preserving-ui-state`
  Use for: `<Activity>`의 상태 유지와 navigation에서 초기화되는 UI 패턴.

- Migrating to Cache Components
  URL: `https://nextjs.org/docs/app/guides/migrating-to-cache-components`
  Use for: 레거시 route segment config 교체와 runtime/edge 제거 단계.

- Upgrade with a coding agent
  URL: `https://nextjs.org/docs/app/guides/upgrading/agent-upgrade`
  Use for: `next upgrade --agent`, 버전 일치 `AGENTS.md` 블록, agent feedback 설정.

- `connection`
  URL: `https://nextjs.org/docs/app/api-reference/functions/connection`
  Use for: 실제 사용자 요청 대기와 Cache Components에서 `io()`를 우선하라는 명시.

- `io`
  URL: `https://nextjs.org/docs/app/api-reference/functions/io`
  Use for: 동기 값을 static shell에서 빼면서 cache와 prefetch 가능 상태로 유지하기.

- `navigation`
  URL: `https://nextjs.org/docs/app/api-reference/functions/navigation`
  Use for: App Shell과 per-link prefetch 너머로 작업 미루기.

- `prefetch` function
  URL: `https://nextjs.org/docs/app/api-reference/functions/prefetch`
  Use for: App Shell만 넘어서 작업 미루기.

- `cacheLife`
  URL: `https://nextjs.org/docs/app/api-reference/functions/cacheLife`
  Use for: 프로필 값, prerender 임계값, client cache stale 규칙.

- `cacheTag`
  URL: `https://nextjs.org/docs/app/api-reference/functions/cacheTag`
  Use for: 호출당 tag 수 한도와 tag 길이 한도.

- `updateTag`
  URL: `https://nextjs.org/docs/app/api-reference/functions/updateTag`
  Use for: Server Action에서의 read-your-own-writes 만료.

- `revalidateTag`
  URL: `https://nextjs.org/docs/app/api-reference/functions/revalidateTag`
  Use for: 두 인자 profile 형식, deprecated 단일 인자 형식, Client Component와 Proxy 제한.

- `refresh`
  URL: `https://nextjs.org/docs/app/api-reference/functions/refresh`
  Use for: Server Action에서 현재 route의 RSC payload 다시 받기.

- `catchError`
  URL: `https://nextjs.org/docs/app/api-reference/functions/catchError`
  Use for: `redirect()`와 `notFound()`를 방해하지 않는 컴포넌트 단위 error boundary.

- `error.js`
  URL: `https://nextjs.org/docs/app/api-reference/file-conventions/error`
  Use for: 세그먼트 error boundary와 `retry()` 복구 함수.

- `root-params`
  URL: `https://nextjs.org/docs/app/api-reference/functions/next-root-params`
  Use for: `[lang]` 같은 루트 파라미터를 어떤 Server Component에서도 읽고 `use cache` key에 반영하기.

- `unstable_noStore`
  URL: `https://nextjs.org/docs/app/api-reference/functions/unstable_noStore`
  Use for: 레거시 유지보수 전용. 새 작업은 `io()`와 `connection`으로 안내합니다.

- `authInterrupts`
  URL: `https://nextjs.org/docs/app/api-reference/config/next-config-js/authInterrupts`
  Use for: 실험적 `forbidden` / `unauthorized` 활성화와 프로덕션 위험 검토.

## Drift Watchlist

다음 동작은 의존하기 전에 공식 문서를 다시 확인합니다:

- Cache Components 권장 상태, `cacheComponents` + `partialPrefetching` 조합, 두 플래그의 예정된 제거.
- `use cache`, `use cache: private`, `use cache: remote`, `cacheLife`, `cacheTag`, `updateTag`, `revalidateTag`, `refresh`, `io()`의 의미.
- Route Segment Config 가용성. `ensureStatic`, `instant`, `prefetch`, `runtime`과 `preferredRegion` deprecation, `cacheComponents` 하위의 v16 제거 항목.
- Route Handler `GET` 캐시와 prerender 동작, `use cache` 도우미 배치.
- Proxy의 runtime과 플랫폼 지원, `runtime` 옵션 부재, static matcher 동작, `_next/data` 예외, Middleware 이전 지침.
- Server Action dispatch 순서, 단일 응답 재렌더 동작, origin과 body 크기 설정, action ID 회전.
- 실험적 `authInterrupts`, `forbidden`, `unauthorized`의 stable 전환.

## Interpretation Rules

- 오래된 커뮤니티 습관보다 최신 공식 문서를 우선합니다.
- 새 Next.js 릴리스가 캐시, prerendering, Proxy, Route Handler, Server Action 동작을 바꾸면 `stacks/nextjs/core.md`를 부풀리지 않고 해당 규칙 파일을 고칩니다.
- 로컬 저장소 관례가 문서를 넘어서면 리뷰와 변경 보고에서 로컬 관례라고 표시합니다.
- 이 파일은 문서 지도이며 버전에 민감한 작업에서 공식 문서를 다시 읽는 일을 대신하지 않습니다.

## Sources

> 확인 2026-11-04. 확인했습니다. 버전 기준선은 `next`의 npm `latest` 태그(16.4.5)와 릴리스 피드로, 페이지 목록과 경로는 `https://nextjs.org/docs/llms.txt`로 확인했고, 각 "Use for" 범위는 해당 canonical 페이지에서 읽었습니다.

| 주장 | 출처 |
|---|---|
| 버전 기준선과 릴리스 날짜 | `https://github.com/vercel/next.js/releases`와 `https://www.npmjs.com/package/next` |
| 위 "Core Sources"의 공식 Next.js 표면과 "Use for" 범위 | 각 항목에 적은 canonical `nextjs.org/docs/...` URL |
| 위 "Drift Watchlist"의 drift 민감 동작 | 같은 canonical URL과 `references/official/nextjs/current-docs-2026-11-04.ko.md` |
