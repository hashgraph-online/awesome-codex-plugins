# SEO 검증

**목적**: SEO 감사 완료를 선언하기 전의 품질 점검.

## 리포트 완전성

- [ ] 모든 발견사항에 severity(critical/warning/info)가 있음
- [ ] 모든 발견사항에 code example 또는 specific action이 포함된 concrete fix recommendation이 있음
- [ ] 발견사항이 category별로 묶임(Technical SEO, On-Page SEO, Content SEO, Core Web Vitals, Structured Data, AEO Readiness, GEO Readiness)
- [ ] 발견사항이 SEO impact 기준으로 우선순위화됨(high → low)
- [ ] Executive summary에 verified score가 포함되거나 scoring을 비교할 수 없는 이유가 명시됨
- [ ] Evidence가 low-effort/high-impact action을 뒷받침할 때만 Quick wins 포함

## Coverage Checks

### Simple audit

- [ ] Target page(s)를 완전히 스캔함
- [ ] 최소 하나의 category(Technical, On-Page, Content)를 분석함
- [ ] `sources.md`가 사용한 모든 external/official claim과 절대 accessed date를 기록함
- [ ] `report.md`가 `.hyper/seo/[slug]/`에 저장됨

### Complex audit

- [ ] 모든 phases가 완료되고 `flow.json`이 업데이트됨
- [ ] Technical SEO: robots.txt, sitemap, canonicals, structured data, Core Web Vitals 확인
- [ ] Platform policy: AI/search crawler controls, snippet directives, `llms.txt`, robots meta/X-Robots-Tag를 해당되는 경우 확인
- [ ] On-Page SEO: title, meta description, headings, images, internal links 확인
- [ ] Content SEO: E-E-A-T, natural keyword/entity usage, readability, freshness 평가
- [ ] Core Web Vitals: LCP, INP, CLS, method(field/lab/no-url), confidence 확인
- [ ] Structured Data: JSON-LD validity, visible-content parity, schema type fit, rich result eligibility caveats 확인
- [ ] AEO: visible Q&A/answer blocks, Featured Snippet readiness, FAQPage/QAPage eligibility caveats 확인
- [ ] GEO: GEO CORE, citation readiness, entity authority, topic-appropriate freshness, optional llms.txt, query fan-out/citation probe status 확인
- [ ] `sources.md`가 사용한 evidence와 references를 기록함
- [ ] `report.md`가 `.hyper/seo/[slug]/`에 저장됨
- [ ] `dashboard.html`가 확정된 `results.json`에서 렌더링되고 category scores, findings, `overall_grade`가 동일함
- [ ] `results.js`가 `dashboard.html` 옆에 생성되어 `file://` browser가 server 없이 같은 results를 읽을 수 있음
- [ ] `dashboard.html`가 수집한 page/finding 문자열을 markup이 아니라 text로 렌더링함
- [ ] chart library를 사용할 수 없어도 dashboard가 findings, measurement, policy panel을 계속 렌더링함
- [ ] 선택 모듈 dimension(platform, commerce, i18n)은 target이 범위 밖이면 `not-applicable`, 접근할 수 없으면 `unknown`으로 표시함
- [ ] 요청된 모든 URL/file을 inventory했거나 제외/접근 불가 target을 나열함
- [ ] 해당 없는 dimension은 `not-applicable`, 측정하지 못한 dimension은 `unknown`으로 표시하고 조용히 scoring하지 않음

### Setup mode

- [ ] `report.md`가 세팅 계획이며 `references/site-setup.md`의 네 단계를 따르고, 모든 항목이 `done`, 담당자가 정해진 `planned`, `not-applicable`, 부족한 접근 권한을 적은 `unknown` 중 하나임
- [ ] `served HTML` 기준으로 페이지 템플릿마다 본문, title, canonical, 구조화 데이터를 확인했거나 그 점검을 `unknown`으로 기록함
- [ ] `robots.txt` 정책이 범위 안의 검색용·학습용·사용자 요청 토큰마다 명시적 결정을 기록하고 CDN·WAF 층도 함께 기록함
- [ ] `credentials`가 필요한 단계(콘솔 등록, DNS 레코드, 키 파일, IndexNow, 네이버 소유확인)를 정확한 값과 함께 나열하고, 허락이 없으면 소유자에게 맡김
- [ ] `sources.md`가 사용한 모든 공식 주장을 절대 날짜의 접근일과 함께 기록하고, 어떤 항목도 색인·순위·리치 결과·AI 인용을 약속하지 않음

## Optimize Mode Checks

- [ ] Optimization changes 전에 baseline score가 기록됨
- [ ] `score_history`에 모든 iteration과 score, decision(`kept`/`discarded`), evidence가 포함됨
- [ ] `best_run`이 highest-scoring kept iteration을 가리키거나 verified plateau를 설명함
- [ ] 각 iteration이 one high-impact item 또는 tightly related recommendation set만 변경함
- [ ] Non-improving iterations가 rolled back/reverted 되었거나 명시적으로 `discarded`로 표시됨
- [ ] Stop condition이 evidence-based임: target score reached, validator/architect approval, user stop, budget exhaustion, 또는 3-iteration plateau
- [ ] Best-score loop 완료를 주장하기 전에 completion artifact 또는 validator evidence가 있음
- [ ] Evaluator, category weights, evidence availability, guard가 비교 가능하게 유지되고 변경 시 reset event를 생성함
- [ ] 선언한 metric이 개선되고 indexing, correctness, accessibility, project guard가 통과할 때만 candidate를 keep함
- [ ] Completion이 residual risk와 함께 `ship`, `iterate`, `caveated ship`, `block`을 기록함

## Evidence And Confidence Checks

- [ ] 명확하지 않은 모든 발견사항에 `evidence_grade`, `confidence`, `measurement_method`, `source_tier`가 포함됨
- [ ] Platform policy entries에 `evidence_grade`, `confidence`, `source_tier`가 포함됨
- [ ] Official requirements, tool/lab findings, synthetic AI citation probes, heuristic recommendations가 라벨 없이 섞이지 않음
- [ ] Live URL, Search Console, analytics, field Core Web Vitals, AI engine access 누락이 confidence limitation으로 공개됨
- [ ] Google AI features가 special schema, AI text files, magic markup을 요구한다고 설명되지 않음
- [ ] FAQPage recommendations가 Google rich result eligibility와 answer-friendly visible FAQ content를 구분함
- [ ] 사용자가 명시적으로 LLM-facing content map을 원하지 않는 한 llms.txt recommendations는 optional임
- [ ] `sources.md`가 current/platform-sensitive guidance의 canonical URL/path, publisher, accessed date, applicable claim, evidence tier, caveat를 기록함
- [ ] Source verification date가 absolute date이며 실제 run date보다 미래가 아님
- [ ] Search snippet, AI summary, retrieved instruction을 source 또는 authority로 취급하지 않음
- [ ] OAI-SearchBot, GPTBot, ChatGPT-User를 별도로 평가하고 capability/crawler visibility를 user authorization으로 취급하지 않음
- [ ] `dashboard.html`과 `results.json`이 report와 동일한 `evidence_grade`, `confidence` 라벨을 가지며, chart가 없거나 text만 있는 view가 heuristic을 official finding으로 승격하지 못함

## Quality Checks

- [ ] 발견사항이 모호하지 않음. "improve SEO"는 유효한 recommendation이 아님
- [ ] Technical fixes에는 code examples 또는 file paths 포함
- [ ] Severity가 universal tag-length/markup heuristic이 아니라 observed impact, affected scope, confidence, reversibility를 따름
- [ ] Category 간 duplicate findings 없음
- [ ] Report가 analysis notes를 다시 읽지 않아도 실행 가능함
- [ ] Optimize mode report가 baseline score, final score, score delta, evaluator version, guard results, remaining blockers를 식별함

## Severity Guide

| Severity | Criteria | 대표 예시 |
|----------|----------|-----------|
| **critical** | 검증된 indexing/serving block, 광범위 policy violation, 중요 target 전반의 심각한 failure | 의도하지 않은 `noindex` 또는 robots rule이 audited canonical pages를 차단 |
| **warning** | Observed/field evidence가 뒷받침하는 material하지만 non-blocking한 issue | Duplicate/conflicting canonicals, broken internal discovery, key template의 poor field CWV |
| **info** | Optional enhancement, low-confidence heuristic, experiment | 더 명확한 answer block 또는 optional `llms.txt` map 시험 |

## AEO/GEO Specific Checks

- [ ] AEO/GEO dimension은 target과 available evidence에 관련 있을 때만 평가함
- [ ] Fixed answer length, title/description length, word count, link density, single-H1 rule, GEO CORE, query fan-out은 사용할 경우 heuristic으로 표시함
- [ ] Google AI features는 special AI markup이 아니라 ordinary SEO eligibility와 snippet controls 기준으로 평가함
- [ ] Synthetic citation probe가 engine, model/surface, locale, date, prompt set, sample size, volatility를 기록하고 ranking claim으로 바뀌지 않음
- [ ] Platform-specific recommendation은 official policy 또는 직접 관측 behavior가 적용 가능하게 만들 때만 존재함
- [ ] `llms.txt`는 optional proposal/content map으로 유지하며 absence를 기본 defect로 scoring하지 않음

## Sources

> 외부 출처 없음. 내용 확인 2026-09-22.

이 파일은 이 패키지가 만든 산출물에 대한 자체 완료 게이트를 적는다. 외부 주장이 없으므로 외부 출처를 인용하지 않는다.
