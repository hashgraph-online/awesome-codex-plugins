# SEO 워크플로

**목적**: SEO 감사의 phase별 실행 규칙.

## 1. 범위 Phase

스캔 전에 감사 대상을 정의한다:

- 대상 URL 또는 file paths(single page, section, full site)
- Focus area: technical only, on-page only, content only, comprehensive
- Framework context: Next.js, static HTML, SPA 등
- Known constraints: Search Console 접근 없음, production URL 없음, local-only

출력: 대상 목록과 focus areas가 포함된 scope summary.

## 2. 측정 Phase

점수화 전에 실제로 측정 가능한 것을 확립한다:

- Access level: live URL, local-only files, Search Console, analytics, field Core Web Vitals, AI citation probe access, available tools
- 각 방법의 evidence class는 정확히 하나의 `official`, `live`, `field`, `tool`, `lab`, `synthetic`, `heuristic`
- Comparable evaluator: target set, scoring rubric, tool/version, dates, pass/fail checks
- Confidence impact와 capability fallback: 사용할 수 없는 live, field, probe, tool access 및 사용한 가장 강한 낮은 등급 방법을 설명
- `results.json.measurement_methods`에 기록할 measurement methods

field-data, live, lab, tool, synthetic, local-only 결과를 동등한 것처럼 비교하지 않는다. 사용할 수 없는 검사는 `unknown`, 관련 없는 검사는 `not-applicable`으로 기록하고 `not-applicable`은 score denominator에서 제외한다. heuristic은 official failure가 아니다.

## 3. Technical SEO Phase

다음을 스캔한다:

- `robots.txt` — 존재 여부, 올바른 directives, accidental blocks 없음
- `sitemap.xml` — 존재, 유효, 모든 indexable pages 포함
- Canonical tags — 존재, self-referencing 또는 올바른 cross-referencing
- Structured data — JSON-LD schema markup 존재 및 검증
- HTTPS — 강제 적용, mixed content 없음
- Core Web Vitals code patterns — image optimization, layout shift prevention, input responsiveness
- Mobile viewport — `<meta name="viewport">` 존재 및 정확성
- HTTP status codes — broken links 없음, proper redirects(301 vs 302)
- Clean URL structure — descriptive, kebab-case, query string abuse 없음

크롤, 렌더링, 색인은 서로 다른 상태이므로 어느 것을 관찰했는지 기록한다:

- `robots.txt`의 allow/disallow rule, `noindex` 또는 X-Robots-Tag directive, canonical target은 서로 다른 신호이며 그중 어느 하나도 페이지가 크롤·색인·서빙되었다는 증거가 아니다.
- raw HTML 응답과 rendered DOM을 별도로 감사하고 각 발견사항의 basis를 표시한다. runtime이 JavaScript를 실행할 수 없거나 live URL에 접근할 수 없으면 capability fallback을 기록하고 DOM 전용 검사는 `unknown`으로 남긴다.
- JavaScript 렌더링은 그 자체로 실패도 보장도 아니다. content와 metadata가 rendered result에 도달하는지가 발견사항이며, browser 렌더링 성공은 색인 증거가 아니다.
- `robots.txt`는 일반적인 색인 제거 수단이 아니며, 제거가 목적이면 `noindex` 또는 X-Robots-Tag directive를 사용한다.
- sitemap 포함은 discovery hint이며 index guarantee가 아니다. scope, absolute URL, `lastmod` 정확성을 확인한다.
- filter, faceted, paginated URL 폭증, empty-result 응답(soft 404), client-side-only navigation은 기본 허용이 아니라 발견사항이다.

Tools: 로컬 스캔에는 파일 목록, 내용 검색, 파일 읽기를 씁니다. live URL 분석에는 쓸 수 있을 때 페이지 가져오기나 브라우저 확인 기능을 씁니다.

## 4. Platform Policy Phase

플랫폼별 crawler와 AI/search visibility controls를 별도로 점검한다:
- Googlebot 및 indexing/snippets용 standard robots directives
- 관련 있을 때 Google AI training/product controls용 Google-Extended
- ChatGPT Search inclusion용 OAI-SearchBot, OpenAI training용 GPTBot, user-triggered fetches용 ChatGPT-User. 목적이 다르므로 각각 별도로 감사하며 하나의 rule이 다른 bot에 적용된다고 추론하지 않는다.
- Claude-SearchBot(검색), ClaudeBot(학습), Claude-User(사용자 요청 fetch), PerplexityBot(검색, 학습 아님)과 Perplexity-User(사용자 요청 fetch), 학습 제어용 Applebot-Extended·Meta-ExternalAgent·CCBot. 학습 차단이 검색 차단을 뜻하지 않으므로 토큰마다 따로 감사한다.
- CDN·WAF 봇 규칙은 별도 층으로 본다. AI 크롤러를 기본 차단하는 엣지 설정은 robots.txt 허용을 무력화할 수 있으므로 robots.txt만 읽고 접근 가능하다고 판단하지 않는다.
- Google AI 기능이 범위에 있으면 Search Console 생성형 AI 설정(포함, 제외, 상속)을 확인한다. 노출의 전제 조건이지 순위 신호가 아니며, 설정을 읽을 수 없으면 `unknown`으로 기록한다.
- `nosnippet`, `data-nosnippet`, `max-snippet`, `noindex`, canonical, X-Robots-Tag effects
- `llms.txt`는 optional proposal/content map이며 표준 또는 ranking/citation requirement가 아님
- Google AI 기능은 일반 SEO 기본 원칙을 사용한다. 관련 indexability와 snippet eligibility를 점검하되 special AI schema나 text file을 요구하지 않으며, eligibility가 inclusion을 보장하지는 않는다.
- target set이 Naver surface를 포함할 때: `Yeti` 크롤러 접근과 서치어드바이저 소유확인, 네이버 자체의 `robots.txt` 응답 처리(4xx는 전체 허용, 5xx는 전체 차단, 리다이렉트 5회 초과는 전체 허용), 소유확인 도메인과 일치하는 RSS·사이트맵 URL, `og:image` 조건(150x150 초과, 5,000 byte 이상, 3:1 이하, 페이지 고유), 그리고 사이트의 AI 자동 생성 출처설명만 억제하는 `nosourceinfo`(AI 브리핑이나 모델 학습 전반을 제외하는 지시자가 아님)를 점검한다.
- Google 전용 지시자를 Naver로 전이하지 않는다. `nosnippet`, `max-snippet`, `data-nosnippet`, `Google-Extended`, FAQPage 리치 결과, `llms.txt`는 네이버에 대응 문서가 없으므로 네이버 요건으로 보고하지 않는다. 네이버 문서가 없다는 사실은 네이버가 그 신호를 무시한다는 근거가 아니다.
- Naver에서는 soft 404 응답과 JavaScript 전용 내비게이션이 색인 제외 위험이다. 내용 없는 200 응답은 정상 문서로 수집되고, JavaScript로만 도달하는 내용은 색인에서 빠질 수 있다.
- target set이 Bing surface를 포함할 때: IndexNow를 변경 알림으로만 다룬다. 200 응답은 URL 수신, 202는 키 검증 대기를 뜻하며 어느 쪽도 색인·순위·AI 인용 증거가 아니다. `key file` 소유 증명(8-128자의 `[A-Za-z0-9-]`, 호스트 루트 또는 `keyLocation` 경로에서 로그인 없이 접근 가능)을 확인하고, POST당 10,000 URL 상한을 기록하며, 429에서는 `Retry-After`를 따르고 배치를 줄이고, 제출한 URL마다 크롤 쿼터가 소모됨을 반영하고, 기존 URL을 소급 제출하지 않는다. 사용자가 요청하지 않으면 URL을 제출하거나 키 파일을 배포하지 않는다.
- Bing 사이트맵 처리는 `changefreq`와 `priority`를 무시하고 ISO 8601 `lastmod`만 읽으므로, 두 필드를 Bing 요건으로 보고하지 않는다.

Crawler controls와 별개인 policy risk review:

- 대량 생성 콘텐츠(scaled content abuse), 만료 도메인 재사용, site reputation abuse, doorway page, thin affiliate page에 대해 target이 spam·abuse policy를 위반하는지 점검한다. 정책 세부는 `references/seo-fundamentals.md`를 참고한다.
- 생성형 AI 사용 자체는 policy violation이 아니며, 사용한 도구가 아니라 결과와 부가 가치를 기준으로 판단한다.
- 모든 policy finding은 정의된 evidence class(`official`, `live`, `tool`, `lab`, `synthetic`, `heuristic`) 중 하나로 기록하고, 확인되지 않은 정책을 사실로 단정하지 않는다.

조건부 platform module — target 조건이 성립할 때만 module에 진입하고, 성립하지 않으면 해당 dimension을 `not-applicable`로 기록한다:

- **Naver** — 감사 대상 target set이 Naver 검색 surface를 포함하거나 사용자가 Naver 감사를 요청한 경우. 조건부 항목은 `references/seo-checklist.md`의 Naver 블록에 있다.
- **Bing/IndexNow** — target set이 Bing surface를 포함하거나 사용자가 변경 알림을 요청한 경우. 조건부 항목은 `references/seo-checklist.md`의 Bing 블록에 있다.
- **Commerce/i18n** — target에 product listing, merchant feed, multi-locale surface가 있는 경우. 별도 dimension이 아니라 Technical SEO와 Structured Data 안에서 평가한다.

Module 조건은 성립하지만 account, console, live 접근이 불가능하면 pass가 아니라 `unknown`으로 기록한다.

Applicable official source 또는 직접 관찰한 files/headers가 뒷받침할 때만 policy findings를 high confidence로 기록한다. source-sensitive claim에는 URL, date, applicable claim, evidence class, limitation이 있는 source-ledger entry를 추가한다.

## 5. On-Page SEO Phase

다음을 스캔한다:

- `<title>` — 페이지 intent가 다를 때 unique하고 result context에 정확하고 유용한지 점검한다. 길이와 keyword placement는 official failure가 아닌 heuristic observation이다.
- `<meta name="description">` — 지원되고 유용한 경우 존재하며 정확하고 설득력 있는지 점검한다. 문자 수와 keyword placement는 official failure가 아닌 heuristic observation이다.
- Heading hierarchy — 페이지에 맞는 의미 있고 접근 가능한 구조인지 점검한다. multiple 또는 absent `<h1>`은 자동 failure가 아니라 맥락 검토 대상이다.
- Image alt text — 의미 있는 non-decorative 이미지에 적절한 text alternative가 있는지 점검한다.
- Open Graph tags — sharing surface가 범위에 있을 때 `og:title`, `og:description`, `og:image`, `og:url`
- Twitter Card tags — sharing surface가 범위에 있을 때 `twitter:card`, `twitter:title`, `twitter:description`
- Internal links — descriptive anchor text와 contextual relevance; link density는 requirement가 아닌 heuristic observation이다.
- URL slug — 프로젝트가 URL을 제어할 때 descriptive하고 stable한지 점검하며 query parameter는 목적에 따라 평가한다.
- Rendering basis — title, description, heading, link를 raw HTML 응답에서 읽었는지 rendered DOM에서 읽었는지 기록하고, client-rendered 값은 그 basis와 함께 보고한다.

Tools: 패턴 매칭에는 내용 검색을, 페이지 내용에는 파일이나 페이지 읽기를 씁니다(`<title>`, `<meta`, `<h1>`, `alt=`).

## 6. Content SEO Phase

다음을 평가한다:

- E-E-A-T signals — 관련 있을 때 experience, expertise, authoritativeness, trustworthiness
- Keyword placement — forced repetition이 아닌 page intent와 자연스러운 alignment
- Keyword and entity usage — 유용한 곳에 자연스럽게 배치하며 stuffing 또는 fixed-density target을 사용하지 않음
- Search intent fit — 라이브 검색이 가능하면 페이지 목차를 상위 결과 형태, 연관 검색어와 질문, 비교 대상, 검색자가 다음으로 궁금해하는 질문과 비교한다. 빠진 하위 주제는 `heuristic` 콘텐츠 finding이며 공식 실패가 아니다.
- Content depth — user intent와 page type에 충분한 coverage; word count는 minimum requirement가 아닌 heuristic observation
- Readability — intended audience와 format에 맞는 structure와 language
- Freshness — 주제의 time sensitivity에 맞는 dates와 updates
- Uniqueness — 페이지 간 harmful duplicate content 없음
- AI content — blanket AI-content rule이 아니라 관련 있을 때 review와 value-add evidence
- Rendering basis — client-side rendering 이후에만 content가 존재하면 rendered DOM으로 평가했음을 밝히고 capability limit을 기록한다.

Tools: 내용 분석에는 파일과 페이지 읽기를, 필요한 경우 competitor/SERP 맥락에는 웹 검색 기능을 씁니다.

## 7. AEO Phase(Answer Engine Optimization)

AI direct answers와 Featured Snippets 준비도를 평가한다:

- **Q&A format** — concise visible answer block이 관련 user question에 도움이 되는지 평가한다. 위치와 길이는 heuristic이다.
- **Featured Snippet readiness** — visible structure가 definition, list, table snippet에 적격할 수 있는지 평가한다. 보장하지 않는다.
- **Voice search readiness** — natural-language question이 target audience에 도움이 되는지 평가한다. 맥락 의존 heuristic이다.
- **Answer extraction ease** — clear structure와 concise passage가 reader와 system에 도움이 되는지 평가한다. 문장 수는 heuristic이다.
- **FAQ/Q&A structure** — visible FAQ/Q&A content의 유용성을 평가하고 Google FAQ rich result eligibility와 answer-friendly content를 구분한다.
- **Platform observations** — ChatGPT, Perplexity, Google AI Overviews에 고정된 content preference를 처방하지 않는다. platform-specific probe는 dated, volatile live 또는 synthetic evidence로 기록한다.
- **Entry condition** — target의 intent가 answer/citation과 관련 있을 때 이 phase를 실행하고, 그렇지 않으면 AEO readiness를 scoring하지 않고 `not-applicable`로 기록한다.

Tools: Q&A 패턴과 제목 구조에는 내용 검색을, 내용 분석에는 파일이나 페이지 읽기를 씁니다. 세부 전략은 `references/aeo-geo-guide.md`를 참고합니다.

## 8. GEO Phase(Generative Engine Optimization)

Generative responses에서 가능한 AI citation 준비도를 평가하되 citation을 보장하지 않는다:
- **GEO CORE assessment**:
  - **Context** — 주제가 충분한 context와 background를 포함하는가.
  - **Organization** — 콘텐츠에 clear hierarchy와 extractable formatting이 있는가.
  - **Reliability** — Verifiable statistics, citations, expert opinions를 포함하는가.
  - **Exclusivity** — Proprietary data, original research, unique perspective를 포함하는가.
- **Entity authority** — Topic cluster structure와 여러 콘텐츠 전반의 knowledge consistency.
- **Citable statements** — Statistics가 포함될 수 있는 짧고 독립적으로 뒷받침 가능한 문장.
- **Content freshness** — 주제의 time sensitivity에 맞는 updated dates와 source dates.
- **llms.txt** — Optional proposed LLM-facing content map이며, 부재는 standard, ranking, citation failure가 아니다.
- **Schema markup** — JSON-LD가 visible entity information과 일치하는지 여부. 이는 AI citation을 보장하지 않는다.

Tools: 인용 패턴과 통계에는 내용 검색을, 콘텐츠 최신성에는 파일이나 페이지 읽기를, `llms.txt`에는 파일 목록을 씁니다. 이름이 있는 점검이나 live probe를 쓸 수 없으면 결과를 꾸며내지 말고 capability fallback과 그에 따른 unknown을 기록합니다.

접근이 허용될 때의 선택적 high-confidence extensions — runtime과 접근이 허용할 때만 각 extension에 진입하고, 그렇지 않으면 `unknown`으로 기록하고 계속 진행한다:
- **Query fan-out simulator** — 유한하고 문서화한 subquery set을 생성하고 content expansion 권장 전에 missing coverage를 매핑한다.
- **AI citation probe** — ChatGPT, Perplexity, Gemini 또는 기타 엔진용 stable, comparable prompt set을 실행하거나 준비한다. Engine, date, sample size, prompts, cited URLs, brand mentions, evidence class, unresolved volatility를 기록한다.

## 9. Score Optimization Phase(Optimize Mode Only)

사용자가 highest score, max score, perfect score, repeated improvement를 요청할 때 이 phase를 실행한다. 이는 infinite loop가 아닌 bounded process다.

1. **Baseline and budget first** — 파일이나 권장사항 변경 전에 현재 category average, `overall_grade`, critical-finding count, target score, finite iteration budget(기본 3회), regression guard를 `results.json.score_history[0]`에 쓴다.
2. **Stable evaluator** — 모든 iteration에서 동일한 comparable target set, scoring categories, evidence classes, tools/versions, pass/fail checks를 유지한다. Evaluator가 바뀌면 reset event를 기록하고 새 점수를 이전 run과 비교하지 않는다.
3. **One change per iteration** — 하나의 high-impact change 또는 긴밀히 관련된 recommendation set 하나를 선택한다. 관련 없는 technical, content, AEO/GEO changes를 같은 iteration에 묶지 않는다.
4. **Comparable re-audit** — Category scores, findings, quick wins, evidence class, capability limits, unknown/not-applicable states를 업데이트한다. `iteration`, `changed`, `score`, `critical_count`, `decision`, `evidence`가 있는 iteration record를 append한다.
5. **Guard and discard** — comparable evidence가 개선되고 regression guard를 통과할 때만 iteration을 유지한다. 그렇지 않으면 가능한 경우 code changes를 rollback/revert하거나 iteration을 `discarded`로 표시하고 `best_run`을 보존한다.
6. **Stop gates** — target, finite budget, plateau, guard failure, safe local fix 부재, required external credential/business decision, user stop 중 하나에서 중단하고 stop reason을 기록한다.
7. **Completion artifact** — `results.json.status: "complete"`, 채워진 `score_history`, 채워진 `best_run`, final result가 best comparable verified run인 이유를 설명하는 evidence로 마무리한다.

Perfect score를 꾸며내거나 ranking, AI-feature inclusion, citation을 보장하지 않는다. unknown과 capability limit을 보고한다.

## 10. Report Phase

발견사항을 `report.md`로 컴파일한다:

1. Overall SEO health score(A/B/C/D/F)가 포함된 executive summary
2. Category별 findings(Technical SEO, On-Page SEO, Content SEO, Core Web Vitals, Structured Data, AEO Readiness, GEO Readiness)
3. 각 finding에는 severity(critical/warning/info), description, location, fix recommendation 포함
4. Impact 기준으로 정렬한 prioritized action items
5. Low-effort/high-impact fixes를 위한 quick wins section

Evidence와 raw data는 `sources.md`에 source ledger로 쓴다. 각 official 또는 external source-sensitive claim에 URL, accessed 또는 published date, applicable claim, evidence class, scope 또는 availability limitation을 기록한다.

## Optimize Mode Rules

- 사용자가 highest score, max score, perfect score, repeated iteration, 또는 infinite-loop-style improvement request를 명시적으로 요청하면 `optimize`를 사용한다.
- `create` 또는 `update` audit output에서 시작한 뒤 Score Optimization Phase로 진입한다.
- 이후 experiments가 discarded되더라도 best-scoring report와 dashboard를 보존한다.
- Implementation edits가 허용되면 각 kept code-changing iteration을 `best_run`으로 취급하기 전에 관련 project checks로 검증한다.

## Mode Rules

### Create mode

- 처음부터 full analysis
- 모든 phases를 순차 실행
- Template-based report generation

### Update mode

- 기존 `report.md`를 먼저 읽음
- 변경되었거나 새로 요청된 영역만 재분석
- Report에 dated changelog entry append
- Superseded되지 않은 prior findings 보존

### Setup mode

- 기획·제작·개편 중인 사이트나 홈페이지에서 점수가 아니라 세팅 계획이나 출시 체크리스트가 요청된 산출물일 때 쓴다.
- `references/site-setup.md`의 단계를 순서대로 따른다. 빌드 전 기획, 출시 전 빌드 점검, 출시일 등록, 첫 30일 순서다.
- `report.md`는 세팅 계획으로, `sources.md`는 원장으로 쓴다. 이미 만든 결과물의 점수형 감사도 함께 요청받았을 때만 `results.json`과 dashboard를 추가한다.
- 모든 항목을 `done`, 담당자가 정해진 `planned`, `not-applicable`, 부족한 접근 권한을 적은 `unknown` 중 하나로 기록한다.
- 콘솔 등록, DNS 레코드, 키 파일, 제출 작업은 정확한 값까지 준비하되, 사용자가 자격 증명 사용을 허락하지 않으면 사이트 소유자에게 맡긴다.

## Research Rule

- Audit에 live SERP data, competitor analysis, current ranking info가 필요하면 specific queries로 web searches를 실행한다.
- 사용자가 충분한 context를 이미 제공했다면 unnecessary external research를 강제하지 않는다.
- 모든 external queries와 sources를 `sources.md`에 기록한다.

## Sources

> 외부 출처 없음. 내용 확인 2026-11-03.

이 파일은 이 패키지 자체의 실행 단계, 증거 등급 분류, 리포트 순서를 적는다. 외부 주장이 없으므로 외부 출처를 인용하지 않는다.
