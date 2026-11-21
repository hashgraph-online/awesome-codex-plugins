# 정석 수치 기준

만들기 전과 숫자로 발견 사항을 판정하기 전에 읽는다. 이 파일은 설계하거나 재스타일하거나 연출 화면으로 만드는 모든 화면이 충족하는 정석 수치를 소유한다. `MUST` 행은 준수 요구 사항이며 실행을 실패 처리한다. `DEFAULT` 행은 프로젝트, 브리프, 플랫폼이 아무것도 말하지 않을 때의 시작값이며 문서화된 프로젝트 값이 이를 대체한다.

## 1. 대비와 색

| 규칙 | 값 | 수준 |
|---|---|---|
| 배경 대비 본문 텍스트 | 반올림 없이 계산한 최소 4.5:1(`references/contrast-check.md`); 회색 쌍은 계산 없이 통과를 주장하지 않는다 | MUST (WCAG 2.2 AA) |
| 큰 텍스트(약 24px, 굵은 약 18.5px) | 최소 3:1 | MUST |
| 아이콘, 컨트롤 경계, 상태 표시, 내용 이해에 필요한 차트 표식 | 인접 색 대비 최소 3:1 | MUST |
| 이미지·영상 위 텍스트 | 최악 픽셀 쌍도 4.5:1을 통과하는 단색 또는 그라디언트 스크림 | MUST |
| 흐린 텍스트와 placeholder 텍스트 | 여전히 4.5:1; 위계는 기준 아래 회색이 아니라 크기와 굵기로 만든다 | MUST |
| 두 색 구성표 | 둘 다 출시할 때 모든 쌍이 라이트와 다크에서 통과한다 | MUST |
| 강조색 비중 | 강조 색상 하나; 강조 채움은 화면에서 작은 비중을 차지한다(KRDS: 최대 5%) | DEFAULT |
| 중성색 착색 | 브랜드가 허용하면 순수 회색 대신 브랜드 색상 쪽으로 중성색을 착색한다 | DEFAULT |
| 색상 수 | 핵심 색 두세 개에 강조색 하나; 중성색은 세지 않는다; 문서화된 시스템이 있을 때만 더 쓴다 | DEFAULT |

WCAG 3는 Working Draft이고 APCA는 어디에서도 규범이 아니다. 대비 기준은 WCAG 2.2 AA로 유지한다.

## 2. 타깃과 포커스

| 규칙 | 값 | 수준 |
|---|---|---|
| 포인터 타깃(웹) | 최소 24×24 CSS px, 또는 WCAG 간격 예외 | MUST |
| 터치 타깃 | 터치 표면에서 44×44 CSS px 또는 pt; Android 48×48 dp | DEFAULT (WCAG AAA, Apple 기본값, Android 지침) |
| Apple 컨트롤 최소 | 28×28 pt가 명시된 최소이고 44×44 pt가 목표 기본값이다 | platform |
| 포커스 표시 | 키보드로 조작 가능한 모든 컨트롤이 포커스 표시를 보인다; 대체 없이 `outline: none`을 쓰지 않는다 | MUST |
| 포커스 표시 대비 | 인접 배경 대비 최소 3:1 | MUST |
| 포커스 가림 없음 | 고정 머리말·바닥글과 비모달 패널이 포커스된 컨트롤을 완전히 덮지 않는다(`scroll-padding`) | MUST |
| 포커스 스타일 | 사용자 에이전트 링이나 프로젝트에 문서화된 링을 유지한다; 직접 만든 링은 최소 2px | DEFAULT |
| 조작 단서 | 켜진 모든 컨트롤이 네이티브 요소이고(동작은 `button`, 이동은 `a href`) 기본 규칙 하나로 `cursor: pointer`를 보이며 접근 가능한 이름이 있고 색만으로 구분하지 않는 서로 다른 hover, active, disabled 상태를 가진다(`references/accessible-interaction.md`) | MUST (이름, 역할, 색만 사용) / DEFAULT (커서) |
| 확대 | viewport meta가 `user-scalable=no`나 `maximum-scale=1`을 설정하지 않는다 | MUST |
| 터치 간격 | 인접한 터치 타깃 사이에 분명한 간격을 두어 엄지로 눌렀을 때 둘 다 눌리지 않는다 | DEFAULT |

브라우저가 그리는 표면(해당 표면이 있을 때 토큰으로 정하고, 플랫폼 기본값을 그대로 두지 않는다):

| 규칙 | 값 | 수준 |
|---|---|---|
| 선택 | `::selection`의 전경과 배경을 토큰으로 정하고 기본 파랑을 쓰지 않는다 | DEFAULT |
| 캐럿 | 편집 표면에서 `caret-color`를 본문 색이나 토큰 색으로 맞춘다 | DEFAULT |
| 스크롤바 | 스크롤이 있는 곳, 오버플로 패널을 포함해 `scrollbar-color`를 준다 | DEFAULT |
| 포커스 링 | 컨트롤 가장자리에서 떨어진, 최소 2px의 보이는 링 | DEFAULT |
| 밑줄 간격 | `text-underline-offset`으로 밑줄이 아래 꼬리 글자를 가로지르지 않게 한다 | DEFAULT |
| 숫자 형태 | 표, 가격, 카운터에 `tabular-nums`(3절의 같은 규칙)를 쓴다 | DEFAULT |

## 3. 타이포그래피

| 규칙 | 값 | 수준 |
|---|---|---|
| 웹 본문 크기 | 최소 16px; 보통 16-18px(한국어 본문: §6) | DEFAULT |
| 가장 작은 UI 텍스트 | 12px; iOS 11pt, macOS 10pt는 플랫폼 최소값이며 기본값이 아니다 | DEFAULT |
| 행 길이 | 이어지는 텍스트 기준 45-75자; 넓은 화면에서 전체 폭 단락을 쓰지 않는다 | DEFAULT |
| 행간, 라틴 본문 | 1.4-1.6; 제목 1.1-1.3 | DEFAULT |
| 타이핑 단계 | 인접한 크기가 최소 1.25x 차이 난다 | DEFAULT |
| 디스플레이 크기 | 디스플레이 텍스트는 최대 6rem | DEFAULT |
| 디스플레이 자간 | 디스플레이 자간은 -0.04em 아래로 내려가지 않는다 | DEFAULT |
| 텍스트 간격 내성 | 행간 1.5, 문단 간격 2em, 자간 0.12em, 단어 간격 0.16em의 사용자 재정의에서도 레이아웃이 버틴다 | MUST |
| 크기 조정 | 텍스트가 내용 손실 없이 200%까지 커진다 | MUST |
| 글꼴 패밀리 | 하나, 또는 역할이 고정된 둘(디스플레이, 텍스트); 셋은 쓰지 않는다 | DEFAULT |
| 굵기 | 본문 400-500; UI 텍스트에 ultralight와 thin을 피한다 | DEFAULT |
| 제목 수준 | 한 화면에서 눈에 보이는 수준은 최대 세 단계; 의미 수준을 건너뛰지 않는다 | DEFAULT |
| 제목 | 문장형 대소문자; 본문과 제목에 전부 대문자를 쓰지 않는다; 자간은 디스플레이 크기(약간 음수)와 작은 레이블(약간 양수)에만 준다 | DEFAULT |
| 숫자 | 표, 가격, 카운터에 tabular figure를 쓴다 | DEFAULT |
| 글꼴 공급 | 선언한 모든 서체를 프로젝트가 로드한다(`@font-face`, 패키지, 시스템 스택); 빌드가 제공하지 않는 서체를 쓰지 않는다 | MUST |

## 4. 공간, 레이아웃, 형태, 깊이

| 규칙 | 값 | 수준 |
|---|---|---|
| 간격 스케일 | 4px 기반 스케일 하나(4, 8, 12, 16, 24, 32, 48, 64, 96) 또는 프로젝트 자체 스케일; 일회성 값을 쓰지 않는다 | DEFAULT |
| 묶음 | 그룹 안 간격이 그룹 사이 간격보다 작다; 제목 위 간격이 아래 간격보다 크다 | DEFAULT |
| 제목 간격 | 제목 위 간격이 제목 아래 간격의 최소 1.5x다 | DEFAULT |
| 그룹 간격 | 그룹 사이 간격이 그룹 안 간격의 최소 2x다 | DEFAULT |
| 본문 폭 | 본문 65-75ch; 디스플레이 텍스트는 최대 6rem | DEFAULT |
| 리플로 | 320 CSS px 폭에서 2차원 스크롤이 없다(표, 지도, 편집기 제외) | MUST |
| 확인 폭 | 프로젝트 중단점, 없으면 375, 768, 1280(한국 공공 부문: 360, 768, 1024, 1280) | DEFAULT |
| 내용 폭 | 최대 내용 폭(약 1200-1280px)과 일관된 거터 하나 | DEFAULT |
| 모서리 반경 | 요소 크기에 연동한 스케일(예: 4 / 8 / 12 / 16 및 full); 중첩 반경은 바깥 반경에서 패딩을 뺀 값 | DEFAULT |
| 깊이 | 고도 단계 몇 개; 계층 그림자(주변광과 직접광) 또는 테두리 중 하나만 쓰고 모든 카드에 둘 다 최대 강도로 쓰지 않는다 | DEFAULT |
| 컨테이너 | 내용이 분리 가능한 객체일 때만 카드를 쓴다; 장식용으로 카드 안에 카드를 넣지 않는다 | DEFAULT |
| 반응형 상태 | 내용이 요구하는 만큼 레이아웃 상태를 만든다(보통 한 열, 두 열, 전체 그리드). 중단점은 기기 폭이 아니라 내용이 깨지는 지점에 두고, 가운데 구간(약 600-1024px)은 물려받지 않고 설계한다(`references/responsive-reflow.md`) | DEFAULT |
| 전체 높이 섹션 | 내용에 맞춰 크기를 정한다; 섹션이 화면을 채워야 할 때만 `dvh`를 쓰고 `100vh`는 쓰지 않는다 | DEFAULT |
| 고정 크롬 | 고정 머리말과 하단 바는 간결하게 유지하고 페이지에서 높이를 예약하며 안전 영역 인셋을 지킨다 | DEFAULT |
| 사용량 상한 | 글래스나 배경 흐림은 최대 요소 하나나 둘; 글로우는 최대 초점 요소 하나나 둘; 그림자는 요소가 떠오르는 곳에만 | DEFAULT |

## 5. 모션

| 규칙 | 값 | 수준 |
|---|---|---|
| 모션 감소 | `prefers-reduced-motion: reduce`를 존중한다: 움직임을 페이드나 없음으로 바꾼다; 시차 효과를 쓰지 않는다 | MUST |
| 상호작용 피드백 | 100-200 ms | DEFAULT |
| 상태·오버레이 전환 | 150-300 ms; 저자가 의도한 중심 등장 하나는 약 500 ms까지 걸릴 수 있다 | DEFAULT |
| 이징 | 등장에는 ease-out 계열(예: `cubic-bezier(0.2, 0, 0, 1)`); 등장에 ease-in을 쓰지 않는다; 습관적으로 바운스나 탄성을 쓰지 않는다 | DEFAULT |
| 속성 | `transform`과 `opacity`를 애니메이션한다; `transition: all`을 쓰지 않는다; 레이아웃 속성을 쓰지 않는다 | DEFAULT |
| 등장 | `scale(0)`에서 시작하지 않는다(불투명도와 함께 0.95 근처에서 시작); 컨테이너마다 등장 하나; 그룹 전체가 약 300 ms 안에 끝나도록 30-80 ms 간격으로 시차를 준다 | DEFAULT |
| 빈도 | 한 세션에서 여러 번 반복하는 동작에는 애니메이션을 넣지 않는다; 키보드로 촉발한 동작은 애니메이션하지 않는다 | DEFAULT |
| 자동 재생 | 5초를 넘는 움직이는 내용에는 일시 정지 컨트롤이 있다 | MUST |

## 6. 한국어 텍스트

| 규칙 | 값 | 수준 |
|---|---|---|
| 줄바꿈 | `word-break: keep-all`과 긴 토큰용 `overflow-wrap: anywhere`(또는 `break-word`) | DEFAULT |
| 본문 크기 | 최소 16px; Pretendard GOV에서 KRDS 기본값은 17px | DEFAULT |
| 행간 | 본문 최소 150%; 긴 읽기에는 160-170%가 합리적인 선택 | DEFAULT |
| 자간 | 한글 본문과 레이블에서 0; "스타일"을 위해 양수 자간을 쓰지 않는다 | DEFAULT |
| 글꼴 스택 | 프로젝트 글꼴, 또는 Pretendard 같은 OFL 한글 패밀리(예약 이름 규칙 유지)에 `"Apple SD Gothic Neo", "Noto Sans KR", "Malgun Gothic", sans-serif` 폴백 | DEFAULT |
| 굵기 | regular와 bold로 충분하다; UI에 얇은 한글 굵기를 피한다 | DEFAULT |

## 7. 상태, 피드백, 폼, 카피

| 규칙 | 값 | 수준 |
|---|---|---|
| 피드백 시점 | 0.1초 미만은 즉각으로 느껴진다; 1초 미만은 흐름을 유지한다; 10초를 넘으면 진행 표시와 빠져나갈 방법이 필요하다 | DEFAULT |
| 로딩 | 약 1초 미만은 없음; 2-10초는 스켈레톤(페이지) 또는 스피너(모듈); 스켈레톤은 최종 레이아웃을 반영한다; 10초 초과는 진행률 | DEFAULT |
| 빈 상태 | 비워 두지 않는다: 상태, 무엇이 채우는지, 직접 행동 하나 | DEFAULT |
| 오류 메시지 | 원천 옆에, 평이한 언어로, 비난하는 말 없이, 해결책과 함께, 입력을 보존하며 색만으로 알리지 않는다 | MUST (색만 사용) / DEFAULT |
| 오류 요약 | 여러 필드 폼은 포커스를 받고 각 필드로 연결되는 요약을 보여 주며 문구는 인라인 메시지와 같게 쓴다 | DEFAULT |
| 폼 | 한 열; 필드 위에 보이는 레이블; placeholder를 레이블로 쓰지 않는다; 선택 필드를 표시한다; 초기화 버튼을 두지 않는다; 별표만으로 필수 표시하지 않는다 | DEFAULT |
| 비활성 컨트롤 | 여전히 읽을 수 있다; 이유가 명백하지 않으면 이유에 도달할 수 있다 | DEFAULT |
| 카피 | 이 제품의 구체적인 동사와 명사; 슬로건 filler("seamless", "supercharge", "next-gen") 없음; 지어낸 숫자 없음 | DEFAULT |
| 아이콘 | 세트 하나; 아이콘만 있는 버튼에는 접근 가능한 이름; 이모지는 콘텐츠이지 아이콘이 아니다 | DEFAULT |

## 8. 성능 메커니즘

| 규칙 | 값 | 수준 |
|---|---|---|
| 미디어 크기 | 모든 `img`, `video`, `iframe`에 `width`와 `height` 또는 `aspect-ratio`가 있다; 늦게 오는 내용(임베드, 배너)의 자리를 미리 잡는다 | DEFAULT |
| 히어로 이미지 | 첫 화면 위에서 가장 큰 이미지는 HTML의 `img`이고 `loading="lazy"`를 쓰지 않으며 `fetchpriority="high"`를 준다; 첫 화면 아래만 지연 로드한다 | DEFAULT |
| 서드파티 스크립트 | `<head>`에 동기 서드파티 스크립트를 두지 않는다; `defer`, `async`를 쓰거나 상호작용 시 로드한다 | DEFAULT |
| 실사용 측정값 | LCP, INP, CLS는 75번째 백분위의 실사용 측정값이다(양호: LCP 최대 2.5초, INP 최대 200ms, CLS 최대 0.1). 이번 실행에서 측정했을 때만 보고하고 아니면 `not measured`로 쓴다 | MUST (측정하지 않은 수치 금지) |

## 9. 체크리스트

변경한 화면마다 실행하고 항목마다 `pass`, `fail`, `n/a`, `not run` 중 하나와 이유를 기록한다.

1. 토큰 계획의 대비 쌍을 두 구성표에서 계산하고 이미지 위 텍스트는 최악 지점에서 확인한다.
2. 모든 상호작용 요소에서 키보드로 포커스가 보이고 가려지지 않는지 확인하며 대화상자는 Escape로 닫힌다.
3. 가장 작은 폭에서 타깃 크기와 간격을 확인한다.
4. 320px 리플로, 200% 텍스트, 가운데 폭 구간을 확인한다.
5. 변경 코드의 모든 값이 토큰 계획이나 프로젝트 토큰에 속하는지 확인한다.
6. 행 길이, 제목 수준, 글꼴 공급을 확인한다.
7. 모션 감소 경로와 `transition: all` 부재를 확인한다.
8. 나열한 모든 상태를 렌더링했거나 구현했는지, 각 빈·로딩·오류 상태가 원인과 다음 행동을 밝히는지 확인한다.
9. 제품 언어가 한국어일 때 한국어 규칙을 적용한다.
10. 조작 단서: 네이티브 요소, 접근 가능한 이름, 포인터 커서, hover·active·disabled 상태, 확대 차단 없음.
11. §8의 성능 메커니즘.
12. 비율 하한과 브라우저 표면이 위 기준값 안에서 렌더링되는지 확인한다.

정적 실행은 5, 6, 10, 11번 항목과 7번의 소스 절반을 통과할 수 있다. 12번은 렌더 계산값이 필요하므로 렌더 캡처 없이는 `static_only`다.

비율 하한은 렌더링된 `computed` 값(글자 크기, 간격, 행 길이) 또는 소스 선언에서 확인할 수 있으며, 이 패키지가 비율을 자동 측정하지는 않는다(렌더 측정은 별도 관심사다).

## Sources

> 확인 2026-11-09.

| 주장 | 출처 |
|---|---|
| 4.5:1, 3:1, 비텍스트 3:1, 리플로 320px, 텍스트 간격, 200% 크기 조정, 타깃 24×24(AA)와 44×44(AAA), 포커스 표시와 가림 없음, 상호작용 애니메이션 | <https://www.w3.org/TR/2024/REC-WCAG22-20241212/> 및 그 Understanding 페이지 |
| WCAG 3는 Working Draft이고 대비 알고리즘은 미정이다; APCA는 규범이 아니다 | <https://www.w3.org/TR/2026/WD-wcag-3.0-20260910/>, <https://readtech.org/ARC/> |
| Apple 텍스트·컨트롤 크기(기본 44×44 pt, 최소 28×28 pt), "make motion optional" | <https://developer.apple.com/design/human-interface-guidelines/accessibility> |
| Android 터치 타깃 48×48 dp | <https://developer.android.com/guide/topics/ui/accessibility/apps> |
| Material 토큰 값(타입 스케일, 형태 0/4/8/12/16/28/full, 고도 단계, `cubic-bezier(0.2, 0, 0, 1)`) | <https://github.com/material-components/material-web/tree/main/tokens/versions/v0_192> (Apache-2.0) |
| 행 길이 45-90자, 행간 120-145%, 제목 수준 최대 세 단계 | <https://practicaltypography.com/line-length.html> |
| 비율 하한(타입 단계 1.25x, 제목 간격 1.5x, 그룹 간격 2x, 본문 65-75ch, 디스플레이 6rem, 자간 -0.04em)과 브라우저 표면 목록(`::selection`, 캐럿, 스크롤바, 포커스 링, 밑줄 간격, 숫자 형태) | `dbc-hbin/omp-ulw @ 74df40f` (2026-11-09)에서 이 패키지의 자체 말로 재작성했다. 원본 저장소에는 라이선스가 없으며 텍스트나 코드를 복사하지 않았다. 임계값은 그 프로젝트의 프런트엔드 표기 문서에 나온 Apache-2.0 상류(<https://github.com/pbakaus/impeccable>, Apache-2.0)에서 가져왔고, 여기서 하한 기본값으로 다시 정했다: 최소 타입 단계 1.25x, 디스플레이 최대 6rem, 자간 하한 -0.04em |
| 히트 타깃, `transition: all`, 중첩 반경, 자동 재생 일시 정지 | <https://github.com/vercel-labs/web-interface-guidelines/blob/434b7f91364665f2f733b310ec54809bf8f37937/AGENTS.md> (MIT) |
| UI 모션 300 ms 미만, ease-in 없음, `scale(0)` 없음, 30-80 ms 시차, 빈도 규칙 | <https://github.com/emilkowalski/skills> (commit `c8a7962`) (MIT) |
| 응답 시간 한계, 로딩 표시, 빈 상태, 오류 메시지, 폼 규칙 | <https://www.nngroup.com/articles/response-times-3-important-limits/>, <https://www.nngroup.com/articles/skeleton-screens/>, <https://www.nngroup.com/articles/empty-state-interface-design/>, <https://www.nngroup.com/articles/error-message-guidelines/>, <https://www.nngroup.com/articles/web-form-design/> |
| 오류 요약, 페이지당 질문 하나, 별표만으로 필수 표시하지 않기 | <https://design-system.service.gov.uk/components/error-summary/>, <https://design-system.service.gov.uk/patterns/question-pages/> (OGL v3.0) |
| 한국어 본문 기본 17px에 최소 16px, 행간 최소 150%, `keep-all`, 중단점 360/768/1024/1280, 강조색 최대 5% | <https://www.krds.go.kr/html/site/style/style_03.html> 및 같은 사이트의 스타일 페이지 |
| `word-break: keep-all` 동작 | <https://developer.mozilla.org/en-US/docs/Web/CSS/word-break> |
| Pretendard는 예약 글꼴 이름이 있는 SIL OFL 1.1이다 | <https://github.com/orioncactus/pretendard> |
| 색상 수 상한, 조작 단서 규칙(네이티브 요소, 이름, 포인터 커서, 서로 다른 상태), 확대 차단 금지, 터치 간격, 두 단계를 넘는 반응형 상태, `100vh` 대신 `dvh`, 간결한 고정 크롬, 글래스와 글로우 사용량 상한, 미디어 크기, 히어로 이미지 우선순위, 지연 로드 서드파티 스크립트, 측정하지 않은 수치를 보고하지 않기 | <https://github.com/miqdadbadjuber/anti-slop> (commit `9504989`, `antislop/SKILL.md` R-03, R-10, R-13, R-29, R-39, R-40; `antislop-layoutmobile/SKILL.md`; MIT) |
| 75번째 백분위 기준 Core Web Vitals 임계값 | <https://web.dev/articles/vitals> |

### Evidence grade

`MUST` 행은 WCAG 2.2 AA와 Level A 요구 사항을 다시 적은 것이며 표준만큼 강하다. `DEFAULT` 행은 출처가 주는 범위에서 값 하나를 고른다. 출처가 어긋나는 곳(Apple 28 pt 대 44 pt, 한국어에서 Butterick 120-145% 대 KRDS 150%)에서는 표가 어느 쪽을 적용하는지 밝힌다. 한국어 160-170% 범위는 긴 읽기를 위해 이 패키지가 고른 값이며 출처가 있는 숫자가 아니다.
