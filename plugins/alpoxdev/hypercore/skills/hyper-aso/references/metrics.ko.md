# 지표 사전

콘솔 지표나 벤더 벤치마크를 읽거나 비교하기 전에 이 레퍼런스를 읽는다.

## Apple App Store Connect (App Analytics)

| 지표 | 정의 | 출처 |
|---|---|---|
| 노출 수 | 검색 결과, 둘러보기, 제품 페이지에서 앱이 1초 넘게 조회된 횟수. 제품 페이지 조회도 포함한다 | AppleGrowth-12, AppleGrowth-13 |
| 제품 페이지 조회 수 | 제품 페이지가 조회된 횟수 | AppleGrowth-12 |
| 전환율 | 총 다운로드와 사전 주문을 고유 기기 노출 수로 나눈 값 | AppleGrowth-13 |
| 최초 다운로드 / 재다운로드 | Apple 계정에서의 첫 다운로드 / 같은 계정의 이후 다운로드 | AppleGrowth-12 |
| 소스 유형 | App Store Search, App Store Browse, App Referrer, Web Referrer 등 | AppleGrowth-13 |
| 리텐션 | 다운로드한 기기 중 이후 날짜에 앱을 사용한 기기의 비율 | AppleGrowth-13 |
| 맞춤 페이지, 테스트, 이벤트 지표 | 페이지, 테스트, 이벤트가 최초 다운로드 5회에 도달하면 표시한다 | AppleGrowth-03, AppleGrowth-05, AppleGrowth-14 |
| Product Page Optimization 결과 | 베이지안 추정. 90% 신뢰수준에서 "Performing Better" 또는 "Worse", 그 밖에는 데이터 수집 중이거나 결론이 나지 않을 가능성 | AppleGrowth-05 |

App Analytics, Sales and Trends, Payments 리포트는 서로 다른 것을 세며 상호 교환할 수 없다(AppleGrowth-11, AppleGrowth-15).

## Google Play Console

| 지표 | 정의 | 출처 |
|---|---|---|
| 스토어 등록정보 방문자 | 스토어 등록정보를 조회한 고유 사용자 | PlayQuality-6 |
| 고유 클릭 | Install, Open, Pre-register를 탭한 고유 사용자. 2026년 6월부터 기본 스토어 등록정보 지표 | PlayQuality-6, PlayListing-30 |
| 클릭률 | 스토어 등록정보 방문자 중 클릭한 비율. 2026년 7월부터 기존 전환율을 대체 | PlayQuality-6 |
| 획득 | Play가 기록한 설치. 2026년 변경으로 Statistics와 내보내기로 이동 | PlayQuality-6 |
| 트래픽 소스 | Google Play 검색, Google Play 탐색, 광고와 추천 | PlayQuality-6 |
| 동종업계 벤치마크 | 큐레이션 그룹(최소 100개 앱) 또는 맞춤 그룹(8-12개 앱)의 중앙값과 25/75 백분위 | PlayQuality-8 |
| 사용자 체감 크래시 및 ANR 비율 | 28일 동안 사용자 체감 크래시나 ANR이 발생한 일간 활성 사용자 비율 | PlayQuality-1 |
| DAU/MAU와 사용자 이탈률 | 등록정보 경고 임계값이 있는 핵심 가치 지표 | PlayQuality-1 |
| 실험 지표 | 변형별 고유 설치, 열기, 사전 등록 클릭. 선택한 신뢰수준과 최소 검출 효과를 포함한다 | PlayListing-7 |

2026년 중반(mid-2026) 정의 변경을 걸쳐 Play 전환 또는 클릭률 숫자를 비교하지 않는다.

## 벤더 벤치마크

- 벤치마크는 벤더, 스토어, 국가, 카테고리, 지표 정의, 날짜가 함께 있을 때만 쓸 수 있다. 예를 들어 한 벤더의 2025년 미국 수치는 App Store 제품 페이지 조회 대비 설치 8.56%, Google Play 16.15%였고 카테고리 편차는 5.2%에서 52.8%였다(AsoIndustry-26). 이 수치는 Play의 2026년 지표 변경보다 앞선다.
- 다른 벤더는 전체 데이터를 스토어만 보유하고 트래픽 구성이 좌우하므로 보편적 벤치마크는 존재하지 않는다고 주장한다(AsoIndustry-27).
- 구독 앱에는 세 비율이 필요하다. 페이지에서 설치, 설치에서 체험, 체험에서 유료. 마지막만 최적화하면 앞의 둘이 가려진다(AsoIndustry-28, AsoIndustry-40).
- 평점은 주로 전환을 통해 결과에 작용한다. 순위에 별점 가중치를 공개한 스토어는 없다(AsoIndustry-38, AppleMeta-16).

모든 벤치마크는 `tool`, 모든 콘솔 판독은 `console`로 등급을 매긴다.

## Sources

> 확인 2026-11-22.

| 주장 | 출처 |
|---|---|
| Apple 지표 정의 | [sources.md](sources.md)의 AppleGrowth-03, AppleGrowth-05, AppleGrowth-11..15 |
| Play 지표 정의와 2026년 변경 | PlayQuality-1, PlayQuality-6, PlayQuality-8, PlayListing-7, PlayListing-30 |
| 벤치마크와 그 한계 | AsoIndustry-26..28, AsoIndustry-38, AsoIndustry-40, AppleMeta-16 |

### Evidence grade

콘솔 정의는 `PRIMARY`다. 벤치마크는 벤더 데이터인 `SECONDARY`다.
