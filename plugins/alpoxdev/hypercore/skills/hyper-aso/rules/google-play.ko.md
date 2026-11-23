# Google Play 점검

**목적**: Google Play가 범위에 들 때 실행할 점검. 한도와 출처는 `references/policy-limits.md`에 있고, 이 파일은 무엇을 점검하고 어떻게 등급을 매기는지 적는다.

## 1. 검색 입력과 순위 신호

- Google은 사용자 관련성, 앱 경험 품질, 편집 가치, 광고, Play 사용자 경험을 순위 요인으로 밝히며, 제목과 설명, 카테고리를 검색 의도 매칭에 쓴다고 밝힌다(PlayListing-23, PlayQuality-9).
- Play에는 숨은 키워드 필드가 없다. 제목, 짧은 설명, 전체 설명이 텍스트 입력이고, 아이콘, 제목, 스크린샷, 동영상, 설명, 링크는 설치 전 품질 신호다(PlayListing-23).
- 기술 품질도 노출 입력이다. Android vitals의 비정상 동작 임계값을 넘는 앱은 발견 가능성이 낮아지고 등록정보에 경고가 표시될 수 있다(PlayQuality-1, PlayQuality-12).

## 2. 필드 점검

| 점검 항목 | 실패 시 발견사항 | 증거 등급 |
|---|---|---|
| 제목에 브랜드와 설명어를 담고 30자 이내이며, 이모지, 반복 기호, 전체 대문자, 순위나 가격 단어가 없다 | 정책 금지 단어는 `critical`, 수요 없는 브랜드뿐 제목은 `warning` | `official` (PlayListing-2) |
| 짧은 설명이 핵심 혜택을 쉬운 말로 80자 이내에 밝힌다 | `warning` | `heuristic`. 한도는 `official` |
| 전체 설명이 주요 사용 사례를 자연스러운 문장으로 다루고 중요한 용어를 앞에 둔다. 키워드 블록, 익명 추천사, 순위·가격 주장이 없다 | 키워드 블록이나 순위 주장은 `critical` | `official` (PlayListing-1) |
| 용어 반복 | 반복 횟수만 관찰로 보고한다. Google은 이상적인 밀도를 공개하지 않는다 | `heuristic` (AsoIndustry-31) |
| 카테고리와 최대 다섯 개 태그가 앱과 맞는다 | `warning` | `official` (PlayListing-5) |

## 3. 전환 도구

- 맞춤 스토어 등록정보: 한도와 견줘 개수를 세고, 타기팅(국가, 검색 키워드, 사전 등록, 광고 트래픽, 이탈 사용자)과 각 등록정보의 고유 메시지를 확인한다(PlayListing-6).
- Store Listing Experiments: 최근 실험, 무엇을 테스트했는지, 오디언스 비중, 최소 감지 효과, 신뢰 수준, 결과 상태를 확인한다. Console이 보고할 때만 변형이 승리하며, 요일 패턴을 담으려면 최소 일주일 돌린다(PlayListing-7, PlayListing-8).
- 프로모션 콘텐츠(LiveOps): 주기, 유형, 태그라인 규칙, 소유자가 제공할 때의 28일 스코어카드를 확인한다(PlayListing-18..20, PlayListing-28, PlayListing-29).
- 출시 전 앱의 사전 등록: 국가별 설정, 선택 보상, 출시 전 맞춤 등록정보를 확인한다(PlayListing-21, PlayListing-22).

## 4. 평점과 리뷰

- 공개 평점은 최근 평점에 가중되고 국가와 기기 유형으로 나뉜다. 버전마다 초기화되지 않는다(PlayListing-10, PlayListing-36). 범위 안 국가별로 읽는다.
- In-App Review API: 과업을 마친 뒤 실행하는지, 사전 질문, 변형한 카드, CTA 없이 실행하는지 확인하고, 숨은 할당량이 반복 호출을 억제할 수 있음을 예상한다(PlayListing-13).
- 보상 평점, 강제 팝업, 유료 또는 자동 리뷰는 정책 위반이다(PlayListing-12, PlayQuality-17).
- 답변: 최근 저평점 리뷰의 답변 범위를 확인한다. Google은 부정 리뷰에 답하면 그 리뷰어의 평점이 오르는 경향이 있다고 보고하며, 이는 보장된 효과가 아니라 Google 자체 주장으로 `official` 등급을 매긴다(PlayListing-37).

## 5. 품질 신호

- 소유자가 Android vitals를 내보내면 사용자 체감 크래시율과 ANR율을 전체와 최악 기기 모델에서 비정상 동작 임계값과 비교한다(PlayQuality-1). 내보낸 자료가 없으면 그 범주는 `unknown`이다.
- 핵심 가치: DAU/MAU와 사용자 이탈률이 임계값을 넘으면 등록정보 경고가 표시될 수 있다(PlayQuality-1).
- 대형 화면 품질: 2027년 4월부터 Google은 게시와 업데이트에 적응형 품질 Tier 3과 폴더블 스크린샷을 요구한다. 휴대폰만 타깃으로 하는 앱을 표시한다(PlayQuality-4, PlayQuality-5).
- 크기: 다운로드 크기를 기록한다. 크기가 커지면 설치 성공률이 낮아지고, 큰 다운로드는 모바일 데이터 경고를 띄운다(PlayQuality-10, PlayQuality-11).

## 6. 메타데이터 정책 위험

Metadata, Deceptive Behavior, Ratings and Reviews 정책과 충돌하는 요소를 정책 이름과 함께 표시한다(PlayListing-1, PlayListing-2, PlayListing-12, PlayQuality-16). 오해를 부르는 기능 주장, 운영체제나 다른 앱 모방, 텍스트나 그래픽의 순위·가격 주장, 키워드 목록, 추천사, 보상 리뷰가 해당한다. 이것은 위험 표시이며 준수 판정이 아니다.

## 7. 측정

- 2026년 6월과 7월부터 스토어 등록정보 보고서는 고유 Install, Open, Pre-register 클릭을 세고 기존 전환율 대신 클릭률(CTR)을 보고한다. 변경 뒤의 비율을 이전 전환율과 절대 비교하지 않는다(PlayQuality-6, PlayListing-30).
- 트래픽 유입: Google Play 검색, Google Play explore, 광고와 추천(PlayQuality-6).
- 동종 벤치마크는 큐레이션하거나 직접 짠 동종군의 중앙값과 백분위수다. 어느 쪽인지 기록한다(PlayQuality-8).
- Google Ads App 캠페인은 Play 검색과 둘러보기 표면에 게재되므로 유료 트래픽이 explore에 섞인다. 해당 기간에 캠페인이 돌았는지 기록한다(PlayQuality-19).

## Sources

> 확인 2026-11-22.

| 주장 | 출처 |
|---|---|
| 순위 요인, 필드 규칙, 태그, 맞춤 등록정보, 실험, 프로모션 콘텐츠, 사전 등록, 평점 | PlayListing-1..2, PlayListing-5..8, PlayListing-10, PlayListing-12, PlayListing-13, PlayListing-18..23, PlayListing-28..30, PlayListing-36, PlayListing-37 in [../references/sources.md](../references/sources.md) |
| Android vitals, 핵심 가치, 적응형 품질, 크기, 지표 변경, 벤치마크, App 캠페인, 기만적 동작 | PlayQuality-1, PlayQuality-4..6, PlayQuality-8..12, PlayQuality-16, PlayQuality-17, PlayQuality-19 |
| 벤더 추정으로서의 밀도 | AsoIndustry-31 |

### Evidence grade

Google 페이지에서 가져온 규칙은 `PRIMARY`이고, 벤더에서 도출한 점검은 표에서 `heuristic`으로 표시한다.
