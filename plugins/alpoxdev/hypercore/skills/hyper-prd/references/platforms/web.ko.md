# Web Platform Checklist

PRD에서 판정한 플랫폼에 웹이 포함될 때만 이 파일을 불러온다. 플랫폼 요구사항 블록과 출시 게이트 표를 채우는 항목을 소유한다. 지원 브라우저, 반응형 레이아웃, 접근성 적합성, Core Web Vitals, 세션 처리, 검색 노출이 여기에 해당한다.

## Contents

- How to use
- Supported browsers
- Responsive layout
- Accessibility
- Core Web Vitals
- Sessions and re-authentication
- Search visibility
- Release gate rule
- Sources

## How to use

- 항목을 플랫폼 요구사항 블록으로 옮기고 PRD의 문장으로 각각 답한다. 이 표를 PRD에 그대로 붙이지 않는다.
- 등급이 출시 게이트 표에 무엇이 들어가야 하는지를 정한다. `[M]`·`[M-조건]` 항목은 모두 결론을 적는다(해당, 비해당과 이유, `[확인 필요]`). `[G]` 항목은 제품에 관련 있을 때만 적는다.
- `[M-조건]` 항목은 문장 안에 조건을 밝힌다. 조건이 거짓이면 행을 지우지 않고 게이트 표에 "비해당"과 이유를 적는다.
- 쓴 그대로 검증할 수 없는 항목은 요구사항이 아니다. "접근성 지침을 준수한다"는 금지하고, 성공 기준과 관측 가능한 상태를 적는다.
- PRD의 모든 수치 목표에는 임계값, 측정 방법, 분위수를 함께 적는다. "충분히 빠르게"는 목표치가 아니다.
- 확인 날짜는 모든 행이 2026-11-07이다. 표준 개정, 브라우저 지원 기간, 지표 임계값은 바뀌므로 분기마다 각 행을 다시 확인하고 날짜를 갱신한다.

## Supported browsers

| Id | Grade | What the PRD must settle | Source | Checked |
|---|---|---|---|---|
| W1 | `[G]` | Baseline 하한: 지원 약속이 어느 Baseline 단계를 쓰는지(`newly available` 또는 `widely available`)와 그 단계가 출시일에 가리키는 브라우저·버전 집합을 적는다. 빌드가 기대는 웹 플랫폼 기능마다 그 단계를 어디서 확인하는지 기록한다. | https://web-platform-dx.github.io/baseline/ | 2026-11-07 |
| W2 | `[G]` | 하한 미만 동작: 오래된 브라우저의 방문자가 보는 것(필요 버전을 밝히는 안내 또는 읽기 전용 축소 화면)과 그 부족을 검출하는 확인을 적는다. | https://web-platform-dx.github.io/baseline/ | 2026-11-07 |

## Responsive layout

| Id | Grade | What the PRD must settle | Source | Checked |
|---|---|---|---|---|
| W3 | `[G]` | 콘텐츠 기준 중단점: 중단점마다 CSS 픽셀 단위의 콘텐츠 폭과 그 폭을 필요로 하는 콘텐츠 요소를 적는다. "Don't define breakpoints based on device classes": 중단점에 기기 이름이 들어가면 결함이다. | https://web.dev/articles/responsive-web-design-basics | 2026-11-07 |
| W4 | `[G]` | 지원 폭 범위: 레이아웃이 감당하는 뷰포트 최소·최대 폭을 CSS 픽셀로 적고, 그 범위 밖에서 페이지가 무엇을 하는지 적는다. 측정: 창 하나를 범위 전체에 걸쳐 연속으로 늘리고 레이아웃이 바뀌는 지점을 모두 기록한다. | https://web.dev/articles/responsive-web-design-basics | 2026-11-07 |

## Accessibility

| Id | Grade | What the PRD must settle | Source | Checked |
|---|---|---|---|---|
| W5 | `[M-조건]` | 조건: 법률, 규정, 공공 조달 규칙, 고객 계약이 WCAG 2.2 AA 적합성을 요구한다. 적합 수준, 적용 대상 페이지, 감사 기록(AA 성공 기준별 통과·실패 하나씩)을 적는다. | https://www.w3.org/TR/WCAG22/ (5.2.1 Conformance Level) | 2026-11-07 |
| W6 | `[M-조건]` | 조건: 법률, 규정, 조달 규칙, 계약이 WCAG 2.2 AA 적합성을 요구한다. 포인터 대상은 100% 확대에서 가로·세로 각각 24 CSS 픽셀 이상이다. 대상이 그보다 작으면 다섯 예외 중 무엇이 적용되는지 적는다: Spacing(작은 대상의 경계 상자마다 지름 24 CSS 픽셀 원을 그렸을 때 다른 대상이나 다른 작은 대상의 원과 겹치지 않게 배치), Equivalent(같은 페이지에서 기준을 만족하는 다른 컨트롤로 같은 기능을 할 수 있음), Inline(대상이 문장 안에 있거나 대상이 아닌 텍스트의 줄 높이 때문에 크기가 제약됨), User Agent Control(크기가 사용자 에이전트가 정하고 저자가 바꾸지 않음), Essential(그 대상의 특정 표현이 정보 전달에 본질적이거나 법이 요구함). 임계값: 24×24 CSS px. 측정: 상호작용 대상마다 렌더된 상자를 잰다. | https://www.w3.org/TR/WCAG22/ (2.5.8 Target Size (Minimum)) | 2026-11-07 |
| W7 | `[M-조건]` | 조건: 같은 WCAG 2.2 AA 의무. A·AA 수준의 나머지 신규 기준 다섯 개에 각각 결론을 적는다: 2.4.11 Focus Not Obscured (Minimum) AA, 2.5.7 Dragging Movements AA, 3.2.6 Consistent Help A, 3.3.7 Redundant Entry A, 3.3.8 Accessible Authentication (Minimum) AA. | https://www.w3.org/TR/WCAG22/ | 2026-11-07 |

## Core Web Vitals

페이지 그룹의 필드 데이터를 모바일과 데스크톱으로 나눠 보고한다. 값마다 페이지 로드 75백분위수(p75)를, 자체 실사용자 모니터링이나 CrUX 데이터셋에서 얻어 적는다. 필드 데이터 출처의 집계 창은 PRD가 적는다. 실험실 측정은 빌드 시점 확인이지 게이트 값이 아니다.

| Id | Grade | What the PRD must settle | Source | Checked |
|---|---|---|---|---|
| W8 | `[G]` | Largest Contentful Paint: 임계값 LCP ≤ 2.5s @p75, 모바일과 데스크톱 분리. 측정: 페이지 그룹 필드 데이터, 페이지 로드 p75, PRD가 적은 집계 창. | https://web.dev/articles/vitals | 2026-11-07 |
| W9 | `[G]` | Interaction to Next Paint: 임계값 INP ≤ 200ms @p75, 모바일과 데스크톱 분리. 측정: 페이지 그룹 필드 데이터, 페이지 로드 p75, PRD가 적은 집계 창. | https://web.dev/articles/vitals | 2026-11-07 |
| W10 | `[G]` | Cumulative Layout Shift: 임계값 CLS ≤ 0.1 @p75, 모바일과 데스크톱 분리, 단위 없는 점수. 측정: 페이지 그룹 필드 데이터, 페이지 로드 p75, PRD가 적은 집계 창. | https://web.dev/articles/vitals | 2026-11-07 |

## Sessions and re-authentication

| Id | Grade | What the PRD must settle | Source | Checked |
|---|---|---|---|---|
| W11 | `[G]` | 타임아웃: 유휴 타임아웃을 분 단위로, 절대 타임아웃을 시간 단위로 적고, 세션이 닿을 수 있는 대상의 위험도로 그 값을 정한다. 재인증을 강제하는 동작(비밀번호 변경, 이메일 주소 변경, 결제, 관리자 동작)을 나열한다. 측정: 시험 세션을 유휴 타임아웃 너머로 두고 재인증 요구가 뜨는지 확인하고, 절대 타임아웃 뒤 민감 동작 하나를 실행해 거부되는지 확인한다. | https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html (Idle Timeout, Absolute Timeout) | 2026-11-07 |
| W12 | `[G]` | 갱신과 무효화: 세션 식별자는 로그인과 권한 변경 시점에 바뀌고, 로그아웃은 브라우저에서만이 아니라 서버에서 세션을 무효화한다. 측정: 로그인 전, 로그인 뒤, 권한 변경 뒤에 식별자를 잡아 매번 바뀌었는지 확인하고, 로그아웃 전 값을 이후에 거부하는지 확인한다. | https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html (Renew the Session ID, Logout) | 2026-11-07 |

## Search visibility

| Id | Grade | What the PRD must settle | Source | Checked |
|---|---|---|---|---|
| W13 | `[G]` | 크롤링과 색인 가능: 색인 대상 페이지 템플릿마다 200을 반환하고, 핵심 콘텐츠를 응답 HTML에 담고, 링크로 도달할 수 있으며, `robots.txt`나 `noindex` 지시로 막히지 않는다. 측정: 템플릿마다 URL 하나를 크롤러로 요청해 상태 코드, 지시, 렌더된 텍스트를 기록한다. | https://developers.google.com/search/docs/essentials | 2026-11-07 |
| W14 | `[G]` | 메타데이터와 발견: 색인 대상 템플릿마다 고유한 제목과 설명, 정규 URL 하나, 제출한 사이트맵 항목 하나를 갖는다. 측정: 템플릿을 나열하고 템플릿마다 URL 하나의 제목, 설명, 정규 URL, 사이트맵 항목을 기록한다. | https://developers.google.com/search/docs/essentials | 2026-11-07 |

## Release gate rule

위의 `[M]`·`[M-조건]` 행은 모두 PRD 출시 게이트 표에 결론 하나와 함께 들어간다.

| Conclusion | When to write it |
|---|---|
| 해당 | 의무가 성립하고, PRD가 그것을 만족하는 관측 가능한 상태를 적는다. |
| 비해당 + 이유 | 조건이 거짓이다(접근성 의무 없음, 다른 채널). 이유는 그 결정을 밝힌다. |
| `[확인 필요]` | 답이 저장소나 대화에 없다. 누가 답하는지 적는다. |

## Sources

> 확인 2026-11-07.

| Claim | Source |
|---|---|
| WCAG 2.2 AA의 포인터 대상 최소 크기 | [WCAG 2.2](https://www.w3.org/TR/WCAG22/) - "The size of the target for pointer inputs is at least 24 by 24 CSS pixels" |
| 2.5.8의 다섯 예외 | [WCAG 2.2](https://www.w3.org/TR/WCAG22/) - "The size of the target for pointer inputs is at least 24 by 24 CSS pixels, except when:" 뒤에 Spacing, Equivalent, Inline, User Agent Control, Essential |
| 중단점은 기기 분류가 아니라 콘텐츠를 따른다 | [Responsive web design basics](https://web.dev/articles/responsive-web-design-basics) - "Don't define breakpoints based on device classes" |
| Core Web Vitals 임계값과 p75 필드 측정 | [Web Vitals](https://web.dev/articles/vitals) - "a good threshold to measure is the 75th percentile of page loads, segmented across mobile and desktop devices" |
| Baseline 단계와 단계별 브라우저 집합 | [Baseline](https://web-platform-dx.github.io/baseline/) |
| 세션 타임아웃, 갱신, 무효화 | [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html) |
| 크롤링, 색인, 페이지 메타데이터 | [Google Search Essentials](https://developers.google.com/search/docs/essentials) |

### Evidence grade

`LOCAL` - ID 체계, 등급, 출시 게이트 규칙은 위 출처를 조합한 이 패키지의 설계다. WCAG 문장과 중단점 문장은 나열한 문서에서 그대로 인용했고, 지표 임계값은 Web Vitals 문서를 따랐다. 표준 개정과 지표 임계값은 바뀌므로 출시 게이트를 승인하기 전에 분기마다 인용문과 2026-11-07 확인 날짜를 다시 검증해야 한다.
