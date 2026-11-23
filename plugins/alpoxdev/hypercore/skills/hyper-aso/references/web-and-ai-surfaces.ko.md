# 웹과 AI 표면

웹-앱 연결이나 AI 어시스턴트 추천이 범위에 들어올 때 이 레퍼런스를 읽는다.

## 1. 웹-앱 연결

| 항목 | 확인할 것 | 출처 |
|---|---|---|
| Apple Universal Links | `https://<domain>/.well-known/apple-app-site-association`가 파일 확장자 없이 제공되고, 앱에 대해 `applinks`를 선언하며, 사용하는 모든 서브도메인에 존재한다. 앱의 associated-domains 엔타이틀먼트에 해당 도메인이 나열된다 | AppleGrowth-24, AppleGrowth-25 |
| Smart App Banner | 앱을 홍보할 페이지에 `<meta name="apple-itunes-app" content="app-id=...">`가 있다. `app-argument`는 선택이다 | AppleGrowth-23 |
| Android App Links | `https://<domain>/.well-known/assetlinks.json`에 `delegate_permission/common.handle_all_urls` 관계와 서명 인증서 지문이 있다. Play 앱 서명을 쓰면 Console에 표시되는 지문을 쓴다 | PlayQuality-13, PlayQuality-14 |
| 맞춤 페이지와 등록정보 링크 | Apple 맞춤 제품 페이지 URL과 딥링크(iOS/iPadOS 18 이상), Play 맞춤 스토어 등록정보 URL, 스토어 배지의 캠페인 파라미터 | AppleGrowth-01, PlayListing-6 |
| 종료된 링크 서비스 | Firebase Dynamic Links는 2025-08-25에 종료되어 링크가 404를 반환한다. Google Play Instant는 2025년 12월부터 앱 접수를 중단했다. Firebase App Indexing 문서는 더 이상 제공되지 않는다 | PlayQuality-15, PlayQuality-21, PlayQuality-24 |

각 파일을 가져와 HTTP 상태, 콘텐츠 유형, 앱 식별자 일치 여부를 기록한다. 응답하는 링크 파일은 구성의 증거이지 설치나 순위 영향의 증거가 아니다. 웹사이트 자체의 검색 노출은 이 스킬의 산출물 범위 밖이다.

## 2. AI 추천 표면

| 표면 | 2026-11-22 기준 상태 | 출처 |
|---|---|---|
| Apple App Store 앱 태그 | 메타데이터, AI, 큐레이션으로 생성한다. 미국 스토어프런트만 지원한다. 소유자가 태그를 해제할 수 있다 | AppleMeta-30, KoreaAeo-19 |
| Apple 리뷰 요약 | LLM이 작성하며 iOS 18.4 이상이다. 미국과 추가 영어 스토어프런트 8곳에서 영어 요약을 제공한다 | AppleMeta-21, KoreaAeo-21 |
| Apple Intelligence 동작 | 앱은 선언한 App Intents 스키마로 도달 가능하다. 등록정보 메타데이터와는 별개 축이다 | KoreaAeo-23 |
| Google Play Ask Play와 Gemini | I/O 2026에서 발표한 대화형 검색과 앱 발견이다. Gemini는 키워드 제안에서 맞춤 스토어 등록정보 초안을 작성할 수 있다 | KoreaAeo-24 |
| ChatGPT 앱 디렉터리 | 메타데이터와 테스트 안내를 담아 앱을 제출한다. OpenAI 메타데이터 가이드는 "Use this when..." 설명과 골든 프롬프트 평가를 권장한다 | KoreaAeo-25..27 |

여기서 따라오는 것:

- 실제 사용 사례를 평이한 말로 밝힌 등록정보 메타데이터는 스토어 검색, AI 태그, 어시스턴트 답변에 동시에 기여한다. 따로 존재하는 마법의 필드는 없다. 스토어가 문서화하지 않은 AI 표면 권장사항은 `heuristic`으로 등급을 매긴다.
- 리뷰 텍스트는 요약의 입력이 된다. 평점 요청과 답변 품질도 그곳에서 중요하다.

## 3. AI 어시스턴트 프로브

사용자가 요청할 때만 실행하고 `synthetic`으로 기록한다.

- 로캘별로 고정한 열린 프롬프트 집합("X에 가장 좋은 앱"), 엔진, 모델 또는 표면, 국가, 날짜, 표본 크기
- 앱이 언급되는지, 그 순서, 함께 언급된 대안, 인용된 출처
- 한 번의 실행은 노이즈이다. 날짜가 붙은 반복 실행의 추세만 보고한다(KoreaAeo-29). 프로브 결과는 순위나 설치 주장이 아니며, 연구에 따르면 LLM 앱 추천은 스토어 지표와 어긋날 수 있다(KoreaAeo-30).

## Sources

> 확인 2026-11-22.

| 주장 | 출처 |
|---|---|
| 링크 파일, 배너, 맞춤 링크, 종료된 서비스 | [sources.md](sources.md)의 AppleGrowth-01, AppleGrowth-23..25, PlayListing-6, PlayQuality-13..15, PlayQuality-21, PlayQuality-24 |
| AI 표면 | AppleMeta-21, AppleMeta-30, KoreaAeo-19, KoreaAeo-21, KoreaAeo-23..27 |
| 프로브 방법과 한계 | KoreaAeo-29, KoreaAeo-30 |

### Evidence grade

링크 규격과 표면 제공 여부는 `PRIMARY`다. 프로브 방법은 실무자·연구 안내인 `SECONDARY`다.
