# 스토어 정책 한도

글자수, 바이트, 크기, 개수, 기간, 임계값 한도를 말하기 전에 이 레퍼런스를 읽는다. 모든 행은 확인일 기준 공식 페이지에서 직접 읽었다. 출처 id는 [sources.md](sources.md)의 행을 가리킨다. 한도는 바뀐다. 중요한 발견사항이 특정 한도에 의존하면 출처를 다시 열고 실행의 `sources.md`에 새 확인일을 기록한다.

## 목차

- Apple App Store 텍스트 필드
- Apple App Store 에셋
- Apple 전환 도구
- Apple 평점
- Google Play 텍스트 필드
- Google Play 에셋
- Google Play 전환 도구
- Google Play 평점과 품질
- 원스토어(한국)
- 미해결 충돌

## Apple App Store 텍스트 필드

2026-11-22 확인.

| 필드 | 한도 | Apple 기준 검색 입력 | 새 버전 없이 변경 | 출처 |
|---|---|---|---|---|
| 앱 이름 | 2-30자 | 예 | 아니오 | AppleMeta-1, AppleMeta-16 |
| Subtitle | 30자 | 예 | 아니오 | AppleMeta-1, AppleMeta-16 |
| 키워드 | "up to 100 bytes of content", 각 키워드는 2자 초과, 쉼표 구분 | 예 | 아니오 | AppleMeta-2 |
| 설명 | 4,000자 | App Store 검색 입력으로 명시되지 않음. Apple은 웹 엔진 검색 결과에 쓰인다고 밝힘 | 아니오 | AppleMeta-2, AppleMeta-9 |
| Promotional Text | 170자 | 아니오. Apple은 순위에 영향을 주지 않는다고 밝힘 | 예 | AppleMeta-2, AppleMeta-15, AppleMeta-16 |
| What's New | 4,000자 | 아니오 | 버전과 함께 배포 | AppleMeta-2 |
| 카테고리 | 기본 1개(필수)와 선택 보조 1개. 기본 카테고리는 둘러보기 배치에 영향을 주고 텍스트 관련성의 일부다 | 기본 카테고리만 예 | 아니오 | AppleMeta-16, AppleMeta-17 |
| 메타데이터 로캘 | 50개 언어 | — | — | AppleMeta-5 |
| 전파 | 메타데이터 수정은 반영까지 최대 24시간이 걸릴 수 있음 | — | — | AppleMeta-9 |

Apple은 텍스트 관련성(이름, 부제, 키워드, 기본 카테고리)과 사용자 행동(다운로드, 평점과 리뷰)을 검색 요인으로 든다(AppleMeta-16). 개발자 이름도 검색된다(AppleMeta-2).

## Apple App Store 에셋

2026-11-22 확인.

| 에셋 | 한도 | 출처 |
|---|---|---|
| 스크린샷 | 기기 크기당 1-10장. JPEG 또는 PNG, 알파 없음. iPhone과 (iPad 앱이면) 13인치 iPad 세트 필수. 처음 1-3장이 검색 결과에 표시될 수 있음 | AppleMeta-3, AppleMeta-15 |
| 앱 미리보기 | 현지화 및 기기 크기당 최대 3개. 15-30초. 최대 500 MB. 미리보기는 스크린샷보다 먼저 재생 | AppleMeta-2, AppleMeta-4 |
| 앱 아이콘 | 메타데이터로 업로드하지 않고 앱 바이너리에 포함해 배포. 변경하려면 새 버전 필요 | AppleMeta-11 |
| 크리에이티브 에셋(제품 페이지 헤더, 검색, 유니버설) | 헤더 21:9 3840x1646 PNG. 검색 3:2. 유니버설 16:9 5244x2950 PNG. 헤더 동영상 5-30초 | AppleMeta-12 |
| 에셋 내용 | 핵심 경험과 관련되어야 함. 크리에이티브 에셋에 가격, 할인, URL, 검증할 수 없는 주장 금지 | AppleMeta-40 |

## Apple 전환 도구

2026-11-22 확인.

| 도구 | 한도 | 출처 |
|---|---|---|
| 맞춤 제품 페이지 | 앱당 최대 70개(2025-10-29에 35개에서 상향). 각 페이지는 자체 스크린샷, 미리보기, 프로모션 텍스트, 지정 키워드를 가질 수 있음. 승인되고 노출된 뒤에는 지정 키워드로만 검색에 나타남. 지표는 최초 다운로드 5회 후 표시. 딥링크는 iOS/iPadOS 18 이상 필요 | AppleGrowth-01, AppleGrowth-03, AppleGrowth-31, AppleMeta-29 |
| Product Page Optimization | 원본 대비 최대 3개 트리트먼트. 한 번에 테스트 1개. 최대 90일. 아이콘, 스크린샷, 미리보기만. 테스트 아이콘은 1024x1024로 이미 라이브 바이너리에 있어야 함. 결과는 90% 신뢰수준 | AppleGrowth-02, AppleGrowth-04, AppleMeta-27, AppleMeta-28 |
| In-App Events | 이름 30자, 짧은 설명 50자, 긴 설명 120자. 동시 게시 최대 10개, 승인 최대 15개. 시작 최대 14일 전 게시. 이벤트 기간 15분-31일 | AppleGrowth-06, AppleGrowth-08 |
| 프로모션 인앱 구매 | 제품 페이지에 최대 20개 | AppleGrowth-10, AppleMeta-15 |
| Win-back offers와 offer codes | 구독별·분기별 상한은 AppleGrowth-29와 AppleGrowth-30 참고 | AppleGrowth-29, AppleGrowth-30 |
| 추천(featuring) 요청 | App Store Connect에서 제출. Apple은 최소 3주 리드 타임을 요청 | AppleGrowth-32 |

## Apple 평점

2026-11-22 확인.

| 규칙 | 한도 | 출처 |
|---|---|---|
| 앱 내 평점 요청 | 시스템이 사용자당 365일 기간에 최대 3회 표시. 평점을 남긴 뒤에는 새 버전이고 365일이 지난 경우에만 다시 표시 가능. TestFlight에서는 표시되지 않음 | AppleMeta-25, AppleMeta-26 |
| 평점 초기화 | 새 버전을 출시할 때만 가능. 되돌릴 수 없음. 모든 스토어프런트에 한꺼번에 적용. 작성된 리뷰는 유지 | AppleMeta-23 |
| 개발자 답변 | 리뷰당 공개 답변 1개, 수정 가능. 반영까지 최대 24시간 | AppleMeta-24 |
| AI 리뷰 요약 | iOS 18.4 이상. 미국과 추가 영어 스토어프런트 8곳에서 영어 요약 제공. 확인일 기준 한국은 미제공 | AppleMeta-21, KoreaAeo-20 |
| 앱 태그 | 메타데이터, AI, 큐레이션으로 생성. 확인일 기준 미국 스토어프런트만 | AppleMeta-30, KoreaAeo-19 |

## Google Play 텍스트 필드

2026-11-22 확인.

| 필드 | 한도 | 출처 |
|---|---|---|
| 앱 이름(제목) | 30자. 이모지, 반복 특수문자, 브랜드 밖 전체 대문자, "free", "#1", "best" 같은 단어 금지 | PlayListing-1, PlayListing-2 |
| Short description | 80자 | PlayListing-1, PlayListing-3 |
| 전체 설명 | 4,000자 | PlayListing-1 |
| 글자 계산 | 전각과 반각 문자에 같은 한도 적용 | Play Console 도움말 답변 9859152(리드 재확인, 2026-11-22) |
| 태그 | 앱당 최대 5개. 변경 반영까지 최대 24시간 | PlayListing-5 |
| 검색 사용 | 제목, 설명, 카테고리를 검색 의도 매칭에 사용. 아이콘, 제목, 스크린샷, 동영상, 설명, 링크는 설치 전 품질 신호 | PlayListing-23, PlayQuality-9 |

## Google Play 에셋

2026-11-22 확인.

| 에셋 | 한도 | 출처 |
|---|---|---|
| 앱 아이콘 | 512x512 32비트 PNG, sRGB, 최대 1,024 KB. Play가 모서리 마스크와 그림자를 적용. 순위나 Play 프로그램 마크 금지 | PlayListing-3, PlayListing-4 |
| 피처 그래픽 | 1024x500 JPEG 또는 24비트 PNG, 알파 없음 | PlayListing-3 |
| 휴대전화 스크린샷 | 2-8장. 변당 320-3,840 px. 최대 8 MB. 긴 변은 짧은 변의 최대 2.3배 | PlayListing-3 |
| 폴더블 / 대형 화면 스크린샷 | 폴더블 3-8장, 960-3,840 px. 대형 화면 세트는 Console에 표시된 기준 | PlayListing-3, PlayQuality-5 |
| 미리보기 동영상 | YouTube URL 1개, 재생목록이나 타임코드 없음 | PlayListing-3 |

## Google Play 전환 도구

2026-11-22 확인.

| 도구 | 한도 | 출처 |
|---|---|---|
| 맞춤 스토어 등록정보 | 최대 50개. 대상은 국가, 광고 트래픽, 사전 등록, 검색 키워드, 사용자 상태 | PlayListing-6 |
| Store Listing Experiments | 기본 그래픽 실험 1개 또는 현지화 실험 최대 5개를 동시에. 현재 등록정보 대비 최대 2개 변형. 이름 50자. 6개월 후 중지. 앱 이름은 테스트할 수 없음. Google은 최소 1주를 권장 | PlayListing-7, PlayListing-8, PlayListing-35 |
| 프로모션 콘텐츠 | 시작 최대 60일 전 제출. 검토 최대 4일. 기간 한정 이벤트는 30일 안에 종료. 태그라인 80자, 가치를 처음 40자에 | PlayListing-19, PlayListing-20 |
| 사전 등록 | 국가별. Google은 출시 3-6주 전 개시를 제안 | PlayListing-21, PlayListing-22 |
| 번역 | 29개 언어 무료 기계 번역. 최대 48개 언어 유료 전문 번역 | PlayListing-16 |

## Google Play 평점과 품질

2026-11-22 확인.

| 규칙 | 한도 | 출처 |
|---|---|---|
| 공개 평점 | 최근 평점에 가중. 평점 5개 미만이면 총점을 숨김. 국가와 기기 유형별로 분리. 버전별로 초기화되지 않음 | PlayListing-10, PlayListing-36 |
| 개발자 답변 | 리뷰당 공개 답변 1개, 수정 가능. Reply to Reviews API는 최근 1주일 내 댓글이 있는 운영 리뷰를 대상으로 하며 시간당 GET 200회, 일 POST 2,000회 | PlayListing-10, PlayListing-14 |
| In-App Review API | Google이 공개하지 않는 기간 기반 할당량. 한 달 안에 두 번 이상 호출하면 아무것도 표시되지 않을 수 있음. 사전 질문, 변형 카드, CTA 금지 | PlayListing-13 |
| Android vitals 비정상 동작 | 사용자 체감 크래시율 전체 1.09% 또는 기기 모델 1개에서 8%. 사용자 체감 ANR율 전체 0.47% 또는 기기 모델 1개에서 8%. 임계값을 넘으면 앱 발견성이 낮아지고 등록정보 경고가 표시될 수 있음. 28일 기간 | PlayQuality-1(리드 재확인, 2026-11-22) |
| 핵심 가치 지표 | DAU/MAU 8% 미만 또는 사용자 이탈률 5% 초과면 등록정보 경고가 발생할 수 있음 | PlayQuality-1 |
| 크기 | 모바일 데이터에서 200 MB 초과 시 경고. 크기 증가는 설치 성공률을 낮춤 | PlayQuality-10, PlayQuality-11 |
| 보고 변경 | 2026년 6월부터 기본 스토어 등록정보 지표는 고유 Install/Open/Pre-register 클릭. 2026년 7월부터 클릭률이 기존 전환율을 대체 | PlayQuality-6, PlayListing-30(리드 재확인, 2026-11-22) |

## 원스토어(한국)

2026-11-22 확인. 사용자가 원스토어를 지정할 때만 적용한다.

| 필드 | 한도 | 출처 |
|---|---|---|
| 제목 | 50자 | KoreaAeo-1, KoreaAeo-2 |
| 한 줄 설명 | 100자 | KoreaAeo-2 |
| 설명 | 1,300자 | KoreaAeo-2 |
| 키워드 | 1-10개 | KoreaAeo-2 |
| 스크린샷 | 2-8장, 최대 1 MB, 최대 1,300x1,300 px | KoreaAeo-2 |
| 그래픽 이미지 / 아이콘 | 1024x578 / 512x512 | KoreaAeo-2 |
| 패키지 이름 | Google Play 패키지 이름을 입력하면 원스토어 기준 검색 정확도가 향상됨 | KoreaAeo-3 |

## 미해결 충돌

| 주제 | 충돌 | 처리 |
|---|---|---|
| Apple 키워드 필드 단위 | App Store Connect 레퍼런스는 "100 bytes"라고 하고, Apple 마케팅 페이지와 대부분 벤더는 100자라고 하며, 한국 벤더 하나는 한글이 글자당 1자로 계산된다고 한다 | UTF-8 바이트를 안전한 상한으로 계산하고(한글은 3바이트이므로 약 33음절) 소유자에게 App Store Connect 카운터로 확인하라고 안내한다. `미확인/충돌`로 기록. (AppleMeta-2, AppleMeta-15, KoreaAeo-13) |
| iOS 스크린샷 캡션 색인 | 벤더는 2025년부터 캡션 텍스트가 OCR로 색인된다고 주장한다. Apple 검색 페이지는 스크린샷이 순위에 영향을 주지 않는다고 하고, 벤더 테스트 하나는 이를 재현하지 못했다 | 캡션은 전환 문구로 취급하고 순위 효과는 `heuristic`으로 둔다. (AppleMeta-32, KoreaAeo-17, KoreaAeo-18, AsoIndustry-15..18) |
| Apple Ads 인기도 척도 | Apple Ads는 인기도를 1-5 막대로 표시하고, API와 벤더는 5-100으로 보고한다. Apple은 2025년 10월과 2026년 10월에 유사 변형을 다시 묶었다 | 인기도 값마다 척도와 날짜를 함께 적고, 변화 전후 값을 비교하지 않는다. (AppleGrowth-21, AsoIndustry-4, AsoIndustry-5, AsoIndustry-42) |
| Google Play 릴리스 노트 길이 | 500자는 벤더 자료에만 나온다 | 공식으로 진술하지 않는다. (PlayListing-34) |

## Sources

> 확인 2026-11-22.

| 주장 | 출처 |
|---|---|
| 위의 모든 행 | 각 표에 적힌 장부 행, [sources.md](sources.md). 리드 재확인은 해당 행에 표시 |

### Evidence grade

`PRIMARY` - 모든 한도를 Apple, Google, 원스토어 페이지에서 읽었다. 벤더 행은 미해결 충돌에만 나온다.
