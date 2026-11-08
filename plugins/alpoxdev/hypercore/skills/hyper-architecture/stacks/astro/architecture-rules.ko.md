# 아키텍처 규칙 참조

> `hyper-architecture`의 Astro 프로젝트 전체 규칙 세트와, 이 스택 가이드가 변경을 판정하는 게이트 표입니다.

아래 일부 규칙은 Astro 기본값보다 엄격합니다. 보편적인 프레임워크 요구사항이 아니라 `hypercore-default` 팀 관례로 표시합니다. 연 공식 페이지가 그대로 진술한 규칙은 `official`로 표시합니다.

브라운필드 적용 규칙: 손대지 않은 레거시 코드는 문제가 스타일이나 Hypercore 전용 사항이면 즉시 실패가 아니라 마이그레이션 작업으로 추적할 수 있습니다. 렌더링 모드 오류, 어댑터 누락, 권한 공백, 비밀 값 노출, 직렬화할 수 없는 아일랜드 prop은 특히 손댄 코드에서 즉시 막습니다.

---

## Forbidden

| 범주 | 금지 사항 |
|---|---|
| Detection | `astro` 의존성도 `astro.config.*`도 없는 프로젝트에 Astro 규칙 적용 |
| Precedence | 매니페스트에 `vite`가 있다는 이유로 Astro 대상을 Vite 가이드로 라우팅 |
| Routes | 손으로 쓴 라우트 표, 또는 `src/pages/` 밖의 라우트 |
| Dynamic routes | 온디맨드 라우트의 `getStaticPaths()`, 그곳에서 `props`를 기대하는 것 |
| Endpoints | `GET`/`POST`를 내보내는 엔드포인트 대신 `Response`를 돌려주는 페이지 파일 |
| Rendering | `output: 'static'`에 어댑터도 없는데 Actions, 세션, 서버 아일랜드, 라이브 컬렉션, 라우트 캐싱 추가 |
| Rendering | 라우트 하나를 동적으로 만들려고 사이트 전체를 `output: 'server'`로 전환 |
| Headers | 페이지 수준이 아니라 자식 컴포넌트 안에서 응답 헤더 설정 |
| Islands | `client:*` 지시어와 이유 없이 프레임워크 JS 전송 |
| Islands | 하이드레이션 아일랜드나 서버 아일랜드에 함수, 클래스 인스턴스, 순환 구조 전달 |
| Content | `src/content.config.ts` 대신 `src/content/config.ts`(제거된 레거시 위치) 사용 |
| Content | 정렬하지 않은 `getCollection()` 결과를 안정된 순서처럼 제시 |
| Actions | 사소하지 않은 입력에 Zod 검증이 없는 Action |
| Actions | 핸들러나 미들웨어에서 권한을 확인하지 않고 페이지 수준 인증에만 기대는 Action |
| Middleware | 명명된 `onRequest` 대신 default export, 또는 `context.locals` 재할당 |
| Env | 공유 코드에서 `import.meta.env`로 비밀 값 읽기, `context: 'client'`에 `access: 'secret'` 선언 |
| Advanced routing | `src/fetch.ts` 안에서 `url.pathname` 접두사로 권한 판정 |
| Build output | `dist/`나 `.astro/` 아래 파일을 손으로 작성 |
| Performance | 프로덕션 빌드의 전후 수치 없이 성능 개선 주장 |
| Reporting | Hypercore 관례를 공식 Astro 동작으로 제시 |

---

## Gate Table

게이트는 순서대로 돕니다. 앞 게이트가 실패하면 그 대상은 멈춥니다.

### Gate 1: Detection and Rendering Mode

| 확인 | 규칙 |
|---|---|
| 대상에 `astro` 의존성도 `astro.config.*`도 없음 | Astro 대상이 아니므로 멈추고 다른 경로로 라우팅 |
| `astro` 의존성은 있는데 `src/pages/`가 없음 | BLOCKED. 그 폴더가 없으면 사이트에 라우트가 없음 |
| 서버 기능을 권하기 전에 `output`을 기록하지 않음 | BLOCKED |
| `output: 'static'`이고 `adapter`도 설정되지 않았는데 서버 기능을 요청 | BLOCKED |
| 라우트가 요청 데이터를 필요로 하는데 `export const prerender = false`가 없음 | BLOCKED |
| `prerender` 값이 정적으로 분석되지 않고 런타임에 계산됨 | BLOCKED |
| 동적 라우트 하나 때문에 사이트 전체 `output: 'server'`를 제안 | WARNING, 대부분 라우트가 정적으로 남으면 BLOCKED |

### Gate 2: Routing and Structure

| 확인 | 규칙 |
|---|---|
| 라우트 파일이 `src/pages/` 밖에 있음 | BLOCKED |
| `[...rest]`가 필요한 곳에 `[param]`을 쓰거나 그 반대 | BLOCKED |
| 온디맨드 라우트에 `getStaticPaths()`를 쓰거나 그곳의 `props`를 기대 | BLOCKED |
| 엔드포인트에 메서드 export나 `satisfies APIRoute`가 없음 | BLOCKED |
| 우선순위 표(정적 우선 동적, 엔드포인트 우선 페이지)를 확인하지 않고 라우트 구성에 의존 | WARNING |
| 파일 이름이 예약 라우트 접두사(`_astro`, `_server_islands`, `_actions`)와 충돌 | BLOCKED |
| 재사용 UI, 레이아웃, 도우미 코드를 `src/pages/`에 둠 | WARNING. 그곳에는 라우트만 둠 |
| `redirects` 설정으로 처리할 수 있는 리다이렉트를 페이지로 구현 | WARNING |
| 정적 전용 사이트에 `src/pages/500.astro` 추가 | BLOCKED. 온디맨드 렌더링에서만 동작 |

### Gate 3: Islands and Framework Boundaries

| 확인 | 규칙 |
|---|---|
| 프레임워크 컴포넌트가 상호작용해야 하는데 `client:*` 지시어가 없음 | BLOCKED |
| `client:visible`이나 `client:idle`로 충분한 곳에 `client:load` 사용 | WARNING |
| 서버에서 렌더링할 수 있는 컴포넌트에 `client:only` 사용 | WARNING |
| 하이드레이션 컴포넌트나 서버 아일랜드에 직렬화할 수 없는 prop 전달 | BLOCKED |
| 요청 데이터가 필요 없는 조각에 서버 아일랜드 사용 | WARNING |
| 서버 아일랜드 prop이 쿼리 문자열 한도를 넘어 POST로 넘어갈 크기 | WARNING. 캐싱이 깨짐 |
| `.astro` 파일만 프레임워크를 섞는데 프레임워크 컴포넌트가 다른 프레임워크 컴포넌트를 import | BLOCKED |

### Gate 4: Content Layer

| 확인 | 규칙 |
|---|---|
| `loader`가 없는 컬렉션 | BLOCKED |
| Zod가 아닌 검증기로 스키마를 정의하거나 `astro:content`의 `z`를 사용 | BLOCKED |
| `getCollection()` 순서를 안정된 것으로 취급 | BLOCKED |
| `reference()`를 쓰면서 `getEntry()`/`getEntries()`로 해석하지 않음 | WARNING |
| 어댑터 없이 라이브 컬렉션 추가 | BLOCKED |
| 빌드 시점 컬렉션과 재빌드로 충분한 곳에 라이브 컬렉션 사용 | WARNING |
| 빌드 메모리를 재보지 않고 `deferRender: true` 사용 | WARNING |

### Gate 5: Server Boundaries

| 확인 | 규칙 |
|---|---|
| Action 입력을 검증 없이 신뢰 | BLOCKED |
| Action을 페이지 수준 확인으로만 인가 | BLOCKED |
| API 엔드포인트에 요구할 권한 검사 없이 `/_actions/<name>`으로 노출된 Action | BLOCKED |
| `context.locals`를 재할당하고 필드만 채우지 않음 | BLOCKED |
| 미들웨어를 명명된 `onRequest` 대신 default로 export | BLOCKED |
| 드라이버를 설정하지 않고 세션을 읽거나 씀 | BLOCKED |
| 공유 코드에서 스키마 밖의 환경 변수를 읽음 | WARNING, 비밀 값이면 BLOCKED |
| 기록된 이유 없이 `security.checkOrigin` 비활성화 | BLOCKED |
| `<ClientRouter />`와 함께 `security.csp` 활성화 | BLOCKED |
| `src/fetch.ts`에서 `url.pathname` 접두사로 권한 판정 | BLOCKED |

### Gate 6: Verification

| 확인 | 규칙 |
|---|---|
| `astro check`를 돌리지 않았거나, `@astrojs/check`와 `typescript` 없이 실행 | BLOCKED |
| `astro check`가 타입 게이트인데 TypeScript를 7.x로 고정 | BLOCKED |
| `.astro`를 `prettier-plugin-astro` 대신 JSX 파서로 포맷 | BLOCKED |
| oxlint로 `.astro`의 템플릿이나 접근성 lint를 한다고 주장 | BLOCKED |
| 컴포넌트를 렌더해야 하는데 Container API 없이 컴포넌트 테스트 작성 | WARNING |
| 프로덕션 빌드 측정 없이 성능 개선 주장 | BLOCKED |

---

## Layer Architecture

```text
Adapter / Worker Entrypoint
  astro.config.*  adapter: node | vercel | cloudflare | netlify
       |
       v
Routing Surface
  src/pages/**  (+ src/fetch.ts for a custom entrypoint)
       |
       v
Layouts and Pages
  src/layouts/*.astro  ->  src/pages/*.astro
       |
       v
Islands and Components
  src/components/**  client:* only where interaction is required
       |
       v
Server Boundaries
  src/actions/**, src/middleware.ts, src/lib/server/**
       |
       v
Data
  src/content.config.ts (build time), src/live.config.ts (request time)
```

**데이터 흐름 규칙:**

- 프레임워크 법칙은 `src/pages/`뿐입니다. `components`, `layouts`, `styles`, `lib`은 라벨을 붙인 팀 관례입니다.
- 페이지는 렌더링을 조율합니다. 저장 로직이나 provider SDK 호출을 담지 않습니다.
- 서버 전용 코드는 `client:*` 아일랜드가 import할 수 있는 곳 밖에 둡니다.
- 빌드 시점 데이터는 콘텐츠 컬렉션에서, 요청 시점 데이터는 라이브 컬렉션, Actions, 미들웨어가 채운 `locals`에서 옵니다.
- 빌드 산출물(`dist/`, `.astro/`)은 손으로 고치지 않습니다.

---

## Project Structure and Scalability

폴더를 추가하거나 소유권을 바꾸거나 라우트를 옮기기 전에 `rules/astro/project-structure.md`를 읽습니다.

핵심 불변 조건은 여기에 남깁니다.

- `src/pages/`에는 라우트만 둡니다.
- 중첩 폴더는 소유권이나 의존 압력이 관찰될 때 생기며, 빈 계층으로 미리 만들지 않습니다.
- `src/lib/server/`와 `src/lib/client/`를 분리해 클라이언트 아일랜드가 비밀 값을 담은 모듈을 import할 수 없게 합니다.
- 예약 파일 이름(`src/middleware.ts`, `src/fetch.ts`, `src/content.config.ts`, `src/live.config.ts`, `src/actions/index.ts`, `src/env.d.ts`)은 정확한 경로를 유지합니다.
- 브라운필드 이전은 공개 URL, `prerender` 값, 미들웨어 순서를 보존합니다.

---

## Rendering Rules

- `output`은 `'static'` 또는 `'server'`뿐이고 기본값은 `'static'`입니다.
- `'server'`는 기본 렌더링 동작만 바꾸고 그 밖의 기능을 더하지 않습니다.
- 라우트별 `prerender`는 런타임 값이 아니라 정적 export입니다.
- 온디맨드 라우트에는 어댑터가 필요하고, 서버 아일랜드와 라이브 컬렉션도 마찬가지입니다.
- 온디맨드 라우트의 HTML은 기본적으로 스트리밍되며, 응답 헤더는 페이지 수준에서 설정합니다.
- 조각 하나만 개인화된다면 페이지 전체를 온디맨드로 바꾸지 말고 서버 아일랜드를 씁니다.

---

## Content Rules

- `src/content.config.ts`가 `collections`를 export하고, 각 항목은 `loader`와 선택적 `schema`를 가집니다.
- `glob()`과 `file()`은 `astro/loaders`에서, `z`는 `astro/zod`에서 옵니다.
- 조회 결과의 순서는 비결정적이므로 정렬해야 합니다.
- `reference()` 관계는 해석 시점에 검증됩니다.
- 라이브 컬렉션은 별도 `src/live.config.ts`에 두고, 커스텀 로더와 어댑터가 필요합니다.

---

## Server Boundary Rules

- Actions는 `/_actions/<name>`의 공개 POST 엔드포인트이며 API 라우트와 같은 권한 검사가 필요합니다.
- 미들웨어는 명명된 `onRequest`를 export하고 `sequence()`로 조합하며, 요청 상태는 타입이 붙은 `locals`로 공유합니다.
- 세션에는 드라이버가 필요합니다. Node, Cloudflare, Netlify는 어댑터 기본값이 있고 Vercel은 명시 설정이 필요합니다.
- 모든 환경 변수는 `env.schema`에 선언하고 `astro:env/client` 또는 `astro:env/server`에서 import합니다.
- `context: 'client'` 필드는 절대 `access: 'secret'`일 수 없습니다.

---

## Performance Rules

- 무엇이든 바꾸기 전에 프로덕션 빌드를 측정하고, 측정마다 레버 하나만 바꿉니다.
- 아일랜드 지시어는 성능 결정이므로 각각 이유가 필요합니다.
- 이미지는 `astro:assets`를 거치고, `public/` 이미지는 절대 최적화되지 않습니다.
- 폰트는 Fonts API로 자체 호스팅합니다.
- 측정이 바꿀 이유를 주지 않는 한 `build.concurrency`는 1로 둡니다.

측정 절차는 `rules/astro/performance.md`에 있습니다.

---

## Verification Rules

- `astro check`가 타입 게이트이며 `@astrojs/check`와 `typescript`가 모두 필요합니다.
- `astro check`가 타입 게이트인 동안 TypeScript는 6.x로 고정합니다. 7.0은 CLI가 거부합니다.
- `.astro`는 `prettier-plugin-astro`로 포맷하고, oxlint는 `<script>` 블록만 lint한다고 봅니다.
- 컴포넌트 테스트는 Container API를 쓰고, 종단 테스트는 `astro preview`에 대한 Playwright를 씁니다.

---

## Checklist

- [ ] Astro 판정을 확인했고 그 근거 신호를 밝혔습니다.
- [ ] `output`, 어댑터, 프레임워크 통합을 기록했습니다.
- [ ] 손댄 모든 라우트에 `prerender` 결정이 명시돼 있고, 동적 라우트가 모드와 맞습니다.
- [ ] 아일랜드에 이유가 적힌 가장 좁은 `client:*` 지시어가 붙어 있고, 직렬화할 수 없는 prop이 경계를 넘지 않습니다.
- [ ] 컬렉션에 로더와 스키마가 있고, 조회 결과를 명시적으로 정렬합니다.
- [ ] Actions가 입력을 검증하고 권한을 확인하며, 미들웨어 결과가 타입이 붙은 `locals`로 페이지에 도달하고, 세션에 드라이버가 있습니다.
- [ ] 환경 변수를 `env.schema`에 선언했고, 클라이언트 문맥 필드가 비밀이 아닙니다.
- [ ] `@astrojs/check`와 TypeScript 6.x가 설치된 상태에서 `astro check`가 통과합니다.
- [ ] 모든 판정에 `official` 또는 `hypercore-default` 라벨이 붙어 있습니다.

---

## Sources

> Checked 2026-11-07. 위 모든 규칙은 2026-11-07에 공식 페이지를 연 Astro 조사 레인에서 나왔고, 레인의 출처 id를 괄호에 남겼습니다.

| Claim | Source |
|---|---|
| `output`이 `'static'`과 `'server'`만 받고 기본값이 `'static'`이며 `'server'`는 기본값만 바꿉니다 (L-09, L-17) | https://docs.astro.build/en/reference/configuration-reference/ |
| 라우트별 `prerender` 선택과 해제, 어댑터 요구, 페이지 수준 헤더 제한 (L-09) | https://docs.astro.build/en/guides/on-demand-rendering/ |
| 파일 기반 라우팅, 라우트 우선순위, 예약 라우트, `getStaticPaths()` 규칙, 리다이렉트와 리라이트 (L-06, L-07) | https://docs.astro.build/en/guides/routing/ |
| 엔드포인트 메서드 export, `satisfies APIRoute`, 확장자를 가진 URL (L-08) | https://docs.astro.build/en/guides/endpoints/ |
| `404.astro`와 온디맨드 전용 `500.astro` (L-37) | https://docs.astro.build/en/basics/astro-pages/ |
| `src/pages/`만 예약되고 다른 폴더는 관례입니다 (L-05) | https://docs.astro.build/en/basics/project-structure/ |
| `client:*` 지시어, 기본 정적 렌더링, 직렬화 가능한 props, 프레임워크를 섞는 유일한 표면인 `.astro` (L-19, L-58) | https://docs.astro.build/en/guides/framework-components/ |
| 서버 아일랜드, `server:defer`, fallback slot, 암호화된 props, 2048바이트 POST 대체 (L-18) | https://docs.astro.build/en/guides/server-islands/ |
| 콘텐츠 계층 로더, `astro/zod` 스키마, `getCollection()` 순서, `reference()`, 라이브 컬렉션 (L-10) | https://docs.astro.build/en/guides/content-collections/ |
| Actions가 `/_actions/<name>` 공개 엔드포인트이고 권한 검사가 필요합니다 (L-11, L-12) | https://docs.astro.build/en/guides/actions/ |
| 명명된 `onRequest`, `sequence()`, `context.locals`, `App.Locals` 타입 (L-13) | https://docs.astro.build/en/guides/middleware/ |
| 세션 드라이버와 어댑터 기본값 (L-14, L-17) | https://docs.astro.build/en/guides/sessions/ |
| `env.schema`, `astro:env` import, 클라이언트 비밀 값의 불가능성 (L-15, L-16) | https://docs.astro.build/en/guides/environment-variables/ |
| `checkOrigin`, `allowedDomains`, CSP 제한과 미지원 조합 (L-17) | https://docs.astro.build/en/reference/configuration-reference/ |
| `src/fetch.ts` 파이프라인과 pathname 권한 판정 주의 (L-06, L-32) | https://docs.astro.build/en/reference/modules/astro-fetch/ |
| 라우트 캐싱과 `routeRules` (L-30, L-31) | https://docs.astro.build/en/guides/caching/ |
| `astro check` 요구사항, TypeScript 7.0 거부, `prettier-plugin-astro` (L-51, L-40, L-28) | https://docs.astro.build/en/reference/cli-reference/ |
| oxlint가 `<script>` 블록만 lint하고 `.astro` 템플릿 lint가 없습니다 (L-43, L-44) | https://oxc.rs/compatibility.html |
| Container API와 Playwright 설정 (L-25, L-27) | https://docs.astro.build/en/guides/testing/ |
| 이미지 최적화 범위와 `public/` 제외 (L-20, L-21) | https://docs.astro.build/en/guides/images/ |
| Fonts API 자체 호스팅 (L-24) | https://docs.astro.build/en/guides/fonts/ |
| `build.concurrency` 기본값과 주의 (L-17) | https://docs.astro.build/en/reference/configuration-reference/ |
