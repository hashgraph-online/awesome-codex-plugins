---
name: hyper-seo
description: "[Hyper] 사용자가 이름이 지정된 대상의 SEO, AEO, GEO, LLMO 감사나 최적화 리포트, 새 사이트 출시 세팅 계획, 점수 개선 반복을 요청할 때 이 스킬을 사용합니다. 온페이지, 기술, 콘텐츠, Core Web Vitals, 답변 엔진, 생성형 엔진, AI 검색 노출, AI 크롤러 정책, 메타데이터, 인용 준비도를 아우르며 결과는 `.hyper/seo/[slug]/`에 저장합니다. 페이지나 제품 디자인, 릴리스 게이트, 검색 맥락 없는 순수 성능 작업, 대상 사이트가 없는 시장 조사에는 사용하지 않습니다."
compatibility: 라이브 웹 접근, 브라우저 점검, 로컬 소스 검색, 가능한 경우 Lighthouse나 Core Web Vitals 데이터, 리포트 산출물 쓰기 권한이 있으면 가장 잘 동작합니다.
---

@rules/seo-workflow.md
@rules/validation.md

# Hyper SEO

> 프로젝트의 검색 노출을 전통 검색엔진과 AI 답변 엔진 양쪽에서 감사하고 개선합니다.

<instruction_contract>

| 항목 | 계약 |
|---|---|
| 의도 | 이름이 지정된 대상의 증거 등급이 매겨진 SEO/AEO/GEO/LLMO 감사와 우선순위화된 실행 가능 개선안 리포트를 만들고, 사이트나 홈페이지를 기획·출시할 때는 단계별 세팅 계획을 만들며, 사용자가 도달 가능한 최고 점수를 요청하면 유한 예산의 점수 개선 루프를 돌린다. |
| 범위 | 대상 분류, 측정 방법 선택, 온페이지·기술·콘텐츠·Core Web Vitals·AEO·GEO·LLMO 평가, 새 사이트 세팅 계획, 점수 산정, 발견 사항, 개선안, 리포트 워크스페이스를 담당한다. 감사 대상 밖의 구현, 릴리스 게이트, 페이지·제품 디자인, 허락받지 않은 소유자 자격 증명 기반 계정 작업, 대상 사이트나 콘텐츠 집합이 없는 광범위한 시장 조사는 담당하지 않는다. |
| 권한 | 시스템/하네스와 사용자 지시 > 감사 대상 자체 파일과 라이브 관측 > 공식 플랫폼 문서 > 이 스킬 > 휴리스틱 선호. 도구·lab·synthetic·heuristic 관측은 공식 요구사항으로 승격하지 않는다. |
| 근거 | 점수를 매기기 전에 대상 자체 파일, 렌더된 페이지, 라이브 응답을 읽고, 모든 critical·warning 발견 사항에 명령 출력·URL·파일 경로·probe 결과를 붙인다. 확인할 수 없는 점검은 `unknown`, 해당 없는 점검은 `not-applicable`로 기록하고, 점수·순위·포함·인용을 지어내지 않는다. |
| 도구 | 사용 가능한 읽기/검색/브라우저 도구를 쓰고, 대시보드는 `bash scripts/render-dashboard.sh <artifact-dir>`로 렌더한다. 웹 검색, 브라우저 점검, 필드 Core Web Vitals, Search Console, AI 인용 probe는 실제로 사용 가능할 때만 쓰고, 없으면 능력 한계와 더 낮은 등급의 대체 방법을 밝힌다. |
| 루프 | optimize 모드 전용으로 `audit -> 수정 또는 개선안 -> re-audit`을 유한하게 반복하며 기본 예산은 3회다. 피드백은 비교 가능한 재감사 증거, 지표는 `unknown`·`not-applicable` 카테고리를 제외한 100점 점수, 가드는 비교 가능한 카테고리 회귀 없음과 증거 등급 승격 없음, 중단은 목표 달성·예산 소진·정체·가드 실패·외부 자격 증명이나 사업 판단이 필요한 시점이다. |
| 출력 | `.hyper/seo/[slug]/`에 `results.json`, `results.js`, `dashboard.html`, `report.md`, `sources.md`, complex·optimize 모드의 `flow.json`을 둔다. simple·setup 모드는 `report.md`와 `sources.md`가 최소다. `sources.md`는 URL, 날짜, 적용 주장, 증거 등급, 한계를 적는 출처 원장이다. |
| 검증 | 완료 시 `rules/validation.md`를 적용한다. 모든 critical·warning 발견 사항에 증거가 있고, 점수는 관측 증거에서 나오며 `unknown`·`not-applicable`을 명시적으로 처리하고, optimize 모드는 기준선·평가자·예산·가드·폐기한 반복·중단 사유·비교 가능한 최고 검증 결과를 기록한다. 패키지 변경 시에는 집중 코퍼스 검증기, 저장소 표준 게이트, 패키지 테스트를 함께 실행한다. |
| 중단 조건 | 요청된 감사나 리포트가 등급이 매겨진 증거와 미해결 critical 공백 없이 끝났을 때, 또는 optimize 모드가 목표·예산·정체·가드·외부 의존에 도달했을 때 중단한다. 증거가 뒷받침하지 않는 순위·AI 기능 포함·인용을 주장하며 중단하지 않는다. |

</instruction_contract>

<output_language>

사용자에게 보이는 모든 산출물, 저장 아티팩트, 리포트, 계획서, 생성 문서, 요약, 인수인계 메모, 커밋/메시지 초안, 검증 메모는 기본적으로 한국어로 작성합니다.

소스 코드 식별자, CLI 명령, 파일 경로, 스키마 키, JSON/YAML 필드명, API 이름, 패키지명, 고유명사, 인용한 원문 발췌는 필요한 언어 또는 원문 그대로 유지합니다. 사용자가 명시적으로 다른 언어를 요청했거나, 기존 대상 산출물의 언어 일관성을 맞춰야 하거나, 기계 판독 계약상 정확한 영어 토큰이 필요한 경우에만 다른 언어를 사용하며, 로컬라이즈된 템플릿/참조(`*.ko.md`, `*.ko.json` 등)가 있으면 사용자-facing 산출물에 우선 사용합니다.

</output_language>

<purpose>

- 웹사이트나 프로젝트의 SEO를 체계적으로 감사합니다.
- 온페이지 SEO, 기술 SEO, 콘텐츠 SEO, Core Web Vitals를 함께 다룹니다.
- Featured Snippet, 음성 검색, 직접 답변 지점에 대한 AEO 준비도를 평가합니다.
- 생성형 AI 응답에서 인용될 가능성에 대한 GEO 준비도를 평가합니다.
- AI 크롤러 접근성, 최신성, 모델이 읽을 수 있는 맥락에 대한 LLMO 준비도를 평가합니다.
- 우선순위가 매겨진 개선안과 근거를 `.hyper/seo/[slug]/`에 저장합니다.
- 새 사이트나 홈페이지 출시를 단계별(기획, 출시 전 빌드 점검, 등록, 첫 30일)로 계획해 검색엔진과 AI 답변 엔진이 크롤·색인·인용할 수 있게 합니다.
- 기존 리포트를 갱신해 SEO 개선 이력을 추적할 수 있게 하고, 사용자가 최고 점수, 만점, 지속적 개선을 요청하면 감사, 수정 또는 개선안, 재감사로 이어지는 반복을 돌려 가장 좋은 결과를 유지합니다.

</purpose>

<routing_rule>

주된 산출물이 SEO/AEO/GEO/LLMO 감사, 최적화 리포트, 근거 기반 검색 노출 개선 계획일 때 `hyper-seo`를 사용합니다.

인접한 작업은 다른 곳으로 보냅니다.

- 페이지나 제품 UI 디자인: 검색 노출 감사가 아니라 디자인 산출물입니다.
- 사이트 감사가 없는 경쟁사·시장 조사: 출처 기반 리서치 workflow로 보냅니다.
- 검색 노출 감사가 아니라 배포 가부만 판정하는 릴리스 게이트: 이 스킬의 산출물이 아닙니다.
- 검색 맥락이 없는 순수 성능 엔지니어링: 해당 성능·최적화 workflow를 씁니다.
- 대상 사이트나 콘텐츠 집합이 없는 AI 검색 트렌드 조사: 출처 기반 리서치 workflow로 보냅니다.

</routing_rule>

<activation_examples>

긍정 예시:

- "이 사이트의 SEO를 분석해줘."
- "메타데이터랑 구조화 데이터 점검해줘."
- "검색엔진 최적화 상태를 확인하고 개선안을 알려줘."
- "AI 검색엔진이 우리 콘텐츠를 인용하도록 최적화해줘."
- "ChatGPT나 Perplexity에서 우리 브랜드가 노출되는지 점검해줘."
- "SEO 점수가 최대한 높아질 때까지 계속 고쳐줘."
- "검색 최적화 점수가 만점에 가까워질 때까지 감사하고 수정하고 재검증해줘."
- "다음 달에 새 홈페이지를 오픈하는데, 오픈 전에 SEO·GEO·AI 크롤러 설정을 잡아줘."

부정 예시:

- "이 랜딩 페이지 디자인해줘." -> 페이지나 제품 디자인 산출물이며 이 스킬의 산출물이 아닙니다.
- "경쟁사 시장 포지셔닝 조사해줘." -> 출처 기반 리서치 workflow로 보냅니다.
- "배포 전 릴리스 체크리스트 확인해줘." -> 배포 게이트 판정이며 검색 노출 감사가 아닙니다.

경계 예시:

- "이 페이지 성능 최적화해줘."
  성능을 SEO/Core Web Vitals 영향으로 평가할 때만 `hyper-seo`를 씁니다.
- "AI 검색 트렌드 조사해줘."
  산출물이 대상 사이트, 페이지, 콘텐츠 목록에 묶여 있을 때만 `hyper-seo`를 씁니다.
- "새 홈페이지 만들어줘."
  검색 노출 세팅 계획이나 점검일 때만 `hyper-seo`를 씁니다. 페이지 제작은 이 스킬의 산출물이 아닙니다.

</activation_examples>

<trigger_conditions>

| 상황 | 모드 |
|------|------|
| 새 프로젝트나 사이트의 SEO 전체 감사 | create |
| 특정 페이지의 온페이지 SEO 점검 | create |
| 기존 SEO 리포트에 새 분석 추가 | update |
| Core Web Vitals나 기술 SEO 집중 분석 | create |
| SEO 개선 후 재점검 | update |
| 최고 점수나 만점을 향한 반복 개선 | optimize |
| AEO/GEO 인용 준비도 분석 | create |
| 기존 리포트에 AEO/GEO 분석 추가 | update |
| 검색엔진과 AI 답변 엔진을 위한 새 사이트나 홈페이지 기획·출시 | setup |

대상 사이트, 페이지, 콘텐츠 집합이 없는 요청은 이 trigger가 아닙니다.

</trigger_conditions>

<skill_architecture>

- Core(`SKILL.md`): 모드, 인테이크, 점수 산정, 산출물 계약, 단계 순서, 중단 조건을 담습니다.
- Rules: [rules/seo-workflow.md](rules/seo-workflow.md)가 단계 절차와 optimize 루프를, [rules/validation.md](rules/validation.md)가 완료 게이트를 소유합니다.
- References: [references/seo-fundamentals.md](references/seo-fundamentals.md)(E-E-A-T, Core Web Vitals, 스키마), [references/aeo-geo-guide.md](references/aeo-geo-guide.md)(AEO, GEO, LLMO), [references/seo-checklist.md](references/seo-checklist.md)(점검 항목), [references/site-setup.md](references/site-setup.md)(setup 모드), [references/artifact-spec.md](references/artifact-spec.md)(워크스페이스와 `results.json` 스키마).
- Assets: 한국어·영어 리포트 템플릿, 대시보드 템플릿, trigger와 행동 사례를 담은 `assets/evals/`.
- Script: `bash scripts/render-dashboard.sh <artifact-dir>`는 Bash 3.2+와 jq가 필요하고, 대시보드 템플릿을 복사해 `results.json`을 `results.js`에 넣고 `dashboard.html`을 씁니다. payload 구조가 잘못되면 문제가 된 `results.json` 필드를 밝히고 0이 아닌 값으로 종료합니다.

</skill_architecture>

<loop_policy>

- optimize 모드만 반복하고, 나머지 모드는 완료 게이트를 둔 한 번의 통과입니다.
- 첫 변경 전에 기준선, 평가자, 예산, 가드를 기록하고, 루프가 끝나면 중단 사유를 기록합니다.
- 비교 가능한 카테고리가 회귀 없이 개선되고 증거 등급이 승격되지 않았을 때만 반복을 유지합니다. 그렇지 않으면 가능한 경우 되돌리고 `discarded`로 표시합니다.
- 루프 절차는 [rules/seo-workflow.md](rules/seo-workflow.md) 9단계에, 기록할 필드는 [rules/validation.md](rules/validation.md)의 Optimize Mode Checks에 있습니다.

</loop_policy>

<language_and_translation_default>

- 이 패키지의 정본 파일은 영어이고 모든 `*.ko.md`는 같은 규칙을 담은 구조 정렬 한국어 번역이며, 산출물은 `<output_language>`를 따르고 리포트 기본 템플릿은 `assets/report.template.ko.md`입니다.

</language_and_translation_default>

<reference_routing>

- 어떤 감사든 시작할 때 [rules/seo-workflow.md](rules/seo-workflow.md)를 읽습니다. 단계별 절차가 여기 있습니다.
- E-E-A-T, Core Web Vitals, 랭킹 요소, 엔터티 신호, 스키마 마크업을 판단할 때 [references/seo-fundamentals.md](references/seo-fundamentals.md)를 읽습니다.
- AEO, GEO, LLMO 차원을 다룰 때, GEO CORE 프레임워크와 `llms.txt` 안내를 포함해 [references/aeo-geo-guide.md](references/aeo-geo-guide.md)를 읽습니다.
- 스캔 중 항목별 점검에는 [references/seo-checklist.md](references/seo-checklist.md)를 읽습니다.
- setup 모드에서만 [references/site-setup.md](references/site-setup.md)를 읽습니다.
- `.hyper/seo/[slug]/`를 쓰거나 검토하기 전에 `flow.json`을 포함해 [references/artifact-spec.md](references/artifact-spec.md)를 읽습니다.
- 리포트를 쓸 때 `assets/report.template.ko.md`를 읽고, 영어가 필요할 때만 `assets/report.template.md`를 읽습니다.
- 대시보드를 렌더할 때만 [assets/dashboard-template.html](assets/dashboard-template.html)을 읽습니다.
- 감사를 완료로 선언하기 전에 [rules/validation.md](rules/validation.md)를 읽습니다.

</reference_routing>

<support_file_read_order>

1. 이 core 파일로 모드, 복잡도, 대상을 확정합니다.
2. `rules/seo-workflow.md`, `references/seo-fundamentals.md`, `references/aeo-geo-guide.md`, `references/seo-checklist.md` 순서로 읽습니다.
3. setup 모드에서는 `references/site-setup.md`를, 워크스페이스를 쓰기 전에는 `references/artifact-spec.md`를 읽습니다.
4. 리포트에는 `assets/report.template.ko.md`를, 렌더할 때만 [assets/dashboard-template.html](assets/dashboard-template.html)을 씁니다.
5. 완료 전에 `rules/validation.md`를 읽습니다.

</support_file_read_order>

<workflow>

| 단계 | 작업 | 산출물 |
|------|------|------|
| 0 | 대상, 모드, 복잡도, 증명 표면, universal intake 필드를 정합니다. | 실행 브리프 |
| 1 | 측정 방법과 신뢰 한계를 세웁니다. | `measurement_methods` |
| 2 | 로컬 코드, 페이지, 브라우저 점검, 웹 출처에서 근거를 모읍니다. | 근거 로그 |
| 3 | 기술 SEO, 플랫폼 정책, AEO, GEO, LLMO, Core Web Vitals, 구조화 데이터를 감사합니다. | 구조화된 발견 사항 |
| 4 | 공식 요구사항과 field·tool·lab·synthetic·heuristic 발견 사항을 분리합니다. | 증거 등급이 매겨진 발견 사항 |
| 5 | 영향, 확신도, 노력, 출처 등급으로 우선순위를 정합니다. | 개선안 집합 |
| 6 | 산출물과 대시보드를 씁니다. | `.hyper/seo/[slug]/` |
| 7 | optimize 모드이면 수정을 적용하거나 제안하고 재감사합니다. | 최고 검증 결과 |
| 8 | 점수, 성과, 신뢰 한계, 위험, 다음 행동을 정리합니다. | 최종 리포트 |

</workflow>

<complexity_routing>

| 복잡도 | 신호 | 처리 |
|------|------|------|
| **Simple** | 단일 페이지 점검, SEO 요소 하나, 빠른 메타데이터 감사 | **Direct**: `report.md`를 바로 씁니다. |
| **Complex** | 전체 사이트 감사, 다수 페이지, 기술 SEO와 콘텐츠 SEO와 Core Web Vitals 동시, 경쟁사 비교 | **Tracked**: `flow.json`으로 단계를 추적합니다. |

시작 전에 `Complexity: [simple/complex] — [한 줄 이유]`, `Mode: [create/update/optimize/setup]`, `Target: [site/page/project path]`, `Proof surface: [commands, browser checks, web sources, or local files]`를 기록합니다.

</complexity_routing>

<universal_intake>

어떤 프로젝트든 점수화 전에 감사 맥락을 먼저 분류해 이 스킬이 여러 스택에서 동작하게 합니다.

- `target_type`: `live-url`, `local-static`, `nextjs`, `react-spa`, `docs-site`, `ecommerce`, `blog`, `app-with-marketing-pages`
- `access_level`: live URL, 로컬 파일만, Search Console 사용 가능, analytics 사용 가능, 필드 Core Web Vitals 사용 가능, AI 인용 probe 사용 가능
- `allowed_action`: `audit-only`, `recommend`, `edit-code`, `optimize-loop`
- `measurement_confidence`: live URL, Search Console, 필드 Core Web Vitals, AI 인용 probe가 없으면 확신도를 낮춥니다.
- `evaluator`: 비교 가능한 대상 집합, 점수 기준, 도구와 버전, 날짜, 근거 채널

모든 발견 사항과 점수 입력은 `official`, `live`, `field`, `tool`, `lab`, `synthetic`, `heuristic` 중 정확히 하나로 분류합니다. 한 등급을 다른 등급의 근거로 쓰지 않습니다. 로컬 스캔은 live나 field 근거가 아니고, tool·lab 결과는 공식 요구사항이 아닙니다.

확인할 수 없는 점검은 `unknown`, 해당 없는 점검은 `not-applicable`로 기록하고 `not-applicable`은 카테고리 분모에서 제외합니다. 빠진 근거를 숨기지 않습니다. 정적 파일, lab 데이터, synthetic probe, 휴리스틱에 근거한 개선안은 `results.json`에 그렇게 표시합니다.

라이브 브라우징, Search Console, 필드 데이터, AI probe, 특정 도구를 쓸 수 없으면 가장 강한 하위 등급 방법을 쓰고 능력 한계와 대체 방법을 밝히며, 라이브 성능·순위·포함·인용을 주장하지 않습니다.

</universal_intake>

<artifact_contract>

`.hyper/seo/[slug]/`를 만들거나 갱신합니다.

예상 파일:

```text
.hyper/seo/[slug]/
├── dashboard.html      # 브라우저에서 읽는 대시보드
├── results.json        # 구조화된 감사 결과
├── results.js          # file:// 브라우저 렌더링 폴백
├── report.md           # 마크다운 리포트
├── sources.md          # 출처와 근거 기록
└── flow.json           # complex·optimize 모드에서 필요
```

simple 모드는 `report.md`와 `sources.md`가 최소입니다. complex나 optimize 모드는 모든 파일을 기대합니다.

파일 스키마는 [references/artifact-spec.md](references/artifact-spec.md)를 따릅니다.

새 리포트는 기본적으로 [assets/report.template.ko.md](assets/report.template.ko.md)를 씁니다. 영어가 명시적으로 필요할 때만 [assets/report.template.md](assets/report.template.md)를 씁니다.

모은 근거로 `results.json`을 먼저 쓰고, 로컬 브라우저에서 바로 보도록 `results.js`를 만들고, `bash scripts/render-dashboard.sh <artifact-dir>`로 `dashboard.html`을 렌더한 뒤 `report.md`와 `sources.md`를 씁니다. `sources.md`는 출처 원장으로, 외부나 공식 주장마다 URL, 접근일이나 게시일, 적용 주장, 증거 등급, 범위·가용성 한계를 적습니다.

complex나 optimize 모드에서 `flow.json`은 `scope` → `measurement` → `technical` → `platform_policy` → `onpage` → `content` → `aeo` → `geo` → `report` 순서로 단계를 추적합니다.

</artifact_contract>

<audit_dimensions>

대상에 해당할 때 다음 차원을 감사합니다. 기술 SEO(크롤 가능성, 색인 가능성, canonical, sitemap, robots 지시자, 응답 상태, 리다이렉트, 중복 페이지), 플랫폼 정책(Googlebot, Google-Extended, OAI-SearchBot, GPTBot, ChatGPT-User, Claude-SearchBot, ClaudeBot, PerplexityBot과 그 밖의 검색용·학습용·사용자 요청 토큰을 각각 별개 제어로 보고, CDN·WAF 봇 규칙, Search Console 생성형 AI 설정, snippet 제어와 X-Robots-Tag, 대상에 해당할 때만 Naver와 Bing/IndexNow 모듈), 온페이지 SEO(title, description, 제목 계층, 키워드 정합, URL 가독성, 내부 링크), 콘텐츠 SEO(검색 의도 일치, 깊이, 주제 커버리지, 최신성, 고유성, 가독성), Core Web Vitals(LCP, INP, CLS, 렌더 차단 리소스, 이미지 크기, 상호작용 지연), 구조화 데이터(JSON-LD 유효성, Schema.org 타입 적합성, 보이는 콘텐츠와의 일치, AI 신뢰 신호), AEO(Q&A 구조, 직접 답변, 스니펫 준비도, 음성 검색 표현), GEO/LLMO(인용 가능한 주장, 출처가 붙은 통계, 엔터티 권위, `llms.txt`, AI 크롤러 접근성, 최신성).

차원별 기준과 조건부 플랫폼 모듈은 [rules/seo-workflow.md](rules/seo-workflow.md) 3-8단계, [references/seo-checklist.md](references/seo-checklist.md), [references/seo-fundamentals.md](references/seo-fundamentals.md), [references/aeo-geo-guide.md](references/aeo-geo-guide.md)에 있습니다.

Naver(`Yeti` 크롤러 접근, 서치어드바이저 소유확인, RSS·사이트맵 소유 도메인 일치, `og:image` 조건, `nosourceinfo` 범위)와 Bing(IndexNow 변경 알림, 색인·인용 증거가 아닌 수신 코드, 키 파일 소유 증명, POST당 제출 상한, 사이트맵 필드 처리)은 대상 집합에 포함될 때만 감사합니다.

글자 수, 제목 개수, 링크 밀도, 답변 길이, 단어 수, 플랫폼 콘텐츠 선호는 맥락에 따라 달라지는 휴리스틱으로 다룹니다. Google AI 기능은 특별한 AI 스키마나 텍스트 파일을 요구하지 않고 일반 SEO 기본기로 평가합니다.

</audit_dimensions>

<scoring>

근거가 충분할 때 투명한 100점 점수를 씁니다.

- 기술 SEO: 20
- 온페이지 SEO: 20
- 콘텐츠 SEO: 15
- Core Web Vitals: 15
- 구조화 데이터: 10
- AEO 준비도: 10
- GEO/LLMO 준비도: 10

근거가 불완전하면 해당 카테고리를 `unknown`으로 표시합니다. 해당 없는 카테고리는 `not-applicable`로 표시하고 점수 분모에서 제외합니다.

각 발견 사항에는 심각도(`critical`, `warning`, `info`), 확신도, `evidence_grade`(`official`, `live`, `field`, `tool`, `lab`, `synthetic`, `heuristic`), `measurement_method`, `source_tier`, 근거 자체, 기대 영향이 붙은 구체적 개선안, 담당 표면(code, content, infrastructure, analytics, external platform)을 넣습니다. 허용 값과 스키마는 [references/artifact-spec.md](references/artifact-spec.md)에 있습니다.

</scoring>

<required>

| 범주 | 요구 사항 |
|---|---|
| 대상 | 점수화 전에 이름이 지정된 대상과 모드, 복잡도, 증명 표면을 기록 |
| 근거 | 모든 critical·warning 발견 사항에 명령 출력·URL·파일 경로·probe 결과와 증거 등급, 출처 등급을 붙임 |
| 점수 | 관측한 카테고리로만 합계를 내고 `unknown`과 `not-applicable`은 가정하지 않고 제외 |
| 산출물 | 고른 모드에서 `<artifact_contract>`가 요구하는 산출물 집합 |
| 한계 | 쓸 수 없는 채널을 대체 방법과 함께 능력 한계로 밝히고 덮지 않음 |

</required>

<forbidden>

| 범주 | 금지 |
|---|---|
| 근거 | 기록된 측정 없이 점수·순위·포함·인용을 주장하기, 합계를 맞추려고 `unknown`을 채우기 |
| 등급 | 휴리스틱을 공식 통과·실패 요구사항으로 제시하기, tool·lab·synthetic 결과를 공식 요구사항으로 승격하기 |
| 보장 | 구조화 데이터나 `llms.txt`, 색인·스니펫 자격이 리치 결과·순위·AI 포함·인용을 보장한다고 암시하기, 만점을 약속하기 |
| 범위 | 감사 대상 밖을 수정하기, 허락 없이 소유자 자격 증명이 필요한 계정 작업을 하기 |
| 주장 | 그것을 증명할 채널이 없을 때 라이브 성능·순위·인용을 주장하기 |

</forbidden>

<validation>

감사를 완료로 선언하기 전에 [rules/validation.md](rules/validation.md)를 적용합니다. 이 파일은 모든 critical·warning 발견 사항의 근거, 엔지니어·마케터·콘텐츠 담당자가 실행할 수 있을 만큼 구체적인 개선안, `unknown`과 `not-applicable`을 가정이 아니라 명시적으로 처리한 관측 근거 기반 점수, 일반 SEO 기본기로 설명한 Google AI 기능과 Google 리치 결과 자격과 답변 친화적 FAQ 콘텐츠를 구분하는 FAQPage 권장, URL·날짜·적용 주장·증거 등급·한계를 담은 `sources.md` 출처 원장, 그리고 optimize 모드의 기준선·평가자·유한 예산·가드·변경과 개선안·재감사 근거·폐기한 반복·중단 사유 기록을 요구합니다.

남아 있어야 할 산출물은 `<artifact_contract>`에 있습니다.

</validation>

## Sources

> 확인 2026-11-09. 모드 집합, 100점 가중치, optimize 가드는 이 패키지의 설계(사용자 지시, 2026-08-20)이며 [rules/seo-workflow.md](rules/seo-workflow.md)에 다시 적혀 있습니다. 감사에 적용하는 외부 사실은 그것을 담은 참조 파일에 날짜가 붙어 있고, 패키지 형태는 `instructions/skill/SKILL_AUTHORING.md`를 따릅니다.
