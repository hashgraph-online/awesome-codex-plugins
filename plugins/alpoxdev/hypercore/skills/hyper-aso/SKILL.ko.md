---
name: "hyper-aso"
description: "사용자가 App Store나 Google Play ASO 감사, 새 앱의 스토어 등록정보 세팅 계획, 이름이 지정된 앱의 유한한 키워드·전환 최적화 루프를 요청할 때 이 스킬을 사용합니다. 메타데이터와 키워드, 스크린샷, 미리보기와 아이콘, 현지화, 평점과 리뷰, 맞춤 페이지와 등록정보 실험, 품질 신호, 메타데이터 정책 위험, 웹-앱 연결을 아우르며 결과는 `.hyper/aso/[slug]/`에 저장합니다. 웹사이트 검색 노출, 스토어 심사나 규정 준수 판정, 유료 캠페인 운영, 이름이 지정된 앱이 없는 시장 조사에는 사용하지 않습니다."
compatibility: "공개 스토어 페이지와 Apple·Google 공식 문서 접근, 선택적인 App Store Connect·Play Console 내보내기 파일 읽기, `.hyper/aso/[slug]/` 읽기·쓰기 권한이 있을 때 가장 잘 동작합니다. `results.json` 검증에는 jq 1.6 이상이 필요합니다."
---

아래 규칙은 본문 안내에 따라 엽니다. 번들 파일 경로는 이 문서가 있는 폴더 기준, 프로젝트 경로는 작업 대상 프로젝트 기준으로 해석합니다.

- [rules/aso-workflow.md](rules/aso-workflow.md)
- [rules/validation.md](rules/validation.md)

# Hyper ASO

> 이름이 지정된 앱이 Apple App Store와 Google Play 안에서 어떻게 발견되고 선택되는지 감사하고 개선합니다.

- **목적**: 지정된 앱의 증거 등급 기반 App Store·Google Play ASO 감사, 출시 전 등록정보 세팅 계획, 유한 키워드·전환 최적화 루프를 수행합니다.
- **쓰지 않을 때**: 웹사이트 SEO/GEO 감사, 스토어 심사·규정 준수 판정, 유료 광고 입찰 운영, 앱 UI 설계, 지정된 앱이 없는 시장 조사일 때.
- **입력**: 지정된 앱(이름, 번들 ID·패키지명 또는 스토어 URL), 대상 스토어·로캘, 선택 콘솔 내보내기 파일, 모드(`create`, `update`, `setup`, `optimize`).
- **산출물**: `.hyper/aso/[slug]/` 워크스페이스(`report.md`, `sources.md` 최소, complex·`optimize`는 `check-results.jq` 통과 `results.json`, `results.js`, `dashboard.html`, `flow.json` 포함).

<instruction_contract>

| 항목 | 계약 |
|---|---|
| 의도 | 지정된 앱의 증거 등급 기반 ASO 감사와 우선순위 실행안, 출시 전 스토어 세팅 계획, 또는 유한 최적화 루프를 만듭니다. |
| 범위 | 스토어·상태·로캘 분류, 측정 방법 선택, 메타데이터·키워드·크리에이티브·현지화·평점·전환 도구·품질 신호·정책 위험·웹 링크 평가, 점수화, 문구 제안, `.hyper/aso/[slug]/` 작성을 담당합니다. 라이브 등록정보 직접 편집·제출, 심사 판정, 유료 광고 운영은 범위 밖입니다. |
| 권한 | 시스템·사용자 지시 > 소유자 콘솔 데이터와 라이브 스토어 페이지 > Apple·Google 공식 정책·문서 > 이 스킬 > 서드파티·휴리스틱 조언. 서드파티 추정치나 실무 속설을 공식 규칙으로 승격하지 않습니다. |
| 근거 | 모든 `critical`·`warning` 발견 사항에 스토어 URL·콘솔 내보내기·공식 문서를 인용하고 미확인은 `unknown`, 비해당은 `not-applicable`로 기록하며 순위·검색량·전환율·다운로드 수를 지어내지 않습니다. |
| 도구 | 공개 스토어·공식 문서 열람, 내보내기 파일·스크린샷 로컬 읽기, `jq -r -f <skill-dir>/assets/runtime/check-results.jq <artifact-dir>/results.json` 검증을 사용합니다. |
| 루프 | `optimize` 모드 전용 `audit -> 등록정보 변경/실험 계획 -> re-audit`(기본 3회) 루프로, 회귀나 정책 위험 증가 없이 비교 가능 카테고리가 개선될 때만 유지합니다(진행 중 스토어 실험은 `pending`). |
| 출력 | `.hyper/aso/[slug]/` 아래 최소 `report.md`·`sources.md`, complex·`optimize`는 `results.json`·`results.js`·`dashboard.html`·`flow.json` 포함. |
| 검증 | [rules/validation.md](rules/validation.md) 완료 게이트 및 `check-results.jq`의 `ok` 출력 확인. |
| 중단 조건 | 등급이 매겨진 증거와 미해결 critical 공백 없이 완료됐거나, `optimize` 모드가 목표·예산·정체·가드·소유자 콘솔 단계에 닿았을 때 멈춥니다. |

</instruction_contract>

<output_language>

사용자에게 보이는 산출물, 리포트, 세팅 계획, 요약, 검증 메모는 기본으로 한국어로 작성하며 식별자, CLI 명령, 파일 경로, JSON 키, 스토어 필드명(`Subtitle`, `Promotional Text`, `Short description`)은 원문으로 두고 제안 등록정보 문구는 대상 로캘 언어로 작성합니다(`instructions/harness-engineering/references/skill-common-rules.ko.md`).

</output_language>

<purpose>

- Apple App Store와 Google Play(및 요청 시 원스토어)에서 검색 발견성과 전환율을 감사하고, 날짜가 붙은 공식 한도·정책을 콘솔 수치·라이브 관측·서드파티 추정치·휴리스틱과 분리합니다.
- 출시 전 스토어 세팅 계획이나 유한 최적화 루프 결과를 `.hyper/aso/[slug]/`에 저장합니다.

</purpose>

<routing_rule>

주된 결과가 지정된 앱의 스토어 내 노출이나 전환(ASO 감사, 출시 등록정보 계획, 로캘·키워드·크리에이티브 개선안, 최적화 루프)일 때 사용합니다.

다음 작업은 제외합니다.
- 웹사이트 SEO/AEO/GEO 감사(Universal Links·App Links·Smart App Banner는 앱 스토어 감사의 일부일 때만 포함)
- 심사 거절·규정 준수 최종 판정, Apple Ads·Google App 유료 입찰 운영, 앱 내부 화면 설계, 대상 앱 없는 시장 조사

</routing_rule>

<activation_examples>

긍정 예시:
- "우리 iOS 앱 앱스토어 등록정보를 감사하고 먼저 고칠 항목을 알려줘."
- "플레이스토어 등록정보 ASO 점검해 줘. 키워드랑 스크린샷 위주로."
- "다음 달 양대 스토어 출시 예정인데 ko-KR과 en-US 스토어 세팅 계획을 짜줘."
- "앱스토어 키워드 필드 100자 어떻게 채울지 한국어로 제안해 줘."

부정·경계 예시:
- "우리 웹사이트 SEO 감사해줘." -> 웹 검색 노출 산출물.
- "가이드라인 4.3 거절 사유 판정해줘." -> 규정 준수 판정.
- "Apple Ads 키워드 입찰가 올려줘." -> 유료 캠페인 운영.
- "상위 피트니스 앱들 ASO 조사해줘." -> 사용자의 지정 앱에 연결될 때만 `hyper-aso` 사용.

</activation_examples>

<trigger_conditions>

| 상황 | 모드 |
|---|---|
| 라이브 앱 전체 또는 특정 표면(키워드·스크린샷·평점) ASO 감사 | `create` |
| 등록정보 변경·실험 완료 후 재점검 또는 스토어·로캘 추가 | `update` |
| 출시 전 신규 앱의 스토어 등록정보 세팅 계획 | `setup` |
| 도달 가능한 최고 등록정보를 향한 반복 개선 | `optimize` |

지정된 앱 이름·번들 ID·패키지명·스토어 URL이 없으면 질문 1개로 먼저 확인합니다.

</trigger_conditions>

<skill_architecture>

- 코어(`SKILL.ko.md`): 모드, 인테이크, 100점 가중치, 산출물 계약, 하네스 워크플로.
- 규칙: [rules/aso-workflow.md](rules/aso-workflow.md), [rules/validation.md](rules/validation.md), [rules/apple.md](rules/apple.md), [rules/google-play.md](rules/google-play.md), [rules/listing-assets.md](rules/listing-assets.md), [rules/localization.md](rules/localization.md).
- 참조: [references/policy-limits.md](references/policy-limits.md), [references/keyword-research.md](references/keyword-research.md), [references/metrics.md](references/metrics.md), [references/web-and-ai-surfaces.md](references/web-and-ai-surfaces.md), [references/artifact-spec.md](references/artifact-spec.md), [references/sources.md](references/sources.md).
- 자산: [assets/report.template.ko.md](assets/report.template.ko.md), `assets/report.template.md`, `assets/dashboard-template.html`, `assets/runtime/check-results.jq`, `assets/evals/`.

</skill_architecture>

<loop_policy>

`optimize` 모드만 반복합니다(기본 예산 3회). 첫 변경 전 기준선·평가자·예산·가드를 기록하며, 스토어 실험(`Product Page Optimization`, `Store Listing Experiments`)은 스토어 통계로 끝난 뒤에만 인정하고 대기 중에는 `kept`가 아닌 `pending`으로 기록합니다([rules/aso-workflow.md](rules/aso-workflow.md)).

</loop_policy>

<language_and_translation_default>

패키지 정본은 영어이며 `*.ko.md`가 구조 정렬 번역본이고, 리포트는 기본 [assets/report.template.ko.md](assets/report.template.ko.md)를 따르되 제안 등록정보 문구는 대상 로캘 언어로 작성합니다.

</language_and_translation_default>

<reference_routing>

- 시작 시 [rules/aso-workflow.md](rules/aso-workflow.md)를 읽고, App Store는 [rules/apple.md](rules/apple.md), Google Play는 [rules/google-play.md](rules/google-play.md), 크리에이티브는 [rules/listing-assets.md](rules/listing-assets.md), 다국어·한국어·원스토어는 [rules/localization.md](rules/localization.md)를 읽습니다.
- 한도 언급 전 [references/policy-limits.md](references/policy-limits.md), 키워드 제안 전 [references/keyword-research.md](references/keyword-research.md), 콘솔 지표 해석 전 [references/metrics.md](references/metrics.md), 웹-앱 링크·AI 표면 점검 시 [references/web-and-ai-surfaces.md](references/web-and-ai-surfaces.md)를 읽습니다.
- 워크스페이스 작성 전 [references/artifact-spec.md](references/artifact-spec.md)와 [assets/report.template.ko.md](assets/report.template.ko.md), 주장 출처 추적 시 [references/sources.md](references/sources.md), 마감 전 [rules/validation.md](rules/validation.md)를 읽습니다.

</reference_routing>

<support_file_read_order>

1. 이 `SKILL.ko.md`, `rules/aso-workflow.md`, 해당 스토어 규칙(`rules/apple.md`, `rules/google-play.md`).
2. `references/policy-limits.md`, `references/keyword-research.md`, `references/metrics.md` 및 필요 시 `rules/listing-assets.md`, `rules/localization.md`, `references/web-and-ai-surfaces.md`.
3. `references/artifact-spec.md`, `assets/report.template.ko.md`, `assets/runtime/check-results.jq`, `rules/validation.md`.

</support_file_read_order>

<workflow>

재개 절차: 0단계 전에 `.hyper/aso/[slug]/`(`flow.json`, `results.json`, `report.md`, `sources.md`)를 먼저 확인합니다. 중단된 실행이나 `update`·`optimize` 기준선이 디스크에 있으면 기준선이나 `pending` 실험 기록을 덮어쓰지 않도록 `flow.json`과 `results.json`을 먼저 읽고 미완료 첫 단계부터 재개합니다.

| 단계 | 수행 작업 | 끝 조건 | 건너뛰면 안 되는 이유 |
|---|---|---|---|
| 0 | 앱 식별자(없으면 질문 1개), 스토어, `app_state`, 로캘, 모드, 복잡도, `<universal_intake>` 확정 및 `flow.json` 초기화 | 실행 브리프 기록 완료 | 잘못된 스토어프런트·로캘·출시 상태로 감사하는 오류를 막음 |
| 1 | 가용 측정 채널과 확신도 한계 설정([references/metrics.md](references/metrics.md)) | `measurement_methods` 기록 완료 | 서드파티 `tool` 추정치가 `console` 실측치로 둔갑하는 일을 막음 |
| 2 | 라이브 스토어 페이지, 내보낸 메타데이터, 콘솔 데이터, 날짜가 붙은 공식 한도 수집([references/policy-limits.md](references/policy-limits.md)) | 근거 로그와 `sources.md` 작성 시작 | 글자 수·바이트 한도를 추측하면 제출 시 거부되는 문구가 나옴 |
| 3 | 스토어·로캘별 메타데이터/키워드, 크리에이티브/전환 도구, 평점/품질 신호, 정책 위험, 웹-앱 링크 평가 | 증거 등급(`official`∼`heuristic`)이 붙은 발견 사항 기록 | 일부 표면만 보면 정책 위반 위험과 전환 병목을 놓침 |
| 4 | 관측 기반 100점 점수 산정, 스토어 자체 단위(글자 대 바이트) 문구 길이 확인, `results.json` 작성 후 `check-results.jq` 검증 | `check-results.jq`가 `ok` 출력 및 산출물 생성 | 스키마 누락과 스토어 필드 한도 초과를 납품 전에 차단함 |
| 5 | `optimize`면 최대 3회 비회귀 개선(미완료 실험은 `pending`) 수행 후 최종 `report.md`·`sources.md` 완성 | [rules/validation.md](rules/validation.md) 통과 | 근거 없는 순위·설치 약속과 무허가 콘솔 수정을 막음 |

단계별 예/아니오 체크리스트:

| # | 예/아니오 질문 | 위반 시 되돌아갈 단계 |
|---|---|---|
| 1 | 시작·재개 시 `.hyper/aso/[slug]/`를 확인하고 점수화 전에 앱 식별자, 스토어, 로캘, 모드, 복잡도, `<universal_intake>`를 기록했는가? (예/아니오) | 0단계 |
| 2 | 모든 글자 수·바이트·에셋 한도가 [references/policy-limits.md](references/policy-limits.md) 등 날짜가 붙은 공식 출처를 인용하며 제안 문구가 스토어 단위에 맞는가? (예/아니오) | 2단계 |
| 3 | 모든 `critical`·`warning` 발견 사항이 구체적 근거와 정확한 `evidence_grade`를 가지며 서드파티 추정치나 속설을 `official`로 적지 않았는가? (예/아니오) | 3단계 |
| 4 | `unknown`·`not-applicable`을 분모에서 제외했고 `jq -r -f <skill-dir>/assets/runtime/check-results.jq <artifact-dir>/results.json`이 `ok`를 출력했는가? (예/아니오) | 4단계 |
| 5 | 순위·추천·승인·설치 증가 약속이나 라이브 콘솔 무단 수정 없이 `report.md`와 `sources.md`를 저장했는가? (예/아니오) | 5단계 |

</workflow>

<complexity_routing>

| 복잡도 | 신호 | 처리 |
|---|---|---|
| **Simple** | 스토어 1개, 로캘 1개, 표면 1개(키워드만 또는 스크린샷만) | **Direct**: `report.md`와 `sources.md` 바로 작성 |
| **Complex** | 양대 스토어, 다수 로캘, 전체 감사, 경쟁사 비교, `optimize` | **Tracked**: `flow.json`으로 단계 추적 |

시작 시 `Complexity`, `Mode`, `App`, `Stores`, `Locales`, `Proof surface`를 기록합니다.

</complexity_routing>

<universal_intake>

점수화 전에 `stores`(`app_store`, `google_play`, 둘 다, 명시 시에만 `one_store`), `app_state`(`pre-launch`, `live`, `relaunch`), `locales`, `access_level`(공개 페이지, 내보내기 파일, App Store Connect, Play Console, 서드파티 ASO 도구, 없음), `allowed_action`(`audit-only`, `recommend`, `draft-copy`, `optimize-loop`), `evaluator`를 분류합니다. 모든 입력은 `official`, `live`, `console`, `tool`, `synthetic`, `heuristic` 중 하나로 등급을 매깁니다.

</universal_intake>

<artifact_contract>

```text
.hyper/aso/[slug]/
├── dashboard.html      # 브라우저용 대시보드
├── results.json        # 구조화된 감사 결과 (check-results.jq 검증 필수)
├── results.js          # results.json에서 생성한 file:// 폴백
├── report.md           # 한국어 마크다운 리포트 또는 세팅 계획
├── sources.md          # 출처와 근거 원장
└── flow.json           # complex·optimize 모드 단계 추적기
```

`results.json` 작성 직후 `jq -r -f <skill-dir>/assets/runtime/check-results.jq <artifact-dir>/results.json`(`ok` 필수)으로 게이트한 뒤 `results.js`, `dashboard.html`, [assets/report.template.ko.md](assets/report.template.ko.md) 기반 `report.md`, `sources.md`를 작성합니다.

</artifact_contract>

<scoring>

근거가 충분할 때 투명한 100점 점수를 씁니다.

- 메타데이터와 키워드: 25
- 크리에이티브 에셋: 20
- 평점과 리뷰: 15
- 현지화: 10
- 전환 도구(맞춤 페이지, 실험, 이벤트, 프로모션 콘텐츠): 10
- 품질 신호(안정성, 크기, 스토어 경고): 10
- 정책 위험: 5
- 웹-앱 연결: 5

`unknown`과 `not-applicable` 카테고리는 분모에서 제외하며 스키마는 [references/artifact-spec.md](references/artifact-spec.md)에 있습니다.

</scoring>

<required>

| 범주 | 요구 사항 |
|---|---|
| 대상·한도 | 지정된 앱 + 스토어 식별자, 인테이크 필드, 모든 한도의 날짜가 붙은 공식 출처([references/policy-limits.md](references/policy-limits.md)) |
| 근거·점수 | 모든 `critical`·`warning` 발견 사항에 URL·내보내기·관측과 `evidence_grade` 부착 및 관측 카테고리로만 합계 산출 |
| 문구·검증 | 스토어 자체 단위(글자 대 바이트)에 맞춘 문구 제안 및 `results.json`의 `check-results.jq` 통과 |

</required>

<forbidden>

- 측정 없는 순위·검색량·전환율 주장, 서드파티 속설의 `official` 승격, 순위·추천·승인 약속, 키워드 도배·경쟁사 브랜드명·보상형 평점 권고, 무허가 라이브 콘솔 조작.
- 나쁜 예: "iOS 설명문이 키워드 색인된다"거나 스크린샷 OCR 속설을 Apple `official` 규칙으로 단정 -> 좋은 예: 실무 가설은 `heuristic`으로 분리하고 `references/policy-limits.md`의 공식 문서를 인용.
- 나쁜 예: iOS 키워드 필드를 100자/바이트 넘게 작성하거나 경쟁사 앱 이름·순위 문구를 삽입 -> 좋은 예: 각 스토어 단위 길이를 정확히 세고 정책 위험 표현을 배제.
- 나쁜 예: 아직 끝나지 않은 스토어 실험을 `optimize`에서 `kept` 개선으로 계산 -> 좋은 예: 콘솔 통계가 끝날 때까지 `pending`으로 기록.

</forbidden>

<validation>

- [ ] 시작·재개 시 `.hyper/aso/[slug]/`를 확인했고 점수화 전에 앱 식별자, 스토어, 로캘, 모드, 인테이크를 기록했습니다.
- [ ] 모든 `critical`·`warning` 발견 사항이 구체적 근거와 정확한 `evidence_grade`를 갖습니다.
- [ ] 모든 한도가 날짜가 붙은 공식 출처를 인용하며 제안 등록정보 문구가 스토어 자체 단위 한도에 맞습니다.
- [ ] 점수가 관측된 카테고리(`25/20/15/10/10/10/5/5`)에서만 계산되었고 `unknown`·`not-applicable`을 제외했습니다.
- [ ] `results.json` 생성 시 `check-results.jq`가 `ok`를 출력했고 `sources.md`와 `report.md`가 디스크에 저장되었습니다.
- [ ] `optimize` 모드에서 기준선, 평가자, 예산, 가드, `pending`·`discarded` 반복, 중단 사유를 모두 기록했습니다.

</validation>

## Sources

> 2026-11-22 확인. 모드 집합, 100점 가중치, optimize 가드는 사용자 지시(2026-11-22)에 따른 패키지 설계이며, 외부 스토어 한도와 사실은 `instructions/skill/SKILL_AUTHORING.md` 기준에 맞춰 [references/policy-limits.md](references/policy-limits.md)와 [references/sources.md](references/sources.md)에 출처·확인 날짜와 함께 기록되어 있습니다.
