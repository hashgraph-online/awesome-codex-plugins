# Architecture Rules Reference

> App Router를 기본 모드로 삼는 Next.js 프로젝트용 official-first 통합 규칙입니다.

Brownfield adoption rule: untouched legacy `pages/` code는 자동 실패가 아닙니다. 단, touched code의 safety, boundary, auth, data-leak issue는 즉시 차단합니다.

---

## Project Modes

| Mode | Indicators | Enforcement |
|---|---|---|
| App Router | `app/` 또는 `src/app/` | 전체 skill 적용 |
| Shared Next.js | `pages/` only | shared platform, env, boundary, safety rules만 적용 |
| Mixed | `app/`와 `pages/` 모두 | touched `app/` code에 App Router rules/nextjs 적용; 요청 없는 broad migration 회피 |

---

## 현재 공식 기준선

- App Router에서 Server Components가 기본입니다. interactivity, browser APIs, client hooks가 필요한 client entry point에만 `'use client'`를 추가합니다.
- 최신 App Router docs 기준 `fetch` requests는 기본 cached가 아니지만, routes는 여전히 prerender되고 HTML이 cached될 수 있습니다. cache intent는 명시해야 합니다.
- Next.js 16.4부터 공식 문서는 Cache Components를 모든 App Router 앱의 최선 선택으로 권장하고, 새 `create-next-app` 앱은 이것이 켜진 채 나옵니다. 기존 앱 도입에는 명시적 마이그레이션 이유가 필요합니다.
- Cache Components는 `cacheComponents: true`와 `partialPrefetching: true`로 켭니다. `partialPrefetching`을 두면 경고가 남고, `cacheComponents` 없이 `partialPrefetching`만 두면 설정 검증에서 실패합니다.
- `cacheComponents`는 PPR, `useCache`, `dynamicIO`를 묶는 v16 unified switch입니다. experimental PPR flags와 `experimental_ppr` segment option은 제거되었습니다.
- `cacheComponents`에서는 `dynamic`, `dynamicParams`, `revalidate`, `fetchCache` route segment config options가 제거됩니다. 남는 옵션은 `runtime`(`'edge'` deprecated), `preferredRegion`(deprecated), `maxDuration`이고, pages와 layouts에는 `ensureStatic`이 추가됩니다. `dynamicParams`는 Cache Components 밖에서 그대로 유효합니다.
- `use cache`는 request-time APIs를 직접 읽을 수 없습니다. serializable value를 인자로 넘깁니다. `use cache: private`은 이것들을 읽을 수 있고, 한 요청 안에서 중복을 제거하며, `stale` 구간 동안 client 메모리 사본을 두고, 요청 사이 server에는 아무것도 저장하지 않습니다. `use cache: remote`는 정당화된 durable shared cache용이며 `use cache: private`과 중첩할 수 없습니다.
- 모든 `use cache` scope에는 `cacheLife`를 짝지어 씁니다. 없으면 암묵 `default` 프로필이 적용됩니다.
- Cache Components에서는 `connection()`보다 `io()`를 먼저 씁니다. `io()`는 static shell에서 빠지면서도 cache와 prefetch 대상으로 남고, `connection()`은 실제 사용자 요청을 기다려야 하는 작업에 씁니다. `unstable_noStore`는 레거시 전용입니다.
- `navigation()`과 `prefetch()`(v16.4)는 비용이 큰 작업을 뒤 navigation 단계로 미루고, `ensureStatic`(v16.4)은 static shell, prefetch, navigation 출력을 강제합니다.
- Edge Runtime은 deprecated입니다. `runtime` export를 제거하고, Cache Components에서는 `runtime = 'nodejs'`까지 제거합니다.
- Server Actions는 UI/forms/events에서 호출되는 Server Functions입니다. 모든 action을 reachable POST surface로 보고 내부에서 auth/authz를 재확인합니다.
- Next.js는 client마다 Server Action을 한 번에 하나씩 dispatch하므로 client의 `Promise.all`로 병렬화되지 않습니다. `updateTag`, `revalidatePath`, `refresh`, cookie 변경, `redirect`는 같은 응답에서 현재 route를 다시 렌더링하고, stale-while-revalidate 프로필의 `revalidateTag`는 다시 렌더링하지 않습니다.
- 공식 data-security guidance는 sensitive data에 대해 server-only DAL, authorization checks, minimal DTO를 권장합니다. Server Components는 boundary가 안전하면 ORM/database를 직접 query할 수 있지만, non-trivial logic에는 local architecture가 여전히 DAL을 요구할 수 있습니다.
- `updateTag`는 read-your-own-writes용 Server Action-only API입니다. `revalidateTag`는 Server Functions와 Route Handlers에서 사용할 수 있고 stale-while-revalidate에는 `'max'` 같은 두 번째 인자를 써야 합니다. 단일 인자 form은 deprecated입니다. 둘 다 Client Components와 Proxy에서는 실행되지 않습니다.
- Route Handlers는 HTTP-native endpoints용이며 standard Web `Request`/`Response` APIs와 method exports를 지원합니다. Cache Components에서는 `GET` handlers가 UI routes와 같은 prerendering model을 따르며 `use cache`는 handler body가 아니라 helper에 둬야 합니다.
- 기존 `middleware` convention은 `proxy.ts`로 대체되어 deprecated입니다. Proxy는 last-resort network-boundary 도구이고 Node.js runtime이 기본이며 `runtime` export를 거부하고 static하고 좁은 matcher가 필요합니다.
- `next/error`의 `catchError`(v16.3 stable)는 `redirect()`와 `notFound()`와 공존하는 컴포넌트 단위 error boundary를 제공합니다.
- Cache Components에서 navigation은 React `<Activity mode="hidden">`으로 상태를 유지합니다. 상태는 남고, effect는 숨김 동안 정리되며 다시 보일 때 재생성됩니다.
- Drizzle schema/config/migrations와 connection lifecycle은 독립적인 DB architecture concern입니다. generic services guidance 안에 숨기지 말고 `rules/nextjs/db.md`에 둡니다. `drizzle-orm >= 0.45.2`를 고정하고 여러 브랜치가 schema를 건드리면 `drizzle-kit check`를 돌립니다.

---

## Core Principles

- 로컬 취향보다 공식 Next.js docs를 우선합니다.
- Server Components를 기본값으로 두고 interactive leaf에만 `'use client'`를 추가합니다.
- internal UI mutations와 forms에는 Server Actions를 우선합니다.
- privileged data access는 server-only modules 또는 DAL에 둡니다.
- cache behavior는 우발적이 아니라 의도적으로 만듭니다.
- 모든 Server Action은 외부 도달 가능하다고 보고 내부에서 re-authorize합니다.
- Route Handlers는 HTTP-native concerns에 사용하고 default internal mutation surface로 쓰지 않습니다.
- Proxy는 redirects, rewrites, headers, render-time logic으로 부족할 때만 사용합니다.

---

## Layer Taxonomy

| Layer | Classification | Default responsibility |
|---|---|---|
| `app/` 또는 `src/app/` route segments | Official routing surface | UI routes, layouts, special files, segment-local private folders |
| Server Components | Official rendering/data surface | initial reads, server-rendered UI, 안전한 direct server-only DAL/ORM calls |
| Client Components and hooks | Official client boundary + Hypercore convention | interactivity, browser APIs, UI state, client orchestration only |
| Server Actions | Official mutation surface | validation, auth/authz, DTO return shaping, freshness가 있는 UI-originated writes |
| Route Handlers | Official HTTP endpoint surface | webhooks, feeds, CORS, streams, public machine-readable responses |
| `src/modules/<domain>/<feature>/` | Hypercore local convention | domain feature orchestration, reusable actions/queries/schemas/DTOs |
| `src/services/<domain>/` | Hypercore local convention | service naming을 선호하는 repo의 domain service entrypoints |
| `src/db/<area>/` | Hypercore local convention | Drizzle schema, client, repositories, migrations, transaction helpers |
| `src/server/<area>/` | Hypercore local convention | request/session/server runtime utilities |
| `src/integrations/<provider>/` | Hypercore local convention | external SDK clients, webhook schemas, provider-specific mapping |
| `src/config/<area>/` | Hypercore local convention | env/runtime config, feature flags, deployment config |

`src/modules`, `src/services`, `src/db`, `src/server`, `src/integrations`, `src/config`를 official Next.js requirements로 보고하지 않습니다. ownership과 runtime boundaries를 보이게 하는 Hypercore local folder conventions입니다.

---

## Forbidden

| Category | Forbidden |
|---|---|
| Routing | 같은 route segment의 `page.tsx`와 `route.ts` |
| Client Boundary | 실제 interaction 필요 없는 broad top-level `'use client'` |
| Secrets | Client Components에서 private env, DB clients, server-only modules import |
| Hooks | Client hooks가 Drizzle schema/client, DAL, private env, request APIs, provider secrets import |
| Data Safety | Server Components에서 Client Components로 broad raw records 전달 |
| Services | client-visible boundaries를 넘어 raw DB rows 또는 provider payloads 반환 |
| Drizzle | request lifecycle code에서 migrations 실행 또는 schema/config drift 숨김 |
| Cache Intent | 이유를 이해하지 못한 implicit caching 또는 dynamic rendering 의존 |
| Cache Components | serializable inputs 전달 없이 `use cache` scope 안에서 runtime request APIs 읽기. `use cache: private`은 지원되는 우회로지만, runtime 읽기를 밖으로 빼기 어려울 때만 씁니다 |
| Cache Components | 새 dynamic work에 `io()` 또는 `connection()` 대신 `unstable_noStore` 추가 |
| Cache Components | 새 앱이나 마이그레이션한 앱에서 `partialPrefetching` 없이 `cacheComponents: true`만 두기 |
| Cache Components | `io()`로 충분한데 `connection()`으로 static shell에서 빼기. `connection()`은 prefetch를 막습니다 |
| Server Actions | client input 신뢰, auth/authz 생략, raw internal objects 반환 |
| Server Actions | client에서 `Promise.all`로 Server Action 병렬화. dispatch는 client마다 순차입니다 |
| Server Actions | multi-instance 배포에서 `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY`를 인스턴스마다 다르게 두기 |
| Freshness | 필요한 revalidation/tag update 전 redirect 또는 freshness 누락 |
| Freshness | stale-while-revalidate 프로필의 `revalidateTag`가 action 응답에서 현재 route를 다시 렌더링한다고 가정 |
| Route Handlers | Server Action 또는 Server Component가 맞는데 `route.ts`를 default internal RPC로 사용 |
| Route Handlers | Route Handler 안에서 `NextResponse.next()` 사용 |
| Proxy | `next.config.*` 또는 render-time logic으로 충분한데 `proxy.ts` 추가 |
| Env Setup | `.env*` files가 `src/`에서 load된다고 기대 |

---

## Required

| Category | Required |
|---|---|
| Validation | 편집 전 Next.js mode 확인 |
| Routing | special files를 valid route segments에 배치 |
| Boundaries | Client Components는 좁게, props는 serializable하게 유지 |
| Safety | privileged modules에 `server-only` 또는 명확한 server boundary 사용 |
| Services | Server Actions 또는 delegated server-only services에서 validate, authorize, DTO shaping 수행 |
| Hooks | hooks는 client orchestration only로 유지하고 server/data layers를 넘지 않음 |
| DB | Drizzle client/schema/repositories는 server-only로 유지하고 `drizzle.config.ts` schema/out을 명시 |
| Cache | data/UI가 uncached, `use cache` cached, remote/private cached, tag-revalidated, path-revalidated, refreshed 중 무엇인지 명시 |
| Cache | 모든 `use cache` scope에 명시적 `cacheLife` 프로필이나 inline 값을 짝지음 |
| Cache | `cacheComponents`와 `partialPrefetching`을 함께 켬. `partialPrefetching`만 두면 설정 검증에서 실패 |
| Prerendering | 동기 값을 static shell에서 빼려면 `io()`를 쓰고, 실제 요청을 기다려야 하는 작업에만 `connection()`을 씀 |
| Prerendering | route에 단계적이거나 보장된 static 출력이 필요하면 `navigation()`, `prefetch()`, `ensureStatic`을 의도적으로 씀 |
| Auth | 각 Server Action 또는 delegated server-only layer에서 authentication/authorization 재확인 |
| Platform | env handling, route segment config, Proxy, Next config를 명시적으로 유지 |
| Platform | runtime을 고르지 말고 `runtime` export를 제거. Cache Components에서는 `runtime = 'nodejs'`까지 제거 |
| Platform | proxy나 업로드가 많은 배포에서는 `experimental.serverActions.allowedOrigins`와 `bodySizeLimit`을 확인 |
| Errors | 컴포넌트 단위 복구에는 `catchError`, 실패한 server 작업 재시도에는 `retry()`를 씀 |
| Reporting | repo-local conventions를 framework law가 아닌 convention으로 표시 |
| Shared folders | `src/modules`, `src/lib`, `src/services`, `src/db`, `src/server`, `src/integrations`, `src/config`, `lib`, `services` 아래 new touched shared code는 explicit exception이 없으면 nested domain/provider grouping 사용 |

---

## Decision Order

1. App Router surface, legacy Pages Router surface, mixed repo 중 무엇인가?
2. code가 server-only, client-interactive, shared, cached, request-time dynamic 중 어디에 속하는가?
3. HTML/UI rendering, internal UI mutation, HTTP-native endpoint 중 무엇이 필요한가?
4. read가 uncached인지, `use cache`인지, tag/path revalidated인지, mutation 후 refreshed인지?
5. 작업을 어느 navigation 단계가 맡아야 하는가. App Shell, per-link prefetch, navigation, 실제 요청 중 어디인가?
6. env, Proxy, runtime, route segment config, Server Action origins 같은 deployment-sensitive config에 영향이 있는가?

Default surface order:

1. initial reads와 server-rendered UI는 Server Components
2. internal UI writes와 forms는 Server Actions
3. HTTP-native endpoints는 Route Handlers
4. pre-render network-boundary interception이 정말 필요할 때만 Proxy

---

## Rule Files

- `rules/nextjs/project-structure.ko.md`: touched `src/modules` / `src/services` / `src/db` shared root 아래 direct leaf files 금지 포함
- `rules/nextjs/services.ko.md`
- `rules/nextjs/hooks.ko.md`
- `rules/nextjs/db.ko.md`
- `rules/nextjs/routes.ko.md`
- `rules/nextjs/execution-model.ko.md`
- `rules/nextjs/data-fetching.ko.md`
- `rules/nextjs/server-actions.ko.md`
- `rules/nextjs/route-handlers.ko.md`
- `rules/nextjs/platform.ko.md`
- `references/official/nextjs/current-docs-2026-11-04.ko.md`
- `references/official/nextjs/nextjs-docs.ko.md`
- `references/official/nextjs/drizzle-docs.ko.md`

항상 이 파일부터 읽고, active change를 다루는 가장 작은 rule set만 추가로 읽습니다.
