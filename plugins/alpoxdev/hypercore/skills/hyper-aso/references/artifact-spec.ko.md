# ASO 산출물 명세

ASO 실행의 결과 워크스페이스를 만들거나 검토할 때 이 레퍼런스를 읽는다.

## 목차

- 워크스페이스 형태
- `results.json`
- 렌더링
- `flow.json`
- 생명주기 규칙

## 워크스페이스 형태

```text
.hyper/aso/[slug]/
├── dashboard.html       # assets/dashboard-template.html에서 복사
├── results.json         # 구조화된 결과
├── results.js           # results.json에서 생성하는 file:// 폴백
├── report.md            # 리포트 또는 셋업 계획
├── sources.md           # 출처 장부
└── flow.json            # complex 또는 optimize 모드
```

디렉터리는 프로젝트 루트에 만들고 스킬 폴더 안에는 절대 만들지 않는다. `[slug]`는 앱 이름을 케밥 케이스로 쓴 것이며, 쓸모 있으면 실행 범위를 덧붙인다(`acme-budget-ios-ko`).

## `results.json`

```json
{
  "project_name": "Acme Budget",
  "date": "2026-11-22",
  "scope": "App Store ko-KR and en-US, full audit",
  "status": "complete",
  "overall_grade": "C",
  "stores": {
    "app_store": { "status": "in-scope", "locales": ["ko", "en-US"], "evidence_grade": "live", "confidence": "high", "notes": "id1234567890, iPhone storefront KR and US" },
    "google_play": { "status": "not-applicable", "notes": "no Android app" }
  },
  "categories": [
    { "name": "Metadata and keywords", "status": "measured", "score": 55, "evidence": "live page plus exported metadata", "confidence": "high" },
    { "name": "Creative assets", "status": "measured", "score": 70, "evidence": "live screenshots, iPhone and iPad", "confidence": "medium" },
    { "name": "Ratings and reviews", "status": "measured", "score": 60, "evidence": "live rating KR 4.2 (1,203) on 2026-11-22", "confidence": "medium" },
    { "name": "Localization", "status": "measured", "score": 40, "evidence": "two locales, no en-GB for KR storefront", "confidence": "high" },
    { "name": "Conversion tools", "status": "unknown", "score": null, "evidence": "no App Store Connect access", "confidence": "low" },
    { "name": "Quality signals", "status": "unknown", "score": null, "evidence": "no crash export", "confidence": "low" },
    { "name": "Policy risk", "status": "measured", "score": 80, "evidence": "guideline 2.3 scan", "confidence": "high" },
    { "name": "Web-to-app links", "status": "measured", "score": 50, "evidence": "AASA 200, no Smart App Banner", "confidence": "high" }
  ],
  "measurement_methods": {
    "store_page": { "status": "completed", "evidence_grade": "live", "confidence": "high", "notes": "KR and US storefronts, 2026-11-22" },
    "app_store_connect": { "status": "unavailable", "confidence_impact": "high", "reason": "owner did not share analytics" },
    "aso_tool": { "status": "not-run", "reason": "no vendor account" }
  },
  "keyword_set": {
    "status": "draft",
    "keywords": [
      { "term": "가계부", "store": "app_store", "locale": "ko", "placement": "name", "popularity": null, "rank": null, "source": "" },
      { "term": "budget", "store": "app_store", "locale": "en-US", "placement": "subtitle", "popularity": 61, "rank": 48, "source": "Apple Ads API 5-100, 2026-11-20" }
    ],
    "gaps": ["지출 관리", "expense tracker"]
  },
  "findings": [
    {
      "id": "M1",
      "severity": "warning",
      "store": "app_store",
      "category": "Metadata and keywords",
      "finding": "Keyword field repeats 'budget', already in the subtitle",
      "location": "en-US keyword field",
      "evidence": "exported metadata, keywords line 1",
      "evidence_grade": "official",
      "confidence": "high",
      "measurement_method": "field comparison against Apple's search rules",
      "owner_surface": "listing",
      "needs_new_version": true,
      "recommendation": "Replace 'budget' in the keyword field with 'expense,bills' (13 bytes)"
    }
  ],
  "quick_wins": [
    { "action": "Rewrite promotional text around the year-end budgeting use case", "impact": "Medium", "effort": "Low" }
  ],
  "actions": [
    { "priority": 1, "category": "Metadata and keywords", "action": "Remove repeated words across name, subtitle, keyword field", "impact": "High", "effort": "Low" }
  ]
}
```

### 필드 규칙

- `stores` 키: `app_store`, `google_play`, `one_store`, `other`. `status`: `in-scope`, `not-applicable`, `unknown`.
- `categories[].status`: `measured`(점수 0-100), `unknown` 또는 `not-applicable`(점수 `null`). 기본 8개 카테고리와 가중치는 `SKILL.md`의 `<scoring>`에 있다.
- `findings[].evidence_grade`: `official`, `live`, `console`, `tool`, `synthetic`, `heuristic`. `confidence`: `high`, `medium`, `low`. `store`: `app_store`, `google_play`, `both`, `other`. `evidence`는 `critical`과 `warning`에 필수다.
- `findings[].needs_new_version`: 그 스토어의 앱 버전과 함께만 변경이 배포되면 `true`다.
- 발견사항 id: `M` 메타데이터와 키워드, `A` 크리에이티브 에셋, `R` 평점과 리뷰, `L` 현지화, `X` 전환 도구, `Q` 품질 신호, `P` 정책 위험, `W` 웹-앱 연결.
- `keyword_set.keywords[]`: `term`은 필수다. `popularity` 값에는 벤더나 Apple, 척도, 날짜를 밝히는 `source`가 필요하다.

### 최적화 모드 필드

- `target_score`와 그 근거.
- `score_history[]`: `iteration`, `score`, `grade`, `critical_count`, `decision`(`baseline`, `kept`, `discarded`, `reset`), `changed`, `evidence`, `evaluator_version`, `weights`. 0번 항목이 기준선이다.
- `best_run`: 점수가 가장 높은 유지 또는 기준선 반복. `status`가 `complete`이면 필수다.
- 대기 중인 스토어 실험은 `score_history`가 아니라 `report.md`에 나열한다.

## 렌더링

프로젝트 루트에서 실행한다. `<skill-dir>`은 이 스킬이 설치된 폴더이고 `D`는 산출물 디렉터리다.

```bash
D=.hyper/aso/<slug>
jq -r -f <skill-dir>/assets/runtime/check-results.jq "$D/results.json"
{ printf 'window.__ASO_RESULTS__ = '; jq -c . "$D/results.json"; printf ';\n'; } > "$D/results.js"
cp <skill-dir>/assets/dashboard-template.html "$D/dashboard.html"
```

- 첫 명령은 `ok`를 출력하거나, 위반마다 stderr에 `E<TAB>message` 한 줄을 쓰고 종료 코드 1로 끝난다. `results.json`을 고치고 다시 실행한 뒤 렌더링한다.
- `results.js`는 생성 산출물이다. `results.json`을 바꿀 때마다 다시 생성한다.
- 대시보드는 HTTP에서는 `results.json`을, `file://`에서는 `results.js`를 읽고 10초마다 새로 고치며 모든 문자열을 텍스트로 렌더링한다. 차트 라이브러리를 불러오지 못해도 표는 계속 표시한다.

## `flow.json`

```json
{
  "status": "running",
  "resume_at": "creative",
  "phases": [
    { "name": "scope", "status": "complete" },
    { "name": "measurement", "status": "complete" },
    { "name": "metadata", "status": "complete" },
    { "name": "creative", "status": "running" },
    { "name": "ratings_quality", "status": "pending" },
    { "name": "policy_links", "status": "pending" },
    { "name": "report", "status": "pending" }
  ]
}
```

`phases[].status`는 `pending`, `running`, `complete`, `skipped` 중 하나이고, `resume_at`은 완료되지 않은 첫 단계를 가리키며, 재개한 실행은 그 지점에서 이어진다.

## 생명주기 규칙

- Update 모드는 기존 워크스페이스를 먼저 읽고 `report.md` § Changelog에 날짜가 붙은 항목을 덧붙인다.
- 이전 `results.json`을 삭제하지 않는다. 평가자가 바뀌면 `reset` 반복을 기록한다.
- `sources.md` 행은 덧붙이기만 하고 다시 쓰지 않는다. 대체된 행은 이유와 함께 `rejected` 또는 `conflict`로 표시한다.

## Sources

> 외부 출처 없음. 내용 확인 2026-11-22.

이 파일은 이 패키지 자체의 워크스페이스 배치, `results.json` 스키마, 렌더링 순서를 규정한다. 외부 주장은 하지 않는다.
