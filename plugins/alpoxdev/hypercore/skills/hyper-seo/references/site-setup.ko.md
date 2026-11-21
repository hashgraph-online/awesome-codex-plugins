# 새 사이트 세팅 가이드

**목적**: 검색엔진과 AI 답변 엔진이 새 사이트나 홈페이지를 크롤·색인·인용할 수 있도록 기획하고 출시하는 setup 모드용 레퍼런스.
**최종 확인**: 2026-11-03, Google Search Central과 Search Console 도움말, Next.js 문서, OpenAI·Anthropic·Perplexity 크롤러 문서, Bing Webmaster 블로그, IndexNow, 네이버 서치어드바이저, RFC 9309 기준.

## 목차

- 범위와 증거 규칙
- 1단계: 빌드 전 기획
- 2단계: 출시 전 빌드 점검
- 3단계: 출시일 등록
- 4단계: 첫 30일
- 크롤러 정책 템플릿
- 프레임워크 메모
- 세팅하지 않을 것
- 세팅 완료 기준
- Source Ledger

## 범위와 증거 규칙

- setup 모드는 아직 없거나 다시 만드는 사이트의 세팅 계획과 출시 체크리스트를 만든다. 코드는 `allowed_action`이 `edit-code`일 때만 고친다.
- 모든 항목에 증거 등급을 붙인다. 공식 요구사항은 플랫폼 문서를 인용하고, 실무 습관은 `heuristic`으로 남긴다.
- 등록과 제출은 알림·진단 통로다. 어느 것도 색인, 순위, 리치 결과, AI 인용을 보장하지 않는다.
- 계정 작업(콘솔 등록, DNS 레코드, 키 파일, IndexNow 제출)에는 사이트 소유자의 자격 증명이 필요하다. 절차와 값은 준비하되, 명시적 허락 없이 실행하지 않는다.

## 1단계: 빌드 전 기획

| 항목 | 정할 것 | 증거 등급 |
|---|---|---|
| 키워드·의도 지도 | 페이지마다 주 의도 하나. 메뉴부터 만들지 말고 사람들이 검색하는 질문에서 페이지를 만든다 | `heuristic` |
| 의도 조사 | 목표 키워드를 직접 검색해 상위 결과 형태, 연관 검색어와 질문, 비교 대상, 사람들이 다음으로 묻는 질문을 기록하고 페이지 목차로 바꾼다 | `heuristic` |
| 정보 구조 | 계층, 내비게이션, 브레드크럼, 관련 페이지 사이 내부 링크 | `official`(브레드크럼, 링크) + `heuristic`(깊이) |
| URL 규칙 | 소문자, 하이픈 구분, 안정적, 콘텐츠 하나에 URL 하나. 파라미터 변형은 고유 가치가 없으면 canonical로 합친다 | `official` |
| 페이지 템플릿 | 홈, 카테고리, 상세, 글, 문의. 템플릿마다 title, description, 제목, 구조화 데이터 계획을 정한다 | `official` |
| 엔터티 정보 | 사이트 이름, 조직 이름, 주소, 연락처를 사이트 전체와 외부 프로필에서 같게 쓴다 | `official`(site names, Organization) |
| 언어·지역 | hreflang이 필요한지. 각 언어 페이지가 자기 자신과 나머지를 모두 가리킨다 | `official` |
| 색인 범위 | `noindex`로 둘 페이지(검색 결과, 얇은 유틸리티 페이지)와 크롤 절약만을 위해 disallow할 경로 | `official` |

## 2단계: 출시 전 빌드 점검

- **서버 렌더링 HTML** — 본문, title, description, canonical, 링크가 첫 HTML 응답에 들어 있다. 일부 AI 크롤러와 Common Crawl은 JavaScript를 실행하지 않고, 네이버 소유확인은 원본 HTML을 읽는다. Dynamic rendering은 폐기된 임시방편이다.
- **Canonical** — 자기 참조, 절대 URL, 페이지당 하나, 클라이언트 JavaScript가 아니라 HTML에서 지정한다. canonical을 고르려고 `robots.txt`나 `noindex`를 쓰지 않는다.
- **Sitemap** — canonical이고 색인 가능하며 200을 돌려주는 URL만 넣는다. 파일당 50,000 URL 또는 50 MB 이하. `lastmod`는 정확할 때만 넣는다. Google은 `priority`와 `changefreq`를 무시한다.
- **robots.txt** — `text/plain`, 200으로 응답한다. 실제 비공개 경로나 크롤 낭비 경로만 disallow하고 `Sitemap:` 줄을 넣는다. robots 규칙은 접근 제어가 아니다. 네이버에서는 5xx 응답이 크롤 전체 차단으로 해석된다.
- **구조화 데이터** — 지원되는 유형만 JSON-LD로 쓴다. 홈에는 `WebSite`(사이트 이름)와 `Organization`, 하위 페이지에는 `BreadcrumbList`, 글에는 `Article`, 상품 페이지에는 `Product`. 마크업은 보이는 내용과 같아야 한다. FAQ와 HowTo 리치 결과는 더 이상 표시되지 않는다.
- **메타데이터** — 페이지마다 고유한 title과 description, Open Graph 태그(`og:title`, `og:type`, `og:image`, `og:url`), 네이버가 범위에 있으면 네이버 조건을 충족하는 페이지 고유 `og:image`.
- **Core Web Vitals 예산** — 75번째 백분위에서 LCP 2.5초, INP 200ms, CLS 0.1을 목표로 둔다. 순위 스위치가 아니다.
- **상태 코드** — 없는 페이지는 실제 404, 영구 이동은 301, soft 404 없음.
- **크롤러 정책** — 업체별로 검색용과 학습용 접근을 결정하고 CDN·WAF에도 같은 결정을 반영한다. 아래 템플릿을 본다.

## 3단계: 출시일 등록

| 단계 | 할 일 | 주의 |
|---|---|---|
| Google Search Console | DNS로 인증하는 Domain 속성을 추가하고, 데이터를 따로 봐야 하는 하위 도메인이나 섹션은 URL 접두어 속성을 추가한다 | Domain 속성은 모든 하위 도메인과 프로토콜을 섞어 보여주고, 링크 거부 도구는 Domain 속성을 지원하지 않는다 |
| 사이트맵 제출 | Search Console에 sitemap을 제출한다 | 발견 힌트이지 색인 보장이 아니다 |
| 생성형 AI 설정 | 소유자가 달리 정하지 않았다면 속성이 포함(기본값) 상태인지 확인한다 | Google 생성형 AI 기능 노출의 전제 조건이며 순위 신호가 아니다 |
| Bing Webmaster Tools | Search Console에서 가져오거나 직접 인증하고 sitemap을 제출한다 | Bing 데이터는 Copilot 인용 보고서에도 쓰인다 |
| IndexNow | 키를 만들어 호스트 루트에 키 파일을 두고, 발행·수정·삭제 때 알린다 | 알림일 뿐이다. 한 번 보내면 네이버를 포함한 참여 엔진에 공유된다 |
| 네이버 서치어드바이저 (target: naver) | 서버가 내려주는 `<head>`의 메타 태그나 HTML 파일로 소유를 확인하고 sitemap을 제출한다 | 노출을 위한 네이버 등록 절차는 없다. 소유확인은 진단과 제출 기능을 여는 것이다 |
| Daum 웹마스터도구 (target: naver) | 선택 사항인 진단 등록 | 등록 여부는 수집 포함과 무관하다 |
| 분석 | Referrals보다 위에 "AI assistants" 맞춤 채널 그룹을 둔 GA4 | AI 앱 유입은 direct로 잡히는 경우가 많아 채널이 실제보다 적게 센다 |

## 4단계: 첫 30일

- Search Console 페이지 보고서에서 "크롤링됨 - 현재 색인이 생성되지 않음"과 "발견됨" 묶음을, 사이트맵 보고서에서 읽기 오류를 확인한다.
- 생성 AI 성과 보고서는 웹 검색 보고서와 따로 읽는다. 인용이 아니라 노출 수를 보여준다.
- Bing AI Performance(인용, grounding 질의)와, 제공되면 Citation Share를 확인한다.
- 새 URL과 바뀐 URL은 sitemap과 IndexNow로 알린다. 수동 색인 요청은 중요한 URL 몇 개에만 한다. 같은 URL을 여러 번 요청해도 크롤이 빨라지지 않고, Google과 네이버 모두 요청이 노출을 보장하지 않는다고 밝힌다.
- AI 노출은 고정 프롬프트 세트와 기간의 빈도(예: 7-30일 중 인용된 날의 비율)로 측정하고, 한 번의 관찰로 판단하지 않는다.

## 크롤러 정책 템플릿

토큰마다 명시적 그룹을 둔다. `User-agent: *`만으로는 업체별 결정을 표현하지 못한다. 각 그룹은 소유자의 결정에 맞춰 바꾼다.

```text
# Search and answer surfaces (citations)
User-agent: Googlebot
User-agent: Bingbot
User-agent: OAI-SearchBot
User-agent: Claude-SearchBot
User-agent: PerplexityBot
User-agent: Applebot
User-agent: Meta-WebIndexer
User-agent: Yeti
Allow: /

# Model training (allow or disallow by owner decision)
User-agent: GPTBot
User-agent: ClaudeBot
User-agent: Google-Extended
User-agent: Applebot-Extended
User-agent: Meta-ExternalAgent
User-agent: CCBot
Disallow: /

Sitemap: https://example.com/sitemap.xml
```

- 학습용 토큰을 막아도 그 업체의 검색 답변에서 빠지지 않는다. 검색용 토큰을 막으면 빠진다.
- 사용자 요청 fetcher(`ChatGPT-User`, `Perplexity-User`)는 robots.txt를 따르지 않을 수 있다. 실제로 막으려면 CDN이나 WAF가 필요하다.
- AI 크롤러를 기본 차단하는 CDN 설정은 허용 규칙을 무력화할 수 있다. 엣지 설정은 따로 확인한다.

## 프레임워크 메모

- **Next.js App Router** — 루트 layout에 `metadataBase`를 둔다(없으면 상대 경로 메타데이터 URL이 빌드 오류가 된다). `generateMetadata`에서 `alternates.canonical`과 `alternates.languages`를 쓰고, `app/sitemap.ts`와 `app/robots.ts`를 두며, JSON-LD는 layout이나 page의 `<script>`에 넣고 `<`를 이스케이프한다. `opengraph-image`에는 크기와 alt를 선언한다.
- **다른 프레임워크** — 프레임워크의 head·sitemap 기능을 쓰고, 개발자 도구가 아니라 view-source나 `curl`로 실제 응답 HTML을 확인한다.

## 세팅하지 않을 것

- 노출 수단으로서의 `llms.txt`. Google은 이를 무시하고 공개된 파일 대부분은 한 번도 요청되지 않는다. 코딩 에이전트가 읽는 개발자 문서에만 둔다.
- AI 노출을 위해 추가하는 AI 전용 schema, "쪼갠" 콘텐츠, FAQ 블록. Google은 필요 없다고 밝히고, 같은 사이트 안 비교에서도 인용 효과가 견고하지 않다.
- 키워드마다 거의 같은 페이지를 대량으로 만들거나 위성 사이트를 만드는 것. 서로 경쟁하고 scaled content abuse에 해당할 수 있다.

## 세팅 완료 기준

- 모든 단계 항목이 `done`, 담당자가 정해진 `planned`, `not-applicable`, 부족한 접근 권한을 적은 `unknown` 중 하나다.
- 페이지 템플릿마다 실제 응답 HTML에서 본문, title, canonical, 구조화 데이터를 확인했다.
- 크롤러 정책에 범위 안의 검색용·학습용 토큰마다 명시적 결정이 있다.
- 자격 증명이 필요한 등록 단계는 정확한 값과 함께 나열했고, 허락이 없으면 소유자에게 맡겼다.
- 어떤 항목도 색인, 순위, 리치 결과, AI 인용을 약속하지 않는다.

## Source Ledger

| Source | Accessed | Supports | Caveat |
|---|---|---|---|
| https://developers.google.com/search/docs/fundamentals/ai-optimization-guide | 2026-11-03 | 생성형 AI 검색 최적화는 여전히 SEO, llms.txt와 chunking은 불필요, 생성형 AI 포함 설정이 필요 | Google surface에만 해당 |
| https://developers.google.com/search/docs/appearance/ai-features | 2026-11-03 | AI Overviews와 AI Mode에 추가 파일·마크업 불필요 | 계속 갱신되는 문서 |
| https://support.google.com/webmasters/answer/16908024 | 2026-11-03 | Search 생성 AI 포함·제외·상속 설정 | 순위나 학습 제어가 아님 |
| https://support.google.com/webmasters/answer/34592 | 2026-11-03 | Domain 속성과 URL 접두어 속성의 범위, DNS 인증 | 콘솔 문구는 바뀔 수 있음 |
| https://support.google.com/webmasters/answer/2648487 | 2026-11-03 | 링크 거부 도구는 Domain 속성을 지원하지 않음 | 링크 거부는 거의 필요 없음 |
| https://developers.google.com/search/docs/crawling-indexing/ask-google-to-recrawl | 2026-11-03 | 크롤 요청은 포함을 보장하지 않음, 할당량, 반복 요청은 효과 없음 | Google에만 해당 |
| https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls | 2026-11-03 | 자기 참조 canonical, robots.txt로 canonical 지정 금지 | canonical은 지시가 아니라 신호 |
| https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap | 2026-11-03 | sitemap 한도, 정확한 lastmod, priority·changefreq 무시 | Google 동작 |
| https://developers.google.com/search/docs/crawling-indexing/javascript/dynamic-rendering | 2026-11-03 | Dynamic rendering은 장기 해법이 아닌 임시방편 | Google은 JavaScript를 렌더하지만 다른 크롤러는 아닐 수 있음 |
| https://developers.google.com/search/docs/appearance/site-names | 2026-11-03 | 사이트 이름용 WebSite 구조화 데이터는 홈에 둠 | 도메인·하위 도메인 단위만 |
| https://nextjs.org/docs/app/api-reference/functions/generate-metadata | 2026-11-03 | metadataBase, alternates.canonical, alternates.languages | Next.js App Router에만 해당 |
| https://www.rfc-editor.org/rfc/rfc9309 | 2026-11-03 | robots 규칙은 접근 권한이 아님, 그룹 매칭 | 2022년 표준 |
| https://platform.openai.com/docs/bots | 2026-11-03 | OAI-SearchBot, GPTBot, ChatGPT-User의 목적 | Bot string은 바뀔 수 있음 |
| https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler | 2026-11-03 | ClaudeBot, Claude-SearchBot, Claude-User의 목적 | Bot string은 바뀔 수 있음 |
| https://docs.perplexity.ai/guides/bots | 2026-11-03 | PerplexityBot은 모델 학습에 쓰이지 않음, Perplexity-User는 대체로 robots.txt를 따르지 않음 | 업체 진술 |
| https://commoncrawl.org/faq | 2026-11-03 | CCBot은 JavaScript를 실행하지 않음 | 답변 엔진이 아님 |
| https://blogs.bing.com/webmaster/2026/2/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview/ | 2026-11-03 | Bing AI Performance 인용 보고서 | Public preview |
| https://www.indexnow.org/documentation | 2026-11-03 | IndexNow 제출은 참여 엔진에 공유됨 | 알림일 뿐 |
| https://searchadvisor.naver.com/guide/faq-start-register | 2026-11-03 | 네이버 등록 절차 없음, 소유확인 메타는 서버 렌더링 head에 둠 | 네이버 문서는 날짜 표기 없음 |
| https://searchadvisor.naver.com/guide/indexnow-about | 2026-11-03 | 네이버는 IndexNow를 지원하지만 색인을 보장하지 않음 | 네이버 문서는 날짜 표기 없음 |
| https://searchadvisor.naver.com/guide/request-crawl | 2026-11-03 | 수집요청은 네이버 노출을 보장하지 않음 | 네이버 문서는 날짜 표기 없음 |
| https://www.threads.com/@avcd.eee/post/DfMnpWEj3ij | 2026-11-03 | 실무자의 기획, 출시, 의도 조사, 콘텐츠 작업 흐름 | 실무자 1인 자료이므로 `heuristic`으로만 쓰고 위 행들과 교차 확인함 |

## Sources

> 확인 2026-11-03.

이 파일의 모든 외부 주장은 위 Source Ledger에 읽은 날짜와 함께 기록되어 있다. 이번 개정의 전체 조사 기록은 패키지 밖에 있다.
