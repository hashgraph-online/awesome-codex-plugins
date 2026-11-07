# 접근 사다리

> 대상을 분류하고, 그 대상에 닿을 수 있는 가장 싼 tier에서 시작하며, 다시 시도할 때는 축 하나만 바꾸고, tier가 통과할 수 없을 때만 오릅니다.

## 1. 대상 분류

첫 요청 전에 네 가지 질문에 답하고 분류 줄로 출력합니다.

| 질문 | 값 | 판단 방법 |
|---|---|---|
| 플랫폼 | `official-endpoint`, `media`, `generic` | `references/public-endpoints.md`에 그 호스트가 있으면 `official-endpoint`, 대상이 영상·음성·팟캐스트 항목이면 `media`, 나머지는 `generic` |
| 모양 | `single`, `bulk` | 여러 항목, 페이지네이션, "전부", "모두", "크롤링", "N개 이상", 사이트 한 구역 전체를 요청하면 `bulk` |
| 신선도 | `live-required`, `copy-acceptable` | 페이지가 사라졌거나 지워졌거나, 사용자가 과거 날짜를 묻거나, 아카이브 사본을 받아들일 때 `copy-acceptable`, 나머지는 `live-required` |
| 권한 | `public`, `own-account`, `outside` | `rules/access-policy.md` §1과 §2 |

`outside`로 분류한 대상은 여기서 멈추고 종료 상태 `needs_user`나 `blocked`로 끝냅니다(`rules/access-policy.md` §2). `bulk` 대상은 tier 1 전에 대량 게이트(`rules/access-policy.md` §3)를 통과합니다.

키워드만 있는 요청("X에서 AI 관련 글")은 아직 대상이 없습니다. 검색 기능으로 URL을 먼저 얻고 그 URL을 분류합니다. 검색 결과 목록만으로는 이 스킬의 결과물이 되지 않습니다.

## 2. Tier

tier는 이 순서로 실행합니다. 해당 행의 사유가 있을 때만 건너뛰고, 건너뛴 사실을 기록에 남깁니다.

| Tier | 방법 | 쓰는 때 | 건너뛰는 때 |
|---|---|---|---|
| 0 | 같은 플랫폼의 공식 공개 엔드포인트(JSON, Atom, oEmbed, syndication, 레지스트리 API) | 플랫폼이 `official-endpoint` | 요청한 내용을 다루는 엔드포인트가 없음 |
| 1 | 헤드리스 요청 격자: 브라우저 같은 헤더의 평범한 curl, 그다음 URL 변형, referer 전략, 기기 종류, 클라이언트 지문 위장(curl_cffi가 있을 때), 리더, 구조화 메타데이터 추출, 피드 발견, `media`면 미디어 추출기 | `generic`과 `media`에서 항상, tier 0이 실패한 뒤 | 앞 tier가 받아들여짐 |
| 2 | 아카이브 사본: Wayback availability 조회, 그다음 다른 아카이브 | 신선도가 `copy-acceptable` | 신선도가 `live-required`. tier 3·4가 실패하거나 건너뛰어지면 사본을 한 번 제안하고, 사용자가 받아들일 때만 tier 2를 실행 |
| 3 | 자체 브라우저: 실행이 새 작업 전용 프로필로 직접 띄우는 브라우저. 헤드리스 우선, 런타임 자체의 브라우저 기능으로 실행 | tier 1과 tier 2가 실패했거나 건너뛰어졌거나, 내용에 JavaScript, 클릭, 스크롤, 미디어 재생, 스크린샷이 필요함 | 브라우저 자동화 기능이 없음: `skipped`로 표시하고 `blocked`나 `fetched_partial`로 끝냄 |
| 4 | 연결 브라우저: 사용자가 이미 로그인한 본인 브라우저를 런타임의 연결 기능으로 조작 | 권한이 `own-account`이거나, 모든 자체 브라우저가 막혀 사용자가 본인 브라우저에서 열기로 동의함 | 연결 기능이 없거나, 로그인·챌린지 단계에 사용자가 함께 있지 않음 |

`references/headless-recipes.md`에 tier 1·2 명령이, `references/public-endpoints.md`에 tier 0이, `references/browser-tier.md`에 tier 3·4가 있습니다.

## 3. 한도

| Tier | 시도 한도 | 일찍 떠나는 때 |
|---|---|---|
| 0 | 대상마다 엔드포인트 호출 2회 | 엔드포인트가 401, 403, 문서화된 "인증 필요" 오류를 두 번 돌려줌 |
| 1 | 대상마다 12회 | 서로 다른 축을 바꾼 세 번의 연속 시도가 `references/block-signals.md`에서 `needs_js`나 `needs_real_browser`인 제품의 같은 챌린지를 돌려줌. `needs_real_tls` 제품은 모든 위장 계열을 시도한 뒤에만 떠남 |
| 2 | Wayback 조회 1회와 스냅숏 요청 1회, 그다음 다른 아카이브마다 1회 | 모든 아카이브가 스냅숏 없음, 타임아웃, 스텁을 돌려줌 |
| 3 | 브라우저 세션 1회, 탐색 최대 3회 | 렌더링한 페이지가 새로 고침 한 번과 10초 대기 뒤에도 챌린지를 보여 줌 |
| 4 | 연결 세션 1회 | 사용자가 거절하거나, 로그인·챌린지 단계에 사용자가 필요한데 함께 있지 않음 |

`bulk` 실행은 항목마다 이 한도를 적용하고 `rules/access-policy.md` §3의 페이지 상한과 속도를 더합니다. 통과를 강제하려고 한도를 올리지 않습니다. 다 쓴 한도를 보고합니다.

## 4. 재시도 축

tier 안의 재시도는 직전 시도에서 축 하나만 바꾸고 기록의 `method` 열에 적습니다.

| 축 | 값 | 비고 |
|---|---|---|
| URL 변형 | 원본, 모바일 호스트(`www.`를 `m.`로), `www.` 제거, 페이지가 스스로 연결할 때만 AMP나 인쇄 경로 | 같은 내용을 주는 변형만 셉니다. 제목이나 canonical 링크로 확인합니다 |
| 클라이언트 지문 | curl 기본, 그다음 계열별 curl_cffi 위장 대상(Safari, Safari iOS, Chrome, Chrome Android, Firefox) | curl_cffi는 이미 설치됐거나 작업 전용 가상 환경에 설치할 때만 씁니다. 시스템이나 사용자 Python에는 설치하지 않습니다 |
| Referer | 없음, 사이트 자체 루트, 검색 엔진 referer | referer는 헤더 선택이지 신원 주장이 아닙니다. 쿠키는 절대 더하지 않습니다 |
| 기기 종류 | 데스크톱, 모바일 | 모바일은 모바일 사용자 에이전트, 모바일 호스트 변형과 짝을 이룹니다 |
| 리더 | 페이지를 텍스트로 렌더링하는 리더 서비스 | 결과는 출처 `reader`입니다. 리더에 쿠키나 인가를 보내지 않습니다 |

## 5. 상승 규칙

- HTTP 200은 증명 검사의 시작이며 그 자체로 tier를 끝내지 않습니다(`rules/evidence-and-report.md` §1).
- `references/block-signals.md`의 행이 `needs_js`나 `needs_real_browser`라고 밝힌 제품에서 `challenge` 판정이 나오면 §3의 일찍 떠나기 조건으로 tier 1을 끝냅니다. 신선도가 사본을 허용하면 tier 2로, 아니면 tier 3으로 갑니다.
- `stub` 판정(리다이렉트 페이지, 인터스티셜, 원본으로 되돌리는 캐시 껍데기)은 성공으로 세지 않고 tier를 일찍 끝내지도 않습니다.
- tier 3에서는 내용이 데이터(상품 목록, 피드, 검색 결과)일 때 DOM보다 페이지 자신의 JSON 호출을 먼저 봅니다. 네트워크 요청을 잡은 뒤 그 JSON URL을 tier 1로 다시 요청합니다. API 층은 HTML보다 방어가 얕은 경우가 많습니다.
- `bulk` 대상은 첫 항목에서 통하는 경로 하나를 찾은 뒤 나머지에 그 경로를 다시 씁니다. 실패한 항목에만 다시 오릅니다.
- 첫 `strong_ok` 시도에서 멈춥니다. `weak_ok` 시도는 남겨 두고, 한도 안에서 같은 tier의 다른 축 하나나 다음 tier를 실행한 뒤 더 나은 결과를 받아들입니다. 끝까지 `weak_ok`이면 `fetched_partial`입니다.

## 6. 사이트 이름 금지 규칙

이 패키지의 규칙에는 특정 사이트의 선택자, 바이트 크기, 쿠키 값, 특이 동작을 저장하지 않습니다. 사이트의 성공 선택자, 선호 referer, 통하는 변형은 이번 실행에만 쓰는 입력입니다. 플랫폼 이름은 참조 문서에 예시로, 그리고 공식 엔드포인트 색인으로만 나옵니다.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| tier 순서, 12회 격자, 재시도 축(URL 변환, TLS 위장, referer, 기기 종류), 네트워크 요청을 잡아 API를 먼저 치는 분기, 사이트 이름 금지 규칙 | `code-yeongyu/oh-my-openagent`(`dev` 브랜치)의 `ultimate-browsing` 스킬, 2026-11-07에 읽음 |
| curl_cffi 브라우저 위장 대상 | <https://pypi.org/project/curl-cffi/>, 2026-11-07에 확인한 0.17.0 |
| tier별 한도, 축 하나만 바꾸는 재시도 규칙, 일찍 떠나기 조건 | 이 패키지가 고른 설계이며 검증된 최적값이 아님 |
