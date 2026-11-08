# SEO 기본 레퍼런스

**목적**: 감사 분석을 위한 핵심 SEO 지식. 발견사항을 기준과 비교해 평가할 때 로드한다.
**최종 확인**: 2026-09-21, Google Search Essentials와 spam policies, Google Search updates log, Google structured-data policies와 Search Gallery, Google AI-features guidance, web.dev Core Web Vitals guidance 기준.
**근거 메모**: Official requirement는 platform policy이며 ranking outcome을 보장하지 않는다. Current/platform-sensitive recommendation 전에는 applicable page를 다시 확인한다.

## 목차

- Search Essentials
- 크롤·렌더·색인·노출 파이프라인
- E-E-A-T 프레임워크
- Core Web Vitals
- 우선순위 모델
- Schema Markup Types
- 구조화 데이터 지원 상태
- Keyword And Intent Strategy
- AI Content Guidelines
- 스팸·어뷰즈 정책
- Entity And Trust Signals
- Source Ledger
- 측정 도구

## Search Essentials

다음을 가장 신뢰도 높은 기준선으로 사용한다:

1. 중요한 페이지가 크롤링, 렌더링, 색인되고 snippet과 함께 표시될 수 있도록 기술 요구사항을 충족한다.
2. 스팸 또는 기만적 전술을 피한다.
3. 유용하고 신뢰할 수 있으며 사람 중심의 콘텐츠를 만든다.
4. 사람들이 콘텐츠를 찾을 때 사용할 단어를 title, main heading, alt text, link text 같은 눈에 띄는 위치에 사용한다.
5. 링크를 crawlable하게 만들고 중요한 콘텐츠를 visible text로 제공한다.
6. 관련성이 있을 때 structured data, images, videos, JavaScript best practices를 사용한다.

## 크롤·렌더·색인·노출 파이프라인

검색 자격은 다음 네 단계를 순서대로 지난다. 한 단계를 충족했다고 다음 단계까지 보장되지는 않는다. 크롤된 페이지가 모두 렌더링되지 않고, 렌더링된 페이지가 모두 색인되지 않으며, 색인된 페이지가 모두 노출되지 않는다. 단계를 각각 따로 감사하고, 발견사항이 어느 단계에 속하는지 표시한다.

| Stage | 확인할 것 | 보장하지 않는 것 |
|---|---|---|
| `crawl` | 서버 응답, robots.txt 규칙, 접근 가능한 URL, sitemap 발견, 실제 `<a href>` 링크 | 크롤 성공은 렌더링·색인·노출에 대해 아무것도 말해주지 않는다 |
| `render` | 원본 응답과 비교한 렌더링 DOM의 본문, meta, canonical, structured data, 내부 링크 | 브라우저나 lab 렌더는 Google이 렌더링·색인했다는 증거가 아니며, 렌더링 자체가 보장되지 않는다 |
| `index` | 색인 상태 어휘(discovered, crawled, duplicate, indexed), canonical 선택, `noindex`, soft 404, 필터·빈약 URL | 색인은 ranking, snippet, rich result를 보장하지 않는다 |
| `appearance` | title, snippet, rich result, AI surface와 Search Console에서의 측정 방식 | 노출은 안정적이지 않다. 플랫폼은 공지 없이 기능과 보고를 추가·종료한다 |

단계 경계에서 지킬 것:

- robots.txt 차단 해제는 색인 복구가 아니다. 차단된 URL이 색인에 남을 수 있고, 해제된 URL이 색인에 들어오지 않을 수 있다.
- 렌더링 검사는 색인 검사에서 콘텐츠가 빠진 이유를 설명한다. 렌더링 검사 자체가 색인 검사는 아니다.
- 관측은 어느 단계에 속하는지와 어떤 도구로 얻었는지를 함께 기록한다.

## E-E-A-T 프레임워크

E-E-A-T는 단일 직접 ranking factor가 아니다. 특히 YMYL 주제에서 trust signals를 식별하는 데 도움이 되는 self-assessment 및 quality framework로 다룬다.

| 축 | 의미 | 신호 |
|----|------|------|
| **Experience** | 주제에 대한 직접 경험 | 원본 사진, 테스트된 예시, case studies, 실제 또는 제품 경험 |
| **Expertise** | 자격과 깊은 주제 지식 | Author bio, credentials, technical accuracy, expert review |
| **Authoritativeness** | 다른 이들의 인정 | Quality citations, reputable mentions, topic cluster consistency |
| **Trustworthiness** | 신뢰성과 투명성 | HTTPS, clear contact, privacy policy, accurate sourcing, no deception |

Trust는 가장 중요한 축이다. 콘텐츠가 모든 E-E-A-T 신호를 동일하게 가질 필요는 없지만 YMYL 주제에는 더 엄격한 증거와 전문성이 필요하다.

## Core Web Vitals

Field data가 있을 때 실제 사용자 전체의 75th percentile에서 Core Web Vitals를 평가한다. Lab tools는 디버깅에 유용하지만 field data보다 낮은 신뢰도로 라벨링해야 한다.

| Metric | Full Name | Good | Needs Improvement | Poor |
|--------|-----------|------|-------------------|------|
| **LCP** | Largest Contentful Paint | ≤ 2.5s | > 2.5s – 4.0s | > 4.0s |
| **INP** | Interaction to Next Paint | ≤ 200ms | > 200ms – 500ms | > 500ms |
| **CLS** | Cumulative Layout Shift | ≤ 0.1 | > 0.1 – 0.25 | > 0.25 |

### LCP 최적화

- Fold 위의 가장 큰 image/text block을 최적화한다.
- Hero assets에는 framework image components 또는 올바른 `<img>` loading priorities를 사용한다.
- 정말 critical한 리소스만 preload한다.
- Server response time(TTFB)과 render-blocking resources를 최소화한다.

### INP 최적화

- Long tasks(> 50ms)를 나눈다.
- Scheduling APIs 또는 framework-specific lazy loading으로 non-critical work를 지연한다.
- Main thread blocking JavaScript와 expensive event handlers를 최소화한다.
- Lighthouse 점수만 보지 말고 interaction-specific profiling을 선호한다.

### CLS 최적화

- Images/videos에 explicit `width`와 `height` 또는 aspect ratio를 설정한다.
- Ads, embeds, banners, dynamic content를 위한 공간을 예약한다.
- Load 후 기존 콘텐츠 위에 콘텐츠를 삽입하지 않는다.
- 적절한 경우 stable font loading과 layout containment를 사용한다.

## 우선순위 모델

이를 보편적인 ranking-factor 순서로 제시하지 않는다. 실무 감사 triage model로 사용한다:

1. **Eligibility** — crawlability, indexability, canonical correctness, snippet eligibility.
2. **People-first usefulness** — intent를 만족하는 original, complete, accurate content.
3. **Trust and safety** — transparent authorship/organization, sourcing, policies, no deceptive behavior.
4. **Search appearance** — titles, descriptions, structured data, images/video metadata.
5. **Page experience** — Core Web Vitals, mobile usability, HTTPS, intrusive interstitial avoidance.
6. **Authority and discovery** — internal links, external mentions/backlinks, relevant communities에서의 promotion.
7. **AEO/GEO readiness** — answer blocks, sourceable claims, entity clarity, AI crawler policy, citation probes.

## Schema Markup Types

고려할 수 있는 일반 Schema.org type이다. Schema.org validity와 Google rich-result eligibility는 별개이므로 missing type을 scoring하기 전에 현재 Google Search Gallery와 type-specific policy를 확인한다. Structured data는 visible page content와 일치하고 가장 구체적인 applicable type을 사용해야 한다.

| Type | 사용할 때 | 주의사항 |
|------|-----------|----------|
| `Article` | Blog posts, news articles, guides | Visible하거나 적절한 author/date/image를 정확히 포함 |
| `Organization` | Company/about pages | name/logo/contact/social profiles를 일관되게 유지 |
| `Person` | Author/team profile pages | 실제 visible people/entities에만 사용 |
| `FAQPage` | 질문당 accepted answer가 하나인 FAQ content | Google FAQ rich result는 종료됐다. 어휘는 유효하고 FAQ 콘텐츠는 사람에게 계속 유용하다 |
| `QAPage` | 하나의 질문에 user-submitted multiple answers가 있는 경우 | Forums 또는 multi-answer Q&A에 FAQPage를 사용하지 않음 |
| `Product` | Ecommerce product pages | Price/availability/reviews가 visible content와 일치해야 함 |
| `Review` | Review content/testimonials | Fake 또는 hidden reviews 금지 |
| `BreadcrumbList` | Navigation breadcrumbs | Visible 또는 logical site hierarchy와 일치 |
| `WebSite` | Site identity와 지원되는 site-level properties | 특정 visual search feature를 보장하지 않음 |
| `LocalBusiness` | Local business pages | Address/hours를 visible content 및 profiles와 일관되게 유지 |
| `HowTo` | 실제로 유용한 semantic step-by-step content | Google HowTo rich result는 종료됐다. 절차형 콘텐츠에 HowTo 마크업을 요구하지 않는다 |

## 구조화 데이터 지원 상태

Google의 rich-result 기능 지원은 Schema.org 어휘와 별개로 바뀐다. 어휘는 유효하고 유용한 채로 남아 있어도 Google 기능은 종료될 수 있으므로, missing type을 점수화하기 전에 현재 상태를 확인한다.

| Type | Status | Notice | Effective | 비고 |
|---|---|---|---|---|
| `FAQPage` | retired | 2026-05-08 | 2026-05-07 | Google FAQ rich result는 더 이상 표시되지 않고 문서는 2026-06-15에 삭제됐다. 어휘와 사람이 읽는 FAQ 콘텐츠는 계속 유용하다 |
| `HowTo` | retired | unconfirmed | unconfirmed | Google HowTo rich result는 종료됐다. 절차형 콘텐츠에 HowTo 마크업을 요구하지 않는다. Google 외 소비자 대응은 별개 문제다 |
| `Product` | supported | — | — | 단일 상품 페이지의 Product snippet. 가격·재고·리뷰가 visible content와 일치해야 한다 |
| `merchant listing` | supported | — | — | Merchant Center 자격이 필요하다. 마크업 유효성만으로 페이지가 자격을 얻지 않는다 |
| `ProductGroup` | supported | — | — | 변형이 한 페이지를 공유할 때 `variesBy`, `hasVariant`, `productGroupID`와 함께 사용한다 |
| `LocalBusiness` | supported | — | — | 주소·영업시간을 visible content 및 profiles와 일관되게 유지한다 |
| `SpecialAnnouncement` | retired | 2025-04-23 | 2025-07-31 | 폐기 공지가 효력일보다 앞선다. 문서는 2025-09-09에 삭제됐다 |
| `ClaimReview` | unverified | — | — | 이번 조사에서 현재 상태를 확정하지 못했다. 지원·종료 어느 쪽으로도 단정하지 않는다 |
| `Book actions` | unverified | — | — | 공지 후 철회됐고 현재 상태를 확정하지 못했다. 지원·종료 어느 쪽으로도 단정하지 않는다 |

커머스 분기: 상품을 판매하지 않는 사이트에는 커머스 마크업 발견사항을 만들지 않는다. 상품을 판매하는 사이트는 페이지 구조와 Merchant Center 자격에 따라 `Product`, `merchant listing`, `ProductGroup` 중 하나를 사용하며, 기본값으로 셋을 모두 쓰지 않는다.

`Notice`는 변경이 공지된 날짜, `Effective`는 효력이 발생한 날짜다. 두 날짜는 다를 수 있고 공지가 효력일 이후에 게시될 수도 있다. `unconfirmed`는 1차 출처로 확인하지 못한 날짜를 뜻한다.

## Keyword And Intent Strategy

- **Intent first**: Content format을 informational, commercial, transactional, navigational intent에 맞춘다.
- **Natural language**: 사용자가 실제로 검색할 terms를 titles, headings, first paragraphs, alt text, links에 사용한다.
- **No stuffing**: Scoring shortcut으로 fixed-density targets를 피한다. Readability와 intent fit이 더 중요하다.
- **Semantic coverage**: Related entities, comparisons, limitations, examples를 자연스럽게 포함한다.

## AI Content Guidelines

- AI-generated content도 helpful, accurate, reviewed, people-first라면 허용될 수 있다.
- AI-assisted drafts에 human review, fact checking, source verification, original examples를 더하는 방식을 선호한다.
- Mass-produced thin pages, unreviewed generated text, unsupported claims, search traffic capture만을 위한 콘텐츠를 피한다.

## 스팸·어뷰즈 정책

스팸 정책은 자격 축이며 문체 지침이 아니다. 위반은 순위를 낮추거나 결과에서 페이지를 제거할 수 있으므로, 각 정책을 의견이 아니라 근거가 필요한 감사 항목으로 다룬다.

| Policy | 다루는 범위 | 감사 질문 |
|---|---|---|
| `scaled content abuse` | 순위 조작을 주목적으로 대량 생성된 비독창적 콘텐츠 | 사용자에게 도움이 아니라 순위를 위해 존재하는 페이지 묶음이 있는지, 각 페이지가 무엇을 더하는지 |
| `expired domain abuse` | 순위 조작을 주목적으로 사들여 재활용한 만료 도메인 | 현재 콘텐츠가 도메인의 이전 소유자로부터 audience를 물려받았는지 |
| `site reputation policy` | 호스트의 기존 ranking signal 때문에 호스트 사이트에 게시된 서드파티 콘텐츠 | 서드파티 콘텐츠가 호스트의 signal 때문인지, 사이트 자체 audience를 위한 것인지 |
| `doorway abuse` | 방문자를 다른 목적지로 보내기만 하는 페이지 | 각 페이지가 스스로 성립하는지, 다른 페이지로 가는 경로일 뿐인지 |
| `thin affiliation` | 설명과 리뷰를 판매처에서 그대로 복사한 제휴 페이지 | 판매처 문구 외에 자체 평가·테스트·비교가 있는지 |
| `scraped content` | 부가 가치 없이 다른 사이트에서 복사한 콘텐츠 | 각 주장이 사이트 자체 작업이나 인용 출처로 추적되는지 |
| `generative AI use` | 그 자체로는 위반이 아님 | 생성형 AI로 만들었는지, 그렇다면 검토·검증·독창적 가치를 더했는지. 자동화·사람 작업·혼합을 같은 기준으로 판정한다 |

지킬 규칙:

- 생성형 AI 사용 여부만으로 위반을 판정하지 않는다. 목적과 사용자 가치, 운영 맥락을 함께 본다.
- 서드파티 콘텐츠 자체가 site reputation 문제는 아니다. 호스트의 기존 ranking signal 때문에 게시하는 것이 문제다.
- 지역 분기가 있다. 2026-08-30부터 site reputation policy는 EEA 안과 밖에서 집행 효과가 다르므로 적용 지역과 확인일을 기록한다.
- 정책 페이지는 날짜 표기 없이 바뀔 수 있으므로 정책을 읽은 날짜를 기록한다.

## Entity And Trust Signals

명확하고 일관된 entity information은 machine readability와 auditability를 높이지만 ranking 또는 AI citation 효과는 deterministic하지 않다.

### 점검

- Organization, product, author, topic names가 페이지 전반에서 일관적인지.
- Author/about/contact pages와 visible expertise signals가 있는지.
- Definitions, comparisons, implementation, risks, examples를 다루는 topic clusters가 있는지.
- JSON-LD `@id`/`@graph` links가 visible content를 정확히 반영하는지.

### 피할 것

- Schema가 AI citations 또는 rich results를 보장한다고 주장하기.
- Invisible, misleading, irrelevant content를 마크업하기.
- Domain authority, entity authority, freshness를 하나의 magic lever로 취급하기.

## Source Ledger

`Notice`는 변경이 공지된 날짜, `Effective`는 효력이 발생한 날짜이며 `—`는 출처가 그런 날짜를 제시하지 않음을 뜻한다. `Accessed`는 이 레퍼런스가 출처를 마지막으로 읽은 날짜, `Observed`는 기록된 상태를 마지막으로 직접 관찰한 날짜다. `Confirmed at`은 행의 날짜를 다시 확인할 수 있는 위치다.

| Source | Notice | Effective | Confirmed at | Accessed | Observed | Supports | Caveat |
|---|---|---|---|---|---|---|---|
| https://developers.google.com/search/docs/essentials | — | — | — | 2026-09-21 | 2026-09-21 | Search eligibility와 crawlable-content 기준선 | Eligibility와 best practice가 indexing/ranking을 보장하지 않음 |
| https://developers.google.com/search/docs/essentials/spam-policies | — | — | — | 2026-09-21 | 2026-09-21 | 정책 절에서 쓰는 스팸·어뷰즈 정의 | 페이지에 개정일 표기가 없다. 정책 본문은 날짜 공지 없이 바뀔 수 있음 |
| https://developers.google.com/search/blog/2026/08/update-site-reputation-policy | 2026-08-28 | 2026-08-30 | https://developers.google.com/search/blog/2026/08/update-site-reputation-policy | 2026-09-21 | 2026-09-21 | site reputation policy의 EEA 분기 | EEA 안과 밖의 집행이 다르다. 공지는 사이트별 결과가 아님 |
| https://developers.google.com/search/updates | — | — | — | 2026-09-21 | 2026-09-21 | 기능 폐기(FAQ, SpecialAnnouncement)의 공지일·효력일 | 로그 항목은 공지를 서술한다. 공지가 효력일 이후에 게시될 수 있음 |
| https://developers.google.com/search/docs/appearance/structured-data/sd-policies | — | — | — | 2026-07-28 | 2026-07-28 | Visible-content parity, specificity, supported formats, no rich-result guarantee | Type-specific eligibility는 변하므로 current feature docs 확인 필요 |
| https://developers.google.com/search/docs/appearance/structured-data/search-gallery | — | — | — | 2026-09-21 | 2026-09-21 | 지원 상태 표의 근거가 되는 현행 rich-result 기능 목록 | Gallery 등재는 특정 사이트의 보장이 아님 |
| https://developers.google.com/search/docs/appearance/structured-data/product-variants | — | — | — | 2026-09-21 | 2026-09-21 | ProductGroup 속성과 merchant listing 자격 | Merchant Center 자격은 마크업 유효성과 별개 |
| https://developers.google.com/search/docs/fundamentals/creating-helpful-content | — | — | — | 2026-09-21 | 2026-09-21 | People-first 콘텐츠 기준선, 선호 단어 수 없음 | 품질 지침은 측정 가능한 pass/fail 규칙이 아님 |
| https://developers.google.com/search/docs/appearance/ai-features | — | — | — | 2026-07-28 | 2026-07-28 | Special AI schema/text-file requirement 부재 | Google AI surface/reporting은 변할 수 있음 |
| https://web.dev/articles/vitals | — | — | — | 2026-09-21 | 2026-09-21 | LCP/INP/CLS thresholds, 75th-percentile field measurement | Lab result는 field data를 대체하지 않음 |

## 측정 도구

| Tool | 목적 | Evidence grade |
|------|------|----------------|
| Google Search Console | Indexing, performance, coverage, Search traffic | `field`/`official` |
| Google Analytics / server logs | Traffic, user behavior, conversions, AI referrers | `field` |
| PageSpeed Insights / CrUX | Core Web Vitals field and lab diagnostics | `field` + `lab` |
| Lighthouse | Performance/accessibility/SEO lab audit | `lab` |
| Rich Results Test / Schema validator | Structured data validation | `tool` |
| Local crawler/static scan | Links, metadata, robots, schema, headings | `lab` |
| AI citation prompt set | AI answers에서 citation/mention visibility | `synthetic` |
| Ahrefs/Semrush/etc. | Backlinks, keyword rankings, competitor research | `tool` |

AEO/GEO measurement KPIs, crawler policy, citation probe guidance는 `references/aeo-geo-guide.md`를 참고한다.

## Sources

> 새 외부 출처는 사용하지 않았다. 내용 확인 2026-09-22. 아래 출처의 마지막 열람일은 위 원장에 기록된 날짜와 같다.

| 주장 | 출처 |
|---|---|
| 검색 노출 자격과 크롤 가능 콘텐츠 기준선 | <https://developers.google.com/search/docs/essentials>, 2026-09-21 확인 |
| 정책 절에서 쓰는 스팸·어뷰즈 정의 | <https://developers.google.com/search/docs/essentials/spam-policies>, 2026-09-21 확인 |
| site reputation policy의 EEA 분기 | <https://developers.google.com/search/blog/2026/08/update-site-reputation-policy>, 2026-09-21 확인 |
| 기능 폐기(FAQ, SpecialAnnouncement)의 공지일·효력일 | <https://developers.google.com/search/updates>, 2026-09-21 확인 |
| Visible-content parity, specificity, 지원 형식, rich result 비보장 | <https://developers.google.com/search/docs/appearance/structured-data/sd-policies>, 2026-07-28 확인 |
| 지원 상태 표의 근거가 되는 현행 rich-result 기능 목록 | <https://developers.google.com/search/docs/appearance/structured-data/search-gallery>, 2026-09-21 확인 |
| ProductGroup 속성과 merchant listing 자격 | <https://developers.google.com/search/docs/appearance/structured-data/product-variants>, 2026-09-21 확인 |
| People-first 콘텐츠 기준선, 선호 단어 수 없음 | <https://developers.google.com/search/docs/fundamentals/creating-helpful-content>, 2026-09-21 확인 |
| Special AI schema/text-file requirement 부재, 색인·snippet 자격이 있는 보조 페이지 | <https://developers.google.com/search/docs/appearance/ai-features>, 2026-07-28 확인 |
| LCP/INP/CLS 임계값과 75백분위 필드 측정 | <https://web.dev/articles/vitals>, 2026-09-21 확인 |
