# 차단 신호

> 응답 자체에서 챌린지, 실패한 센서, 스텁을 알아보고, 어떤 WAF 제품이 실제 브라우저를 필요로 하는지 압니다.

## 1. 챌린지 표식

본문이나 제목에 다음이 있으면 상태 코드와 무관하게 `challenge`입니다.

| 제품 계열 | 본문·제목 표식 | 쿠키·헤더 신호 | 실제 브라우저 필요 |
|---|---|---|---|
| Cloudflare | `Just a moment...`, `Checking your browser`, `cf-chl-`, `Attention Required! \| Cloudflare` | `cf-ray`, `server: cloudflare`, `__cf_bm`, `cf_clearance` | `needs_js`(브라우저 엔진이면 통과, 실제 TLS는 불필요) |
| Akamai Bot Manager | `sec-if-cpt-container`, `Powered and protected by Akamai`, 참조 번호가 붙은 `Access Denied` | `_abck`, `bm_sz`, `ak_bmsc`, `server: AkamaiGHost` | `needs_real_browser`(실제 TLS 스택과 JavaScript 센서) |
| DataDome | `DataDome`, `captcha-delivery.com` | `datadome` 쿠키 | `needs_real_browser` |
| HUMAN (PerimeterX) | `px-captcha`, `Press & Hold to confirm you are a human` | `_px3`, `_pxhd`, `_px2` | `needs_real_browser` |
| F5 BIG-IP ASM | `The requested URL was rejected`, `support ID is:` | `BigIPServer*`, `TS01*` | `needs_real_tls` |
| AWS WAF | `awswaf`의 챌린지나 CAPTCHA 페이지 | `aws-waf-token`, `x-amzn-waf-*` | `needs_real_tls` |
| 알 수 없음 | JavaScript나 쿠키를 켜라고 요구하는 짧은 페이지, 또는 CAPTCHA 위젯 | 없음 | `needs_js`로 취급 |

그 행을 믿기 전에 신호를 두 개 이상 확인합니다. 신호가 하나면 잠정 일치입니다. 이 행들은 사이트가 아니라 제품을 설명합니다.

## 2. 실패한 센서 상태

| 신호 | 의미 |
|---|---|
| `_abck` 값에 `~-1~` 포함 | Akamai 센서 미완료 |
| Cloudflare 챌린지 페이지 뒤에 `cf_clearance` 없음 | 챌린지 통과 실패 |
| WAF 쿠키의 `Set-Cookie`와 3KB 미만 본문 | 챌린지가 나갔고 내용은 보류됨 |
| 같은 실행에서 앞서 본 챌린지 페이지 크기와 같은 200 본문 | 상태 코드만 다를 뿐 같은 챌린지 |

## 3. 스텁

| 스텁 | 알아보는 방법 |
|---|---|
| 리다이렉트 페이지 | 3KB 미만에 `<meta http-equiv="refresh">`나 `location` 스크립트가 있고, 차단된 호스트로 되돌림 |
| 검색 인터스티셜 | 캐시 URL에서 제목이 `Google Search` 같은 검색 홈. 구글 웹 캐시는 2024년에 끝났고 그 URL은 이제 검색 인터스티셜을 돌려줌(2026-11-07 관측: HTTP 200, 93,735바이트, 제목 `Google Search`) |
| 빈 JavaScript 껍데기 | `<div id="root"></div>`, `<div id="__next"></div>` 같은 루트 요소에 텍스트가 없고 스크립트 태그만 있음 |
| 동의 벽 | 선택 전에는 내용을 가리는 쿠키 동의 페이지 |
| AMP 캐시 리다이렉트 | AMP 캐시 호스트의 짧은 `Redirecting` 페이지가 클라이언트를 원본으로 되돌림 |
| 아카이브 호스트의 챌린지 본문 | 스냅숏 대신 챌린지 페이지가 본문인 아카이브 응답(2026-11-07에 재작성본 `web/<ts>/<url>`에서 한 번 관측, 몇 분 뒤에는 재현되지 않음). 축 하나를 바꿉니다: 원본 `web/<ts>id_/<url>` 경로나 다른 스냅숏 시각 |

## 4. 상태 코드

| 상태 | 첫 해석 | 다음 단계 |
|---|---|---|
| 401 | 인증 필요 | 계정이 사용자 것이 아니면 `rules/access-policy.md` §2 |
| 403 | 거부. 흔히 클라이언트 필터, 때로는 실제 차단 | 본문 표식을 봅니다. 챌린지 본문이면 tier 1 재시도 축, 정상 방문 뒤의 평범한 거부면 §2 |
| 407 | 프록시 인증 | 사이트가 아니라 네트워크 문제. 보고합니다 |
| 429 | 속도 제한 | `Retry-After`를 지킵니다. 즉시 재시도하지 않습니다 |
| 451 | 법적 차단 | 경계 밖 |
| 챌린지 본문이 붙은 503 | 장애가 아니라 챌린지 | `challenge`로 취급 |
| 000 또는 연결 리셋 | 이 네트워크에서 응답 없음 | 기록하고 다음 아카이브나 tier로 갑니다. 같은 요청을 반복하지 않습니다 |

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| 제품 표식, 쿠키 계열, 실제 TLS 필요 여부 | `code-yeongyu/oh-my-openagent`(`dev` 브랜치)의 `ultimate-browsing` 스킬, 2026-11-07에 읽음 |
| Google Cache 인터스티셜과 AMP 리다이렉트 스텁 | 같은 스킬, 그리고 2026-11-07에 이 저장소의 네트워크에서 한 측정 |
| Cloudflare 호스트의 `server: cloudflare`와 `cf-ray` 헤더 | 2026-11-07에 `https://www.cloudflare.com/` 측정 |
| 상태 코드 의미 | RFC 9110, <https://www.rfc-editor.org/rfc/rfc9110.html>; RFC 6585; RFC 7725 |
| 신호 두 개 규칙과 스텁 목록 | 이 패키지가 고른 설계이며 검증된 최적값이 아님 |
