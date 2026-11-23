# Apple App Store 점검

**목적**: Apple App Store가 범위에 들 때 실행할 점검. 한도와 출처는 `references/policy-limits.md`에 있고, 이 파일은 무엇을 점검하고 어떻게 등급을 매기는지 적는다.

## 1. 검색 입력

- Apple은 텍스트 관련성(앱 이름, 부제, 키워드 필드, 기본 카테고리)과 사용자 행동(다운로드, 평점, 리뷰)을 검색 요인으로 밝힌다(AppleMeta-16). 개발자 이름도 검색된다(AppleMeta-2).
- 텍스트 관련성 입력으로는 그 필드만 점수화한다. 설명, 프로모션 텍스트, What's New, 스크린샷 캡션은 전환용 문구다. 그중 하나가 App Store 순위에 영향을 준다는 주장은 기껏해야 `heuristic`이다(AppleMeta-9, AppleMeta-16, AsoIndustry-15..18).
- 키워드를 지정한 맞춤 제품 페이지는 그 키워드의 추가 검색 표면이다(AppleGrowth-31, AppleMeta-29).

## 2. 필드 점검

| 점검 항목 | 실패 시 발견사항 | 증거 등급 |
|---|---|---|
| 이름에 브랜드와 타깃 사용자가 검색하는 설명어를 하나 이상 담는다 | 이름이 브랜드뿐이고 브랜드에 검색 수요가 없으면 `warning` | `heuristic`, 수요 근거를 함께 밝힌다 |
| 이름, 부제, 키워드 필드가 같은 단어를 반복하지 않는다. Apple은 이 필드들의 단어를 조합한다 | 반복 단어마다 `warning`, 낭비하는 바이트나 글자 수를 함께 적는다 | `official` (AppleMeta-16) |
| 키워드 필드: 쉼표로 구분하고 쉼표 뒤에 공백이 없으며, 단수·복수 중복, 이미 있는 앱 이름이나 카테고리 이름, 세 글자 미만 단어가 없다 | 결함마다 `warning` | 필드 규칙은 `official`, 복수형 처리는 `heuristic` (AsoIndustry-11, AppleMeta-33) |
| 키워드 필드 길이는 UTF-8 바이트로 센다 | 제안 문구가 100바이트를 넘으면 `critical` | `official` (AppleMeta-2). `references/policy-limits.md`의 미해결 충돌을 참고한다 |
| 부제는 이름을 반복하지 않고 핵심 혜택이나 사용 사례를 밝힌다 | `info` 또는 `warning` | `heuristic` |
| 설명 첫 줄과 프로모션 텍스트는 가치와 현재 제공 내용을 밝힌다. 프로모션 텍스트는 버전 없이 바꿀 수 있다 | `info` | `heuristic`. 수정 가능성은 `official` (AppleMeta-15) |
| 기본 카테고리가 주 기능과 맞는다 | `warning`. 관련 없는 카테고리는 가이드라인 위험이다 | `official` (AppleMeta-17) |

## 3. 전환 도구

- 맞춤 제품 페이지: 한도와 견줘 운영 중인 페이지 수를 세고, 각 페이지가 서로 다른 대상이나 키워드 주제를 가지는지, 지정 키워드가 승인됐는지, 광고나 링크가 그 페이지를 가리키는지 확인한다(AppleGrowth-01, AppleGrowth-03).
- Product Page Optimization: 최근 90일 안에 테스트가 돌았는지, 무엇을 테스트했는지, 결과 상태, 테스트 아이콘이 바이너리에 있는지 확인한다. App Store Connect가 "Performing Better"로 표시할 때만 그 결과를 승자로 본다(AppleGrowth-02, AppleGrowth-05).
- In-App Events: 이벤트 주기, 배지 유형, 카드 문구 한도, 이벤트가 앱의 실제 콘텐츠 순간을 다루는지 확인한다(AppleGrowth-06, AppleGrowth-07, AppleGrowth-09).
- 프로모션 인앱 구매와 구독 제안: 구매를 프로모션하고 검색 사용자를 위해 이름을 붙였는지 확인한다(AppleGrowth-10, AppleGrowth-29, AppleGrowth-30).

## 4. 평점과 리뷰

- 범위 안 스토어프런트마다 요약 평점과 개수를 읽는다. 평점은 지역별이다(AppleMeta-21).
- 평점 요청: 시스템 API를 쓰는지, 긍정 과업을 마친 뒤 실행하는지, 실행과 온보딩 중에는 절대 띄우지 않는지, "Do you like the app?" 필터 뒤에 숨기지 않는지 확인한다. 시스템은 연 3회 표시로 제한한다(AppleMeta-20, AppleMeta-25).
- 평점 초기화: 낮은 평점의 원인을 고치는 릴리스에만 권하고, 되돌릴 수 없고 전역으로 적용된다는 점을 밝힌다(AppleMeta-23).
- 답변: 최근 저평점 리뷰의 답변 범위와 답변이 Apple의 리뷰 1건당 답변 1건 규칙에 맞는지 확인한다(AppleMeta-24).
- AI 리뷰 요약과 앱 태그: 범위 안 스토어프런트에 적용되는지 적는다. 확인일 기준 한국에는 적용되지 않는다(AppleMeta-21, AppleMeta-30).

## 5. 메타데이터 정책 위험

App Review Guidelines 2.3(정확한 메타데이터)과 충돌하는 요소를 가이드라인 번호와 함께 표시한다(AppleMeta-18).

- 이름이나 부제의 키워드 반복, 또는 모든 필드의 상표, 경쟁사, 유명인 용어(2.3.7)
- 앱 사용 모습을 보여 주지 않는 스크린샷(2.3.3)이나 앱에서 캡처하지 않은 콘텐츠를 담은 미리보기
- 크리에이티브 자산의 가격, 할인, URL, 검증할 수 없는 주장(AppleMeta-40)
- 가이드라인이 금지하는 방식으로 다른 모바일 플랫폼이나 Apple 제품을 언급하는 문구

이것은 발견 가능성과 거절 위험을 표시하는 것이다. 제출 준비 상태의 통과·실패 판정은 이 스킬의 산출물이 아니다.

## 6. 측정

- App Analytics: 노출, 제품 페이지 조회수, 전환율, 최초 다운로드, 재다운로드, 유입 유형(App Store Search, App Store Browse, App Referrer, Web Referrer). 정의는 `references/metrics.md`에서 읽는다.
- 맞춤 페이지, 테스트, 이벤트 지표는 최초 다운로드가 5건을 넘은 뒤에만 나타난다(AppleGrowth-03, AppleGrowth-05).
- Apple Ads 검색어 보고서는 키워드 선택의 자사 수요 근거다. 유료 트래픽을 측정하므로 소유자가 내보냈을 때만 `console`로 등급을 매긴다.

## Sources

> 확인 2026-11-22.

| 주장 | 출처 |
|---|---|
| 검색 요인, 필드 규칙, 카테고리, 평점, 리뷰 요청, 정책 섹션 | AppleMeta-2, AppleMeta-9, AppleMeta-15..18, AppleMeta-20..25, AppleMeta-29, AppleMeta-30, AppleMeta-33, AppleMeta-40 in [../references/sources.md](../references/sources.md) |
| 맞춤 페이지, 테스트, 이벤트, 프로모션 구매, 제안 | AppleGrowth-01..10, AppleGrowth-29..31 |
| 캡션 색인 논쟁, 키워드 필드 전술 | AsoIndustry-11, AsoIndustry-15..18 |

### Evidence grade

Apple 페이지에서 가져온 규칙은 `PRIMARY`이고, 벤더에서 도출한 점검은 표에서 `heuristic`으로 표시한다.
