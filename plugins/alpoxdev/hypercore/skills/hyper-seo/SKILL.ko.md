---
name: "hyper-seo"
description: "[Hyper] 사용자가 이름이 지정된 대상의 SEO, AEO, GEO, LLMO 감사나 최적화 리포트, 새 사이트 출시 세팅 계획, 점수 개선 반복을 요청할 때 이 스킬을 사용합니다. 온페이지, 기술, 콘텐츠, Core Web Vitals, 답변 엔진, 생성형 엔진, AI 검색 노출, AI 크롤러 정책, 메타데이터, 인용 준비도를 아우르며 결과는 `.hyper/seo/[slug]/`에 저장합니다. 페이지나 제품 디자인, 릴리스 게이트, 검색 맥락 없는 순수 성능 작업, 대상 사이트가 없는 시장 조사에는 사용하지 않습니다."
compatibility: "라이브 웹 접근, 브라우저 점검, 로컬 소스 검색, 가용 시 Lighthouse·Core Web Vitals 데이터, `.hyper/seo/[slug]/` 읽기·쓰기 권한과 Bash 3.2+ 및 jq가 있을 때 가장 잘 동작합니다."
---

아래 규칙은 본문 안내에 따라 엽니다. 번들 파일 경로는 이 문서가 있는 폴더 기준, 프로젝트 경로는 작업 대상 프로젝트 기준으로 해석합니다.

- [rules/seo-workflow.md](rules/seo-workflow.md)
- [rules/validation.md](rules/validation.md)

# Hyper SEO

> 프로젝트의 검색 노출을 전통 검색엔진과 AI 답변 엔진 양쪽에서 감사하고 개선합니다.

- **목적**: 지정된 사이트·프로젝트의 증거 등급 기반 SEO/AEO/GEO/LLMO 감사, 신규 출시 세팅 계획, 유한 예산 점수 개선 루프를 수행합니다.
- **쓰지 않을 때**: 페이지·제품 UI 디자인, 배포 가부만 판정하는 릴리스 게이트, 검색 맥락 없는 순수 성능 작업, 대상 사이트 없는 시장 조사일 때.
- **입력**: 지정된 대상 URL·페이지·저장소 경로, 선택 모드(`create`, `update`, `optimize`, `setup`), 가용 접근 채널.
- **산출물**: `.hyper/seo/[slug]/` 워크스페이스(`report.md`, `sources.md` 최소, complex·`optimize`는 `results.json`, `results.js`, `dashboard.html`, `flow.json` 포함).

<instruction_contract>

| 항목 | 계약 |
|---|---|
| 의도 | 지정된 대상의 증거 등급 기반 SEO/AEO/GEO/LLMO 감사와 우선순위화된 실행안, 신규 사이트 단계별 세팅 계획, 또는 유한 예산 점수 개선 루프를 만듭니다. |
| 범위 | 대상 분류, 측정 방법 선택, 기술·플랫폼 정책·온페이지·콘텐츠·CWV·스키마·AEO·GEO/LLMO 평가, 점수화, 개선안, `.hyper/seo/[slug]/` 작성을 담당합니다. 대상 밖 코드 수정, 릴리스 게이트, UI 디자인, 무허가 계정 조작, 대상 없는 시장 조사는 범위 밖입니다. |
| 권한 | 시스템·사용자 지시 > 감사 대상 파일과 라이브 관측 > 공식 플랫폼 문서 > 이 스킬 > 휴리스틱 선호. tool·lab·synthetic·heuristic 관측을 공식 요구사항으로 승격하지 않습니다. |
| 근거 | 모든 `critical`·`warning` 발견 사항에 명령 출력·URL·파일 경로·probe 결과를 붙이고 미확인 점검은 `unknown`, 비해당 점검은 `not-applicable`로 기록하며 점수·순위·인용을 지어내지 않습니다. |
| 도구 | 가용 읽기·검색·웹·브라우저 도구와 `bash <skill-dir>/scripts/render-dashboard.sh <artifact-dir>`를 쓰며 미가용 채널은 한계와 하위 등급 대체 방법을 명시합니다. |
| 루프 | `optimize` 모드 전용 `audit -> 수정/개선안 -> re-audit`(기본 3회) 루프로, 비교 가능 카테고리가 회귀·증거 등급 승격 없이 개선될 때만 유지합니다. |
| 출력 | `.hyper/seo/[slug]/` 아래 최소 `report.md`·`sources.md`, complex·`optimize` 모드는 `results.json`·`results.js`·`dashboard.html`·`flow.json` 포함. |
| 검증 | [rules/validation.md](rules/validation.md) 완료 게이트 및 `render-dashboard.sh`의 `results.json` 스키마 검증. |
| 중단 조건 | 등급이 매겨진 증거와 미해결 critical 공백 없이 완료됐거나, `optimize` 모드가 목표·예산·정체·가드·외부 자격 증명 경계에 닿았을 때 멈춥니다. |

</instruction_contract>

<output_language>

사용자에게 보이는 모든 산출물, 리포트, 계획서, 요약, 검증 메모는 기본으로 한국어로 작성하며 코드 식별자, CLI 명령, 파일 경로, 스키마 키, API·패키지명, 인용 원문은 그대로 유지합니다(`instructions/harness-engineering/references/skill-common-rules.ko.md`). 로컬라이즈된 템플릿(`*.ko.md`)을 우선 사용합니다.

</output_language>

<purpose>

- 기술 SEO, 검색·AI 크롤러 정책, 온페이지·콘텐츠 SEO, Core Web Vitals, 구조화 데이터, AEO, GEO/LLMO 준비도를 증거 등급으로 분리해 감사합니다.
- 신규 사이트 출시를 단계별(기획, 빌드 점검, 등록, 첫 30일)로 세팅하거나 유한 점수 개선 루프를 돌려 `.hyper/seo/[slug]/`에 기록합니다.

</purpose>

<routing_rule>

주된 산출물이 지정된 대상의 SEO/AEO/GEO/LLMO 감사, 최적화 리포트, 출시 검색 세팅 계획, 점수 개선 루프일 때 `hyper-seo`를 사용합니다.

다음 작업은 제외합니다.
- 랜딩 페이지나 제품 UI 디자인
- 대상 사이트나 콘텐츠 집합이 없는 시장·경쟁사·AI 검색 트렌드 조사
- 검색 노출 맥락 없는 배포 릴리스 게이트 판정이나 순수 백엔드 성능 튜닝

</routing_rule>

<activation_examples>

긍정 예시:
- "이 사이트의 SEO와 메타데이터·구조화 데이터를 점검해줘."
- "AI 검색엔진이 우리 콘텐츠를 인용하도록 최적화해줘."
- "SEO 점수가 최대한 높아질 때까지 감사하고 수정하고 재검증해줘."
- "다음 달 새 홈페이지 오픈 전에 SEO·GEO·AI 크롤러 설정을 잡아줘."

부정·경계 예시:
- "이 랜딩 페이지 디자인해줘." -> 페이지·제품 디자인 산출물.
- "경쟁사 시장 포지셔닝 조사해줘." -> 대상 사이트 감사가 없는 리서치.
- "이 페이지 성능 최적화해줘." -> SEO/Core Web Vitals 영향으로 평가할 때만 `hyper-seo` 사용.

</activation_examples>

<trigger_conditions>

| 상황 | 모드 |
|---|---|
| 새 사이트·단일 페이지·기술/CWV·AEO/GEO 감사 | `create` |
| 개선 후 재점검 또는 기존 `.hyper/seo/[slug]/` 리포트에 분석 추가 | `update` |
| 도달 가능한 최고 점수를 향한 반복 개선 | `optimize` |
| 새 사이트·홈페이지 검색 및 AI 답변 엔진 출시 세팅 계획 | `setup` |

대상 사이트·페이지·콘텐츠 집합이 없으면 질문 1개로 먼저 확인합니다.

</trigger_conditions>

<skill_architecture>

- 코어(`SKILL.ko.md`): 모드, 인테이크, 100점 가중치, 산출물 계약, 하네스 워크플로.
- 규칙: [rules/seo-workflow.md](rules/seo-workflow.md), [rules/validation.md](rules/validation.md).
- 참조: [references/seo-fundamentals.md](references/seo-fundamentals.md), [references/aeo-geo-guide.md](references/aeo-geo-guide.md), [references/seo-checklist.md](references/seo-checklist.md), [references/site-setup.md](references/site-setup.md), [references/artifact-spec.md](references/artifact-spec.md).
- 스크립트·자산: `bash <skill-dir>/scripts/render-dashboard.sh <artifact-dir>`, [assets/report.template.ko.md](assets/report.template.ko.md), [assets/report.template.md](assets/report.template.md), [assets/dashboard-template.html](assets/dashboard-template.html), `assets/evals/`.

</skill_architecture>

<loop_policy>

`optimize` 모드만 반복합니다(기본 예산 3회). 첫 변경 전 기준선·평가자·예산·가드를 기록하고, 비교 가능 카테고리가 회귀와 증거 등급 승격 없이 개선될 때만 유지하며 실패 반복은 `discarded`로 기록합니다([rules/seo-workflow.md](rules/seo-workflow.md)).

</loop_policy>

<language_and_translation_default>

패키지 정본은 영어이며 `*.ko.md`가 구조 정렬 번역본이고, 기본 리포트 템플릿은 [assets/report.template.ko.md](assets/report.template.ko.md)입니다.

</language_and_translation_default>

<reference_routing>

- 시작 시 [rules/seo-workflow.md](rules/seo-workflow.md)를, 완료 전 [rules/validation.md](rules/validation.md)를 읽습니다.
- 점검 중 [references/seo-fundamentals.md](references/seo-fundamentals.md)(E-E-A-T·CWV·스키마), [references/aeo-geo-guide.md](references/aeo-geo-guide.md)(AEO·GEO·LLMO·`llms.txt`), [references/seo-checklist.md](references/seo-checklist.md)를 읽고, `setup` 모드에서만 [references/site-setup.md](references/site-setup.md)를 읽습니다.
- 워크스페이스 작성 전 [references/artifact-spec.md](references/artifact-spec.md), 리포트 작성 시 [assets/report.template.ko.md](assets/report.template.ko.md)(영어 요청 시 [assets/report.template.md](assets/report.template.md)), 대시보드 렌더 시 [assets/dashboard-template.html](assets/dashboard-template.html)을 읽습니다.

</reference_routing>

<support_file_read_order>

1. 이 `SKILL.ko.md`와 `rules/seo-workflow.md`.
2. `references/seo-fundamentals.md`, `references/aeo-geo-guide.md`, `references/seo-checklist.md`(`setup`은 `references/site-setup.md`).
3. `references/artifact-spec.md`, `assets/report.template.ko.md`, `assets/dashboard-template.html`, `rules/validation.md`.

</support_file_read_order>

<workflow>

재개 절차: 0단계 전에 `.hyper/seo/[slug]/`(`flow.json`, `results.json`, `report.md`, `sources.md`)를 먼저 확인합니다. 중단된 실행이나 `update`·`optimize` 이력이 있으면 기준선을 덮어쓰지 않도록 디스크의 `flow.json`과 `results.json`을 먼저 읽고 미완료 첫 단계부터 재개합니다.

| 단계 | 수행 작업 | 끝 조건 | 건너뛰면 안 되는 이유 |
|---|---|---|---|
| 0 | `Complexity`, `Mode`, `Target`, `Proof surface`와 `<universal_intake>` 기록 및 complex/`optimize`용 `flow.json` 초기화 | 실행 브리프와 `flow.json`(`scope`) 기록 완료 | 대상·가용 채널 확인 없이 점수를 매기는 오류를 막음 |
| 1 | 가용 측정 방법과 확신도 한계 설정 | `measurement_methods` 기록 완료 | 정적·lab 결과를 live·field 근거로 오인하는 일을 막음 |
| 2 | 로컬 코드, 렌더 페이지, 응답 헤더·robots, 공식 문서에서 근거 수집 | 원본 근거 및 `sources.md` 행 기록 | 근거 없는 지적은 검증 게이트를 통과할 수 없음 |
| 3 | 기술 SEO, 크롤러·플랫폼 정책, 온페이지, 콘텐츠, CWV, 구조화 데이터, AEO, GEO/LLMO 감사 | 차원별 발견 사항 및 `flow.json` 갱신 | 일부 차원 누락 시 크롤 차단이나 AI 봇 정책 오류를 놓침 |
| 4 | 모든 발견 사항에 증거 등급(`official`∼`heuristic`) 부여 및 우선순위 산정 | 등급 분류와 분모 제외 항목 확정 | 휴리스틱과 공식 요구사항이 섞이면 100점 점수가 왜곡됨 |
| 5 | `results.json` 작성, `scripts/render-dashboard.sh` 실행(complex/`optimize`), `report.md`·`sources.md` 저장 | `.hyper/seo/[slug]/` 검증 산출물 생성 | `render-dashboard.sh`가 잘못된 `results.json` 필드를 잡아냄 |
| 6 | `optimize`면 최대 3회 수정·재감사로 비회귀 개선분만 유지하고 점수·한계·다음 행동 요약 | [rules/validation.md](rules/validation.md) 통과 리포트 완성 | 동일 기준 재측정 없는 점수 상승 주장을 차단함 |

단계별 예/아니오 체크리스트:

| # | 예/아니오 질문 | 위반 시 되돌아갈 단계 |
|---|---|---|
| 1 | 시작·재개 시 `.hyper/seo/[slug]/`를 확인하고 점수화 전에 `Complexity`, `Mode`, `Target`, `Proof surface`, `<universal_intake>`를 기록했는가? (예/아니오) | 0단계 |
| 2 | 모든 `critical`·`warning` 발견 사항이 파일·URL·명령 근거와 정확한 `evidence_grade`를 갖추고 휴리스틱을 `official`로 둔갑시키지 않았는가? (예/아니오) | 4단계 |
| 3 | `unknown`·`not-applicable` 카테고리를 추측 없이 분모에서 제외했고 `results.json` 작성 시 `render-dashboard.sh`가 종료 코드 `0`으로 통과했는가? (예/아니오) | 5단계 |
| 4 | 순위·AI 인용 보장 없이 `sources.md`와 `report.md`를 저장했고(`optimize`면 기준선·가드·폐기 반복·중단 사유 포함) 완료 게이트를 통과했는가? (예/아니오) | 6단계 |

</workflow>

<complexity_routing>

| 복잡도 | 신호 | 처리 |
|---|---|---|
| **Simple** | 단일 페이지 점검, SEO 요소 하나, 빠른 메타데이터 감사 | **Direct**: `report.md`와 `sources.md` 바로 작성 |
| **Complex** | 전체 사이트 감사, 다수 페이지 기술+콘텐츠+CWV, 경쟁사 비교, `optimize` | **Tracked**: `flow.json`으로 단계 추적 |

시작 시 `Complexity: [simple/complex]`, `Mode: [create/update/optimize/setup]`, `Target: [site/page/path]`, `Proof surface: [channels]`를 기록합니다.

</complexity_routing>

<universal_intake>

점수화 전에 감사 맥락을 분류합니다.
- `target_type`: `live-url`, `local-static`, `nextjs`, `react-spa`, `docs-site`, `ecommerce`, `blog`, `app-with-marketing-pages`
- `access_level`: live URL, 로컬 파일만, Search Console, analytics, 필드 CWV, AI 인용 probe
- `allowed_action`: `audit-only`, `recommend`, `edit-code`, `optimize-loop`
- `measurement_confidence` 및 `evaluator`(비교 대상 집합, 루브릭, 도구·날짜)

모든 발견 사항을 `official`, `live`, `field`, `tool`, `lab`, `synthetic`, `heuristic` 중 하나로 분류하고 미확인 점검은 `unknown`, 비해당 점검은 `not-applicable`(분모 제외)로 기록합니다.

</universal_intake>

<artifact_contract>

```text
.hyper/seo/[slug]/
├── dashboard.html      # 브라우저용 대시보드 (render-dashboard.sh 생성)
├── results.json        # 구조화된 감사 결과
├── results.js          # file:// 폴백 페이로드
├── report.md           # 한국어 마크다운 리포트 (기본 assets/report.template.ko.md)
├── sources.md          # 출처 원장 (URL, 날짜, 주장, 증거 등급, 한계)
└── flow.json           # complex·optimize 모드 단계 추적기
```

complex·`optimize` 모드의 `flow.json`은 `scope` → `measurement` → `technical` → `platform_policy` → `onpage` → `content` → `aeo` → `geo` → `report` 순서를 따르며, 대시보드는 `bash <skill-dir>/scripts/render-dashboard.sh <artifact-dir>`로 생성합니다.

</artifact_contract>

<audit_dimensions>

[rules/seo-workflow.md](rules/seo-workflow.md), [references/seo-checklist.md](references/seo-checklist.md), [references/seo-fundamentals.md](references/seo-fundamentals.md), [references/aeo-geo-guide.md](references/aeo-geo-guide.md)에 따라 기술 SEO(크롤·색인, canonical, sitemap, robots, 응답·리다이렉트), 플랫폼 정책(Googlebot, Google-Extended, OAI-SearchBot, GPTBot, ChatGPT-User, Claude-SearchBot, ClaudeBot, PerplexityBot, WAF 규칙, snippet·X-Robots-Tag, 대상 포함 시 Naver `Yeti`/서치어드바이저 및 Bing/IndexNow), 온페이지 SEO, 콘텐츠 SEO, Core Web Vitals(LCP, INP, CLS), 구조화 데이터(JSON-LD 정합성 및 Google FAQPage 리치 결과 자격과 보이는 FAQ 본문 구분), AEO, GEO/LLMO(`llms.txt`, 출처 통계, 엔터티 명확성, 최신성)를 감사합니다. Google AI 기능은 일반 SEO 기본기로 평가합니다.

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

근거가 불완전한 카테고리는 `unknown`, 비해당 카테고리는 `not-applicable`로 표시하고 분모에서 제외합니다. 스키마는 [references/artifact-spec.md](references/artifact-spec.md)를 따릅니다.

</scoring>

<required>

| 범주 | 요구 사항 |
|---|---|
| 대상·인테이크 | 점수화 전에 지정된 대상, 모드, 복잡도, 증명 표면, `<universal_intake>` 기록 |
| 근거 | 모든 `critical`·`warning` 발견 사항에 명령·URL·파일 경로·probe 결과와 `evidence_grade`, `source_tier` 기재 |
| 점수 | `unknown`과 `not-applicable`을 제외하고 관측된 카테고리로만 합계 산출 |
| 산출물 | 모드별 `.hyper/seo/[slug]/` 산출물, `render-dashboard.sh` 검증 통과, `sources.md` 출처 원장 |

</required>

<forbidden>

- 측정 없는 점수·순위·인용 주장, 합계를 맞추기 위한 `unknown` 임의 채움, 휴리스틱·lab 점수의 `official` 승격, 순위·AI 인용 보장, 감사 대상 밖 무단 수정.
- 나쁜 예: 정적 파일만 읽고도 100점 만점을 채우려고 Core Web Vitals나 라이브 크롤 점수를 임의 부여 -> 좋은 예: 미관측 항목은 `unknown`으로 두고 `not-applicable`은 분모에서 제외하며 정적 점검은 `tool`·`heuristic`으로 표기.
- 나쁜 예: 글자 수 권장치나 `llms.txt` 유무를 Google 공식 랭킹 필수 요건처럼 단정 -> 좋은 예: 휴리스틱은 `heuristic` 등급으로 분리하고 Google AI 기능은 일반 SEO 기본기로 설명.
- 나쁜 예: `optimize` 모드에서 동일 조건 재감사 없이 수정만으로 점수가 올랐다고 보고 -> 좋은 예: 기준선, 가드, 재감사 결과, `discarded` 반복과 중단 사유를 모두 기록.

</forbidden>

<validation>

- [ ] 시작·재개 시 `.hyper/seo/[slug]/`를 확인했고 점수화 전에 대상, 모드, 복잡도, 인테이크 필드를 기록했습니다.
- [ ] 모든 `critical`·`warning` 발견 사항에 구체적 근거, `evidence_grade`, `source_tier`, 담당 표면, 실행 가능한 개선안이 있습니다.
- [ ] 점수가 관측된 근거(`20/20/15/15/10/10/10` 가중치)에서만 계산되었고 `unknown`·`not-applicable`을 명시적으로 제외했습니다.
- [ ] Google AI 기능을 일반 SEO 기본기로 서술했고 FAQPage 권장 시 리치 결과 자격과 보이는 FAQ 본문을 구분했습니다.
- [ ] `sources.md`에 URL·날짜·주장·증거 등급·한계를 적었고 complex·`optimize` 실행에서 `render-dashboard.sh`가 `0`으로 통과했습니다.
- [ ] `optimize` 모드에서 기준선, 평가자, 유한 예산, 가드, 재감사 근거, 폐기한 반복, 중단 사유를 모두 기록했습니다.

</validation>

## Sources

> 확인 2026-11-09. 모드 집합, 100점 가중치, optimize 가드는 사용자 지시(2026-08-20) 및 [rules/seo-workflow.md](rules/seo-workflow.md) 설계를 따르며, 외부 플랫폼 사실은 `instructions/skill/SKILL_AUTHORING.md` 기준에 따라 각 `references/*.md`에 확인 날짜와 함께 기록되어 있습니다.
