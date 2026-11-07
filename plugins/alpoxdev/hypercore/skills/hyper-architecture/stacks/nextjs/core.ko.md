`hyper-architecture`의 Next.js 스택 가이드입니다. `rules/stack-detection.ko.md`가 대상을 Next.js로 라우팅하면 이 파일을 읽고, 이 파일이 그 대상의 작업을 맡습니다.

- 범위: 기존 Next.js 프로젝트를 점검하거나 고치거나 확장할 때 사용합니다. 특히 App Router 작업이나 App Router 마이그레이션에서 Server/Client 경계, 데이터와 캐시 최신성, mutation, Route Handler, Proxy, env와 플랫폼 설정, 공유 폴더 배치를 건드리는 경우가 대상입니다. 현재 공식 Next.js 동작과, 그와 구분해 표시한 Hypercore 관례를 함께 강제합니다. 일반 React 아키텍처, Remix나 TanStack Start 프로젝트, 아키텍처 경계를 건드리지 않는 문구만 고치는 편집에는 쓰지 않습니다.
- 실행 조건: Next.js 애플리케이션에서 저장소를 살펴보고 공식 Next.js 문서를 확인하며 직접 코드를 고칠 때 가장 잘 맞습니다.

@architecture-rules.ko.md
@../../rules/nextjs/routes.ko.md
@../../rules/nextjs/project-structure.ko.md
@../../rules/nextjs/execution-model.ko.md
@../../rules/nextjs/data-fetching.ko.md
@../../rules/nextjs/server-actions.ko.md
@../../rules/nextjs/route-handlers.ko.md
@../../rules/nextjs/services.ko.md
@../../rules/nextjs/hooks.ko.md
@../../rules/nextjs/db.ko.md
@../../rules/nextjs/platform.ko.md
@../../rules/nextjs/validation.ko.md
@../../references/official/nextjs/current-docs-2026-11-04.ko.md
@../../references/official/nextjs/nextjs-docs.ko.md
@../../references/official/nextjs/drizzle-docs.ko.md

# Next.js Architecture Enforcement

<output_language>

사용자에게 보이는 결과물, 저장하는 산출물, 보고서, 계획, 생성 문서, 요약, 핸드오프 노트, 커밋 메시지 초안, 검증 노트는 이 표준 파일이 영어로 쓰여 있어도 기본적으로 한국어로 작성합니다.

소스 코드 식별자, CLI 명령, 파일 경로, 스키마 키, JSON/YAML 필드 이름, API 이름, 패키지 이름, 고유명사, 인용한 원문은 원래 표기를 유지합니다.

사용자가 다른 언어를 명시적으로 요청했거나, 기존 산출물이 일관성을 위해 다른 언어를 유지해야 하거나, 기계가 읽는 계약이 정확한 영어 토큰을 요구할 때만 다른 언어를 씁니다. 번역본 템플릿이나 참고 자료가 있으면(예: `*.ko.md`, `*.ko.json`) 사용자에게 보이는 산출물에는 그것을 먼저 씁니다.

</output_language>

<purpose>

- 저장소가 Next.js 프로젝트인지 확인하고, App Router인지 Pages Router인지 아니면 둘이 섞였는지를 먼저 가립니다.
- 파일 규칙, Server/Client Component 경계, 데이터와 캐시 동작(16.4부터 Cache Components가 권장 기본값), Server Actions, Route Handlers, Proxy, env와 플랫폼 안전성에 대해 공식 Next.js 동작을 강제합니다.
- `src/modules/<domain>/`, `src/services/<domain>/`, `src/db/<area>/`, `src/server/<area>/`, `src/integrations/<provider>/`, `src/config/<area>/` 같은 중첩 공유 폴더 관례는 Hypercore/저장소 로컬 규칙으로 적용하고, 공식 Next.js 법칙처럼 제시하지 않습니다.
- Drizzle, DAL/service 경계, 클라이언트 hook 조합은 주제별 규칙 파일로 넘기고, 버전에 민감한 공식 사실은 `references/official/nextjs/`에 둡니다.

</purpose>

<routing_rule>

기존 Next.js 프로젝트의 아키텍처 강제, 구현 안내, 리뷰에 씁니다. App Router 작업, App Router 마이그레이션, Server/Client 경계, 캐시와 최신성, Server Actions, Route Handlers, Proxy, env와 플랫폼 안전성, service/DAL 경계, 클라이언트 hook 조합, Drizzle과 DB 배치, 중첩 공유 폴더 구성이 여기에 해당합니다.

일반 React 아키텍처, Remix나 TanStack Start 프로젝트, 문서 요약만 하는 요청, 아키텍처 경계를 건드리지 않는 문구 편집에는 쓰지 않습니다. 문구 편집이라도 안전성 확인 한 번은 남깁니다. Pages Router만 쓰는 프로젝트에서는 Next.js 공통 안전성과 플랫폼 검사를 적용하되, 마이그레이션을 요청하지 않았다면 App Router 전용 파일 규칙을 강요하지 않습니다.

</routing_rule>

<instruction_contract>

| Field | Contract |
|---|---|
| Intent | Next.js 프로젝트를 공식 문서와, 그와 구분해 표시한 Hypercore/저장소 로컬 관례에 맞춰 아키텍처 측면에서 안전하게 유지합니다. |
| Trigger | App Router, Pages Router, Server/Client 경계, 데이터와 캐시 동작, Server Actions, Route Handlers, Proxy, 플랫폼과 env, 공유 폴더 배치를 다루는 Next.js 작업. |
| Scope | 수정하는 프로젝트 아키텍처, 주제별 규칙 파일, 공식 참고 자료, 검증 노트, 되돌리기 쉬운 작은 아키텍처 수정을 검토하고 안내합니다. |
| Authority | 사용자와 프로젝트 지시가 이 스킬보다 우선합니다. 프레임워크 동작에서는 현재 공식 Next.js 문서가 로컬 관례보다 우선합니다. 안전 정책은 위험한 런타임, 인증, 비밀 값, import 경계 변경을 막습니다. |
| Evidence | 로컬 패키지·설정·라우터 표지, 수정한 소스 경로, 주제별 규칙, 공식 참고 자료, 검증 스크립트, 프로젝트 검사 출력을 근거로 씁니다. |
| Tools | 로컬 검색·읽기·편집·검증 명령을 쓰고, API가 달라졌을 수 있으면 현재 공식 문서를 확인합니다. 파괴적 마이그레이션, 자격 증명, 프로덕션 부작용, 광범위한 일괄 수정은 게이트를 둡니다. |
| Loop | 없습니다. 요청마다 강제 절차를 한 번만 돌리고, 사용자가 다시 요청할 때만 새로 시작합니다. |
| Output | 규칙 분류, 변경한 파일, 검증 근거, 남은 위험, 날짜를 붙인 공식 문서 모호성 메모를 담은 한국어 아키텍처 판단이나 리뷰. |
| Verification | 수정한 영역에 해당하는 `rules/nextjs/validation.ko.md` 검사를 돌리고, 이 스킬 폴더를 고쳤으면 `bash skills/hyper-architecture/scripts/validate-architecture.sh`를 실행합니다. |
| Stop condition | 프로젝트 모드를 확인했고, 적용되는 안전 게이트를 통과했고, 로컬 관례를 적용했거나 미뤘고, 검증 근거를 남겼고, 남은 API 차이에 날짜와 출처를 붙인 상태에서 멈춥니다. |

</instruction_contract>

<activation_examples>

Positive examples:

- "Audit this Next.js App Router feature for Server/Client boundaries and cache correctness."
- "Refactor this form to use Server Actions instead of an internal route handler."
- "Add a Route Handler for a webhook and verify it follows the current Next.js docs."
- "Next.js 16 cacheComponents 기준으로 data fetching 규칙을 점검해줘."
- "Next.js App Router에서 src/lib/auth/session.ts와 src/services/billing/mutations.ts처럼 nested shared folders로 정리해줘."
- "Add Drizzle schema and migrations to this Next.js app without leaking DB access into client hooks."
- "Split this Next.js form into client hooks, Server Actions, and a server-only service/DAL."

Negative examples:

- "Create a generic React architecture guide."
- "Review a Remix or TanStack Start app."
- "Write marketing copy for a Next.js landing page without touching architecture."

Boundary examples:

- "Make a tiny copy-only text change in a Next.js page." 아키텍처 경계가 걸리지 않으면 직접 고쳐도 되지만, 손댄 파일은 안전성 확인을 한 번 거칩니다.
- "This repo is Pages Router only and I am not migrating to App Router." Next.js 공통 플랫폼, env, server/client 안전성 검사를 적용하고 App Router 전용 파일 규칙은 풉니다.

</activation_examples>

<trigger_conditions>

라우터 모드가 어떤 규칙 묶음을 적용할지 정합니다. 모드 표는 `stacks/nextjs/architecture-rules.ko.md`의 Project Modes가 갖고 있습니다. `next` 의존성이 없으면 여기서 끝냅니다.

| 작업이 이런 형태라면 | 기본 표면 | 기본으로 피할 것 |
|---|---|---|
| App Router에서 form이나 내부 UI mutation 추가 | Server Action | `route.ts` RPC |
| webhook, feed, CORS endpoint, 공개 API, XML, JSON, stream 추가 | Route Handler | Server Action |
| 화면 초기 데이터 가져오기 | Server Component | 클라이언트 우선 fetch |
| 상호작용, 브라우저 API, 클라이언트 hook 추가 | 범위를 좁힌 Client Component | 트리 상단의 `'use client'` |
| Server Action 주변의 클라이언트 조합 추가 | action을 호출하는 클라이언트 hook | DB/DAL/server-only 코드를 import하는 hook |
| 도메인 로직, provider 호출, 권한 확인 추가 | server-only service/DAL 계층 | route 파일이나 Client Component가 직접 소유 |
| Drizzle 스키마, 마이그레이션, repository, DB 클라이언트 추가 | `rules/nextjs/db.ko.md` + server-only `src/db` 관례 | 클라이언트 hook이나 Route Handler 요청 주기 |
| Next.js 16.4 이상에서 반복되는 데이터/UI 캐시(권장 기본값) | `cacheComponents` + `partialPrefetching` + `use cache` / `cacheTag` / `cacheLife` | 오래된 `fetch` 기본값 가정 |
| 동기 값을 static shell에서 빼기 | `<Suspense>` 안의 `io()` | `io()`면 cache 가능한데 `connection()`을 씀 |
| 비용 큰 작업을 App Shell이나 navigation 뒤로 미루기 | `prefetch()`, `navigation()`, `ensureStatic` | prefetch 없는 blocking 작업 |
| mutation 뒤 화면 갱신 | `updateTag`, `revalidateTag`, `revalidatePath`, `refresh`, redirect 흐름 | 근거 없는 최신성 |
| 여러 요청에서 render 전 redirect/rewrite | 먼저 `next.config.*`, 필요하면 Proxy | 범용 미들웨어로서의 Proxy |
| Pages Router만 쓰고 마이그레이션 요청 없음 | Next.js 공통 검사 | App Router 전용 파일 규칙 |

</trigger_conditions>

<skill_architecture>

- 핵심(`stacks/nextjs/core.md`): 트리거, 계약, 게이트 순서, 검증, 정지 조건. 규칙: `stacks/nextjs/architecture-rules.ko.md`(분류와 게이트 요약)와 `reference_routing`에 적힌 주제별 파일 열한 개.
- 참고: `references/official/nextjs/current-docs-2026-11-04.ko.md`, `nextjs-docs.ko.md`, `drizzle-docs.ko.md`에 날짜가 붙은 공식 사실을 둡니다. 트리거와 동작 사례는 `assets/evals/nextjs-cases.jsonl`에 있습니다.
- 이 스킬은 스스로 완결되며 다른 스킬의 경로, 문서, 호출을 필요로 하지 않습니다.

## Available scripts

`scripts/validate-architecture.sh`는 이 스킬 폴더 자체를 검사합니다. 모든 스택 가이드가 규칙 묶음과 함께 있는지, Markdown의 로컬 경로가 실제로 있는지, 영어 파일마다 한국어 짝 파일이 있는지, 코드 펜스가 맞는지, 가이드가 크기 상한 안에 있는지, eval fixture가 해석되는지 확인합니다. 저장소 루트에서 `bash skills/hyper-architecture/scripts/validate-architecture.sh`로 실행하고(bash 3.2 이상, jq 1.6 이상), JSON 요약을 출력하며 실패하면 0이 아닌 종료 코드를 냅니다.

</skill_architecture>

<loop_policy>

최적화 루프는 없습니다. 요청마다 게이트, 편집, 검증을 한 번씩 돕니다. 검증은 요청당 한 번이고, 새 요청이 오거나 보고된 검사가 실패했을 때만 두 번째 패스를 돌리며 그때도 손댄 영역에 걸린 검사만 다시 돌립니다. 판정은 게이트 표와 프로젝트 검사에서 나오며 같은 diff를 다시 읽는 것으로 대신하지 않습니다.

</loop_policy>

<language_and_translation_default>

판단, 리뷰, 변경 요약은 한국어로 씁니다. 식별자, 파일 경로, 라우트 세그먼트, API 이름, 규칙 라벨(`BLOCKED`, `WARNING`)은 원래 표기를 유지해 이 문서의 표와 일대일로 맞출 수 있게 합니다. `stacks/nextjs/core.ko.md`는 이 파일과 절 단위로 짝을 이루며, 규칙을 바꾸면 같은 편집에서 함께 바꿉니다.

</language_and_translation_default>

<reference_routing>

`stacks/nextjs/architecture-rules.md`는 항상 먼저 읽습니다. 그다음 손댄 영역에 해당하는 파일만 읽습니다.

| 손댄 영역 | 파일 |
|---|---|
| 파일 규칙, 세그먼트 규칙, route group, private folder, parallel/intercepted route | `rules/nextjs/routes.md` |
| 최상위 프로젝트 구성, `src/`, 중첩 `src/modules` / `src/services` / `src/db` / `src/server` / `src/integrations` / `src/config` | `rules/nextjs/project-structure.md` |
| Server/Client Component, `'use client'`, provider, 직렬화 가능한 props, `server-only` | `rules/nextjs/execution-model.md` |
| 서버 우선 읽기, 스트리밍, Cache Components, `use cache`, 캐시 태그, 재검증 | `rules/nextjs/data-fetching.md` |
| `use server`, form, 검증, 인증, DAL 위임, mutation 뒤 최신성 | `rules/nextjs/server-actions.md` |
| `route.ts`, HTTP 메서드, 캐시 의도, params, CORS, webhook | `rules/nextjs/route-handlers.md` |
| DAL/service/provider 경계, DTO, 권한 위임 | `rules/nextjs/services.md` |
| 클라이언트 hook 조합과 그 경계 | `rules/nextjs/hooks.md` |
| Drizzle 스키마, 마이그레이션, 연결 수명, server-only DB 배치 | `rules/nextjs/db.md` |
| env, `next.config.*`, `typedRoutes`, Proxy, route segment 설정, 배포 관련 설정 | `rules/nextjs/platform.md` |
| 손댄 영역의 변경 후 검사 | `rules/nextjs/validation.md` |
| 번들 무게, 렌더링과 캐시 비용, Core Web Vitals, React Compiler, `next analyze`, `next/image` | `rules/nextjs/performance.md` |
| lint, format, 타입 검사 설정(oxlint, Prettier, tsconfig, 패키지 매니저 고정) | `rules/setup/typescript.md` |
| 스냅숏 이후 달라졌을 수 있는 Next.js 동작 | `references/official/nextjs/current-docs-2026-11-04.md`, 그다음 `references/official/nextjs/nextjs-docs.md`. Drizzle 주장은 `references/official/nextjs/drizzle-docs.md` |

`https://r.jina.ai/https://nextjs.org/docs/...`는 공식 스냅숏 두 개가 어긋나거나 해당 페이지를 마크다운으로 읽어야 할 때만 씁니다.

</reference_routing>

<support_file_read_order>

1. 어떤 판단이나 편집보다 먼저 `stacks/nextjs/architecture-rules.md`.
2. 손댄 영역의 주제별 규칙 파일. 순서는 `reference_routing` 표를 따릅니다.
3. 변경을 다 쓴 뒤 검사가 필요하면 `rules/nextjs/validation.md`.
4. 공식 스냅숏은 프레임워크 동작이 버전에 민감할 때만 `current-docs-2026-11-04.md`, 그다음 `nextjs-docs.md`, Drizzle 주장이면 `drizzle-docs.md`.

</support_file_read_order>

<workflow>

| 단계 | 할 일 | 산출물 |
|---|---|---|
| 0 | 프로젝트와 라우터 모드를 확인합니다. | 모드 판정 |
| 1 | 손댄 영역에 필요한 규칙 파일만 읽습니다. | 최소 근거 묶음 |
| 2 | 계획한 변경을 게이트 1~6에 대봅니다. | BLOCKED 또는 WARNING 라벨이 붙은 판정 |
| 3 | 구현 정책을 적용합니다. 국소적이고 되돌릴 수 있는 문제는 고치고, 광범위한 마이그레이션은 하지 않습니다. | 편집 또는 이유를 붙인 거절 |
| 4 | 변경 후 검사를 돌리고 근거를 남깁니다. | 검증 기록 |

0단계는 `rules/nextjs/validation.md`에 있는 프로젝트 확인 명령을 씁니다. `next` 의존성이 없으면 여기서 끝냅니다.

2단계는 게이트입니다. 브라운필드 규칙에 따라 손대지 않은 레거시 편차를 기본 실패로 보지 않습니다. 안전성, 비밀 값, 인증, 경계 문제는 손댄 파일에서 즉시 막습니다. 광범위한 마이그레이션이 필요하지 않다면 손댄 파일을 규칙에 맞춥니다.

### Gate 1: Routing, File Conventions, and Project Structure

| 확인 | 규칙 |
|---|---|
| `page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx`, `not-found.tsx`, `route.ts`가 유효한 세그먼트 구조 밖에 있음 | BLOCKED |
| 같은 route 세그먼트에 `route.ts`와 `page.tsx`를 함께 만듦 | BLOCKED |
| route group을 URL이 바뀌는 것처럼 사용 | BLOCKED |
| private 구현 파일을 `_folder` 대신 라우팅되는 세그먼트로 노출 | BLOCKED |
| 중첩 도메인/provider 묶음이 손댄 코드를 더 분명하게 만드는데도 공유 `src/modules` / `src/services` / `src/db` / `src/server` / `src/integrations` / `src/config` 구성을 평면이나 단일 파일로 강제 | WARNING. 중첩 묶음을 권장 |
| 저장소 로컬 폴더 취향을 공식 Next.js 법칙처럼 보고 | BLOCKED |
| parallel/intercepted route를 대응하는 layout slot이나 hard-navigation 동작 확인 없이 추가 | 위험도에 따라 WARNING/BLOCKED |

### Gate 2: Server and Client Boundaries

| 확인 | 규칙 |
|---|---|
| 상호작용하는 컴포넌트에 `'use client'`가 없음 | BLOCKED |
| 필요 없이 트리 상단에 `'use client'`를 붙임 | BLOCKED |
| Client Component가 DB 코드, private env, `cookies()`, `headers()`, server-only 도우미를 import | BLOCKED |
| Server에서 Client로 넘기는 props가 넓거나 비밀 값을 담거나 직렬화할 수 없음 | BLOCKED |
| Provider가 필요한 범위보다 넓게 감쌈 | WARNING |
| 클라이언트 hook이 DB, Drizzle 스키마, DAL, private env, `cookies()`, `headers()`, server-only provider 클라이언트를 import | BLOCKED |

### Gate 3: Data Fetching, Cache, and Freshness

| 확인 | 규칙 |
|---|---|
| 클라이언트 전용 필요가 없는데 Client Component에서 초기 UI 데이터를 가져옴 | BLOCKED |
| 캐시 동작이 우연히 정해졌거나, 문서화되지 않았거나, 오래된 기본값에 기댐 | BLOCKED |
| `cacheComponents`가 켜져 있는데 캐시하지 않는 런타임 데이터에 `use cache`, `io()`, `loading.tsx`, `<Suspense>` 의도가 없음 | BLOCKED |
| `partialPrefetching` 없이 `cacheComponents`를 켜거나, `cacheComponents` 없이 `partialPrefetching`을 켬 | BLOCKED |
| `use cache` 범위에 `cacheLife`가 없고 실제 수명을 말할 수 없음 | BLOCKED |
| `use cache` 범위 안에서 `cookies()` / `headers()`를 읽고 직렬화 가능한 인자로 받지 않음 | runtime 읽기를 밖으로 뺄 수 없어 `use cache: private`이 정당화된 경우가 아니면 BLOCKED |
| static shell에서 빼면 되는 곳에 `io()` 대신 `connection()`을 씀 | WARNING |
| `use cache: private`을 `use cache: remote`과 중첩하거나 runtime 읽기 이유 없이 씀 | BLOCKED |
| 새 App Router 작업에 `io()` 또는 `connection()` 대신 `unstable_noStore`를 추가 | 레거시 코드를 유지하는 경우가 아니면 BLOCKED |
| mutation에 `updateTag`, `revalidateTag`, `revalidatePath`, `refresh`, redirect 최신성, 문서화된 대안 중 아무것도 없음 | BLOCKED |

### Gate 4: Server Actions

| 확인 | 규칙 |
|---|---|
| Server Action으로 충분한 내부 UI mutation을 `route.ts`로 구현 | HTTP 의미가 필요하지 않으면 BLOCKED |
| Action이 `FormData`, params, headers, search params를 검증이나 재확인 없이 신뢰 | BLOCKED |
| Action이 페이지 수준 인증 확인에만 기댐 | BLOCKED |
| Action이 DB 원본 행이나 넓은 내부 객체를 그대로 반환 | BLOCKED |
| Action이 권한 확인, DTO 형태 맞추기, provider 조합에 필요한 server-only service/DAL 경계를 우회 | 위험도에 따라 WARNING/BLOCKED |
| 필요한 재검증이나 태그 갱신 전에 `redirect()`를 실행 | BLOCKED |
| 클라이언트 코드가 Server Action 병렬 dispatch를 가정하거나 `Promise.all`로 병렬화하려 함 | BLOCKED |
| Action 응답에서 `revalidateTag(tag, 'max')`가 현재 route를 다시 렌더링한다고 기대 | BLOCKED |
| Server Action 밖에서 `updateTag` 또는 `refresh`를 호출 | BLOCKED |

### Gate 5: Route Handlers and Proxy

| 확인 | 규칙 |
|---|---|
| UI 전용 흐름에서 Route Handler를 기본 내부 RPC로 사용 | BLOCKED |
| Route Handler 안에서 `NextResponse.next()` 사용 | BLOCKED |
| 정확성이 중요한데 Route Handler 캐시를 명시하지 않고 가정 | BLOCKED |
| `use cache`를 도우미 함수로 빼지 않고 Route Handler 본문에 직접 둠 | BLOCKED |
| 새 `middleware.ts`를 만들고 `proxy.ts`를 쓰지 않음 | BLOCKED |
| `next.config.*`, 헤더, redirect, rewrite, render 시점 로직으로 충분한데 Proxy를 추가 | BLOCKED |
| Proxy matcher가 없거나, 너무 넓거나, metadata/정적 표면을 빼야 하는데 빠뜨림 | BLOCKED |

### Gate 6: Platform and Environment

| 확인 | 규칙 |
|---|---|
| `.env*` 파일이 `src/`에서 읽힌다고 가정 | BLOCKED |
| 클라이언트 코드가 `NEXT_PUBLIC_`이 아닌 env 값을 읽음 | BLOCKED |
| 런타임 클라이언트 env를 빌드 시점 공개 env처럼 취급 | BLOCKED |
| `cacheComponents`가 켜진 상태에서 v16에서 빠진 route segment 설정(`dynamic`, `dynamicParams`, `revalidate`, `fetchCache`)을 사용 | BLOCKED |
| `runtime: 'edge'`나 Cache Components 하위 `runtime: 'nodejs'`를 포함해 `runtime` export를 추가하거나 유지 | BLOCKED |
| 배포에 민감한 Server Action origin, body 크기, 암호화 키 변경을 문서화하지 않음 | 위험도에 따라 WARNING/BLOCKED |

3단계는 구현 정책입니다. 국소적이고 되돌릴 수 있는 문제는 바로 고칩니다. 클라이언트 경계를 좁히고, server-only 코드를 DAL이나 도우미 뒤로 옮기고, `server-only`를 붙이고, 빠진 최신성을 채우고, UI 전용 `route.ts` mutation을 작은 Server Action으로 바꾸고, Proxy matcher를 좁히고, 캐시 의도를 분명히 합니다. 광범위한 마이그레이션은 스스로 적용하지 않습니다. Pages에서 App Router로의 재작성, 캐시 모델 전면 교체, Route Handler에서 Server Action으로의 대량 전환, 배포에 민감한 origin이나 암호화 변경이 여기에 해당합니다.

4단계는 검증 절의 변경 후 검사를 `rules/nextjs/validation.md` 명령으로 돌리고, 실행한 명령을 근거로 남깁니다.

</workflow>

<required>

- 규칙을 적용하기 전에 확인한 프로젝트 모드. 모드 때문에 App Router 규칙을 빼는 경우에는 그 이유.
- 강제 기본값 네 가지: 공식 문서가 로컬 관례보다 우선, `app/`에는 App Router 규칙이 기본, App Router UI에서 시작한 쓰기는 Server Action, 모든 Server Action을 외부에서 닿는 POST 진입점으로 취급.
- 모든 판정을 게이트 행과 연결하고 BLOCKED 또는 WARNING으로 표시. 저장소 로컬 관례는 그렇게 표시.
- 손댄 영역에 해당하는 4단계 검사의 근거.
- 이 스킬 폴더 자체를 고쳤을 때 `bash skills/hyper-architecture/scripts/validate-architecture.sh` 실행.

</required>

<forbidden>

- 마이그레이션을 요청하지 않은 Pages Router 전용 프로젝트에 App Router 파일 규칙을 적용하는 것.
- Hypercore/저장소 로컬 폴더 취향을 공식 Next.js 동작으로 보고하는 것.
- Pages에서 App Router로의 재작성, mutation 방식 대량 전환, 캐시 모델 전면 교체를 스스로 적용하는 것.
- 명시적 권한 없이 자격 증명, 프로덕션 부작용, 배포에 민감한 origin이나 암호화 설정을 건드리는 것.
- 저장소의 다른 곳에 같은 패턴이 손대지 않은 채 있다는 이유로 게이트를 끄는 것.
- 돌리지 않은 검증을 돌렸다고 하거나, 실행한 검사 없이 게이트를 통과로 기록하는 것.

</forbidden>

<validation>

- [ ] 프로젝트 모드를 확인했고 편집한 영역과 맞는다.
- [ ] 손댄 파일을 게이트 1~6에 대보았고 해당 행을 기록했다.
- [ ] `'use client'` 경계가 좁고, 클라이언트 파일이 server-only 코드나 private env에 닿지 않으며, 캐시와 최신성 동작이 명시적이고 현재 스냅숏과 맞는다.
- [ ] Route Handler와 Proxy 사용이 정당화되고, 저장소 로컬 관례에 라벨이 붙어 있으며 프레임워크 법칙처럼 제시되지 않는다.
- [ ] 남은 위험, 미룬 마이그레이션, 날짜를 붙인 API 모호성을 보고했다.
- [ ] 이 스킬 폴더를 고쳤다면 번들 검사기가 통과했다.

정지 조건: Next.js 모드를 확인했고, 손댄 영역이 해당 게이트를 통과했고, 검증 출력이 최신이며, 남은 저장소 로컬 관례나 위험을 분명히 보고한 상태에서 멈춥니다.

</validation>
