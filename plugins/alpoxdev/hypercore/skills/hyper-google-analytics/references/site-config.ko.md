# 사이트 설정

CSP 항목, 교차 도메인 질문, 내부·개발자 트래픽 필터, 원치 않는 추천, 향상된 측정 토글에서 이 참조를 읽습니다. 최소 CSP 지시문, 링커, 트래픽 필터, 추천 목록, 향상된 측정 스위치를 소유합니다.

> 영어판: [`site-config.md`](site-config.md)

## Contents

- CSP minimum
- Cross-domain linker
- Internal and developer traffic
- Unwanted referrals
- Enhanced measurement

## CSP minimum

GA만 쓰는 속성에는 다음 지시문이 필요합니다. 그 밖의 항목은 다른 업체 몫이며 이 스킬 범위 밖입니다.

```
Content-Security-Policy:
  script-src-elem https://www.googletagmanager.com 'nonce-{SERVER-GENERATED-NONCE}';
  img-src https://www.googletagmanager.com https://*.google-analytics.com;
  connect-src https://www.googletagmanager.com https://*.google-analytics.com https://*.google.com;
```

- 인라인 컨테이너 코드에는 자체 허용이 필요하고, "권장 방법은 nonce를 쓰는 것입니다". `script-src-elem`에 `'nonce-<값>'`을 쓰고 스니펫의 `nonce` 속성에 같은 값을 렌더합니다.
- 컨테이너가 프레임을 렌더하면 `frame-src https://www.googletagmanager.com`을 더합니다.
- `'unsafe-eval'`은 Custom JavaScript 변수에만 필요하고, 그것이 없으면 그 변수는 "CSP가 있는 환경에서 `undefined`로 평가됩니다". 정책을 푸는 대신 Custom Templates가 대안입니다.
- 미리보기 모드에는 호스트가 더 필요합니다. `tagmanager.google.com`, `fonts.googleapis.com`, `ssl.gstatic.com`, `fonts.gstatic.com`, `data:`입니다. 미리보기 환경에만 더합니다.
- 요청을 통과시키려고 지시문을 빼는 것은 수리가 아닙니다. 발견 사항은 빠진 지시문이고, 수리는 그 요청을 만족하는 가장 좁은 호스트입니다.
- nonce는 일부 프레임워크에서 동적 렌더링을 강제합니다. nonce 방식을 권하기 전에 그 비용을 밝히고, 스니펫이 정적이면 해시 기반 정책이 대안입니다.

## Cross-domain linker

- 링커는 `_gl`이라는 URL 매개변수로 같은 클라이언트·세션 식별자를 도메인 사이에 넘기므로, 두 도메인 모두 같은 `G-` 측정 ID를 돌려야 합니다.
- "Linker parameters expire after two minutes." 방문자가 착지해 기다렸다가 클릭해 넘어가면 장식 없이 도착해 두 번째 도메인에서 새 세션이 됩니다.
- `gtag('set', 'linker', { domains: [...] })`는 config 호출보다 앞서야 합니다. 옵션은 `accept_incoming`(domains가 있으면 기본 true), `decorate_forms`(기본 false), `url_position`(`query` 또는 `fragment`)입니다.
- 한 도메인 설정에 조건을 100개까지 나열할 수 있고, 그 묶음의 모든 도메인에 같은 측정 ID가 있어야 합니다.
- 확인할 실패 형태는 쿼리 문자열을 떼는 리다이렉트, `Event.stopPropagation()`을 부르는 핸들러, 스크립트로 수행하는 이동입니다. 각각 `_gl`을 떨어뜨려 두 번째 도메인을 추천으로 보이게 합니다.

## Internal and developer traffic

- **내부 트래픽**은 두 부분으로 동작합니다. IP 일치(CIDR이나 정규식 지원)로 규칙을 정의해 `traffic_type=internal`을 붙이고, 그다음 Testing, Active, Inactive 상태를 가진 데이터 필터를 둡니다.
- **개발자 트래픽**은 디버그 모드가 켜진 이벤트를 제외하는 별도 필터입니다. 사이트 자체 시험에는 이 필터를 쓰고, 디버그 트래픽을 내부 트래픽 규칙에 섞지 않습니다.
- 속성이 실제로 강제하는 한도와 효과입니다. 속성당 데이터 필터 10개까지, 활성화한 뒤 수집되는 데이터에 "효과는 영구적", 적용에 24시간에서 36시간.
- 필터 활성화는 승인 등급 행동입니다. 속성, 필터 이름, 상태 변화, 24~36시간 대기, 이미 수집한 데이터에는 효과를 되돌릴 수 없다는 사실을 밝힌 뒤 기다립니다.
- Testing 상태는 필터 효과를 영구 적용 없이 보여 줍니다. 먼저 이것을 권합니다.
- 호스트 이름 Include 필터는 일부 구성에서 gtag.js 트래픽처럼 호스트 이름이 빈 이벤트를 차단하고, Measurement Protocol 이벤트에는 적용되지 않습니다. 빠진 데이터를 내부 트래픽으로 보고하기 전에 규칙의 방향을 확인합니다.

## Unwanted referrals

- 데이터 스트림 하나에 원치 않는 추천을 50개까지 둘 수 있습니다.
- 목록 항목마다 일치하는 세션에 `ignore_referrer=true`를 붙이고, "`ignore_referrer` 매개변수는 어떤 값이든 같은 동작을 냅니다".
- 흔한 항목은 방문자를 돌려보내는 결제 대행사, 이미 교차 도메인 묶음에 든 형제 도메인, 스테이징 호스트입니다.
- 목록 항목을 더하기 전에 자기 추천을 확인합니다. 다른 쿠키 도메인을 쓰는 하위 도메인이 자기 추천을 만들고, 수리는 추천 목록을 늘리는 것이 아니라 쿠키 도메인이나 교차 도메인 묶음입니다.
- 경계를 넘는 세션을 잡아 추천 소스가 돌아온 호스트가 아님을 확인해 검증합니다.

## Enhanced measurement

웹 데이터 스트림에 스위치 일곱 개가 있고 각각 따로 제어합니다.

| Switch | Event | Trigger |
|---|---|---|
| 페이지 조회 | `page_view` | 페이지 로드, 히스토리 옵션이 켜져 있으면 브라우저 히스토리 상태 변경 |
| 스크롤 | `scroll` | 세로 90% 깊이 |
| 외부 링크 클릭 | `click` | 다른 도메인으로 가는 클릭 |
| 사이트 검색 | `view_search_results` | 쿼리 키 `q`, `s`, `search`, `query`, `keyword` |
| 동영상 참여 | `video_start`, `video_progress`, `video_complete` | 10, 25, 50, 75% |
| 파일 다운로드 | `file_download` | `pdf`, `xlsx?`, `docx?`, `pptx?`, `zip`, `mp4`, `mp3`, `wav` 등 확장자 |
| 양식 상호작용 | `form_start`, `form_submit` | 첫 필드 상호작용, 그다음 제출 |

- 페이지 로드에서 오는 `page_view`는 끌 수 없습니다. "수집을 끌 수 없습니다." 전환 가능한 부분은 히스토리 옵션이고, SPA 중복 집계를 만드는 스위치도 그것입니다.
- 단일 페이지 앱에서는 출처를 하나 고릅니다. 페이지 로드와 히스토리 페이지뷰를 모두 켜 두고 손으로 아무것도 보내지 않거나, 히스토리 옵션을 끄고 `page_view`를 직접 보냅니다. 둘 다는 아닙니다.
- 향상된 측정 변경에는 코드가 필요 없고, 토글은 이미 페이지에 있는 태그에 곧바로 적용됩니다. 바꾼 뒤에는 리포트가 아니라 새 요청으로 검증합니다.
- 사이트가 같은 이벤트를 직접 보낼 때만 스위치를 끄고, 어느 스위치가 왜 옮겨 갔는지 보고서에 적습니다.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| GA 전용 CSP는 `googletagmanager.com`용 `script-src-elem`, `*.google-analytics.com`용 `img-src`와 `connect-src`, 인라인 컨테이너 코드용 nonce가 필요합니다 | <https://developers.google.com/tag-platform/security/guides/csp> |
| `'unsafe-eval'`은 Custom JavaScript 변수에만 필요하고 미리보기 모드에는 호스트가 더 필요합니다 | <https://developers.google.com/tag-platform/security/guides/csp> |
| 링커는 `_gl`로 식별자를 넘기고 조건 100개까지이며, 링커 매개변수는 2분 뒤 만료합니다 | <https://developers.google.com/tag-platform/devguides/cross-domain> |
| `linker` 옵션은 `accept_incoming`, `decorate_forms`, `url_position`이고 `set`이 `config`보다 앞서야 합니다 | <https://developers.google.com/tag-platform/devguides/cross-domain> |
| 내부 트래픽은 `traffic_type`을 붙이고, 필터는 Testing·Active·Inactive 상태와 속성당 10개 한도, 영구 효과, 24~36시간 적용을 가집니다 | <https://support.google.com/analytics/answer/10104470> |
| 개발자 트래픽 필터는 디버그 모드로 보낸 이벤트를 제외합니다 | <https://support.google.com/analytics/answer/13296662> |
| 스트림당 원치 않는 추천 50개까지이고 `ignore_referrer`는 어떤 값이든 같은 동작입니다 | <https://support.google.com/analytics/answer/10327750> |
| 하위 도메인 자기 추천은 다른 쿠키 도메인에서 오고 쿠키 도메인이나 교차 도메인 설정으로 고칩니다 | <https://support.google.com/analytics/answer/10071811> |
| 향상된 측정 스위치 일곱 개와 그 이벤트, 페이지 로드 `page_view`를 끌 수 없다는 점 | <https://support.google.com/analytics/answer/9216061> |
| 히스토리 옵션은 페이지 조회 고급 설정에 있고, 자동 히스토리 추적과 태그 관리자 히스토리 트리거를 함께 켜면 중복 집계됩니다 | <https://developers.google.com/analytics/devguides/collection/ga4/single-page-applications> |

### Evidence grade

지시문 목록, 링커 동작과 만료, 필터 한도와 소요 시간, 추천 상한, 스위치 일곱 개는 위 페이지를 2026-11-08에 읽은 `MEASURED`입니다. Testing 상태를 먼저 권하는 것과 빠진 데이터를 보고하기 전에 필터 방향을 확인하라는 규칙은 Google 지시가 아니라 이 패키지의 `LOCAL` 관행입니다.
