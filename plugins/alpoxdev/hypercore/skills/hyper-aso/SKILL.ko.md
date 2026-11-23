---
name: hyper-aso
description: "사용자가 App Store나 Google Play ASO 감사, 새 앱의 스토어 등록정보 세팅 계획, 이름이 지정된 앱의 유한한 키워드·전환 최적화 루프를 요청할 때 이 스킬을 사용합니다. 메타데이터와 키워드, 스크린샷, 미리보기와 아이콘, 현지화, 평점과 리뷰, 맞춤 페이지와 등록정보 실험, 품질 신호, 메타데이터 정책 위험, 웹-앱 연결을 아우르며 결과는 `.hyper/aso/[slug]/`에 저장합니다. 웹사이트 검색 노출, 스토어 심사나 규정 준수 판정, 유료 캠페인 운영, 이름이 지정된 앱이 없는 시장 조사에는 사용하지 않습니다."
compatibility: 공개 스토어 페이지와 Apple·Google 공식 문서에 접근하는 브라우저, 소유자의 App Store Connect나 Play Console 내보내기 파일 읽기(선택), 리포트 산출물 읽기·쓰기 권한이 있으면 가장 잘 동작합니다. `results.json` 검증에는 jq 1.6 이상이 필요합니다.
---

아래 규칙은 본문의 안내에 따라 엽니다. 스킬에 포함된 파일 경로는 이 문서가 있는 폴더를 기준으로 해석하고 프로젝트 경로는 작업 대상 프로젝트를 기준으로 해석합니다.

- [rules/aso-workflow.md](rules/aso-workflow.md)
- [rules/validation.md](rules/validation.md)

# Hyper ASO

> 이름이 지정된 앱이 Apple App Store와 Google Play 안에서 어떻게 발견되고 선택되는지 감사하고 개선합니다.

<instruction_contract>

| 항목 | 계약 |
|---|---|
| 의도 | 이름이 지정된 앱의 증거 등급이 매겨진 ASO 감사와 우선순위화된 실행안, 아직 출시 전인 앱의 단계별 스토어 등록정보 세팅 계획, 또는 사용자가 도달 가능한 최고의 등록정보를 요청할 때 유한한 최적화 루프를 만든다. |
| 범위 | 대상 분류(스토어, 신규 또는 라이브 앱, 로캘), 측정 방법 선택, 메타데이터·키워드·크리에이티브·현지화·평점·전환 도구·품질 신호·정책 위험·웹 링크 평가, 점수 산정, 발견사항, 개선안, `.hyper/aso/[slug]/` 워크스페이스를 담당한다. 라이브 등록정보 편집이나 제출, 스토어 심사나 규정 준수 판정, 유료 캠페인 운영, 앱 UI나 기능 설계, 이름이 지정된 앱이 없는 시장 조사는 담당하지 않는다. |
| 권한 | 시스템/하네스와 사용자 지시 > 소유자 콘솔 데이터와 라이브 스토어 페이지 > Apple·Google 공식 정책과 문서 > 이 스킬 > 벤더나 휴리스틱 조언. 벤더 추정치, 도구 점수, 실무자 주장은 공식 규칙으로 승격하지 않는다. |
| 근거 | 점수를 매기기 전에 라이브 스토어 페이지, 소유자가 내보낸 메타데이터, 콘솔 내보내기를 읽고, 모든 critical·warning 발견사항에 근거가 된 URL·내보내기 파일·관측을 붙인다. 확인할 수 없는 점검은 `unknown`, 해당 없는 점검은 `not-applicable`로 기록하고, 순위·검색량·전환율·다운로드 수를 지어내지 않는다. |
| 도구 | 공개 스토어 페이지와 공식 문서에 접근하는 브라우저나 페치, 내보낸 메타데이터와 스크린샷을 읽는 로컬 파일 읽기, 결과 페이로드를 게이트하는 `jq -r -f <skill-dir>/assets/runtime/check-results.jq <artifact-dir>/results.json`. 콘솔 데이터나 서드파티 ASO 도구는 소유자가 제공할 때만 쓰고, 없으면 한계를 밝히고 가장 강한 하위 등급 방법으로 대체한다. |
| 루프 | optimize 모드 전용으로 `audit -> 등록정보 변경 또는 실험 계획 -> re-audit`을 유한하게 반복하며 기본 예산은 3회다. 피드백은 비교 가능한 재감사 증거나 완료된 스토어 실험이고, 지표는 `unknown`·`not-applicable`을 제외한 100점 점수이며, 가드는 비교 가능한 카테고리 회귀 없음·정책 위험 증가 없음·증거 등급 승격 없음이고, 중단은 목표 달성·예산 소진·정체·가드 실패·소유자 콘솔이나 사업 판단이 필요한 단계다. |
| 출력 | `.hyper/aso/[slug]/`에 `results.json`, `results.js`, `dashboard.html`, `report.md`, `sources.md`, complex·optimize 모드의 `flow.json`을 둔다. simple·setup 모드는 `report.md`와 `sources.md`가 최소다. |
| 검증 | 완료 시 `rules/validation.md`를 적용한다. 모든 critical·warning 발견사항에 증거가 있고, 모든 글자 수·에셋 한도에 날짜가 붙은 공식 출처를 인용하며, 점수는 관측 증거에서 나오고, optimize 모드는 기준선·평가자·예산·가드·폐기한 반복·중단 사유·비교 가능한 최고 결과를 기록한다. |
| 중단 조건 | 요청된 감사·계획·리포트가 등급이 매겨진 증거와 미해결 critical 공백 없이 끝났을 때, 또는 optimize 모드가 목표·예산·정체·가드·소유자 전용 단계에 도달했을 때 중단한다. 증거가 뒷받침하지 않는 순위·추천 배치·승인·다운로드 결과를 주장하며 중단하지 않는다. |

</instruction_contract>

<output_language>

사용자에게 보이는 모든 산출물, 저장 아티팩트, 리포트, 계획서, 생성 문서, 요약, 인수인계 메모, 커밋/메시지 초안, 검증 메모는 이 정본 스킬 파일이 영어로 쓰여 있어도 기본적으로 한국어로 작성합니다.

소스 코드 식별자, CLI 명령, 파일 경로, 스키마 키, JSON 필드명, 스토어 필드명(`Subtitle`, `Promotional Text`, `Short description`), 고유명사, 인용한 원문 발췌는 원문 그대로 유지합니다. 제안하는 등록정보 문구는 각 대상 로캘의 언어로 씁니다. 로컬라이즈된 템플릿(`*.ko.md`)이 있으면 사용자-facing 산출물에 그것을 우선 사용합니다.

</output_language>

<purpose>

- Apple App Store, Google Play, 또는 두 스토어 모두에서 앱의 스토어 존재감을 검색(발견되는가)과 전환(선택되는가) 관점으로 감사한다.
- 공식 한도와 정책을 콘솔 측정값, 라이브 관측, 서드파티 추정치, 휴리스틱과 분리한다.
- 곧 출시할 앱의 스토어 세팅을 계획한다. 필드, 키워드, 에셋, 로캘, 평점 흐름, 링크, 첫 30일 측정을 다룬다.
- 비교 가능한 증거가 뒷받침하는 변경만 남기는 유한한 최적화 루프를 돌린다.
- 근거, 발견사항, 우선순위화된 실행안을 `.hyper/aso/[slug]/`에 저장한다.

</purpose>

<routing_rule>

주된 결과가 이름이 지정된 앱의 앱 스토어 내 노출이나 전환일 때 이 스킬을 사용한다. ASO 감사, 스토어 등록정보 세팅 계획, 키워드나 크리에이티브 제안, 최적화 루프가 여기에 해당한다.

인접한 작업은 산출물 형태로 구분한다.

- 웹사이트의 검색엔진이나 AI 답변 노출 감사: 이 스킬의 산출물이 아니라 웹 검색 노출 산출물이다. 사이트가 앱을 홍보하더라도 마찬가지다. 웹-앱 연결 점검(Universal Links, App Links, Smart App Banner)은 앱 스토어 감사의 일부일 때만 이 스킬에 남는다.
- 제출 준비도, 심사 거절, 개인정보 라벨, 정책 준수 판정: 이 스킬의 산출물이 아니라 규정 준수 산출물이다. 이 스킬은 발견 가능성에 영향을 주는 메타데이터 정책 위험을 표시하고 판정은 넘긴다.
- 유료 캠페인 운영이나 입찰(Apple Ads, Google App campaigns): 이 스킬의 산출물이 아니라 캠페인 관리다. 이 스킬은 그 키워드 데이터를 증거로 읽을 수 있다.
- 앱 화면이나 기능 디자인: 디자인 산출물이다.
- 이름이 지정된 앱이 없는 시장이나 카테고리 조사: 출처 기반 리서치다.

</routing_rule>

<activation_examples>

긍정 예시:

- "Audit our iOS app's App Store listing and tell me what to fix first."
- "플레이스토어 등록정보 ASO 점검해 줘. 키워드랑 스크린샷 위주로."
- "We launch on both stores next month; give me the store listing setup plan for ko-KR and en-US."
- "Keep improving our App Store product page until the ASO score stops going up."
- "앱스토어 키워드 필드 100자 어떻게 채울지 한국어로 제안해 줘."

부정 예시:

- "Audit our website's SEO." -> 웹 검색 노출 산출물입니다.
- "Why was our app rejected under guideline 4.3?" -> 심사나 규정 준수 판정입니다.
- "Raise our Apple Ads bids on these keywords." -> 캠페인 관리입니다.

경계 예시:

- "Our landing page should drive installs; check it." Smart App Banner, 스토어 배지 링크, 앱 링크 파일을 앱 스토어 감사의 일부로 점검할 때만 이 스킬을 씁니다. 페이지 SEO 감사는 다른 산출물입니다.
- "Make sure our listing won't be rejected." 감사 중 발견한 메타데이터 정책 위험을 표시합니다. 승인 판정 자체는 규정 준수 산출물입니다.
- "Research the top fitness apps' ASO." 산출물이 사용자의 이름이 지정된 앱에 묶여 있을 때만 이 스킬을 씁니다. 그렇지 않으면 시장 조사입니다.

</activation_examples>

<trigger_conditions>

| 상황 | 모드 |
|------|------|
| 라이브 앱의 ASO 전체 감사 | create |
| 표면 하나(키워드, 스크린샷, 평점)에 집중한 점검 | create |
| 등록정보 변경이나 완료된 실험 이후 재점검 | update |
| 기존 감사에 스토어나 로캘 추가 | update |
| 아직 출시 전인 앱의 스토어 등록정보 계획 | setup |
| 도달 가능한 최고의 등록정보를 향한 반복 개선 | optimize |

이름이 지정된 앱, 번들 ID, 패키지명, 스토어 URL이 없는 요청은 이 트리거가 아니다. 앱을 한 번만 물어본다.

</trigger_conditions>

<skill_architecture>

- Core(`SKILL.md`): 모드, 인테이크, 점수 산정, 산출물 계약, 단계 순서, 중단 조건을 담는다.
- Rules: [rules/aso-workflow.md](rules/aso-workflow.md)가 단계와 optimize 루프를, [rules/validation.md](rules/validation.md)가 완료 게이트를, [rules/apple.md](rules/apple.md)와 [rules/google-play.md](rules/google-play.md)가 스토어별 점검을, [rules/listing-assets.md](rules/listing-assets.md)가 스크린샷·미리보기·아이콘 점검을, [rules/localization.md](rules/localization.md)가 로캘·스토어프런트·한국어·원스토어 점검을 소유한다.
- References: [references/policy-limits.md](references/policy-limits.md)(날짜가 붙은 공식 한도), [references/keyword-research.md](references/keyword-research.md)(키워드 방법과 지표 주의점), [references/metrics.md](references/metrics.md)(지표 사전), [references/web-and-ai-surfaces.md](references/web-and-ai-surfaces.md)(웹-앱 연결과 AI 추천 표면), [references/artifact-spec.md](references/artifact-spec.md)(워크스페이스와 `results.json` 스키마), [references/sources.md](references/sources.md)(이 패키지 뒤의 리서치 원장).
- Assets: 한국어·영어 리포트 템플릿, `assets/dashboard-template.html`, `assets/runtime/check-results.jq`, 트리거와 행동 사례를 담은 `assets/evals/`.

</skill_architecture>

<loop_policy>

- optimize 모드만 반복하고, 나머지 모드는 완료 게이트를 둔 한 번의 통과다.
- 첫 변경 전에 기준선, 평가자, 예산, 가드를 기록하고, 루프가 끝나면 중단 사유를 기록한다.
- 스토어 실험(Product Page Optimization, Store Listing Experiments)은 스토어 자체 통계로 끝난 뒤에만 증거로 인정한다. 실험을 기다리는 반복은 `kept`가 아니라 `pending`으로 기록한다.
- 비교 가능한 카테고리가 회귀나 정책 위험 증가 없이 개선될 때만 반복을 유지하고, 그렇지 않으면 `discarded`로 표시한다.
- 루프 절차는 [rules/aso-workflow.md](rules/aso-workflow.md) 9단계에, 기록할 필드는 [rules/validation.md](rules/validation.md)의 Optimize Mode Checks에 있다.

</loop_policy>

<language_and_translation_default>

- 패키지 정본 파일은 영어이고 모든 `*.ko.md`는 구조가 정렬된 한국어 번역이며, 산출물은 `<output_language>`를 따르고 기본 리포트 템플릿은 `assets/report.template.ko.md`다.

</language_and_translation_default>

<reference_routing>

- 어떤 실행이든 시작할 때 [rules/aso-workflow.md](rules/aso-workflow.md)를 읽는다. 단계별 절차가 여기 있다.
- App Store가 범위에 있으면 [rules/apple.md](rules/apple.md)를, Google Play가 범위에 있으면 [rules/google-play.md](rules/google-play.md)를 읽는다.
- 스크린샷, 미리보기, 아이콘, 피처 그래픽을 평가할 때 [rules/listing-assets.md](rules/listing-assets.md)를 읽는다.
- 로캘이나 스토어프런트가 둘 이상이거나, 한국어가 대상 언어이거나, 원스토어가 지정됐을 때 [rules/localization.md](rules/localization.md)를 읽는다.
- 글자 수, 크기, 개수, 기간 한도를 말하기 전에 [references/policy-limits.md](references/policy-limits.md)를 읽는다.
- 키워드를 제안하거나 인기도·난이도 수치를 읽기 전에 [references/keyword-research.md](references/keyword-research.md)를 읽는다.
- 콘솔 지표를 읽거나 비교하기 전에 [references/metrics.md](references/metrics.md)를 읽는다.
- 웹-앱 연결이나 AI 비서 추천이 범위에 있을 때 [references/web-and-ai-surfaces.md](references/web-and-ai-surfaces.md)를 읽는다.
- `.hyper/aso/[slug]/`를 쓰기 전에 [references/artifact-spec.md](references/artifact-spec.md)를 읽는다.
- 이 패키지의 주장을 출처로 되짚을 때만 [references/sources.md](references/sources.md)를 읽는다.
- 리포트를 초안할 때 `assets/report.template.ko.md`를 읽고, 영어가 필요할 때만 `assets/report.template.md`를 읽는다.
- 실행을 완료로 선언하기 전에 [rules/validation.md](rules/validation.md)를 읽는다.

</reference_routing>

<support_file_read_order>

1. 이 core 파일로 모드, 스토어, 로캘, 앱을 확정한다.
2. `rules/aso-workflow.md`, 그다음 범위에 있는 스토어마다 해당 스토어 규칙을 읽는다.
3. 해당 단계가 시작될 때 `references/policy-limits.md`, `references/keyword-research.md`, `references/metrics.md`를 읽는다.
4. 해당 표면이 범위에 있을 때 `rules/listing-assets.md`, `rules/localization.md`, `references/web-and-ai-surfaces.md`를 읽는다.
5. 워크스페이스를 쓰기 전에 `references/artifact-spec.md`를, 그다음 리포트 템플릿을 읽는다.
6. 완료 전에 `rules/validation.md`를 읽는다.

</support_file_read_order>

<workflow>

| 단계 | 작업 | 산출물 |
|------|------|------|
| 0 | 앱 식별자, 스토어, 신규/라이브 여부, 로캘, 모드, 복잡도, 증명 표면을 확정 | 실행 브리프 |
| 1 | 측정 방법과 신뢰 한계를 세움 | `measurement_methods` |
| 2 | 라이브 등록정보, 내보낸 메타데이터, 콘솔 데이터, 공식 한도를 수집 | 근거 로그 |
| 3 | 스토어와 로캘별로 메타데이터와 키워드를 평가 | 메타데이터 발견사항 |
| 4 | 크리에이티브 에셋과 전환 도구를 평가 | 크리에이티브·전환 발견사항 |
| 5 | 평점, 리뷰, 품질 신호를 평가 | 평점·품질 발견사항 |
| 6 | 정책 위험과 웹-앱 연결을 평가 | 위험·링크 발견사항 |
| 7 | 점수를 내고 우선순위를 정하고 산출물을 씀 | `.hyper/aso/[slug]/` |
| 8 | optimize 모드이면 변경 하나를 적용하거나 계획하고 재감사 | 비교 가능한 최고 결과 |
| 9 | 점수, 성과, 한계, 위험, 다음 행동을 정리 | 최종 리포트 |

</workflow>

<complexity_routing>

| 복잡도 | 신호 | 처리 |
|------|------|------|
| **Simple** | 스토어 하나, 로캘 하나, 표면 하나(키워드만, 스크린샷만) | **Direct**: `report.md`를 바로 쓴다. |
| **Complex** | 두 스토어, 여러 로캘, 전체 감사, 경쟁사 비교, optimize 모드 | **Tracked**: `flow.json`으로 단계를 추적한다. |

시작 전에 `Complexity: [simple/complex] — [reason]`, `Mode: [create/update/setup/optimize]`, `App: [name, bundle ID or package name, store URLs]`, `Stores: [app_store/google_play/both]`, `Locales: [list]`, `Proof surface: [store pages, exports, console data, official docs]`를 기록한다.

</complexity_routing>

<universal_intake>

점수화 전에 맥락을 분류한다.

- `stores`: `app_store`, `google_play`, 또는 둘 다. `one_store`는 사용자가 이름을 대었을 때만 쓴다.
- `app_state`: `pre-launch`, `live`, `relaunch`.
- `locales`: 범위에 있는 모든 메타데이터 로캘과 스토어프런트, 스토어별 주 언어.
- `access_level`: 공개 스토어 페이지만, 소유자가 내보낸 메타데이터, App Store Connect 분석, Play Console 통계, 서드파티 ASO 도구 데이터, 또는 없음.
- `allowed_action`: `audit-only`, `recommend`, `draft-copy`, `optimize-loop`. 라이브 등록정보 편집과 제출은 항상 소유자에게 남는다.
- `evaluator`: 비교 가능한 앱 집합, 루브릭 버전, 날짜, 스토어, 로캘, 증거 채널.

모든 발견사항과 점수 입력은 `official`, `live`, `console`, `tool`, `synthetic`, `heuristic` 중 정확히 하나로 분류한다. 서드파티 인기도나 난이도 수치는 `tool`이고 `console`이 아니며, 공개 스토어 페이지 판독은 `live`이고 `console`이 아니다.

</universal_intake>

<artifact_contract>

프로젝트 루트에 `.hyper/aso/[slug]/`를 만들거나 갱신한다.

```text
.hyper/aso/[slug]/
├── dashboard.html      # 브라우저에서 읽는 대시보드 (템플릿 복사)
├── results.json        # 구조화된 감사 결과
├── results.js          # file:// 폴백, results.json에서 생성
├── report.md           # 마크다운 리포트 또는 세팅 계획
├── sources.md          # 출처와 근거 원장
└── flow.json           # complex 또는 optimize 모드
```

모은 근거로 `results.json`을 먼저 쓰고, `jq -r -f <skill-dir>/assets/runtime/check-results.jq <artifact-dir>/results.json`로 게이트한 뒤(`ok`를 출력하거나, 위반마다 `E` 한 줄과 함께 종료 코드 1로 끝난다), [references/artifact-spec.md](references/artifact-spec.md)의 방식대로 `results.js`를 만들고 대시보드를 복사한다. 그다음 [assets/report.template.ko.md](assets/report.template.ko.md)로 `report.md`를, 이어서 `sources.md`를 쓴다. `sources.md`는 외부나 공식 주장마다 URL, 접근 날짜, 적용 주장, 증거 등급, 한계를 기록한다.

</artifact_contract>

<scoring>

근거가 충분할 때 투명한 100점 점수를 쓴다.

- 메타데이터와 키워드: 25
- 크리에이티브 에셋: 20
- 평점과 리뷰: 15
- 현지화: 10
- 전환 도구(맞춤 페이지, 실험, 이벤트, 프로모션 콘텐츠): 10
- 품질 신호(안정성, 크기, 스토어 경고): 10
- 정책 위험: 5
- 웹-앱 연결: 5

근거가 없는 카테고리는 `unknown`, 해당하지 않는 카테고리는 `not-applicable`(예: 출시 전의 전환 도구)로 표시하고 둘 다 분모에서 제외한다. 점수는 내부 우선순위 판단 도구이며 스토어 순위 요소가 아니다. 각 발견사항에는 심각도, 스토어, 카테고리, 근거, `evidence_grade`, 확신도, 측정 방법, 구체적 개선안, 소유자 표면을 붙인다. 스키마는 [references/artifact-spec.md](references/artifact-spec.md)에 있다.

</scoring>

<required>

| 범주 | 요구 사항 |
|---|---|
| 대상 | 스토어 식별자가 있는 이름이 지정된 앱, 그리고 점수화 전에 기록한 모드·스토어·로캘·증명 표면 |
| 한도 | 모든 글자 수, 크기, 개수, 기간 한도를 [references/policy-limits.md](references/policy-limits.md)나 공식 페이지에서 다시 읽은 값으로, 확인 날짜와 함께 제시 |
| 근거 | 모든 critical·warning 발견사항에 URL·내보내기 경로·관측과 증거 등급을 붙임 |
| 점수 | 관측한 카테고리로만 합계를 냄 |
| 문구 | 스토어 자체 단위(글자 또는 바이트)로 센 길이가 각 필드 한도에 맞는 등록정보 문구 제안 |

</required>

<forbidden>

| 범주 | 금지 |
|---|---|
| 근거 | 기록된 측정 없이 순위·검색량·전환율·다운로드 수를 주장하기, 합계를 맞추려고 `unknown`을 채우기 |
| 등급 | 벤더 추정치나 실무자 규칙("iOS에서 설명이 색인된다", "캡션 텍스트가 OCR로 색인된다")을 공식 규칙으로 제시하기 |
| 보장 | 어떤 변경으로든 순위·추천·승인·설치 증가를 약속하기 |
| 정책 | 키워드 도배, 경쟁사나 무관한 브랜드명, 메타데이터나 그래픽의 순위·가격 주장, 보상이나 조건부 평점 요청을 권하기 |
| 범위 | 소유자의 명시적 허락 없이 라이브 등록정보를 편집하거나 제출하기, 리뷰에 답하기, 콘솔에서 조작하기 |

</forbidden>

<validation>

실행을 완료로 선언하기 전에 [rules/validation.md](rules/validation.md)를 적용한다. 모든 critical·warning 발견사항의 증거, 모든 한도의 날짜가 붙은 공식 출처, 각 필드에 맞는 문구, `unknown`과 `not-applicable`을 제외한 관측 증거 기반 점수, `sources.md` 원장, 그리고 optimize 모드의 기록된 기준선·평가자·예산·가드·폐기한 반복·중단 사유·비교 가능한 최고 결과를 요구한다.

</validation>

## Sources

> 2026-11-22 확인. 모드 집합, 100점 가중치, optimize 가드는 이 패키지의 설계이며 저장소의 웹 검색 노출 감사 패키지를 모델로 삼았다(사용자 지시, 2026-11-22). 감사에 적용하는 외부 사실은 모두 [references/policy-limits.md](references/policy-limits.md)와 [references/sources.md](references/sources.md)에 출처와 확인 날짜가 붙어 있고, 패키지 형태는 `instructions/skill/SKILL_AUTHORING.md`를 따른다.
