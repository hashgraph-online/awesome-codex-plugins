# 키워드 리서치

키워드를 제안하거나 인기도, 검색량, 난이도 숫자를 읽기 전에 이 레퍼런스를 읽는다.

## 목차

- 과정
- 지표와 그 한계
- 배치
- 순위 추적
- 변경 주기

## 과정

1. **시드**: 사용자가 쓰는 말로 앱의 핵심 작업, 카테고리 어휘, 브랜드, 소유자 자체 검색 데이터의 용어(가능하면 Apple Ads 검색어 리포트, Play Console 검색어)를 나열한다.
2. **확장**: 동의어, 단수·복수형, 두 단어에서 네 단어 길이의 롱테일 문구, 경쟁사 등록정보 어휘(메타데이터에는 경쟁사 브랜드 이름 금지), 로캘별 표기를 더한다(AsoIndustry-1, AsoIndustry-3, AsoIndustry-13).
3. **관련성으로 먼저 거른다**: 사용자가 그 용어를 검색할 때 이 앱을 원할 경우에만 남긴다. 앱과 맞지 않는 인기 용어는 필드 공간을 낭비하고 전환을 해친다(AsoIndustry-33).
4. **후보 순위화**: 관련성, 수요, 달성 가능성 순으로 정렬한다. 수요와 난이도는 후보끼리 순위를 정할 때만 쓰고 개수처럼 쓰지 않는다(AsoIndustry-29).
5. **배치**: 스토어와 로캘마다 용어를 필드 하나에 배정하고(배치 참고) 센 길이를 기록한다.
6. **측정**: 출시 후 스토어, 국가, 기기별 순위를 추적하고 소유자의 노출 수, 소스 데이터와 비교한다(AsoIndustry-14).

실용적인 후보 풀은 거르기 전 30-50개 용어다(AsoIndustry-12). 이는 벤더 안내이지 규칙이 아니다.

## 지표와 그 한계

| 지표 | 산출 주체 | 사용법 |
|---|---|---|
| Apple Ads 검색 인기도 | Apple. Apple Ads에서는 1-5 상대 막대로 표시하고(AppleGrowth-21), API와 벤더 도구에서는 5-100 척도로 보고한다(AsoIndustry-4, AsoIndustry-6) | App Store의 자사 상대 수요다. 척도와 날짜를 기록한다. Apple이 2025년 10월과 2026년 10월에 임계값을 바꾸고 유사 변형을 묶었으므로 그 날짜를 걸친 값은 비교할 수 없다(AsoIndustry-5, AsoIndustry-42) |
| 벤더 검색량 또는 트래픽 점수 | 각 벤더의 자체 모델 | 한 벤더 안에서 서열 비교만 한다. 절대 검색 횟수로 쓰지 않는다. Apple의 실제 검색량을 받는 벤더는 없다(AsoIndustry-29, AsoIndustry-44) |
| 난이도 또는 경쟁도 | 각 벤더의 자체 공식(예: 상위 앱의 강도) | 한 벤더 안에서만 비교한다. 난이도는 앱 자체의 강도에 상대적이다(AsoIndustry-6, AsoIndustry-7, AsoIndustry-30) |
| Google Play 인기도 | 벤더 추정치. Google은 키워드 검색량을 공개하지 않는다 | Apple에서 나온 값보다 신뢰도가 낮다. 한 벤더는 자체 오차를 공개한다(AsoIndustry-30) |
| 순위 | 한 스토어, 국가, 기기에서 질의에 대한 관측 위치 | 개인화와 시간이 위치를 움직인다. 한 번의 스냅샷은 약한 증거이고 "순위 없음"은 0위가 아니라 데이터 누락이다(AsoIndustry-14, KoreaAeo-35) |

`results.json.keyword_set`의 모든 키워드 행이 인기도나 난이도 값을 가지면 그 `source`를 밝힌다. `assets/runtime/check-results.jq`의 게이트는 출처 없는 인기도 값을 거부한다.

## 배치

### Apple App Store

- 가장 강한 용어는 이름과 부제에, 보조 용어는 키워드 필드에 둔다. 이 세 필드에서 같은 단어를 반복하지 않는다(AppleMeta-16, AsoIndustry-11).
- Apple은 이름, 부제, 키워드 필드의 단어를 조합해 문구를 만들므로 단어 하나로 여러 문구를 덮는 경우가 많다(AppleMeta-33). 벤더가 설명한 내용이며 `tool`로 등급을 매긴다.
- 키워드 필드: 쉼표 뒤 공백 없음, 중복 없음, 세 글자 미만 단어 없음, 바이트로 센다(AppleMeta-2).
- 검색 가능한 로캘을 더하면 용량이 늘어난다(`rules/localization.md` 참고).
- 맞춤 제품 페이지는 테마별 지정 키워드를 가질 수 있다(AppleGrowth-31).

### Google Play

- 가장 강한 용어는 제목과 짧은 설명에 두고, 그다음 전체 설명 앞부분과 문맥 안에서 자연스럽게 쓴다(PlayListing-23).
- 반복은 관찰 항목으로 점검한다. 벤더의 밀도 목표는 `heuristic`이고 키워드 나열은 정책 위반이다(AsoIndustry-31, PlayListing-1).
- 맞춤 스토어 등록정보는 검색 키워드를 타기팅할 수 있다(PlayListing-6).

## 순위 추적

- 스토어, 국가, 기기, 로캘별로 이력을 남겨 추적한다(AsoIndustry-14).
- 노출도를 요약할 때 수요로 순위에 가중치를 주고 어느 벤더의 공식을 썼는지 밝힌다(AsoIndustry-47).
- "순위 없음"은 누락이지 0위가 아니다(KoreaAeo-35).

## 변경 주기

- 메타데이터를 바꾼 뒤에는 판단하기 전과 다음 변경 전에 기다린다. 벤더는 App Store에서 2-3주, Google Play에서 3-4주를 제안한다(AsoIndustry-12). 대기 기간은 `heuristic`으로 기록한다.
- 시즌 어휘는 소유자 콘솔 이력을 먼저 따르고 그다음 서드파티 트렌드 데이터를 본다(AsoIndustry-19).

## Sources

> 확인 2026-11-22.

| 주장 | 출처 |
|---|---|
| 과정, 확장, 후보 풀, 변경 주기 | [sources.md](sources.md)의 AsoIndustry-1, AsoIndustry-3, AsoIndustry-12, AsoIndustry-13, AsoIndustry-19 |
| 지표 산출 주체, 척도 변경, 한계 | AppleGrowth-21, AsoIndustry-4..7, AsoIndustry-29, AsoIndustry-30, AsoIndustry-42, AsoIndustry-44 |
| 배치 | AppleMeta-2, AppleMeta-16, AppleMeta-33, AppleGrowth-31, AsoIndustry-11, AsoIndustry-31, PlayListing-1, PlayListing-6, PlayListing-23 |
| 순위 추적 | AsoIndustry-14, AsoIndustry-47, KoreaAeo-35 |

### Evidence grade

`SECONDARY` - 과정은 실무자 방법이다. 그 안의 스토어 규칙은 `PRIMARY`이며 Apple이나 Google을 인용한다.
