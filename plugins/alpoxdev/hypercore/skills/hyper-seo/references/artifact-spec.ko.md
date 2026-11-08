# SEO 감사 산출물 명세

SEO 감사 실행의 결과 워크스페이스를 만들거나 검토할 때 이 레퍼런스를 사용한다.

## 목차

- 워크스페이스 형태
- `results.json`
- `results.js`
- `dashboard.html`
- `report.md`
- `flow.json`
- 생명주기 규칙

## 워크스페이스 형태

```text
.hyper/seo/[slug]/
├── dashboard.html       # 브라우저에서 열 수 있는 대시보드
├── results.json         # 구조화된 감사 결과
├── results.js           # file:// 브라우저 폴백용
├── report.md            # Markdown 리포트(기존)
├── sources.md           # 출처 기록(기존)
└── flow.json            # complex path only(기존)
```

이 디렉터리는 스킬 폴더 안이 아니라 저장소 루트에 만든다.

정식 생성 자산:

- template: `skills/hyper-seo/assets/dashboard-template.html`
- renderer: `skills/hyper-seo/scripts/render-dashboard.sh`
- renderer runtime: bash 3.2+와 `jq`

## `results.json`

```json
{
  "project_name": "my-website",
  "date": "2026-03-27",
  "scope": "Full site audit",
  "status": "complete",
  "overall_grade": "C",
  "categories": [
    { "name": "Technical SEO", "status": "measured", "score": 85, "evidence": "crawl 및 robots/header 스캔", "confidence": "high" },
    { "name": "On-Page SEO", "status": "measured", "score": 72, "evidence": "40개 페이지의 title/meta/heading 표본", "confidence": "high" },
    { "name": "Content SEO", "status": "measured", "score": 68, "evidence": "thin content 및 내부 링크 스캔", "confidence": "medium" },
    { "name": "Core Web Vitals", "status": "measured", "score": 90, "evidence": "Lighthouse lab 실행, field data 없음", "confidence": "medium" },
    { "name": "Structured Data", "status": "measured", "score": 88, "evidence": "schema 정적 스캔 및 rich results test", "confidence": "high" },
    { "name": "AEO Readiness", "status": "measured", "score": 45, "evidence": "상위 페이지 answer block 탐지", "confidence": "medium" },
    { "name": "GEO Readiness", "status": "measured", "score": 38, "evidence": "상위 페이지 인용 및 entity 스캔", "confidence": "low" }
  ],
  "measurement_methods": {
    "search_console": { "status": "unavailable", "confidence_impact": "medium" },
    "pagespeed_insights": { "status": "lab-only", "tool": "Lighthouse", "confidence": "medium" },
    "rich_results_test": { "status": "not-run", "fallback_method": "schema_static_scan", "confidence": "medium" },
    "ai_citation_probe": { "status": "not-run", "reason": "no engine access" },
    "crawler_policy_scan": { "status": "completed", "method": "robots/meta/header scan", "confidence": "high" }
  },
  "platform_policy": {
    "oai_searchbot": { "status": "allowed", "purpose": "ChatGPT Search inclusion", "evidence_grade": "official", "confidence": "high", "source_tier": "official-doc" },
    "gptbot": { "status": "blocked", "purpose": "OpenAI model training", "evidence_grade": "official", "confidence": "high", "source_tier": "official-doc" },
    "llms_txt": { "status": "missing", "severity": "info", "evidence_grade": "heuristic", "confidence": "medium", "source_tier": "research-backed-heuristic" },
    "naver_yeti": { "status": "unknown", "purpose": "Naver Yeti crawler access to the audited pages", "evidence_grade": "official", "confidence": "medium", "source_tier": "official-doc" },
    "naver_nosourceinfo": { "status": "not-applicable", "purpose": "Naver AI-generated source description exclusion", "evidence_grade": "official", "confidence": "high", "source_tier": "official-doc" },
    "naver_feeds": { "status": "unknown", "purpose": "RSS and sitemap ownership-domain match", "evidence_grade": "official", "confidence": "medium", "source_tier": "official-doc" },
    "bing_indexnow": { "status": "unknown", "purpose": "IndexNow change notification for the audited URLs", "http_code": null, "batch_size": 0, "key_location_verified": false, "quota_source": "unknown", "evidence_grade": "official", "confidence": "low", "source_tier": "official-doc" }
  },
  "query_fanout": {
    "status": "not-run",
    "queries": [],
    "missing_topics": []
  },
  "citation_probe": {
    "status": "not-run",
    "engines": [],
    "sample_size": 0,
    "confidence": "low"
  },
  "findings": [
    {
      "id": "T1",
      "severity": "critical",
      "category": "Technical SEO",
      "finding": "robots.txt blocks /blog/ path",
      "location": "/robots.txt:3",
      "evidence_grade": "lab",
      "confidence": "high",
      "measurement_method": "static robots.txt scan",
      "source_tier": "observed-file",
      "recommendation": "Remove Disallow: /blog/ line"
    },
    {
      "id": "A1",
      "severity": "warning",
      "category": "AEO Readiness",
      "finding": "No direct answer in first paragraph",
      "location": "/blog/what-is-seo.html",
      "evidence_grade": "heuristic",
      "confidence": "medium",
      "measurement_method": "answer block detector",
      "source_tier": "research-backed-heuristic",
      "recommendation": "Add a concise visible answer block near the top of the section"
    }
  ],
  "quick_wins": [
    {
      "action": "Add meta descriptions to 12 pages missing them",
      "impact": "High",
      "effort": "Low"
    }
  ],
  "score_history": [
    {
      "iteration": 0,
      "score": 66,
      "grade": "C",
      "critical_count": 1,
      "decision": "baseline",
      "evaluator_version": "2026-03-27.1",
      "weights": [20, 20, 15, 15, 10, 10, 10],
      "evidence": "Initial audit before optimization changes"
    },
    {
      "iteration": 1,
      "score": 78,
      "grade": "B",
      "critical_count": 0,
      "decision": "kept",
      "evaluator_version": "2026-03-27.1",
      "weights": [20, 20, 15, 15, 10, 10, 10],
      "changed": "Removed robots.txt block for /blog/",
      "evidence": "Re-audit confirmed indexability restored"
    }
  ],
  "best_run": {
    "iteration": 1,
    "score": 78,
    "grade": "B",
    "reason": "Highest kept score with zero critical findings"
  },
  "validator": {
    "status": "passed",
    "summary": "Target passed or plateau condition verified"
  },
  "actions": [
    {
      "priority": 1,
      "category": "Technical SEO",
      "action": "Fix robots.txt blocking blog content",
      "impact": "High",
      "effort": "Low"
    },
    {
      "priority": 2,
      "category": "GEO Readiness",
      "action": "Add statistics and citations to top 10 pages",
      "impact": "High",
      "effort": "Medium"
    }
  ]
}
```

### 증거 및 신뢰도 필드

명확하지 않은 모든 발견사항은 다음을 포함해야 한다:

- `evidence_grade`: `official`, `live`, `field`, `tool`, `lab`, `synthetic`, `heuristic`.
- `confidence`: `high`, `medium`, `low`.
- `measurement_method`: 발견사항을 만든 스캔, 도구, probe, 출처.
- `source_tier`: `official-doc`, `observed-file`, `live-observation`, `field-data`, `tool-output`, `lab-result`, `synthetic-probe`, `research-backed-heuristic`.

공식 문서, 직접 파일/헤더 관찰, field data에는 높은 신뢰도를 사용한다. 로컬 전용 정적 스캔, lab-only performance, synthetic AI prompt probe, heuristic AEO/GEO 조언에는 더 낮은 신뢰도를 사용한다.

### 측정 및 플랫폼 필드

- `measurement_methods`는 사용 가능한 증거 채널과 그것이 신뢰도에 미친 영향을 기록한다.
- `platform_policy`는 플랫폼 또는 봇별 검색/AI crawler 및 snippet controls를 기록한다. `OAI-SearchBot` 검색 포함과 `GPTBot` 학습 정책을 분리한다. 조건부 platform 항목은 target 조건에 따라 기록한다. target이 범위 밖이면 `not-applicable`, target은 해당하지만 console·account·live 접근이 불가능하면 `unknown`을 쓴다. target set이 Naver surface를 포함하면 `naver_yeti`, `naver_nosourceinfo`, `naver_feeds`를 기록한다. Bing surface를 포함하면 관찰한 응답 코드, batch 크기, 키 파일 검증 여부, `engine` 또는 `unknown`인 quota source를 담아 `bing_indexnow`를 기록한다. 수신 코드를 색인 증거로 기록하지 않고 할당량 수치를 추정하지 않는다.
- `query_fanout`은 생성된 하위 쿼리와 누락된 주제 커버리지를 기록한다.
- `citation_probe`는 실행 시 AI 엔진, 프롬프트 세트, 인용 URL, 브랜드 언급, 표본 크기, 날짜, 신뢰도를 기록한다. 실행하지 않았다면 `status: "not-run"`과 이유를 저장한다.

### Optimize mode 필드

`mode`가 `optimize`이거나 사용자가 highest/max/perfect score를 요청했을 때 `results.json`에 다음 필드를 추가한다:

- `target_score` — optional user-defined 또는 evaluator-defined goal. 근거를 기록하고 임의의 “perfect” threshold를 기본값으로 두지 않는다.
- `score_history[]` — 순서가 있는 iteration log. 각 항목은 `iteration`, `score`, `grade`, `critical_count`, `decision`, `changed`, `evidence`, `evaluator_version`, `weights`, `guard`를 포함한다.
- `best_run` — 가장 높은 점수를 받은 kept iteration. 완료 전 필수.
- `validator` — `{ "status": "passed" }` 또는 architect review verdict 같은 artifact-gated completion evidence.
- `plateau` — 점수 향상이 더 없어 완료할 때 `consecutive_iterations`와 `reason`을 담는 선택 객체.

규칙:

1. `score_history[0]`은 항상 변경 전 baseline이다.
2. 이후 점수는 evaluator가 안정적으로 유지될 때만 비교 가능하다. scoring이 바뀌면 reset event를 기록한다.
3. `best_run`은 discarded iteration을 가리키면 안 된다.
4. 코드 변경이 있었다면 validator evidence에는 관련 test/build/lint 명령 출력 요약이 포함되어야 한다.
5. 더 높은 rubric score만으로는 충분하지 않다. Indexing, correctness, accessibility, policy, project guard가 regression하면 keep하지 않는다.
6. `unknown`과 `not-applicable` category를 numeric zero로 바꾸지 않는다.
7. 모든 `score_history[]` 항목은 `evaluator_version`과 `weights`(canonical 순서의 category 가중치)를 기록한다. 점수는 같은 evaluator version과 가중치 집합 안에서만 비교한다.
8. `evaluator_version`, `weights`, category 구성이 바뀌면 새 정의 아래의 첫 iteration이 `decision: "reset"`을 달고 있어야 한다. reset을 건너뛰고 점수 delta를 보고하지 않는다.
9. `best_run`은 kept iteration 중 가장 높은 점수의 실행이어야 한다.

### 상태 값

- `running` — 감사 진행 중
- `idle` — 대기 중
- `complete` — 감사 완료

### 기본 카테고리 목록

7개 default category를 사용한다. 각 category는 `status: "measured" | "unknown" | "not-applicable"`, `score: 0..100 | null`, evidence, confidence를 기록한다. Numeric rubric은 internal prioritization aid이며 Google/AI-platform ranking score가 아니다.

1. Technical SEO
2. On-Page SEO
3. Content SEO
4. Core Web Vitals
5. Structured Data
6. AEO Readiness
7. GEO Readiness

### Finding ID 규칙

- `T1`, `T2`... — Technical SEO
- `O1`, `O2`... — On-Page SEO
- `C1`, `C2`... — Content SEO
- `W1`, `W2`... — Core Web Vitals
- `S1`, `S2`... — Structured Data
- `A1`, `A2`... — AEO Readiness
- `G1`, `G2`... — GEO Readiness

### Severity 값

- `critical` — 색인을 차단하거나 랭킹을 심각하게 해침
- `warning` — 랭킹 또는 UX 저하
- `info` — 개선 기회

## `results.js`

`file://`로 열었을 때 `fetch`가 작동하지 않는 브라우저를 위한 폴백:

```javascript
window.__SEO_RESULTS__ = { /* results.json과 동일한 내용 */ };
```

`render-dashboard.sh`가 `dashboard.html`과 같은 `results.json` payload에서 이 파일을 생성한다. 손으로 유지하는 파일이 아니므로 `results.json`이 바뀌면 렌더러를 다시 실행한다. 손으로 고친 내용은 덮어써진다.

## `dashboard.html`

`skills/hyper-seo/assets/dashboard-template.html`에서 복사한다.

필수 동작:

- 10초마다 자동 새로고침
- `results.json` 읽기(`file://`에서는 `results.js` 폴백)
- 7개 카테고리 점수 레이더 차트
- Severity 분포 도넛 차트
- 카테고리 점수 바
- Severity 색상 코딩이 있는 Findings 테이블
- Quick Wins 테이블
- Prioritized Actions 테이블
- Overall Grade 표시(A/B/C/D/F)

## `report.md`

기존 `assets/report.template.md`에서 생성한다. `results.json` 데이터를 Markdown으로 렌더링한 형태다.

## `flow.json`

complex와 optimize 실행은 단계 상태를 여기에 기록한다. 최소 계약:

```json
{
  "status": "running",
  "resume_at": "onpage",
  "phases": [
    { "name": "scope", "status": "complete" },
    { "name": "measurement", "status": "complete" },
    { "name": "technical", "status": "complete" },
    { "name": "platform_policy", "status": "complete" },
    { "name": "onpage", "status": "running" },
    { "name": "content", "status": "pending" },
    { "name": "aeo", "status": "pending" },
    { "name": "geo", "status": "pending" },
    { "name": "report", "status": "pending" }
  ]
}
```

| Field | Contract |
|-------|----------|
| `phases[].name` | 아래 단계 순서에 정의된 canonical phase name |
| `phases[].status` | `pending`, `running`, `complete`, `skipped` 중 하나 |
| `resume_at` | `status`가 `complete`가 아닌 첫 단계의 `name`. 재개한 실행은 `flow.json`을 먼저 읽고 그 지점부터 이어간다 |

Canonical 단계 순서: `scope` → `measurement` → `technical` → `platform_policy` → `onpage` → `content` → `aeo` → `geo` → `report`. 이 목록은 `SKILL.md`의 단계 순서와 동일하게 유지한다.

## 생명주기 규칙

1. 감사 시작 시 `.hyper/seo/[slug]/`를 만든다.
2. `results.json`의 `status`를 `running`으로 설정한다.
3. 각 phase 완료 시 `results.json`에 findings를 추가한다.
4. 모든 phase 완료 후 `status`를 `complete`로 설정하고 `overall_grade`를 계산한다.
4-1. Optimize mode에서는 `score_history`, `best_run`, `validator`를 채우고 최고 점수 또는 plateau 근거를 기록한다.
5. `bash scripts/render-dashboard.sh <artifact-dir>`를 실행해 `dashboard.html`과 `results.js`를 생성한다.
6. `report.md`와 `sources.md`도 작성한다.
7. 런타임이 안전하면 `dashboard.html`을 브라우저에서 연다.

### Grade 계산

가중 산식이 유일한 집계 방식이다. Category 점수는 canonical 순서의 7개 default category에서 오고, 가중치는 `SKILL.md`의 `<scoring>` 블록에서 온다.

```text
overall_score = Σ(category_score × category_weight) / Σ(category_weight)
```

| Rule | Contract |
|------|----------|
| Aggregation | 포함된 category에 대해 `overall_score = Σ(score × weight) / Σ(weight)` |
| Included categories | `status: "measured"` category만 계산한다. `unknown`과 `not-applicable` category는 분자와 분모 모두에서 제외한다 |
| Weights | `SKILL.md`의 `<scoring>` 가중치를 canonical category 순서로 적용한다 |
| Recorded | 포함된 category, 가중치, evaluator version, evidence availability를 기록한다 |
| Definition change | category set, weights, evaluator version이 바뀌면 delta를 보고하지 않고 새 baseline을 시작하며 reset을 기록한다 |

가중 점수에 아래 등급표를 적용한다.

| Average | Grade |
|---------|-------|
| >= 90 | A |
| >= 75 | B |
| >= 60 | C |
| >= 40 | D |
| < 40 | F |

### 렌더 순서

```bash
bash skills/hyper-seo/scripts/render-dashboard.sh .hyper/seo/my-site
open .hyper/seo/my-site/dashboard.html
```

## Sources

> 외부 출처 없음. 내용 확인 2026-09-22.

이 파일은 이 패키지 자체의 워크스페이스 형태, `results.json` 스키마, 대시보드 생명주기, 렌더 순서를 규정한다. 외부 주장이 없으므로 외부 출처를 인용하지 않는다.
