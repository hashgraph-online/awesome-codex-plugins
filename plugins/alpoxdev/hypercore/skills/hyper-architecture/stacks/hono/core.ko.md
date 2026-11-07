`hyper-architecture`의 Hono 스택 가이드입니다. `rules/stack-detection.ko.md`가 대상을 Hono로 라우팅하면 이 파일을 읽고, 이 파일이 그 대상의 작업을 맡습니다.

- 범위: Hono 애플리케이션을 만들거나 점검하거나 구조를 바꿀 때, 또는 기존 코드베이스에 Hono를 도입할 때 사용합니다. 앱 구성, 라우트 모듈, 미들웨어, 검증, 데이터베이스와 ORM 경계, Drizzle, 마이그레이션, 오류 처리, OpenAPI/Swagger, 테스트, 타입이 붙은 RPC를 건드리는 작업이 대상입니다. 코드를 바꾸기 전에 Hono 아키텍처 규칙을 강제합니다. Hono가 아닌 프레임워크, 아키텍처 경계를 건드리지 않는 문구 편집, Hypercore 관례 없이 공식 Hono 기본값만 원하는 요청에는 쓰지 않습니다.
- 실행 조건: Hono 애플리케이션에서 저장소를 살펴보고 공식 Hono 문서를 확인하며 직접 코드를 고칠 때 가장 잘 맞습니다.

@architecture-rules.ko.md
@../../rules/hono/project-structure.ko.md
@../../rules/hono/routes.ko.md
@../../rules/hono/handlers.ko.md
@../../rules/hono/middleware.ko.md
@../../rules/hono/validation.ko.md
@../../rules/hono/database.ko.md
@../../rules/hono/openapi.ko.md
@../../rules/hono/errors.ko.md
@../../rules/hono/testing-rpc.ko.md
@../../rules/hono/platform.ko.md
@../../rules/hono/conventions.ko.md
@../../references/official/hono/hono-docs.ko.md
@../../references/official/hono/drizzle-docs.ko.md

# Hono Architecture Enforcement

<output_language>

사용자에게 보이는 결과물, 저장하는 산출물, 보고서, 계획, 생성 문서, 요약, 핸드오프 노트, 커밋 메시지 초안, 검증 노트는 이 표준 파일이 영어로 쓰여 있어도 기본적으로 한국어로 작성합니다.

소스 코드 식별자, CLI 명령, 파일 경로, 스키마 키, JSON/YAML 필드 이름, API 이름, 패키지 이름, 고유명사, 인용한 원문은 원래 표기를 유지합니다.

사용자가 다른 언어를 명시적으로 요청했거나, 기존 산출물이 일관성을 위해 다른 언어를 유지해야 하거나, 기계가 읽는 계약이 정확한 영어 토큰을 요구할 때만 다른 언어를 씁니다. 번역본 템플릿이나 참고 자료가 있으면(예: `*.ko.md`, `*.ko.json`) 사용자에게 보이는 산출물에는 그것을 먼저 씁니다.

</output_language>

<purpose>

- 코드를 바꾸기 전에 Hypercore의 Hono 아키텍처 규칙을 적용합니다.
- Hono 전용 게이트를 적용하기 전에 대상이 실제 Hono 프로젝트인지 확인합니다.
- 라우트 구성, 핸들러, 미들웨어, 검증, 데이터베이스와 ORM, Drizzle, OpenAPI/Swagger, 플랫폼 진입점, 오류 처리, 테스트, 타입이 붙은 RPC 경계가 서로 맞도록 유지합니다.
- Hono보다 엄격한 요구사항은 판정할 때 Hypercore 관례라고 표시합니다.

</purpose>

<routing_rule>

Hono 앱의 구현, 리뷰, 교정, 아키텍처 강제에 사용합니다.

Hono가 아닌 프로젝트, 일반적인 Express/Fastify 작업, 아키텍처 경계를 건드리지 않는 문구 편집, Hypercore 관례 없이 공식 Hono 기본값만 원한다고 밝힌 요청에는 강제하지 않습니다.

이 스킬은 스스로 완결됩니다. Hono 규칙을 적용하려고 전역 스킬이나 외부 오케스트레이션 표면에 기대지 않습니다.

</routing_rule>

<instruction_contract>

| Field | Contract |
|---|---|
| Intent | Hono 프로젝트를 공식 Hono 동작과, 그와 구분해 표시한 Hypercore 관례에 맞춰 아키텍처 측면에서 안전하고 타입이 맞고 문서화된 상태로 유지합니다. |
| Trigger | 라우트, 핸들러, 미들웨어, 검증, DB/ORM, Drizzle, OpenAPI, 플랫폼 진입점, 오류 처리, 테스트, RPC를 다루는 Hono 작업. |
| Scope | 수정하는 Hono 소스, 주제별 규칙 파일, 공식 참고 자료, 검증 노트, 되돌리기 쉬운 작은 아키텍처 수정을 검토하고 안내합니다. |
| Authority | 사용자와 프로젝트 지시가 이 스킬보다 우선합니다. API 사실에서는 공식 Hono/Drizzle 문서가 Hypercore 관례보다 우선합니다. 안전성, 타입, 검증, 데이터 경계 규칙은 위험한 변경을 막습니다. |
| Evidence | 프로젝트 표지, 로컬 패키지와 소스 파일, 손댄 경로, 주제별 규칙, API가 달라졌을 때의 공식 참고 자료, 검증 명령 출력을 근거로 씁니다. |
| Tools | 로컬 검색·읽기·편집·검증 명령을 씁니다. 마이그레이션, 자격 증명 접근, 프로덕션 부작용, 런타임 어댑터 교체, 광범위한 재작성은 게이트를 둡니다. |
| Loop | 최적화 루프는 두지 않습니다. 교정 패스 뒤 Step 3 게이트와 손댄 검사에 대고 검증-수리를 최대 두 번 돌립니다. 변경이 손댄 범위 안에 있고 그 게이트를 통과할 때만 남기고, 검증 체크리스트를 통과하거나 블로커를 보고하면 멈춥니다. |
| Output | 규칙 분류, 변경한 파일, 검증 근거, 남은 위험, 공식과 Hypercore 구분 라벨을 담은 한국어 아키텍처 판정이나 구현 요약. |
| Verification | 완료를 선언하기 전에 해당 프로젝트 검사와 손댄 영역의 최종 체크리스트를 돌립니다. |
| Stop condition | 프로젝트 모드를 확인했고, 적용되는 게이트를 통과했거나 블로커로 보고했고, 검증 근거를 남긴 상태에서 멈춥니다. |

</instruction_contract>

<activation_examples>

Positive examples:

- `Review this Hono app structure before I add more routes.`
- `Refactor a Hono API so routing, middleware, and validators follow one architecture.`
- `Add a new Hono route and make sure testClient and AppType inference still work.`
- `Wire Drizzle into this Hono API without routes talking to the database directly.`
- `Review database, migration, and OpenAPI boundaries before adding a new persisted endpoint.`
- `hyper-architecture 전체 수정`
- `Run the Hono architecture skill in full-remediation mode.`

Negative examples:

- `Create a generic Express middleware guide.`
- `Review a React SPA that does not use Hono.`

Boundary examples:

- `Make a tiny copy-only response text change in a Hono handler.`
  아키텍처 경계가 걸리지 않으면 직접 고쳐도 됩니다.
- `Use official Hono defaults only, not the extra hypercore conventions.`
  이 스킬은 그대로 적용하되, 공식 문서를 넘어서는 Hypercore 전용 엄격함은 풉니다.

</activation_examples>

<trigger_conditions>

인자는 교정 범위를 바꾸고, 핵심 규칙은 바꾸지 않습니다.

| 인자 | 의미 |
|---|---|
| 없음 | 요청받았거나 손댄 Hono 범위를 검토하고 고칩니다. 손대지 않은 레거시 편차는 Hypercore 전용이거나 마이그레이션 위험이 크면 백로그로 보고할 수 있습니다. |
| `전체 수정` | 전체 교정 모드. 감지한 Hono 애플리케이션 전체를 훑어 안전하고 국소적이며 되돌릴 수 있고 검증 가능한 위반을 모두 고칩니다. 손댄 파일에서 멈추지 않습니다. |
| `full fix` / `fix all` | `전체 수정`과 같습니다. |
| `공식 기본만` / `official defaults only` | 공식 Hono 동작을 기본 표면으로 쓰고, Hypercore 전용 관례는 사용자가 `전체 수정`도 함께 요청하지 않는 한 선택 사항 판정으로 낮춥니다. |

`전체 수정` 모드에서는 다음을 지킵니다.

- Hono 앱 파일, 라우트 모듈, 핸들러, 미들웨어, 검증 스키마, OpenAPI 파일, 데이터베이스와 리포지터리 경계, 테스트와 RPC 표면, 런타임 진입점을 모두 범위에 넣습니다.
- 감지한 Hono 소스 트리 전체에서 폴더와 파일 이름을 훑습니다. `package.json`, `tsconfig.json`, `drizzle.config.ts`, 잠금 파일, 생성된 선언, 설정으로 지정한 마이그레이션 산출물처럼 프레임워크나 도구가 요구하는 이름이 아니면 kebab-case여야 합니다.
- import, 테스트 경로, 라우트 참조, 설정 참조를 같은 변경에서 안전하게 고칠 수 있으면 camelCase나 PascalCase 폴더와 파일을 kebab-case로 바꿉니다.
- Step 3.5의 위험도 낮은 자동 교정을 손댄 파일만이 아니라 앱 전체에 적용합니다.
- 한 번에 안전하게 끝낼 수 없는 위험한 변경은 파일 경로와 실패한 규칙을 붙여 정확한 블로커나 백로그 항목으로 남깁니다. 조용히 넘기지 않습니다.

</trigger_conditions>

<skill_architecture>

- 핵심(`stacks/hono/core.md`): 트리거, 계약, 게이트 순서, 교정 정책, 검증, 정지 조건.
- 규칙: `stacks/hono/architecture-rules.ko.md`와 `reference_routing`에 매핑된 주제별 파일.
- 참고: `references/official/hono/hono-docs.ko.md`와 `references/official/hono/drizzle-docs.ko.md`에 날짜가 붙은 공식 사실을 둡니다.
- 자산: `assets/evals/hono-cases.jsonl`에 트리거와 동작 사례를 둡니다.
- 번들 스크립트는 없습니다. `testClient`, 타입 검사, 주제별 체크리스트가 검증 수단입니다.
- 이 스킬은 스스로 완결됩니다. 다른 스킬의 경로, 문서, 호출을 필요로 하지 않습니다.

</skill_architecture>

<loop_policy>

- 최적화 루프는 없습니다. 요청마다 리뷰나 교정을 한 번 돕니다.
- 교정 뒤에는 Step 3 게이트와 손댄 검사에 대고 검증-수리를 최대 두 번 돌립니다. 변경은 손댄 범위 안에 있고 그 게이트를 통과할 때만 남깁니다.
- 체크리스트를 처음 통과하거나 블로커를 보고할 때 루프가 끝납니다. 결과를 초록으로 만들려고 손댄 범위를 넓히지 않습니다.

</loop_policy>

<language_and_translation_default>

판정, 교정 요약, 검증 노트는 한국어로 씁니다. 식별자, 경로, 폴더 이름, API 이름, `official`과 `hypercore-only` 라벨은 원래 표기를 유지해 규칙 파일과 일대일로 맞출 수 있게 합니다. `stacks/hono/core.ko.md`는 이 파일과 절 단위로 짝을 이루며, 규칙을 바꾸면 같은 편집에서 함께 바꿉니다.

</language_and_translation_default>

<reference_routing>

편집 전에 `stacks/hono/architecture-rules.md`를 읽습니다. 그다음 손댄 영역을 맡은 파일 하나를 엽니다.

| 손댄 영역 | 파일 |
|---|---|
| 프로젝트 프로필, 폴더 소유, 의존 방향, 모노레포, 구조 마이그레이션 | `rules/hono/project-structure.md` |
| 라우트 구성, 마운트 순서, fallback 배치, 서브 앱 구조 | `rules/hono/routes.md` |
| 핸들러 분리, `createFactory()`, `createHandlers()`, 타입이 붙은 context 흐름 | `rules/hono/handlers.md` |
| 공유 요청 경계, auth/logging/request-id 흐름, `c.set()` / `c.get()` | `rules/hono/middleware.md` |
| params, query, json, form 검증 선택 | `rules/hono/validation.md` |
| 데이터베이스 클라이언트, 리포지터리, ORM 경계, Drizzle 스키마, 마이그레이션, 트랜잭션, D1, Neon, Turso/libSQL, `DATABASE_URL` | `rules/hono/database.md` |
| OpenAPI 생성, Swagger UI, operation 메타데이터, 스키마 드리프트, 문서 엔드포인트 | `rules/hono/openapi.md` |
| `HTTPException`, `app.onError()`, 응답 형태 | `rules/hono/errors.md` |
| `testClient()`, `hc<AppType>`, `AppType`, 큰 앱에서의 추론 | `rules/hono/testing-rpc.md` |
| 어댑터, 진입점, 바인딩, env/config 타입, `basePath()` 경계 | `rules/hono/platform.md` |
| 손대는 파일의 이름 규칙, TypeScript 스타일, import, 주석 | `rules/hono/conventions.md` |
| 지연, 처리량, 라우터 선택, 응답 압축, ETag, 공유 캐시, 번들 크기 | `rules/hono/performance.md` |
| lint, format, type-check, tsconfig, package manager, CI 검사 순서 | `rules/setup/typescript.md` |
| 규칙 뒤에 있는 공식 Hono 동작, 또는 공식 기본값 요청 | `references/official/hono/hono-docs.md` |
| `rules/hono/database.md` 주장 뒤에 있는 Drizzle 동작 | `references/official/hono/drizzle-docs.md` |

사용자가 공식 기본값을 요청하면 `references/official/hono/hono-docs.md`에서 시작하고, Hypercore 전용 규칙은 선택 사항 덧씌움으로 다루며, 어떤 판정이 어느 쪽인지 표시합니다.

</reference_routing>

<support_file_read_order>

1. 규칙 분류와 게이트 요약을 위해 `stacks/hono/architecture-rules.md`.
2. 손댄 영역의 주제 파일. 순서는 `reference_routing` 표를 따릅니다.
3. 파일 이름이나 스타일을 고치기 전에 `rules/hono/conventions.md`.
4. 공식 동작이 걸리거나 공식 기본값 요청이 있으면 `references/official/hono/hono-docs.md`.
5. 데이터베이스 동작이 범위에 들어오면 `references/official/hono/drizzle-docs.md`.

</support_file_read_order>

<workflow>

| 단계 | 할 일 | 산출물 |
|---|---|---|
| 1 | 대상이 Hono 프로젝트인지 확인합니다. | 범위 판정 |
| 2 | 손댄 영역의 규칙 파일을 읽습니다. | 최소 근거 묶음 |
| 3 | 계획한 변경을 핵심 게이트에 대봅니다. | 파일 경로가 붙은 판정 |
| 3.5 | 손댄 범위 안에서 위험도 낮은 자동 교정을 적용합니다. | 편집 또는 백로그 항목 |
| 4 | 아래 파일 순서로 구현하고 검증합니다. | 변경한 파일과 근거 |

1단계 — 프로젝트 확인:

```bash
rg -n '"hono"|@hono/' package.json
rg -n "from 'hono'|from \"hono\"" src app .
rg -n "new Hono\\(|createFactory\\(|testClient\\(|hc<|OpenAPIHono|swaggerUI|hono/mount|methodNotAllowed|from '@hono/" src app .
```

이 표지가 하나도 없으면 Hono 규칙을 강제하지 않고 일반 구현이나 리뷰 경로로 돌려보냅니다.

데이터베이스 작업이 범위에 들어오면 데이터베이스 표지도 확인합니다.

```bash
rg -n '"drizzle-orm"|drizzle-kit|DATABASE_URL|D1Database|@neondatabase|@libsql|pg|postgres' package.json drizzle.config.ts src app .
rg -n "from 'drizzle-orm|from \"drizzle-orm|db\\.|transaction\\(|migrate\\(|schema|repositories?" src app .
```

`전체 수정` 모드가 켜져 있으면 편집 전에 넓게 훑습니다.

```bash
rg --files src app routes 2>/dev/null
rg -n "new Hono\\(|app\\.route\\(|app\\.mount\\(|hono/mount|methodNotAllowed|basePath\\(|validator\\(|zValidator\\(|standardValidator\\(|OpenAPIHono|swaggerUI|testClient\\(|hc<|drizzle-orm|DATABASE_URL|D1Database|@neondatabase|@libsql" src app .
```

3단계 — 핵심 게이트. 브라운필드 규칙: 손대지 않은 레거시 스타일 편차는 백로그로 넘길 수 있습니다. 안전성, 타입, 검증, 영속성, OpenAPI, 런타임 경계 문제는 손댄 작업에서 계속 막습니다. `전체 수정` 모드에서는 감지한 Hono 앱 전체가 손댄 범위입니다.

- 런타임에 중립적인 Hono 앱 하나와 분명한 마운트 표 하나를 둡니다. 근거가 뒷받침하는 가장 작은 구조 프로필을 고르고 의존 방향을 지킵니다.
- 손댄 라우트 모듈이 service를 건너뛰고 DB/ORM/스키마/SDK/런타임 어댑터 세부를 직접 import하지 않습니다.
- 사소하지 않은 params, query, json, form 데이터는 도메인 로직 전에 validator 미들웨어로 검증합니다. form과 multipart 검증은 Hono 4.13.16 이상을 요구합니다.
- 분리한 핸들러는 인라인 체이닝이나 `createFactory()` / `createHandlers()`로 타입을 유지합니다.
- 공유 context를 쓰면 미들웨어 순서와 `Bindings`/`Variables` 타입을 명시합니다.
- 손댄 code는 4.x에서 deprecated된 API(`app.mount()`, `hono/<adapter>` import, `@hono/node-ws`)를 쓰지 않고, `methodNotAllowed()`를 켜서 404 계약을 암묵적으로 바꾸지 않습니다.
- Drizzle 스키마, 마이그레이션, 클라이언트, 트랜잭션은 데이터베이스와 service 경계 뒤에 둡니다.
- 공개 문서화 라우트는 런타임 검증, DTO, OpenAPI/Swagger, RPC 응답 형태를 서로 맞춰 둡니다.
- 런타임 어댑터와 부트스트랩 코드는 플랫폼 경계에 둡니다.
- 소스 폴더와 파일은 도구나 외부 계약이 다른 이름을 요구하지 않는 한 kebab-case를 씁니다.

교정 세부는 연결된 지원 파일의 체크리스트를 씁니다. 이 핵심 파일은 그것을 다시 적지 않습니다.

3.5단계 — 자동 교정. 국소적이고 되돌릴 수 있고 위험도 낮은 문제는 바로 고칩니다.

- 손댄 camelCase나 PascalCase 소스 폴더·파일을 kebab-case로 바꾸고 import와 참조를 갱신합니다.
- 손댄 라우트에 빠진 validator 미들웨어를 추가합니다.
- 공유 RPC나 클라이언트 계약이 그것에 기대면 `AppType` 타입 export를 추가합니다.
- 라우트 마운트를 구성 파일 하나로 모읍니다.
- 분리된 타입 없는 핸들러를 `createFactory()` / `factory.createHandlers()`로 바꿉니다.
- `app.onError()`를 추가하거나 HTTP 예외 변환을 개선합니다.
- 런타임 어댑터 import를 핸들러와 라우트 모듈 밖으로 옮깁니다.
- 손댄 직접 데이터베이스 호출을 기존 service나 리포지터리로 옮기고, 손댄 쿼리에 빠진 리포지터리 래퍼를 추가합니다.
- 반복되는 데이터베이스 클라이언트 import를 기존 데이터베이스 클라이언트 경계로 모읍니다.
- 저장소가 이미 스펙을 공개하면 손댄 공개 라우트에 빠진 OpenAPI 메타데이터를 추가합니다.
- Swagger UI 노출을 기존 docs/admin/dev 경계 뒤로 옮깁니다.

다음처럼 광범위하거나 깨질 수 있는 마이그레이션은 근거 없이 스스로 적용하지 않습니다. 대량 라우트·모듈 이름 변경(참조를 모두 갱신하고 검증한 `전체 수정` 모드의 kebab-case 변경은 예외), 앱 전체 계층 재작성, 저장소 전체 검증 라이브러리 교체, 기존 클라이언트를 깨는 RPC 형태 변경, 런타임 어댑터 교체, 데이터베이스 provider나 ORM이나 dialect 교체, 프로덕션 마이그레이션 생성·적용·삭제, 스키마 테이블·컬럼·인덱스 이름 변경, 테스트 없는 트랜잭션 경계 재작성, 앱 전체 OpenAPI 생성기 교체가 여기에 해당합니다.

4단계 — 구현 순서:

1. 현재 구조와 규칙 위반을 확인합니다. `전체 수정` 모드에서는 편집 전에 감지한 Hono 앱 전체를 목록화합니다.
2. 뒤따르는 import와 테스트가 안정된 경로에 기대므로, 안전하면 폴더와 파일 이름을 먼저 kebab-case로 맞춥니다.
3. 라우트 구성과 타입 경계를 고칩니다.
4. 손댄 영속성 동작의 데이터베이스, 리포지터리, 연결 경계를 고칩니다. `전체 수정` 모드에서는 앱 전체를 고칩니다.
5. 검증과 미들웨어 순서를 고칩니다.
6. 손댄 공개 라우트의 OpenAPI/Swagger 계약 드리프트를 고칩니다. `전체 수정` 모드에서는 문서화된 모든 라우트를 고칩니다.
7. 오류 처리와 응답 형태를 고칩니다.
8. 테스트와 RPC 추론 회귀를 고칩니다.
9. 검증을 돌립니다.

</workflow>

<required>

- Hono 규칙을 적용하기 전에 확인한 Hono 프로젝트. 요청이 Hono 범위를 벗어나면 그 이유를 밝힙니다.
- 분명한 마운트 표가 있는 런타임 중립 앱 구성 하나와, 저장소 근거로 정당화한 구조 프로필.
- 저장소의 기존 계층 유지. 라우트가 DB/ORM 클라이언트, 스키마 테이블, 마이그레이션 도우미에 직접 닿지 않습니다.
- 사소하지 않은 요청 입력의 런타임 검증과, 공유 context를 쓰는 곳의 `Bindings`/`Variables` 타입.
- 각 판정에 `official` 또는 `hypercore-only` 라벨을 붙인 보고.
- 해당 표면이 있을 때 `testClient` / `hc` / 타입 검사로 남긴 검증 근거.

</required>

<forbidden>

- 요청이 비슷하게 들린다는 이유로 Express, Fastify, 다른 프레임워크에 Hono 규칙을 강제하는 것.
- 명시적 권한 없이 프로덕션 마이그레이션 이름을 바꾸거나, 마이그레이션을 적용하거나, 스키마 테이블·컬럼·인덱스 이름을 바꾸는 것.
- 아키텍처 리뷰 중에 런타임 어댑터, 데이터베이스 provider, ORM, dialect, 드라이버를 교체하는 것.
- 결정을 기록하지 않고 응답 형태를 바꿔 기존 RPC 클라이언트를 깨뜨리는 것.
- Hypercore 관례를 공식 Hono 동작처럼 제시하는 것.
- 손대지 않은 레거시 코드에 같은 패턴이 있다는 이유로 차단 게이트를 끄는 것.
- 돌리지 않은 검사를 돌렸다고 하거나, 출력 없이 게이트를 통과로 보고하는 것.

</forbidden>

<validation>

- [ ] Hono 프로젝트 감지를 확인했다.
- [ ] 손댄 영역의 규칙 파일을 읽었고, 요청이 있으면 공식 기본값 모드를 적용했다.
- [ ] 손댄 파일과 폴더가 kebab-case를 따르고, `전체 수정` 모드에서는 소스 트리 전체를 훑어 위반을 확인했다.
- [ ] 라우트 구성이 분명하고 마운트 가능하며, 의존 방향이 저장소 근거로 정당화된다.
- [ ] 미들웨어 순서를 확인했고 타입이 붙은 context 바인딩이 명시되어 있다.
- [ ] 사소하지 않은 입력에 검증이 걸려 있다.
- [ ] 손댄 라우트가 DB/ORM 클라이언트, Drizzle 스키마 테이블, 마이그레이션 도우미를 직접 import하지 않는다.
- [ ] 데이터베이스 클라이언트 수명이 한 곳에서 관리되고 런타임에 맞으며, 스키마와 마이그레이션 경로가 설정과 맞는다.
- [ ] 영향을 받는 여러 단계 쓰기에 트랜잭션이 명시되어 있다.
- [ ] 손댄 문서화 라우트의 OpenAPI/Swagger 문서와 Swagger UI 노출이 갱신되었고 환경에 맞는다.
- [ ] 오류 처리 정책이 명시적이고, 해당하면 `testClient` / `hc` / `AppType` 추론이 여전히 동작한다.
- [ ] API DTO, OpenAPI 스키마, RPC 응답 형태가 ORM 원본 행을 노출하지 않는다.
- [ ] 런타임 어댑터 코드가 경계에 머문다.
- [ ] 최종 판정이 공식 Hono 규칙과 Hypercore 전용 관례를 구분한다.

</validation>
