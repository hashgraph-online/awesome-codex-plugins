# TanStack Start 공식 문서 현행 스냅샷

- last_verified_at: 2026-11-04
- source: TanStack 공식 Start 문서 페이지를 직접 가져온 결과(아래 `guide/<page>.md` URL)와 `@tanstack/start-client-core@1.170.39`, `@tanstack/start-plugin-core@1.171.55`의 배포 type
- use_when: Start/Router API 동작, Start plugin 설정, import protection, 실행 경계, 미들웨어, 또는 서버 함수와 서버 라우트의 API 형태가 아키텍처 결정에 영향을 줄 때
- authority: API 사실은 TanStack 공식 문서를 기준으로 삼고, Hypercore 관례는 `rules/tanstack-start/`에 남긴다.
- supersedes: 은퇴한 2026-09-22와 2026-06-02 스냅샷 (아래 "이전 스냅샷에서 바로잡은 것"을 본다.)

## 목차

- [이전 스냅샷에서 바로잡은 것](#이전-스냅샷에서-바로잡은-것)
- [서버 함수](#서버-함수)
- [실행 경계](#실행-경계)
- [전역 Start 설정](#전역-start-설정)
- [CSRF 보호](#csrf-보호)
- [미들웨어](#미들웨어)
- [import protection](#import-protection)
- [서버 라우트](#서버-라우트)
- [드리프트 처리](#드리프트-처리)
- [Sources](#sources)

## 이전 스냅샷에서 바로잡은 것

- **`.inputValidator(...)`는 폐기가 아니라 제거됐다.** 이전 스냅샷들은 이 별칭을 "폐기됐지만 런타임에서 계속 해석된다"고 기록했다. `@tanstack/react-start@1.169.0`(2026-10-12)이 `createServerFn`과 `createMiddleware`에서 제거했다. release note 원문은 "Remove the deprecated `.inputValidator()` from `createServerFn` and `createMiddleware`. Use `.validator()`, which takes the same validator."다.
- 근거는 2026-11-04에 다시 확인했다.
  - type: `start-client-core@1.170.39`의 선언에 `inputValidator`가 한 번도 나오지 않는다.
  - 문서: `guide/server-functions.md`와 `guide/middleware.md`는 `.validator(...)`만 쓰고, `guide/middleware.md`의 비교 표는 `Input Validation | No | Yes (`.validator()`)`다.
  - migration page: 제거된 API 표가 server function과 middleware의 `.inputValidator()`를 `.validator()`로 대응시킨다.
- **이전의 "런타임에서 계속 해석된다"는 기록은 이제 거짓이다.** 그 기록은 commit `fe7f1fd0e6ef73c3f341dd2338b406749538a85d`의 `createServerFn.ts:921`에 있던 `options.validator ?? options.inputValidator` fallback을 설명한 것이고, 그 fallback은 더 이상 없다. `.validator(...)`가 정본이라는 앞선 수정은 맞았지만, 별칭이 계속 동작한다는 부분은 그 commit에 한정된 사실이었다.
- **Start는 stable이고 Release Candidate가 아니다.** overview page는 이제 "TanStack Start is stable."로 시작한다.
- **Vite 8이 필수이고 Node는 22.12 이상이다.** `@tanstack/react-start@1.169.4`는 `peerDependencies.vite >=8.0.0`과 `engines.node >=22.12.0`을 선언하고, release note는 "Vite 7 is no longer supported."라고 밝힌다.
- 2026-06-02 스냅샷의 더 깊은 이력(리네임이 병합된 지 사흘 뒤에 문서의 반대를 기록한 pass)은 경고로만 남긴다. 날짜가 박힌 스냅샷은 그것을 만든 pass만큼만 믿을 수 있다.

## 서버 함수

- `createServerFn()`이 서버 함수를 정의한다. `method`의 기본값은 `GET`이며, 다른 형태는 `createServerFn({ method: 'POST' })`다. `Method`는 정확히 `'GET' | 'POST'`다. `packages/start-client-core/src/createServerFn.ts:449`가 `export type Method = 'GET' | 'POST'`다. 다른 메서드는 없다.
- `.handler(...)`가 체인을 끝내는 종단 호출이다. 여기서 구현을 정의한다. 입력 검증은 `.validator(...)`가 붙이고 그 앞에 `.middleware([...])`가 미들웨어를 붙인다. `.inputValidator(...)`는 없다.
- `strict` 옵션이 있고 기본값은 `strict: true`다. TypeScript 수준의 직렬화 검사를 제어한다. `createServerFn({ strict: false })`와 세분화된 `strict: { input: false }` / `strict: { output: false }` 형태로 해제한다. 문서는 `strict: false`가 타입 검사만 완화한다고 경고한다. 값은 여전히 런타임 직렬화 계층이 제대로 처리해야 한다.
- 파일 구성: 문서는 `*.functions.ts`(서버 함수 래퍼) / `*.server.ts`(서버 전용 헬퍼) 분리를 "one approach"로 소개하며, 강제가 아니다. import protection은 그 명명을 강제하지 않는다. 강제되는 패턴은 `*.server.*`와 `*.client.*`뿐이다.
- 서버 함수의 정적 import는 안전하다. 문서는 동적 import를 피하라고 경고한다(`guide/server-functions.md:150`: "Avoid dynamic imports for server functions").
- 서버 함수는 같은 출처의 앱 RPC 엔드포인트다. loaders, components, hooks, 다른 서버 함수, event handlers에서 호출할 수 있다. hook 사용성이 필요하면 React 래퍼인 `useServerFn()`을 쓴다.

## 실행 경계

- `createServerFn`, `createServerOnlyFn`, `createClientOnlyFn`, `createIsomorphicFn`이 공식 실행 제어 프리미티브다.
- `createIsomorphicFn()`은 `.server(...)`와 `.client(...)`로 환경별 구현을 가진 함수 하나를 구성한다. 한쪽이 없으면 오류가 아니라 `undefined`를 돌려주는 no-op이다.
- `createServerOnlyFn(...)`과 `createClientOnlyFn(...)`은 환경에 묶인 실행을 강제하고, 잘못된 환경에서 호출하면 설명이 담긴 런타임 오류를 던진다.
- 환경 함수는 번들별로 트리 셰이킹된다. `.client()` 본문은 서버 번들에서 빠지고 그 반대도 마찬가지다.
- loader는 서버 전용이 아니라 isomorphic이다. 문서의 "Common Problems" 절이 그 반대로 가정하는 것을 대표적인 비밀 유출 실수로 지목한다.

## 전역 Start 설정

- `src/start.ts`는 기본 Start 템플릿에 **포함되지 않는다**. 전역 미들웨어나 Start 수준 옵션이 필요할 때 만든다.
- 정본 형태는 콜백 형태다. `export const startInstance = createStart(() => ({ requestMiddleware: [...], functionMiddleware: [...] }))`. 소스 시그니처는 `createStart(getOptions: () => StartInstanceOptions | Promise<StartInstanceOptions>)`다.
- 실제 옵션 표면은 `serializationAdapters`, `defaultSsr`, `requestMiddleware`, `functionMiddleware`, `serverFns: { fetch }`다(`packages/start-client-core/src/createStart.ts:15-50`). `requestMiddleware`는 Start가 처리하는 모든 요청에 실행되고, `functionMiddleware`는 모든 서버 함수에 실행된다.
- 이 옵션들은 **새로 생긴 것이 아니다.** 은퇴한 2026-06-02 스냅샷보다 먼저 존재했다. 그 파일이 이들을 나열하지 않았을 뿐이므로, 누락은 상류 드리프트가 아니라 이 스킬 자체의 누락이었다.

## CSRF 보호

- `createCsrfMiddleware()`가 서버 함수를 교차 사이트 요청에서 보호하는 이름 있는 API다. 가이드의 권장 설치는 filter를 함께 쓴다. `createCsrfMiddleware({ filter: (ctx) => ctx.handlerType === 'serverFn' })`이고, 이유는 "by default, `createCsrfMiddleware()` validates every request handled by the middleware"다. `Sec-Fetch-Site`, `Origin`, `Referer`를 검사해 same-origin임을 증명할 수 없는 요청을 거부하고, 셋 다 없는 요청은 `allowRequestsWithoutOriginCheck: true`가 아니면 거부한다. 옵션은 `filter`, `origin`, `secFetchSite`(기본 `'same-origin'`), `referer`(기본 `true`), `allowRequestsWithoutOriginCheck`(기본 `false`), `failureResponse`(기본 `403 Forbidden`)이다. 가이드가 문서화한 것은 `filter`, `origin`, `allowRequestsWithoutOriginCheck`이고 나머지는 type 수준 사실이다.
- **앱이 `src/start.ts`를 정의하지 않으면 Start가 서버 함수용으로 이 미들웨어를 자동 설치한다.** 함정은 여기 있다. `src/start.ts`를 만들면 그 자동 설치가 조용히 빠지므로, 그 파일이 CSRF 미들웨어를 명시적으로 넣어야 한다. `src/start.ts`가 있는데 이 미들웨어가 없으면 Start가 서버 함수 요청에 대해 개발 경고를 남긴다.

## 미들웨어

- 미들웨어는 두 종류다. 요청 미들웨어는 `createMiddleware()`를 쓴다. `createMiddleware({ type: 'request' })`도 허용되지만 요청 타입이 기본값이다. 서버 함수 미들웨어는 `createMiddleware({ type: 'function' })`를 쓰고 `.client(...)`와 `.server(...)` 단계를 정의할 수 있다.
- 서버 함수 미들웨어 검증도 `.validator(...)`를 쓴다. 같은 1.169.0 release에서 `inputValidator`가 `createMiddleware`에서 제거됐다. 미들웨어 `.validator(...)`와 서버 함수 `.validator(...)`를 혼동하지 않는다. 둘은 서로 다른 체인 객체와 서로 다른 데이터 문맥에 속한다.
- route guard는 data authorization 경계가 아니다. 미들웨어와 `beforeLoad`가 페이지 접근을 막을 수는 있지만, 서버 함수나 서버 라우트가 돌려주는 데이터는 세션 주체에 대한 자체 검사를 거쳐야 한다.
- `sendContext`는 명시적이고 홉마다 단방향이다. 클라이언트 문맥은 기본적으로 서버로 전송되지 않는다. `next({ sendContext: {...} })`로 넘겨야 한다. 클라이언트가 보낼 수 있는 값은 클라이언트가 거짓으로 바꿀 수 있으므로, `sendContext`로 도착한 값은 클라이언트가 제공한 데이터다.
- **"Shape validation is not authorization."** (`guide/middleware.md:348`.) 파싱된 UUID나 숫자는 형태가 올바른 식별자일 뿐, 권한이 부여된 식별자가 아니다. 그 값이 어떤 행을 읽거나 쓸지 고르는 데 쓰이면(쿼리 키, 필터, 경로 파라미터) 세션 주체가 그 값에 접근 권한이 있는지 따로 검증해야 한다. 그렇지 않으면 로그인한 사용자가 자기 요청에서 값을 바꿔 다른 테넌트의 데이터에 닿을 수 있다.
- 문서가 요구하는 패턴(`guide/middleware.md:377`): "Always derive the session itself from a server-trusted source (a cookie + DB lookup in `authMiddleware`), never from `sendContext`. Anything the client can send, the client can lie about."

## import protection

- **상태: 문서화됨, Experimental 표시 없음.** 페이지는 "Import protection prevents server-only code from leaking into client bundles and client-only code from leaking into server bundles. It runs inside TanStack Start and is enabled by default."로 시작한다. 문서화된 옵션은 `enabled`, `behavior`, `log`, `include`, `exclude`, `maxTraceDepth`, 환경별 `files`/`specifiers`/`excludeFiles`, `ignoreImporters`, `onViolation`이다.
- 기본 활성화다. 문서화된 기본값은 `enabled: true`, `behavior: { dev: 'mock', build: 'error' }`(`'mock'`은 경고 후 mock 모듈로 대체하고 `'error'`는 빌드를 실패시킨다), `log: 'once'`(반복 위반을 중복 제거한다), 범위 `include` = Start의 `srcDirectory`, `maxTraceDepth: 20`이다.
- 기본 거부 규칙은 `client.files` = `['**/*.server.*']`, `server.files` = `['**/*.client.*']`, `client.specifiers` = 프레임워크 서버 specifier, `server.specifiers` = `[]`, 그리고 양쪽 `excludeFiles` = `['**/node_modules/**']`다.
- **함정은 replace 대 additive 구분이다.** 옵션 표(`guide/import-protection.md:561-567`)에 따르면 다음과 같다.
  - `client.specifiers`는 기본값에 **더해진다**(additive). 제공하면 내장 목록이 확장된다.
  - `client.files`, `client.excludeFiles`, `server.files`, `server.specifiers`, `server.excludeFiles`는 기본값을 **대체한다**. (`server.specifiers`는 "replaces defaults"로 적혀 있지만 기본값이 `[]`이므로 실제로는 additive가 아니다.)
  - `excludeFiles`는 `['**/node_modules/**']`를 **통째로 대체한다**. `node_modules`를 계속 건너뛰면서 경로를 더 제외하려면 둘 다 넘긴다: `excludeFiles: ['**/node_modules/**', '**/vendor/**']`.
  - 따라서 `'**/*.server.*'`를 함께 넣지 않고 `client.files`를 설정하면 기본 거부 규칙이 조용히 사라진다.
- `excludeFiles: []`는 기본값이 건너뛰는 위치(`node_modules` 등)의 resolved-target 검사를 다시 켠다. 권장이 아니라 의도적인 opt-in이다.
- type-only import와 re-export는 런타임에서 제거되므로 무시된다. 런타임 값을 하나라도 담은 mixed import는 여전히 검사 대상이다.
- 명시적 경계용 side-effect marker import는 그대로 쓸 수 있다: `@tanstack/react-start/server-only`, `@tanstack/react-start/client-only`.
- `mockAccess`(`'error' | 'warn' | 'off'`, 선택)는 `@tanstack/start-plugin-core@1.171.55`의 `schema.d.ts`에 있지만 **import protection 가이드에는 없다**. 실제 스키마 옵션이면서 문서가 다루지 않는 항목이므로, 인용할 때는 반드시 그 사실을 함께 적고 문서화된 옵션처럼 제시하지 않는다.
- dev mode 위반은 오탐일 수 있다. build mode는 tree-shaking 뒤까지 검사를 미루므로 production graph에서 사라지는 import가 dev에서 경고로 남는다. boundary를 고치기 전에 production build로 확인한다.

## 서버 라우트

- 서버 라우트는 route 파일의 `createFileRoute(...)(...)` 호출에 `server`를 추가해 선언하고, Router의 파일 기반 라우팅 규칙을 따른다.
- `server` 속성은 `handlers`를 담는다. HTTP 메서드를 핸들러 함수에 매핑한 객체이거나, 미들웨어 구성이 필요한 핸들러를 위해 `createHandlers`를 받는 함수다. 그리고 선택적인 `middleware` 배열이 모든 핸들러에 라우트 수준 미들웨어를 적용한다.
- 서버 라우트 미들웨어를 묶는 데 pathless layout route와 break-out route를 쓸 수 있다. pathless layout은 라우트 묶음에 미들웨어를 더하고, break-out route는 상위 미들웨어에서 빠져나온다.
- 같은 라우트 경로에 같은 HTTP 메서드가 중복되면 무효다. wildcard/splat 라우트는 끝에 `$`를 붙이는 파일 라우트 규칙을 쓴다.

## 드리프트 처리

- 이 파일은 날짜가 박힌 공식 문서 스냅샷이며 영구 규칙집이 아니다. 파일명 날짜와 `last_verified_at`은 구조상 일치한다. 둘 중 하나가 바뀌면 둘 다 함께 바꾼다.
- 갱신 트리거: 아래 공식 문서 페이지가 바뀌었을 때, 또는 권고 확인 시점에 다시 검증한다. 고정한 패키지 버전 집합을 넘어서는지를 트리거로 삼지 **않는다**. router/start는 PATCH 릴리스에서도 파괴적 변경을 흡수하므로 버전 기반 트리거는 과하게도, 모자라게도 발동한다.
- 로컬에 설치된 패키지 타입이 이 파일과 다르면 이 스냅샷을 고치지 말고 typecheck를 돌려 프로젝트별 예외를 기록한다.
- `src/modules`, `src/lib`, `src/db`, `src/server`, `src/integrations`, `src/config` 묶음은 공식 TanStack 요구사항이 아니라 Hypercore 관례다. `.functions.ts` / `.server.ts` 분리는 공식 지침이지만, 이를 `src/modules/<domain>/<feature>/` 중첩 폴더 안에서 강제하는 것은 Hypercore 관례다.

## Sources

> 출처 확인 2026-11-04. 아래 모든 페이지와 출처는 이 스냅샷을 위해 2026-11-04에 직접 가져왔다. The `guide/` path segment is required; the same pages without it return 404. 인용한 line number는 이전에 가져온 사본에서의 위치이므로 페이지가 바뀌면 함께 이동한다. 안정된 기준은 인용문 자체다.

- <https://tanstack.com/start/latest/docs/framework/react/guide/server-functions.md>
- <https://tanstack.com/start/latest/docs/framework/react/guide/middleware.md>
- <https://tanstack.com/start/latest/docs/framework/react/guide/authentication-server-primitives.md>
- <https://tanstack.com/start/latest/docs/framework/react/migrate-from-release-candidate.md>
- <https://tanstack.com/start/latest/docs/framework/react/guide/import-protection.md>
- <https://tanstack.com/start/latest/docs/framework/react/guide/server-routes.md>
- <https://tanstack.com/start/latest/docs/framework/react/guide/code-execution-patterns.md>
- <https://tanstack.com/start/latest/docs/framework/react/guide/environment-functions.md>
- <https://registry.npmjs.org/@tanstack/start-client-core/-/start-client-core-1.170.39.tgz>
- <https://registry.npmjs.org/@tanstack/start-plugin-core/-/start-plugin-core-1.171.55.tgz>
- <https://registry.npmjs.org/@tanstack/react-start/latest>
