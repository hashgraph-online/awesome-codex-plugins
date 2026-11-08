# SEO 감사 체크리스트

**목적**: 스캔 중 사용할 실행 가능한 항목별 체크리스트. 각 감사 phase에서 사용한다.

## 목차

- 측정 및 신뢰도 체크리스트
- Technical SEO 체크리스트
- 플랫폼 정책 체크리스트
- On-Page SEO 체크리스트
- Content SEO 체크리스트
- AEO(Answer Engine Optimization) 체크리스트
- GEO(Generative Engine Optimization) 체크리스트

## 측정 및 신뢰도 체크리스트

- [ ] 접근 수준 기록: live URL, local files, Search Console, analytics, field Core Web Vitals, AI citation probe.
- [ ] 각 증거 채널에 `official`, `live`, `field`, `tool`, `lab`, `synthetic`, `heuristic` 라벨이 있음.
- [ ] 누락된 live/field/probe data는 숨기거나 0점 처리하지 않고 이유와 함께 `unknown` 또는 `not-applicable`로 기록함.
- [ ] 발견사항에 `evidence_grade`, `confidence`, `measurement_method`, `source_tier`가 포함됨.

## Technical SEO 체크리스트

### 크롤링 및 색인

- [ ] `robots.txt`가 root에 있고 중요한 페이지를 차단하지 않음
- [ ] `sitemap.xml`이 존재하고 유효하며 모든 색인 가능 페이지를 포함함
- [ ] `sitemap.xml`이 `robots.txt`에서 참조됨
- [ ] 색인 가능 페이지에 의도치 않은 `noindex` 지시문이 없음
- [ ] Canonical tags가 있고 올바른 URL을 가리킴
- [ ] Orphan pages가 없음(어디에서도 링크되지 않은 페이지)

### 크롤·렌더·색인 해석 경계

- [ ] `source HTML`과 `rendered DOM`을 body text, meta tags, canonical, links 관점에서 별도로 확인하며, JavaScript 렌더링 페이지 자체를 실패로 보지 않음
- [ ] `robots.txt` 차단과 색인 차단을 별도로 보고하며, robots.txt를 일반적인 색인 제거 수단으로 보지 않음
- [ ] `canonical` 지정 값, Google 선택 값, redirects, sitemap 항목을 별도로 보고함
- [ ] `internal links`가 rendered DOM에서 실제 `<a href>` anchor인지 확인하며, framework 문법만으로 실패 판정하지 않음
- [ ] `filtered URLs`와 대규모 사이트에서 URL 폭증, 무결과 응답, 중복 경로를 확인하며, 해당 사이트 유형에 조건부로 적용함
- [ ] `sitemap` 범위, 절대 URL, `lastmod`를 확인하며, 제출을 색인 보장으로 보지 않음

### HTTPS 및 보안

- [ ] HTTPS가 사이트 전체에 강제됨
- [ ] Mixed content가 없음(HTTPS 페이지의 HTTP 리소스)
- [ ] 유효한 SSL certificate
- [ ] HTTP → HTTPS redirects가 있음(301)

### Performance 및 Core Web Vitals

- [ ] Field data가 있을 때 LCP target: p75에서 ≤ 2.5s — hero image optimization, preloading 확인
- [ ] Field data가 있을 때 INP target: p75에서 ≤ 200ms — JavaScript execution, event handlers 확인
- [ ] Field data가 있을 때 CLS target: p75에서 ≤ 0.1 — image dimensions, dynamic content insertion 확인
- [ ] Images optimized(WebP/AVIF, proper sizing, below-fold lazy loading)
- [ ] Critical CSS가 inline 또는 preloaded
- [ ] JavaScript bundle size가 합리적이고 필요 시 code-split됨

### Structured Data

- [ ] 핵심 페이지에 JSON-LD schema markup 존재
- [ ] Schema가 오류 없이 검증됨(Schema Markup Validator)
- [ ] 보이는 콘텐츠에 적합한 schema type(Article, Product, eligible FAQPage/QAPage 등)

### Mobile

- [ ] `<meta name="viewport" content="width=device-width, initial-scale=1">` 존재
- [ ] Responsive design — 모바일에서 horizontal scroll 없음
- [ ] Touch targets ≥ 48px
- [ ] Body text font size ≥ 16px

### URL Structure

- [ ] 깔끔하고 설명적인 URL(kebab-case, lowercase)
- [ ] 색인 가능 URL에 불필요한 query parameters 없음
- [ ] 이동/이름 변경 페이지에 적절한 301 redirects
- [ ] Redirect chains 없음(A→B→C가 아니라 A→C)

## 플랫폼 정책 체크리스트

- [ ] Googlebot indexing/snippet access를 AI training controls와 별도로 확인함.
- [ ] Google-Extended policy는 관련 있을 때만 확인함.
- [ ] OAI-SearchBot과 GPTBot을 ChatGPT Search와 OpenAI training 관점에서 별도로 평가함.
- [ ] `nosnippet`, `data-nosnippet`, `max-snippet`, `noindex`, canonical, X-Robots-Tag 효과를 확인함.
- [ ] High confidence로 표시된 권장사항은 official docs 또는 observed files/headers를 인용함.

### Naver(서치어드바이저)

- [ ] `Yeti` 크롤러의 감사 대상 페이지 접근을 Googlebot과 별도로 확인하고, 서치어드바이저 소유확인이 피드·콘솔·수집요청 점검의 전제임을 기록함 (target: naver)
- [ ] 네이버 자체의 `robots.txt` 응답 처리 규칙을 관찰값으로 기록함. 4xx 응답은 전체 허용, 5xx 응답은 전체 차단, 리다이렉트 5회 초과는 전체 허용으로 해석하며, 차단은 색인 제거와 별개의 finding으로 유지함 (target: naver)
- [ ] `RSS`와 `sitemap.xml` 제출이 소유확인이 끝난 도메인과 일치하는지 확인함. 피드의 모든 URL이 등록한 사이트에 속해야 하며, 파일당 50,000 URL과 10MB 제출 한도를 함께 기록함 (target: naver)
- [ ] `og:image`가 네이버 조건을 충족하는지 확인함. 150x150 초과, 5,000 byte 이상, 가로세로 비율 3:1 이하, 페이지마다 고유한 이미지 (target: naver)
- [ ] `nosourceinfo`를 실제 범위대로 기록함. 사이트에 대해 네이버가 AI로 자동 생성한 출처설명을 제공하지 않는 지시자이며, AI 브리핑이나 모델 학습에서 전면 제외하는 지시자가 아님 (target: naver)
- [ ] `soft 404` 응답과 JavaScript 전용 내비게이션을 색인 제외 위험으로 기록함. 네이버는 내용 없는 200 응답을 정상 문서로 보아 수집 대상으로 넘기며, JavaScript로만 도달하는 내용은 색인에서 제외될 수 있음 (target: naver)
- [ ] `Google-only directives`를 네이버로 전이하지 않음. `nosnippet`, `max-snippet`, `data-nosnippet`, `Google-Extended`, FAQPage 리치 결과, `llms.txt`는 네이버에 대응 항목이 없는 Google 전용 제어이므로 네이버 요건으로 보고하지 않음 (target: naver)

### 커머스(AI 이미지 라벨)

- [ ] 커머스 리스팅에 적용되는 AI 생성 `image` 라벨·메타데이터 요건은 커머스 타깃에서만 점검함. 커머스가 아닌 타깃은 `not-applicable`이고, 리스팅 데이터를 읽을 수 없으면 `unknown`임 (target: commerce)

### 국제화(hreflang)

- [ ] `hreflang`은 상호 참조로 검증함. 대상 URL이 확인해 주지 않는 주석은 효력이 없고, `x-default`는 다른 언어를 대체하는 것이 아니라 기본을 고르는 표시이며, 언어·지역 코드는 형식이 올바라야 하고 각 페이지는 자기 참조 `hreflang`을 포함함 (target: i18n)

### Bing(IndexNow·웹마스터 도구)

- [ ] `IndexNow`를 변경 알림 채널로만 기록함. HTTP 200 응답은 검색엔진이 URL을 수신했다는 뜻이고 202는 키 검증 대기 상태이며, 어느 쪽도 색인·순위·AI 인용을 확인해 주지 않음 (target: bing)
- [ ] 제출 전에 `key file` 소유 증명을 확인함. 8-128자의 `[A-Za-z0-9-]` 문자로 구성하고 호스트 루트 또는 `keyLocation`이 지정한 경로에 UTF-8로 제공하며 로그인 없이 접근할 수 있어야 함. 키 파일 배포와 URL 제출은 사용자가 요청할 때만 수행함 (target: bing)
- [ ] `urlList` 제출은 POST당 10,000 URL 상한을 넘기지 않게 유지하고, 각 제출의 응답 코드를 finding으로 기록함 (target: bing)
- [ ] `429` 응답은 `Retry-After`를 따르고 배치를 줄여 처리하며, 대기 시간을 기록하고 재시도를 반복하지 않음 (target: bing)
- [ ] `crawl quota` 소모를 보고함. IndexNow로 제출한 모든 URL이 사이트의 크롤 쿼터를 소모하므로 변경되지 않은 URL은 제출하지 않고, 사이트 전체 일괄 제출은 사이트맵 담당으로 남김 (target: bing)
- [ ] 기존 URL의 `backfill submissions`은 권장하지 않음. 의미 있게 변경된 URL과 삭제·리다이렉트만 알리며, 같은 URL을 5분 안에 다시 제출하지 않음 (target: bing)
- [ ] Bing 사이트맵 처리는 `changefreq`와 `priority`를 무시하고 ISO 8601 형식의 `lastmod`만 읽으므로, 두 필드를 Bing 요건으로 보고하지 않음 (target: bing)
- [ ] 사이트 검증이나 콘솔 접근이 없어 읽을 수 없는 `Bing Webmaster Tools` 데이터는 실패가 아니라 `unknown`으로 기록함. Bing surface를 target set에 포함하지 않을 때만 module을 `not-applicable`로 제외함 (target: bing)

## On-Page SEO 체크리스트

### Title 및 Meta

- [ ] `<title>`이 페이지별로 고유하고, 제목 길이는 60자 표시 휴리스틱으로 보고하며 Google 제한이 아님 (heuristic)
- [ ] `<title>`에 primary keyword가 자연스럽게 포함됨
- [ ] `<meta name="description">`의 존재와 길이를 보고하며, 150-160자는 스니펫 표시 휴리스틱이고 공식 요구사항이 아님 (heuristic)
- [ ] Meta description이 설득력 있고 call to action 또는 value proposition 포함
- [ ] 페이지 간 duplicate titles 또는 descriptions 없음

### Headings

- [ ] 페이지당 `<h1>` 개수를 관찰하며, `<h1>` 하나는 관례이고 Google 요구사항이 아님 (heuristic)
- [ ] `<h1>`에 primary keyword 포함
- [ ] 논리적 heading hierarchy: h1 → h2 → h3(건너뛴 level 없음)
- [ ] Headings가 설명적이고 generic하지 않음("Section 1" 아님)

### Images

- [ ] 모든 `<img>`에 descriptive `alt` attributes 있음
- [ ] 자연스러울 때 alt text에 관련 keywords 포함
- [ ] Images에 explicit `width`와 `height` 있음(CLS prevention)
- [ ] Decorative images는 `alt=""` 사용

### Social Meta Tags

- [ ] `og:title`, `og:description`, `og:image`, `og:url` 존재
- [ ] `og:image` 크기를 보고하며, 1200×630px은 플랫폼 표시 휴리스틱이고 검증된 요구사항이 아님 (heuristic)
- [ ] `twitter:card`가 `summary_large_image` 또는 `summary`
- [ ] `twitter:title`, `twitter:description` 존재

### Internal Links

- [ ] 중요한 페이지가 navigation 또는 content에서 링크됨
- [ ] Anchor text가 설명적임("click here" 아님)
- [ ] 콘텐츠 1,000단어당 internal links 수를 보고하며, 3-5개는 공식 밀도 목표가 없는 편집 휴리스틱임 (heuristic)
- [ ] Broken internal links(404) 없음

## Content SEO 체크리스트

### 품질 및 관련성

- [ ] 콘텐츠가 target keyword의 search intent와 일치
- [ ] 콘텐츠 깊이를 search intent 기준으로 판단하며, 단어 수는 관찰값이고 공식 최소 기준이 없음 (heuristic)
- [ ] Original content — 다른 페이지나 사이트의 duplicate가 아님
- [ ] 주제의 시간 민감도에 따라 신선도를 관찰하며, 12개월은 휴리스틱이고 공식 임계값이 아님 (heuristic)

### Keyword Usage

- [ ] Primary keyword 배치를 title, H1, first 100 words에서 관찰함 (heuristic)
- [ ] Keywords와 related entities가 자연스럽게 나타남. fixed-density target 또는 stuffing 없음
- [ ] Semantic variations와 related terms가 전체에 사용됨
- [ ] Keyword cannibalization 없음(여러 페이지가 같은 keyword targeting하지 않음)

### E-E-A-T Signals

- [ ] Author information 표시(bio, credentials)
- [ ] Factual claims에 sources cited
- [ ] Contact information 접근 가능
- [ ] Privacy policy와 terms of service 존재
- [ ] Sponsored/affiliate content에 명확한 disclosure

### Readability

- [ ] 짧은 단락(2-4문장)
- [ ] Subheading 간격을 관찰하며, 200-300단어는 가독성 휴리스틱이고 요구사항이 아님 (heuristic)
- [ ] Bullet points와 lists로 스캔 가능
- [ ] 명확하고 jargon-free language(technical audience가 아닌 경우)

## AEO(Answer Engine Optimization) 체크리스트

### Direct Answer Structure

- [ ] 주요 질문에 대한 concise visible answer block이 섹션 상단 근처에 있음(길이 규칙은 heuristic)
- [ ] 질문형 H2/H3 headings 사용, 예: "## What is X?"
- [ ] Definition-style sentences가 "[Term] is [definition]" 패턴을 따름
- [ ] List 또는 table content가 Featured Snippet extraction을 지원함

### FAQ 및 Schema

- [ ] FAQPage/QAPage markup을 visible content 일치와 entity 명확성 관점에서 확인하며, FAQ rich result는 폐기됨(효력 2026-05-07, 문서 삭제 2026-06-15)이므로 rich result 자격을 주장하지 않음
- [ ] FAQ/Q&A answers가 visible content와 structured data에 일치함
- [ ] HowTo markup은 rich result를 기대하고 적용하지 않으며, Google이 HowTo rich results를 종료했으므로 HowTo content는 visible content 일치만 확인함

### Voice Search

- [ ] Natural-language question-style subheadings 사용(Who, What, Where, When, Why, How)
- [ ] Conversational answer structure 존재
- [ ] Answers가 voice assistants가 읽을 수 있을 만큼 concise and direct함

## GEO(Generative Engine Optimization) 체크리스트

### GEO CORE — Context

- [ ] 주제에 대한 충분한 context와 background 제공
- [ ] Related concepts와 definitions 포함
- [ ] Topic scope가 명확히 정의됨

### GEO CORE — Organization

- [ ] 명확한 H2/H3 hierarchy 존재
- [ ] 각 section이 2-3문장 key summary로 시작
- [ ] Short paragraphs(2-3 sentences), bullets, tables 사용
- [ ] Paragraphs가 AI systems에 의해 독립적으로 extract 가능

### GEO CORE — Reliability

- [ ] Verifiable statistics와 numeric data 포함
- [ ] Explicit source citations 포함(author name, organization, date)
- [ ] Expert opinions 또는 case studies 포함
- [ ] E-E-A-T signals 강화(author information, credentials, contact details)

### GEO CORE — Exclusivity

- [ ] Proprietary data, original research, 또는 benchmarks 포함
- [ ] Unique perspective 또는 framework 제공
- [ ] 다른 곳에서 찾을 수 없는 insights 존재

### Entity Authority

- [ ] Topic clusters 구성(pillar + cluster)
- [ ] Internal links가 related content를 연결
- [ ] Organization/Person schema가 entities를 식별
- [ ] 여러 콘텐츠 전반에 consistent expertise 표현

### Content Freshness

- [ ] Content freshness가 topic의 time sensitivity와 일치하고 `dateModified`/source dates가 정확함
- [ ] `dateModified` schema markup 포함
- [ ] Time-sensitive data에 exact dates 포함

### AI Crawler Access

- [ ] `llms.txt`를 optional content map으로 확인하고 missing file을 기본 critical로 처리하지 않음
- [ ] `robots.txt`에서 검색용 크롤러(OAI-SearchBot, Claude-SearchBot, PerplexityBot), 학습용 크롤러(GPTBot, ClaudeBot, Google-Extended, Applebot-Extended, Meta-ExternalAgent, CCBot), 사용자 요청 fetcher(ChatGPT-User, Claude-User, Perplexity-User)를 목적별 그룹으로 나눠 확인하고, robots.txt 의도를 무력화할 수 있는 CDN·WAF 봇 규칙을 별도 층으로 확인
- [ ] Important content가 JavaScript rendering 없이 접근 가능

## Sources

> 외부 출처 없음. 내용 확인 2026-11-03.

이 체크리스트는 `references/seo-fundamentals.ko.md`와 `references/aeo-geo-guide.ko.md`가 서술한 기준을 이 패키지 자체의 스캔 순서로 배열한 것이다. 외부 출처는 그 두 파일의 원장에 있으므로 여기서 새 주장을 하지 않는다.
