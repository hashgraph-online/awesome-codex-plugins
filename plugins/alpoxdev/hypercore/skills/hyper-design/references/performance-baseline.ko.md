# 성능과 페이지 기준

페이지를 운영용으로 만들 때, 발견 사항이 레이아웃 이동이나 느린 첫 페인트, 서드파티 스크립트에 관한 것일 때, 사용자가 웹 품질 검토를 요청할 때 읽는다. 정석 수치 기준(`rules/craft-floor.md` §8)이 모든 페이지가 지키는 메커니즘을 담고 이 파일은 실사용 임계값과 선택 기준 목록을 담는다.

## 1. Core Web Vitals

실제 방문의 75번째 백분위 실사용 데이터다.

| 측정 항목 | 양호 | 개선 필요 | 나쁨 |
|---|---|---|---|
| LCP(가장 큰 콘텐츠 페인트) | 최대 2.5초 | 2.5-4초 | 4초 초과 |
| INP(다음 페인트까지 상호작용) | 최대 200ms | 200-500ms | 500ms 초과 |
| CLS(누적 레이아웃 이동) | 최대 0.1 | 0.1-0.25 | 0.25 초과 |

- 페이지를 쓰는 에이전트에게는 실사용 데이터가 없다. 소스만 보고는 유력한 원인을 지목할 수 있지만 측정 항목이 통과한다거나 실패한다고 주장하지 않는다.
- 측정 순서는 실사용 데이터가 있을 때 p75(페이지 수준인지 출처 수준인지 밝힌다), 그다음 조건을 밝힌 랩 추적, 그다음 실패한 측정 항목의 원인만, 그다음 수정 뒤 랩 재실행이다. 랩 값 하나를 실사용 p75와 비교하지 않는다.
- 이번 실행에서 측정하지 않은 수치는 `not measured`로 쓴다.

## 2. 코드에서 보이는 메커니즘

| 문제 | 수정 |
|---|---|
| 크기 없는 미디어가 레이아웃을 흔든다(`quality.media-unsized`) | 모든 `img`, `video`, `iframe`에 `width`와 `height` 또는 `aspect-ratio`; 임베드와 늦은 배너 자리를 미리 잡는다; 배너는 콘텐츠 위에 삽입하지 말고 겹쳐 놓는다 |
| 히어로 이미지가 지연 로드이거나 CSS 배경이거나 스크립트로 주입된다 | HTML의 `img`에 `fetchpriority="high"`를 주고 `loading="lazy"`를 쓰지 않는다; 첫 화면 아래만 지연 로드한다; 추적에서 발견이 늦을 때만 preload한다 |
| `<head>`에 동기 분석, 채팅, 태그 관리 스크립트가 있다 | `defer`, `async`를 쓰거나 상호작용 시 로드한다 |
| 늦게 도착한 웹 폰트가 레이아웃을 바꾼다 | `font-display: swap`과 메트릭이 맞는 폴백; 쓰는 굵기만 제공한다 |
| 이미지 크기나 형식이 틀렸다 | 표시 크기에 맞는 AVIF나 WebP를 `srcset`과 함께 제공한다 |

## 3. 선택 페이지 기준

운영 준비가 끝난 페이지나 웹 품질 검토에 실행한다. 스크린샷에는 하나도 보이지 않는다.

- 문서: `<!doctype html>`이 맨 앞; `<meta charset="utf-8">`이 `<head>`의 맨 앞; viewport는 `width=device-width, initial-scale=1`에 확대 허용; 중복 `id` 없음.
- 런타임: `document.write`, 동기 XHR, `unload` 핸들러 없음; 스크롤과 터치 리스너는 `preventDefault()`를 호출하지 않는 한 `{ passive: true }`; 콘솔 오류 없음.
- 보안: 모든 리소스가 HTTPS이고 혼합 `http://` 콘텐츠 없음; 새 탭을 여는 외부 링크에 `rel="noopener noreferrer"`; 클라이언트 코드에 비밀번호나 API 키 없음; 신뢰할 수 없는 입력에 `innerHTML`이나 `eval` 대신 `textContent`나 정리기(sanitizer) 사용; 서드파티 CDN 스크립트와 스타일에 하위 리소스 무결성; 권한 요청은 사용자 동작 뒤에만.

## Sources

> 확인 2026-11-07.

| 주장 | 출처 |
|---|---|
| 75번째 백분위 기준 LCP, INP, CLS 임계값 | <https://web.dev/articles/vitals> |
| 측정 순서, "소스만으로 주장하지 않는다", 기준 목록 | <https://github.com/miqdadbadjuber/anti-slop> (commit `9504989`, `antislop-ui/references/CORE-WEB-VITALS.md` and `WEB-BASELINE.md`, adapted there from <https://github.com/addyosmani/web-quality-skills>; MIT, Copyright 2026 Miqdad Badjuber and Copyright 2026 Addy Osmani), 이 패키지용으로 다시 작성 |
| LCP 이미지에 `fetchpriority`를 주고 지연 로드하지 않기 | <https://web.dev/articles/optimize-lcp> |

### Evidence grade

임계값은 Google이 공개한 정의이며 드물게 바뀐다. 브라우저별 기능(추측 규칙, 우선순위 힌트 지원)은 더 빨리 바뀌므로 의도적으로 넣지 않았다.
