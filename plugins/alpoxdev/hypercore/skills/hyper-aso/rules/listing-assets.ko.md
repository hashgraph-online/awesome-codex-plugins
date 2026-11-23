# 등록정보 자산 점검

**목적**: 두 스토어의 아이콘, 스크린샷, 미리보기, 프로모션 동영상, 기능 그래픽을 어떻게 평가하는지 적는다. 정확한 규격은 `references/policy-limits.md`에 있다.

## 1. 수집할 것

- 스토어, 기기 등급, 로캘마다 현재 자산 세트를 라이브 페이지(`live`)나 소유자 내보내기에서 읽는다. 사용한 스토어프런트와 기기를 기록한다.
- 검색 결과에 나타나는 스크린샷: App Store는 처음 1개에서 3개까지(AppleMeta-15), Google Play는 조회한 기기 등급에서 스크롤 없이 보이는 갤러리이다.
- 현지화 자산이 있는지, 아니면 다른 로캘에서 기본 언어 세트가 표시되는지 확인한다(AppleMeta-10, PlayListing-15).

## 2. 규격 점검

| 점검 항목 | 실패 시 심각도 | 증거 등급 |
|---|---|---|
| 필수 기기 등급마다 개수, 픽셀 크기, 형식, 길이가 스토어 한도 안에 있다 | 필수 세트가 없으면 `critical`, 그 밖은 `warning` | `official` |
| Apple: 미리보기는 앱에서 캡처하고, 스크린샷은 앱 사용 모습을 보여 준다 | `warning`. 가이드라인 위험 2.3.3 | `official` (AppleMeta-18) |
| 그래픽에 가격, 할인, 순위 주장("#1", "best"), URL, 검증할 수 없는 주장이 없다 | `critical` | `official` (AppleMeta-40, PlayListing-1) |
| Google Play 아이콘: 정사각형, 풀블리드, 순위 표시나 Play 표시가 없다. Play가 마스크와 그림자를 적용한다 | `warning` | `official` (PlayListing-4) |
| Apple 아이콘은 바이너리에 포함해 배포한다. 변경에는 버전이 필요하고, Product Page Optimization을 쓰려면 테스트 아이콘이 바이너리에 있어야 한다 | 기획 단계에서 `info` | `official` (AppleMeta-11, AppleMeta-28) |
| 앱이 해당 기기를 지원하면 Google Play 대형 화면과 폴더블 세트가 있다 | `warning`, 2027년 4월 요구 사항과 함께 높아진다 | `official` (PlayQuality-5) |

## 3. 전환 판단

이것은 `heuristic` 판단이다. 그렇게 밝히고, 결론은 스토어 실험으로 내리는 편을 앞세운다.

- 처음 프레임마다 짧은 캡션 하나로 핵심 가치를 전달하며, 검색 결과 크기에서 읽힌다.
- 순서는 한 프레임의 기능 목록이 아니라 주요 사용자 과업을 따라가며 프레임마다 기능 하나를 다룬다.
- 캡션은 그 로캘의 언어로 쓰고 그 로캘의 읽기 길이에 맞춘다.
- 아이콘은 작은 크기에서도 알아볼 수 있고, 같은 결과의 상위 경쟁사와 구분된다.
- 벤더 테스트 사례는 스크린샷을 바꾸면 다른 자산보다 전환이 크게 움직인다고 보고한다(AppleMeta-37, AppleMeta-38, AsoIndustry-35). 이것은 규칙이 아니라 `tool`이나 `heuristic` 사례 증거로 다룬다.
- 스크린샷 캡션 문구는 전환용 문구다. App Store 순위에 미치는 영향은 논쟁 중이므로 순위 입력으로 점수화하지 않는다(AsoIndustry-15..18).

## 4. 실험 계획

자산 변경을 제안하면 테스트 계획으로 적는다.

- 스토어 도구: Product Page Optimization(치료 최대 3개, 최대 90일) 또는 Store Listing Experiments(변형 최대 2개, 기본 또는 현지화).
- 테스트마다 변수 하나만 두고, 가설, 오디언스나 로캘, 스토어가 보고하는 지표, 중단 규칙을 밝힌다.
- 트래픽 규모 산정: 트래픽이 작은 앱은 테스트 기간 안에 큰 효과만 감지할 수 있다(AsoIndustry-23). 앱 트래픽이 작으면 이 점을 밝히고 소소한 변경 대신 더 과감한 변형을 제안한다.
- 테스트 중 진행한 계절성과 유료 캠페인은 교란 요인으로 기록한다.

## Sources

> 확인 2026-11-22.

| 주장 | 출처 |
|---|---|
| 자산 규격, 검색 결과 스크린샷, 가이드라인·정책 규칙 | AppleMeta-3, AppleMeta-4, AppleMeta-10, AppleMeta-11, AppleMeta-15, AppleMeta-18, AppleMeta-28, AppleMeta-40, PlayListing-1, PlayListing-3, PlayListing-4, PlayListing-15, PlayQuality-5 in [../references/sources.md](../references/sources.md) |
| 벤더 전환 사례, 캡션 논쟁, 검정력 분석 | AppleMeta-37, AppleMeta-38, AsoIndustry-15..18, AsoIndustry-23, AsoIndustry-35 |

### Evidence grade

규격 점검은 `PRIMARY`이고, 3장은 설계상 `heuristic`이다.
