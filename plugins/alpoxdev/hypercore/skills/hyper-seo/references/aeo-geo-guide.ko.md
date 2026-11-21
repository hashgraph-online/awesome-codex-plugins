# AEO/GEO/LLMO 전략 가이드

**목적**: AEO/GEO 단계에서 사용하는 AI 검색 최적화 레퍼런스.
**최종 확인**: 2026-11-03, Google Search Central(AI 기능, 생성형 AI 최적화 가이드, 문서 업데이트 기록), OpenAI·Anthropic·Perplexity 크롤러 문서, Bing Webmaster 블로그, arXiv GEO·인용 연구, llms.txt 제안과 요청 측정 연구, Search Console 생성 AI 포함 제어·성과 보고서 문서 기준.

## 목차

- 증거 규율
- 공식 주의사항
- 용어
- SEO vs AEO vs GEO
- AEO 전략
- GEO 전략
- 플랫폼 정책 매트릭스
- Search Console 생성 AI 포함 제어(`official`)
- 생성 AI 성과 보고서(`official`)
- 봇 목적과 관측 접근의 구분(`official` + `field`)
- llms.txt
- 측정 KPI
- 실무 최적화 순서
- Source Ledger

## 증거 규율

모든 AEO/GEO 권장사항에 증거 계층을 표시한다:

| 계층 | 의미 | 예시 |
|------|------|------|
| `official` | 플랫폼/벤더 문서 또는 정책 | Google AI 기능 가이드, OpenAI 크롤러 문서 |
| `field` | Search Console, 분석, 서버 로그, 검증된 AI 인용 같은 실제 사용자/검색 데이터 | Search Console 성과, AI referral 로그 |
| `tool` | 결정적 도구 출력 | Rich Results Test, PageSpeed Insights, schema validator |
| `lab` | 통제되었지만 시뮬레이션된 측정 | Lighthouse, 로컬 크롤러, 정적 렌더 체크 |
| `synthetic` | AI 엔진에 대한 프롬프트/인용 probe | 반복 ChatGPT/Perplexity/Gemini 인용 프롬프트 세트 |
| `heuristic` | 모범 사례 추론 또는 업계 관찰 | 40-80단어 answer block, 표/목록 추출 패턴 |

휴리스틱 또는 synthetic 발견사항을 보장된 랭킹/인용 요인처럼 제시하지 않는다. 심각도와 별도로 신뢰도(`high`, `medium`, `low`)를 기록한다.

## 공식 주의사항

- Google은 AI Overviews와 AI Mode가 Search와 동일한 기본 SEO 관행을 사용한다고 설명한다. 포함을 위한 추가 기술 요구사항, 특별한 schema.org 타입 또는 특별한 schema.org 마크업, AI 텍스트 파일은 없다. 생성형 AI 최적화 가이드는 생성형 AI 검색 최적화가 "is optimizing for the search experience, and thus still SEO"라고 밝히고, 콘텐츠 "chunking", `llms.txt`, 진정성 없는 언급 같은 전술은 무시해도 된다고 한다.
- Google AI 기능에서 지원 링크로 표시되려면 페이지가 여전히 색인 가능하고 snippet 대상이어야 하며, 속성이 Search Console 생성 AI 설정에 포함되어 있어야 한다.
- `nosnippet`과 `max-snippet`은 Google AI Overviews와 AI Mode가 직접 입력으로 쓸 수 있는 페이지 내용의 양도 제한한다.
- Google 스팸 정책은 생성형 AI 응답을 조작하려는 시도에도 적용된다(2026-05-15 명시).
- OpenAI, Anthropic, Perplexity는 각각 검색·인용용 크롤러, 학습용 크롤러, 사용자 요청 fetcher를 분리한다. 학습용 크롤러를 막아도 그 업체의 답변에서 빠지지 않고, 검색용 크롤러를 막으면 빠진다. 토큰마다 독립적으로 감사한다.
- `llms.txt`는 informal proposal이자 optional machine-readable content map이며, W3C/IETF standard, ranking factor, 주요 provider의 guaranteed fetch contract가 아니다. Google은 Search가 이 파일을 무시한다고 밝혔고, 2026년 로그 연구에서는 공개된 파일의 97%가 요청을 한 번도 받지 않았다.

## 용어

| 용어 | 전체 이름 | 정의 |
|------|-----------|------|
| **AEO** | Answer Engine Optimization | 보이는 페이지 콘텐츠를 직접 답변으로 추출하기 쉽게 만드는 것 |
| **GEO** | Generative Engine Optimization | AI 생성 답변이 출처를 인용, 언급, 근거로 삼을 가능성을 높이는 것 |
| **LLMO** | Large Language Model Optimization | LLM과 검색 시스템이 콘텐츠를 정확히 파싱, 이해, 재사용하기 쉽게 만드는 것 |
| **AIO** | AI Optimization | 포괄 용어. AEO/GEO가 더 정확할 때는 사용을 피한다 |

## SEO vs AEO vs GEO

| 기준 | SEO | AEO | GEO |
|------|-----|-----|-----|
| **목표** | 크롤링 가능성, 색인 가능성, 랭킹, 검색 노출, CTR | 직접 답변/snippet/음성 스타일 추출 | AI 답변 인용, 브랜드 언급, 출처 선택 |
| **최선의 증거** | Search Console, crawl/index 상태, field CWV, structured data 검증 | snippet controls, 보이는 Q&A/answer blocks, FAQ/QAPage 유효성 | query/prompt probes, 인용 빈도, 공식 crawler 접근, 출처 다양성 |
| **위험** | 랭킹/색인 보장은 없음 | Google FAQ rich result는 2026-05-07부터 표시되지 않음 | 블랙박스 시스템은 달라지므로 결과에 신뢰도 표시가 필요함 |

## AEO 전략

### 직접 답변 블록(`heuristic`)

- 질문형 쿼리를 목표로 하는 섹션 상단 근처에 간결한 답변을 둔다.
- 자연스러울 때 질문과 일치하는 H2/H3 제목을 사용한다.
- 보이는 텍스트, 짧은 단락, 목록, 비교표, 정의/절차 블록을 선호한다.
- 고정 답변 길이 규칙은 휴리스틱으로 취급한다. 40-80단어의 직접 답변은 유용한 작업 범위지만 플랫폼 보장은 아니다.

### FAQ 및 Q&A(`official` + `heuristic`)

- 페이지가 실제로 공통 질문에 답할 때 보이는 FAQ 콘텐츠를 사용한다.
- Google FAQ rich result는 2026-05-07부터 Google 검색에 표시되지 않는다. FAQ 콘텐츠는 사용자와 답변 추출에 도움이 될 수 있지만 Google FAQ rich result를 약속하지 않는다.
- 사용자가 하나의 질문에 여러 답변을 제출할 수 있으면 `FAQPage` 대신 `QAPage`를 사용한다.
- 구조화 데이터는 보이는 콘텐츠와 일치해야 하며 숨겨졌거나 무관하거나 오해를 부르는 정보를 마크업하지 않아야 한다.

## GEO 전략

GEO는 experimental하다. 2023 GEO paper의 gain은 해당 benchmark/setup에만 해당하므로 “up to 40%” 결과를 live engine이나 client site에 일반화하지 않는다. 이후 증거는 대부분의 페이지 단위 전술에 반대 방향을 가리킨다. 2025년 벤치마크에서는 대화형 SEO 기법 대부분이 효과가 없거나 해로웠고 전통 SEO는 여전히 효과가 있었다. 2026년 ChatGPT 인용 468,037건 연구에서는 엔진 자체 검색이 사이트를 가져왔는지가 인용 변동의 약 32%를, 페이지 속성은 2.8%를 설명했고, FAQ 블록과 구조화 데이터는 같은 사이트 안 비교에서 견고한 효과가 없었다. Field evidence 또는 repeatable citation probe를 우선하고 나머지는 heuristic으로 표시한다.

### GEO CORE 프레임워크(`heuristic`)
이는 local audit mnemonic이며 official platform framework나 validated ranking model이 아니다.

| 차원 | 점검 항목 | 증거 예시 |
|------|-----------|-----------|
| Context | 완전한 배경, 정의, 관련 개념 | 주제 커버리지 맵, query fan-out gap |
| Organization | 추출 가능한 계층, 표/목록, 짧은 섹션 | H2/H3 스캔, answer block detector |
| Reliability | 출처, 날짜, 작성자/사이트 신뢰, 사실 검증 가능성 | 인용, 작성자 bio, organization schema, 외부 참고자료 |
| Exclusivity | 원본 연구, 독점 데이터, 고유 사례 | 1자 벤치마크, 사례 연구, 원본 스크린샷/데이터 |

### 인용 가능한 콘텐츠(`synthetic`/`heuristic`, probe 전까지)

- 주변 맥락 없이도 인용할 수 있는 짧고 독립적인 문장을 쓴다.
- 사실 주장에는 날짜, 출처명, 링크를 추가한다.
- 원본 데이터, 비교, 벤치마크 표, 명확히 범위가 정해진 정의를 선호한다.
- AI 답변 조작만을 목적으로 페이지를 만들지 않는다. 사람에게 유용한 콘텐츠를 기본 목표로 유지한다.

### Query fan-out simulator

Coverage experiment가 유용하면 아래 category에서 proportionate subquery set을 생성한다. `10–30`은 broad topic의 optional working range이며 required platform behavior가 아니다:

- 정의와 입문 질문
- 비교와 대안
- 가격, 위험, 제한사항, 구현 질문
- 엔터티/브랜드/제품 질문
- 관련성이 있을 때 지역, 산업, YMYL 변형

미커버 하위 주제를 `results.json.query_fanout`에 기록하고 우선순위 콘텐츠 권장사항으로 전환한다.

### AI citation probe

런타임과 사용자 권한이 허용하면 AI 검색 엔진 전반에서 안정적인 프롬프트 세트를 실행하고 다음을 기록한다:

- 엔진, 날짜, 지역/언어, 프롬프트 텍스트, 표본 크기
- 인용 URL, 브랜드 언급, sentiment, 경쟁사 share of voice
- 반복 실행 변동성과 신뢰도. 인용은 매일 크게 바뀐다(2026년 연구에서 다음날 50-83%가 사라지고 약 75%가 20일 안에 돌아옴). 그러므로 한 번의 관찰이 아니라 고정 기간의 인용 빈도(예: 7-30일 중 인용된 날의 비율)로 보고한다.

Probe를 사용할 수 없으면 신호가 있는 것처럼 꾸미지 말고 prompt pack을 `not-run`으로 저장한다. Google 순위로 ChatGPT 인용을 추정하지 않는다. 겹치는 부분이 일부뿐이고 엔진의 검색 방식이 다르다.

## 플랫폼 정책 매트릭스

| 플랫폼/봇 | 주요 목적 | 최적화 의미 |
|-----------|-----------|-------------|
| Googlebot | Google 크롤링/색인/검색 snippet | 의도적으로 제외하지 않는 한 중요한 색인 가능 페이지와 리소스를 허용해야 함 |
| Google-Extended | 일반 Search 크롤링 외 Google AI 제품/학습 제어 | Search visibility 결정과 분리 |
| OAI-SearchBot | ChatGPT Search 포함 | ChatGPT Search visibility를 원하면 허용 |
| GPTBot | OpenAI 모델 학습 | OAI-SearchBot과 독립적으로 허용 또는 차단 가능 |
| ChatGPT-User | 사용자 트리거 fetch | 일반 자동 search crawler가 아니고 robots.txt가 적용되지 않을 수 있으므로 별도 문서화 |
| Claude-SearchBot / ClaudeBot / Claude-User | Anthropic 검색 색인 / 모델 학습 / 사용자 트리거 fetch | Claude 검색 노출을 원하면 Claude-SearchBot을 허용하고, ClaudeBot은 별도의 학습 결정으로 다룸 |
| PerplexityBot / Perplexity-User | Perplexity 검색 결과(모델 학습 아님) / 사용자 트리거 fetch | Perplexity 노출을 원하면 PerplexityBot을 허용함. Perplexity-User는 대체로 robots.txt를 따르지 않음 |
| Applebot-Extended / Meta-ExternalAgent / CCBot | 학습 용도 제어(Applebot-Extended는 크롤하지 않는 용도 토큰) | 학습 결정임. Meta AI 인용용 크롤러는 별도의 Meta-WebIndexer |
| CDN·WAF 봇 규칙 | 엣지 단계의 허용, 차단, 과금 결정 | AI 크롤러를 기본 차단하는 CDN 설정은 robots.txt 의도를 무력화할 수 있으므로 엣지를 따로 확인 |

## Search Console 생성 AI 포함 제어(`official`)

Google은 생성 AI 포함 여부를 속성별 설정으로 다룬다. 순위 신호가 아니다.

| 항목 | 기록할 내용 | 중요한 이유 |
|------|-------------|-------------|
| 위치 | 속성의 설정 > Search 생성 AI | 포함 여부를 정하는 자리는 여기이고 robots.txt가 아니다 |
| 상태 | 포함, 제외, 상위 속성에서 상속 | 관측한 상태와 그것이 로컬 설정인지 상속인지 함께 기록한다 |
| 대상 | AI Overviews, AI Mode, Discover | 한 속성이 한 surface에는 포함되고 다른 surface에서는 제외될 수 있다 |
| 기본값 | 누군가 제외하지 않았다면 포함 또는 상속 | 명시적 선택이 없다는 사실은 제외의 근거가 아니다 |
| 분리 | AI 제품·학습 용도를 다루는 `Google-Extended`와 별개 | 학습 차단은 포함 결정이 아니고 포함은 학습 허용이 아니다 |
| 순위 | 일반 Search의 순위·포함 신호가 아님 | SEO 지렛대처럼 제시하지 않는다 |

정책과 실제 설정은 별개 항목으로 감사한다. 속성별 접근 조건 때문에 설정을 읽지 못할 수 있으므로 값이 없으면 `unknown`이고, 포함이 꺼졌다는 발견이 아니다.

## 생성 AI 성과 보고서(`official`)

Search Console 생성 AI 성과 보고서가 보고하는 것은 노출 수이고 인용이 아니다.

| 항목 | 기록할 내용 | 중요한 이유 |
|------|-------------|-------------|
| 차원 | 페이지, 국가, 날짜, 기기 | 노출은 어느 차원으로 잘랐는지와 함께라야 해석된다 |
| 날짜 처리 | 날짜는 Pacific Time 기준 | 추세를 판단하기 전에 같은 달력 기준으로 맞춘다 |
| 제공 범위 | 2026-08-31까지 전 세계 배포 완료 | 그 이전의 부재는 배포 시점의 산물이고 성과 신호가 아니다 |
| 집계 | 일반 웹 검색 데이터와 합치지 않는다 | 별도 surface이고 의미도 별도다 |
| 수집 | 2026-09-21 기준 전용 API 미문서화 | 자동 수집은 `unknown`이며 문서화되지 않은 endpoint를 스크립트로 두드리지 않는다 |
| 내보내기 주의 | 내보낸 `~`와 `-` 값이 `0`으로 변환됨 | 내보낸 0은 실측 0이 아니다 |
| 의미 | 노출 가시성만이며 인용을 측정하지 않음 | 노출을 인용 근거로 보고하지 않는다 |

## 봇 목적과 관측 접근의 구분(`official` + `field`)

네 채널을 분리해 둔다. 각 채널이 답하는 질문이 다르기 때문이다.

| 채널 | 근거 등급 | 답하는 질문 |
|------|-----------|-------------|
| 공개 정책 | `official` | 벤더가 그 봇의 용도를 무엇이라 말하는가 |
| 크롤 설정 | `tool` | 사이트가 robots.txt, meta, header에서 현재 무엇을 허용하는가 |
| 실제 요청 | `field` | 실제로 origin에 도달한 것은 무엇인가 |
| 관측 인용 | `synthetic` | 답변이 그 출처를 인용했는가 |

- robots 허용은 크롤의 증거가 아니고, 크롤은 인용의 증거가 아니다.
- `OAI-SearchBot`, `GPTBot`, `ChatGPT-User`는 목적이 다르다. `ChatGPT-User`는 자동 크롤러가 아니므로 이 봇의 요청 부재는 결함이 아니다.
- `OAI-AdsBot`은 search visibility 조사에서 제외한다.
- 타깃이 관련 서비스에 실제로 의존할 때만 이 봇을 점검하고, 아니면 `unknown`으로 남긴다.

## llms.txt

`llms.txt`를 선택적이고 저위험인 콘텐츠 맵으로 사용한다:

```text
# llms.txt
> Site: example.com
> Description: One-line site description

## Core pages
- /about: Company overview
- /docs: Technical documentation
- /blog/key-topic: Best overview of the topic
```

규칙:

- 누락된 `llms.txt`를 기본적으로 critical로 표시하지 않고, 존재 여부를 랭킹이나 인용 요인으로 점수화하지 않는다.
- Maintained content map이 코딩 에이전트에 명확한 user/retrieval value를 줄 때만 docs site, developer tool, API reference, content-heavy product에서 고려한다.
- canonical URL 및 sitemap 우선순위와 일치시킨다.
- 효과를 주장하기 전에 서버 로그를 확인한다. 공개된 파일 대부분은 한 번도 요청되지 않는다.

## 측정 KPI

| KPI | 설명 | 선호 증거 |
|-----|------|-----------|
| AI Citation Frequency | 대상 URL이 AI 답변에 인용되는 빈도 | Synthetic probes 또는 AI visibility tools |
| Brand Mention Rate | 브랜드/엔터티가 언급되는 빈도 | Synthetic probes, AI referrals, third-party tools |
| Share of Voice | 경쟁사 대비 인용/언급 점유율 | 경쟁사를 포함한 반복 프롬프트 세트 |
| AI Overview Inclusion | Google AI 기능이 사이트 링크를 포함하는지 여부 | Search Console 생성 AI 성과 보고서와 수동 SERP 증거 |
| Bing AI Citations | Copilot과 Bing AI 답변의 인용 수, 인용된 페이지, grounding 질의 | Bing Webmaster Tools AI Performance와 Citation Share(preview) |
| Citation Sentiment | 긍정/중립/부정 프레이밍 | 수동 또는 도구 보조 검토 |
| AI-referred Conversion | AI/search referrer에서 온 전환 | AI assistant용 분석 맞춤 채널과 서버 로그. AI 앱 유입은 direct로 잡히는 경우가 많음 |

## 실무 최적화 순서

1. 색인 가능성, 크롤링 가능성, canonical 정확성, snippet eligibility를 보장한다.
2. 보이는 콘텐츠 품질, 신뢰 신호, 구조화 데이터 일치성을 검증한다.
3. 사람에게 유용한 곳에 answer blocks와 Q&A 콘텐츠를 추가한다.
4. 출처, 원본 데이터, 명확한 엔터티를 갖춘 인용 가능한 섹션을 만든다.
5. OAI-SearchBot·GPTBot, Claude-SearchBot·ClaudeBot처럼 검색용과 학습용을 나눠 플랫폼 crawler 정책을 감사하고, CDN·WAF 층도 확인한다.
6. 콘텐츠 맵을 위해 선택적으로 `llms.txt`를 추가한다.
7. 접근 권한이 허용되면 query fan-out과 citation probes를 실행한 뒤 `score_history`와 `best_run`으로 반복 개선한다.

## Source Ledger

| Source | Accessed | Supports | Caveat |
|---|---|---|---|
| https://developers.google.com/search/docs/appearance/ai-features | 2026-07-28 | AI features의 ordinary SEO requirements, snippet eligibility, query fan-out, controls | Inclusion, traffic, citation guarantee 없음 |
| https://developers.openai.com/api/docs/bots | 2026-07-28 | OAI-SearchBot/GPTBot/ChatGPT-User purpose separation | Bot string과 policy는 변할 수 있음 |
| https://llmstxt.org/ | 2026-07-28 | llms.txt proposal의 format과 stated intent | Standards-body/ranking contract가 아닌 proposal |
| https://arxiv.org/abs/2311.09735 | 2026-07-28 | GEO research의 origin과 benchmark scope | 2023 benchmark result는 live-engine guarantee가 아님 |
| https://support.google.com/webmasters/answer/16908024 | 2026-09-21 | Search Console 생성 AI 포함 제어와 속성별 상태 | 설정 감사는 순위·트래픽 보장이 아니고 읽지 못한 설정은 `unknown`으로 남김 |
| https://support.google.com/webmasters/answer/16984139 | 2026-09-21 | 생성 AI 성과 보고서의 차원, Pacific Time 날짜, 내보내기 주의 | 노출 수는 인용 측정이 아니고 내보낸 `0`은 미설정 값일 수 있음 |
| https://developers.google.com/search/docs/fundamentals/ai-optimization-guide | 2026-11-03 | 생성형 AI 최적화는 여전히 SEO, chunking과 llms.txt는 무시 가능, 포함 설정이 전제 | Google surface에만 해당 |
| https://developers.google.com/search/updates | 2026-11-03 | 스팸 정책이 생성형 AI 응답에 적용됨(2026-05-15) | 변경 기록 문구가 짧음 |
| https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler | 2026-11-03 | ClaudeBot, Claude-SearchBot, Claude-User의 목적 | Bot string과 policy는 변할 수 있음 |
| https://docs.perplexity.ai/guides/bots | 2026-11-03 | PerplexityBot은 모델 학습에 쓰이지 않음, Perplexity-User는 대체로 robots.txt를 따르지 않음 | 업체 진술 |
| https://blogs.bing.com/webmaster/2026/2/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview/ | 2026-11-03 | Bing AI Performance 인용 보고서 | Public preview |
| https://arxiv.org/abs/2506.11097 | 2026-11-03 | 대화형 SEO 기법 대부분은 효과가 없고 전통 SEO는 효과가 있음 | 벤치마크 환경 |
| https://arxiv.org/abs/2610.15033 | 2026-11-03 | ChatGPT 인용 변동의 약 32%는 검색 노출, 2.8%는 페이지 속성이 설명 | 프리프린트, 두 시장 |
| https://ahrefs.com/blog/how-stable-are-ai-citations/ | 2026-11-03 | 다음날 인용의 50-83%가 사라지고 약 75%가 20일 안에 돌아옴 | 업체 연구 |
| https://ahrefs.com/blog/llmstxt-study/ | 2026-11-03 | 2026-05에 공개된 llms.txt 파일의 97%가 요청을 받지 않음 | 업체 연구 |

## Sources

> 내용 확인 2026-11-03. 아래 출처의 마지막 열람일은 위 원장에 기록된 날짜와 같다.

| 주장 | 출처 |
|---|---|
| AI features의 ordinary SEO 요구사항, snippet 자격, query fan-out, 크롤 제어 | <https://developers.google.com/search/docs/appearance/ai-features>, 2026-07-28 확인 |
| OpenAI 크롤러 목적 구분(OAI-SearchBot, GPTBot, ChatGPT-User) | <https://developers.openai.com/api/docs/bots>, 2026-07-28 확인 |
| llms.txt 제안의 형식과 표명된 의도 | <https://llmstxt.org/>, 2026-07-28 확인 |
| GEO CORE 프레임워크가 요약하는 GEO 연구의 출처와 벤치마크 범위 | <https://arxiv.org/abs/2311.09735>, 2026-07-28 확인 |
| Search Console 생성 AI 포함 제어와 속성별 상태 | <https://support.google.com/webmasters/answer/16908024>, 2026-09-21 확인 |
| 생성 AI 성과 보고서의 차원, Pacific Time 날짜, 내보내기 주의 | <https://support.google.com/webmasters/answer/16984139>, 2026-09-21 확인 |
| 생성형 AI 최적화 입장, 무시해도 되는 전술, 포함 전제 조건 | <https://developers.google.com/search/docs/fundamentals/ai-optimization-guide>, 2026-11-03 확인 |
| 생성형 AI 응답에 적용되는 스팸 정책 | <https://developers.google.com/search/updates>, 2026-11-03 확인 |
| Anthropic·Perplexity 크롤러 목적 구분 | <https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler>, <https://docs.perplexity.ai/guides/bots>, 2026-11-03 확인 |
| Bing AI 인용 보고서 | <https://blogs.bing.com/webmaster/2026/2/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview/>, 2026-11-03 확인 |
| 2023 논문 이후의 GEO·인용 증거 | <https://arxiv.org/abs/2506.11097>, <https://arxiv.org/abs/2610.15033>, 2026-11-03 확인 |
| 인용 변동성과 llms.txt 요청 비율 | <https://ahrefs.com/blog/how-stable-are-ai-citations/>, <https://ahrefs.com/blog/llmstxt-study/>, 2026-11-03 확인 |
