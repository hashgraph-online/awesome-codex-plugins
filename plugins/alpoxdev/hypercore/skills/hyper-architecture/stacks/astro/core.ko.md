`hyper-architecture`의 Astro 스택 가이드입니다. `rules/stack-detection.md`가 대상을 Astro로 라우팅하면 이 파일을 읽고, 이 파일이 그 대상의 작업을 맡습니다.

- 범위: Astro 프로젝트를 만들거나 점검하거나 구조를 바꿀 때, 또는 기존 사이트를 Astro로 옮길 때 사용합니다. 페이지 라우팅, 렌더링 모드와 어댑터, 아일랜드와 프레임워크 통합, 콘텐츠 컬렉션, Actions, 미들웨어, 세션, 환경 변수, 라우트 캐싱, 테스트, 빌드 성능을 건드리는 작업이 대상입니다. 현재 공식 Astro 동작(7.x, 2026-11-07 스냅숏)과, 그와 구분해 표시한 Hypercore 관례를 함께 강제합니다. Astro 의존성이 없는 Vite 앱, Next.js·TanStack Start·Expo·Lynx 앱, 단독 Hono 서버, 아키텍처 경계를 건드리지 않는 문구만 고치는 편집에는 쓰지 않습니다.
- 실행 조건: 저장소를 살펴보고 `references/official/astro/astro-2026-11-07.md`로 공식 Astro 문서를 확인하며 Astro 프로젝트의 코드를 직접 고칠 때 가장 잘 맞습니다.

@architecture-rules.ko.md
@../../rules/astro/project-structure.ko.md
@../../rules/astro/rendering-and-islands.ko.md
@../../rules/astro/content.ko.md
@../../rules/astro/actions-middleware-env.ko.md
@../../rules/astro/testing.ko.md
@../../rules/astro/performance.ko.md
@../../references/official/astro/astro-2026-11-07.ko.md

# Astro Architecture Enforcement

<output_language>

사용자에게 보이는 결과물, 저장하는 산출물, 보고서, 계획, 생성 문서, 요약, 핸드오프 노트, 커밋 메시지 초안, 검증 노트는 이 표준 파일이 영어로 쓰여 있어도 기본적으로 한국어로 작성합니다.

소스 코드 식별자, CLI 명령, 파일 경로, 스키마 키, JSON/YAML 필드 이름, API 이름, 패키지 이름, 고유명사, 인용한 원문은 원래 표기를 유지합니다.

사용자가 다른 언어를 명시적으로 요청했거나, 기존 산출물이 일관성을 위해 다른 언어를 유지해야 하거나, 기계가 읽는 계약이 정확한 영어 토큰을 요구할 때만 다른 언어를 씁니다. 번역본 템플릿이나 참고 자료가 있으면(예: `*.ko.md`, `*.ko.json`) 사용자에게 보이는 산출물에는 그것을 먼저 씁니다.

</output_language>

<purpose>

- Astro 규칙을 적용하기 전에 대상이 Astro 프로젝트인지 확인하고 어떤 신호로 판정했는지 기록합니다.
- 서버 기능을 권하기 전에 렌더링 모드(`output`)와 어댑터를 먼저 확정합니다. Actions, 세션, 서버 아일랜드, 라이브 컬렉션, 라우트 캐싱은 모두 어댑터를 필요로 합니다.
- `src/pages/` 라우팅, 아일랜드 하이드레이션, 콘텐츠 컬렉션, 서버 진입점, 환경 경계를 서로 어긋나지 않게 유지합니다.
- 공식 동작보다 엄격한 요구사항에는 Hypercore 관례라는 라벨을 붙여 보고합니다.
- 버전에 민감한 사실은 `references/official/astro/astro-2026-11-07.md`에 두어 이 핵심 파일을 가볍게 유지하고 300줄 상한을 지킵니다.

</purpose>

<routing_rule>

Astro 구현, 리뷰, 교정, 아키텍처 강제에 이 가이드를 씁니다.

Astro 의존성이 없는 Vite 프로젝트, 다른 앱 프레임워크, 단독 Hono 서버, 아키텍처 경계를 건드리지 않는 문구 편집에는 강요하지 않습니다. Astro 프로젝트도 `vite`에 의존하고 `hono`에 의존할 수 있지만, 그것은 Astro 대상의 구현 세부이지 별도 스택이 아닙니다. `astro/hono`로 붙인 Hono 계층은 그 계층 자체를 손댈 때만 Hono 가이드를 추가합니다.

이 스킬은 스스로 완결됩니다. Astro 규칙을 적용하려고 다른 스킬이나 외부 조율 표면에서 막히지 않습니다.

</routing_rule>

<instruction_contract>

| Field | Contract |
|---|---|
| Intent | Astro 프로젝트를 공식 Astro 7.x 동작과, 그와 구분해 표시한 Hypercore 관례에 맞춰 아키텍처 측면에서 안전하게 유지합니다. |
| Trigger | 페이지와 라우트, 엔드포인트, `output`과 어댑터, 아일랜드, 콘텐츠 컬렉션, Actions, 미들웨어, 세션, env, 캐싱, 테스트, 빌드 성능을 다루는 Astro 작업. |
| Scope | 수정하는 Astro 소스, 주제별 규칙 파일, 날짜가 붙은 공식 스냅숏, 검증 노트, 되돌리기 쉬운 작은 아키텍처 수정을 검토하고 안내합니다. |
| Authority | 사용자와 프로젝트 지시가 이 스킬보다 우선합니다. 프레임워크 동작에서는 공식 Astro 문서가 Hypercore 관례보다 우선합니다. 안전, 권한, 비밀 값, 데이터 경계 규칙은 위험한 변경을 막습니다. |
| Evidence | 프로젝트 표지, 로컬 매니페스트와 설정, 수정한 경로, 주제별 규칙, 날짜가 붙은 스냅숏, 검증 명령 출력을 근거로 씁니다. |
| Tools | 로컬 검색, 읽기, 편집, 검증 명령을 씁니다. 마이그레이션, 자격 증명 접근, 프로덕션 부작용, 어댑터 교체, 광범위한 재작성에는 게이트를 둡니다. |
| Loop | 최적화 루프는 없습니다. 교정 패스 뒤 손댄 영역의 게이트에 대해 검증-수리 반복을 최대 두 번 허용하고, 체크리스트를 통과하거나 막힌 지점을 보고하면 멈춥니다. |
| Output | 규칙 라벨, 변경한 파일, 검증 근거, 남은 위험, 공식과 Hypercore의 구분을 담은 한국어 아키텍처 판정이나 구현 요약. |
| Verification | `astro check`와 `rules/astro/testing.md`의 손댄 영역 검사를 돌리고, 이 스킬 폴더 자체를 고쳤으면 `bash skills/hyper-architecture/scripts/validate-architecture.sh`를 실행합니다. |
| Stop condition | 스택과 렌더링 모드를 확인했고, 적용되는 게이트를 통과했거나 막힌 지점으로 보고했고, 검증 근거를 남긴 상태에서 멈춥니다. |

</instruction_contract>

<activation_examples>

Positive examples:

- `Audit this Astro site's routing and decide which routes should be prerendered.`
- `Move this page to on-demand rendering so it can read the session cookie.`
- `Convert this whole page to a server island instead of switching the site to output: 'server'.`
- `Astro 콘텐츠 컬렉션 스키마와 정렬을 정리해줘.`
- `Add an Astro Action for this form and validate its input.`
- `Declare these environment variables through astro:env instead of import.meta.env.`
- `Astro 빌드가 느린데 어디부터 재야 하는지 봐줘.`
- `hyper-architecture 전체 수정`

Negative examples:

- `Review my Vite + React SPA router.`
- `Set up a Next.js App Router project.`
- `Write marketing copy for a landing page built with Astro.`

Boundary examples:

- `Fix a typo in an Astro page's Korean copy.` 아키텍처 경계가 걸리지 않으면 직접 고치면 됩니다.
- `Use official Astro defaults only, not the extra Hypercore conventions.` 이 가이드는 그대로 적용하되, Hypercore 전용 엄격함은 선택 사항인 지적으로 낮춥니다.

</activation_examples>

<trigger_conditions>

렌더링 모드와 어댑터가 규칙 묶음을 정합니다. 게이트 표는 `stacks/astro/architecture-rules.md`에 있습니다. `astro` 의존성도 `astro.config.*`도 없으면 여기서 끝냅니다.

| 작업이 이런 형태라면 | 기본 표면 | 기본으로 피할 것 |
|---|---|---|
| 페이지나 중첩 라우트 추가 | `src/pages/` 아래 파일 | 손으로 쓴 라우트 표 |
| JSON, XML, 피드, webhook 엔드포인트 추가 | `satisfies APIRoute`로 `GET`/`POST`를 내보내는 `src/pages/**/*.ts` 엔드포인트 | Response를 돌려주는 페이지 |
| 정적 동적 라우트 추가 | 프리렌더 라우트의 `getStaticPaths()` | 고정된 경로 집합에 온디맨드 렌더링 |
| 쿠키나 헤더를 읽어야 하는 라우트 추가 | 어댑터와 함께 그 라우트에 `export const prerender = false` | 사이트 전체를 `output: 'server'`로 전환 |
| 정적 페이지에 개인화 조각 하나 추가 | `<Component server:defer />` 서버 아일랜드 | 페이지 전체를 온디맨드 렌더링으로 전환 |
| 상호작용 위젯 추가 | 가장 좁은 `client:*` 지시어를 붙인 프레임워크 컴포넌트 | 모든 곳에 `client:load` |
| 빌드 시점 콘텐츠 모델링 | 로더와 Zod 스키마를 갖춘 `src/content.config.ts` | 페이지 안에서 `fs` 읽기 |
| 재빌드를 기다릴 수 없는 데이터 제공 | `src/live.config.ts`와 `getLiveCollection()`, 어댑터 | 변경마다 사이트 재빌드 |
| 내부 form 쓰기 처리 | `src/actions/`의 Astro Action | 직접 만든 POST 페이지 |
| 인증, 리다이렉트, 요청 상태 공유 | `onRequest`와 타입이 붙은 `locals`를 내보내는 `src/middleware.ts` | 페이지마다 중복 |
| 설정과 비밀 값 읽기 | `astro.config.*`의 `env.schema`와 `astro:env/client` 또는 `astro:env/server` | 공유 코드 전반의 `import.meta.env` |
| 커스텀 워커 진입점이나 Hono 마운트 | `astro/fetch` 또는 `astro/hono`를 쓰는 `src/fetch.ts` | `url.pathname` 접두사로 권한 판정 |
| 반복되는 온디맨드 응답 캐시 | `cache` provider와 `Astro.cache.set()` 또는 `routeRules` | 라우트마다 임의의 메모리 맵 |
| 빌드나 번들이 느림 | `astro build --timings` 후 측정한 레버 하나 | 빌드 플래그 여러 개 동시 변경 |

</trigger_conditions>

<skill_architecture>

- 핵심(`stacks/astro/core.md`): 트리거, 계약, 게이트 순서, 검증, 정지 조건.
- 규칙: `stacks/astro/architecture-rules.md`와 `reference_routing`에 적힌 주제별 파일 여섯 개.
- 참고: `references/official/astro/astro-2026-11-07.md`에 날짜가 붙은 패키지, 런타임, 호환성 파괴 변경, 설정 사실을 둡니다.
- 자산: `assets/evals/astro-cases.jsonl`에 트리거와 동작 사례를 둡니다.
- 폴더 검사기 외에 묶인 스크립트는 없습니다. `astro check`, 손댄 영역의 테스트, 주제별 체크리스트가 검증 표면입니다.
- 이 스킬은 스스로 완결되며 다른 스킬의 경로, 문서, 호출을 필요로 하지 않습니다.

</skill_architecture>

<loop_policy>

- 최적화 루프는 없습니다. 요청마다 리뷰나 교정 패스를 한 번 돕니다.
- 교정 뒤 손댄 영역의 게이트에 대해 검증-수리 반복을 최대 두 번 돕니다. 변경은 손댄 범위 안에 있고 그 게이트를 통과할 때만 남깁니다.
- 루프는 체크리스트를 처음 통과하거나 막힌 지점을 보고할 때 끝나며, 초록 결과를 만들려고 손댄 범위를 넓히지 않습니다.
- 성능 작업은 예외로 측정을 계속합니다. 레버 하나, 프로덕션 빌드 한 번, 전후 수치, 그리고 둘 다 없으면 개선 주장 없음입니다.

</loop_policy>

<language_and_translation_default>

판정, 교정 요약, 검증 노트는 한국어로 씁니다. 식별자, 경로, 라우트 세그먼트, API 이름, `official`과 `hypercore-default` 라벨은 원래 표기를 유지해 규칙 파일과 일대일로 맞출 수 있게 합니다. `stacks/astro/core.ko.md`는 이 파일과 절 단위로 짝을 이루며, 규칙을 바꾸면 같은 편집에서 함께 바꿉니다.

</language_and_translation_default>

<reference_routing>

어떤 편집보다 먼저 `stacks/astro/architecture-rules.md`를 읽습니다. 그다음 손댄 영역을 맡는 파일 하나를 엽니다.

| 손댄 영역 | 파일 |
|---|---|
| `src/pages` 라우팅, 동적 라우트, 엔드포인트, 리다이렉트, 리라이트, 오류 페이지, 폴더 소유권, 이름 규칙 | `rules/astro/project-structure.md` |
| `output`, `prerender`, 어댑터, 스트리밍, 서버 아일랜드, `client:*` 지시어, 프레임워크 통합 | `rules/astro/rendering-and-islands.md` |
| `src/content.config.ts`, 로더, Zod 스키마, `getCollection()`, 참조, 라이브 컬렉션 | `rules/astro/content.md` |
| Actions, 미들웨어와 `locals`, 세션, `astro:env`, `checkOrigin`, CSP, `src/fetch.ts` 권한 판정 | `rules/astro/actions-middleware-env.md` |
| `astro check`, tsconfig, Vitest, Container API, Playwright, `.astro`의 oxlint와 Prettier | `rules/astro/testing.md` |
| 빌드 시간, 아일랜드 하이드레이션 선택, 이미지, 폰트, 프리페치, 뷰 전환, 인라인 스타일시트, 라우트 캐싱 | `rules/astro/performance.md` |
| lint, format, 타입 검사, tsconfig, 패키지 매니저 고정(셋업 트랙) | `rules/setup/typescript.md` |
| 스냅숏 이후 달라졌을 수 있는 Astro 동작 | `references/official/astro/astro-2026-11-07.md` |

사용자가 공식 기본값을 요청하면 스냅숏에서 시작하고, Hypercore 전용 규칙은 선택 사항인 덧씌우기로 다루며 어느 판정이 어느 쪽인지 표시합니다.

</reference_routing>

<support_file_read_order>

1. 규칙 분류와 게이트 요약은 `stacks/astro/architecture-rules.md`.
2. 손댄 영역의 주제별 파일. 순서는 `reference_routing` 표를 따릅니다.
3. 프레임워크 동작이나 공식 기본값 요청이면 `references/official/astro/astro-2026-11-07.md`.
4. 성능 트랙일 때만, 그리고 아키텍처 표면을 정리한 뒤에 `rules/astro/performance.md`.

</support_file_read_order>

<workflow>

| 단계 | 할 일 | 산출물 |
|---|---|---|
| 0 | 대상이 Astro 프로젝트인지 확인하고 `output`, 어댑터, 프레임워크 통합을 기록합니다. | 범위 판정 |
| 1 | 손댄 영역의 규칙 파일을 읽습니다. | 최소 근거 묶음 |
| 2 | 계획한 변경을 `stacks/astro/architecture-rules.md`의 게이트에 대봅니다. | BLOCKED 또는 WARNING 라벨이 붙은 판정 |
| 3 | 국소적이고 되돌릴 수 있는 수정을 적용하고, 광범위한 마이그레이션은 거절합니다. | 편집 또는 이유를 붙인 거절 |
| 4 | 손댄 영역의 검사를 돌리고 명령을 기록합니다. | 검증 기록 |

0단계 프로젝트 확인:

```bash
rg -n '"astro"' package.json
ls astro.config.mjs astro.config.ts astro.config.js astro.config.cjs 2>/dev/null
ls -d src/pages src/content.config.ts src/live.config.ts src/actions src/middleware.ts src/fetch.ts 2>/dev/null
rg -n 'adapter:|output:|@astrojs/(react|preact|svelte|vue|solid-js|alpinejs|node|vercel|cloudflare|netlify)' astro.config.* package.json
```

`astro` 의존성도 `astro.config.*`도 없으면 Astro 규칙을 강요하지 말고 정상 경로로 되돌립니다. `astro` 의존성은 있는데 `src/pages/`가 없으면 다른 스택이 아니라 망가진 프로젝트입니다. 그 폴더가 없으면 사이트에 라우트가 없으므로 그대로 보고합니다.

2단계 게이트 순서:

1. **렌더링과 어댑터** — 변경에 필요한 서버 기능마다 어댑터가 있고 `prerender` 결정이 명시돼 있습니다.
2. **라우팅과 구조** — 라우트는 `src/pages`에 있고, 동적 라우트는 모드를 밝히며, 엔드포인트는 엔드포인트입니다.
3. **아일랜드** — `client:*` 지시어와 이유 없이 프레임워크 JS가 나가지 않고, 직렬화할 수 없는 prop이 경계를 넘지 않습니다.
4. **콘텐츠** — 컬렉션에 로더와 스키마가 있고, 조회 결과를 명시적으로 정렬합니다.
5. **서버 경계** — Actions, 미들웨어, 세션, env가 소유권과 권한 규칙을 따릅니다.
6. **검증** — `astro check`가 통과하고 손댄 영역의 검사가 돌았습니다.

3단계 구현 순서:

1. `src/pages` 배치와 동적 라우트 모드를 고칩니다.
2. `output`, `prerender`, 어댑터 배치를 고칩니다.
3. 아일랜드 지시어와 prop 직렬화를 고칩니다.
4. 콘텐츠 컬렉션 로더, 스키마, 정렬을 고칩니다.
5. Actions, 미들웨어, 세션, env 선언을 고칩니다.
6. 검증을 돌립니다.

스스로 적용하지 않는 것: `output` 전환, 어댑터 추가나 교체, 정적 사이트의 온디맨드 렌더링 전환, `import.meta.env`에서 `astro:env`로의 대량 이관, 레거시 콘텐츠 컬렉션 교체, 라우트 트리 재작성.

</workflow>

<required>

- 규칙을 적용하기 전에 확인한 Astro 대상과 렌더링 모드.
- Actions, 세션, 서버 아일랜드, 라이브 컬렉션, 라우트 캐싱을 건드릴 때마다 "이 변경에 어댑터가 필요한가"에 대한 명시적 답.
- 손댄 영역의 규칙 파일을 읽었고, 요청이 있으면 공식 우선 모드를 적용했다는 사실.
- 모든 판정에 `official` 또는 `hypercore-default` 라벨을 붙인 보고.
- `astro check`와 손댄 영역 검사의 근거.

</required>

<forbidden>

- 요청이 비슷하게 들린다는 이유로 Astro 의존성이 없는 Vite 앱이나 다른 프레임워크에 Astro 규칙을 강요하는 것.
- 매니페스트에 `vite`가 보인다는 이유로 Astro 대상을 Vite 가이드로 라우팅하는 것.
- `output`이 `'static'`이고 어댑터도 없는데 서버 기능을 추가하는 것.
- 라우트 하나를 동적으로 만들려고 사이트 전체를 `output: 'server'`로 바꾸는 것.
- Hypercore 관례를 공식 Astro 동작으로 제시하는 것.
- 손대지 않은 레거시 코드에 같은 패턴이 있다는 이유로 게이트를 끄는 것.
- 돌리지 않은 검사를 돌렸다고 하거나, 실행한 출력 없이 게이트를 통과로 기록하는 것.

</forbidden>

<validation>

- [ ] Astro 판정을 확인했고 그 근거 신호를 밝혔습니다.
- [ ] `output`, 어댑터, 프레임워크 통합을 기록했습니다.
- [ ] 손댄 영역의 규칙 파일을 읽었고, 요청이 있으면 공식 우선 모드를 적용했습니다.
- [ ] 변경이 건드리는 모든 라우트에 프리렌더 결정이 명시돼 있고, 동적 라우트가 모드와 맞습니다.
- [ ] 아일랜드에 이유가 적힌 지시어가 붙어 있고, 직렬화할 수 없는 값이 하이드레이션이나 서버 아일랜드 경계를 넘지 않습니다.
- [ ] Actions가 입력을 검증하고 권한을 확인하며, 미들웨어 결과가 타입이 붙은 `locals`로 페이지에 도달합니다.
- [ ] 환경 변수를 스키마에 선언하고 `astro:env`에서 import하며, 클라이언트 문맥에서 비밀 값에 닿을 수 없습니다.
- [ ] `astro check`가 통과하고 손댄 영역의 테스트가 돌았습니다.
- [ ] 최종 판정이 공식 Astro 규칙과 Hypercore 관례를 구분합니다.

</validation>
