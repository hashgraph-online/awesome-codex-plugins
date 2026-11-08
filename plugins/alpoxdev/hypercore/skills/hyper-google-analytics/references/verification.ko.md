# 검증

실행이 수집을 증명해야 하거나 데이터가 빠진 이유를 설명해야 할 때 이 참조를 읽습니다. 전송 계층 점검, 디버그 화면, Measurement Protocol 검증 경로, 진단 순서, 리포트가 증명할 수 있는 것의 경계를 소유합니다.

> 영어판: [`verification.md`](verification.md)

## Contents

- The one rule
- `/g/collect`
- DebugView
- Tag Assistant
- Realtime
- Measurement Protocol validation
- The diagnose order

## The one rule

수집 주장은 리포트가 아니라 전송 관측에 기댑니다. standard reports는 뒤늦게 집계되는 값이라 이번 실행에 대해 아무것도 증명하지 못합니다. **standard reports는 수집 증명이 아닙니다.** 처리에 24시간에서 48시간이 걸리므로, 빈 리포트는 태그가 고장 난 경우와 정상 동작 중인데 아직 처리되지 않은 경우 모두와 들어맞습니다. "데이터가 없으니 태그가 고장 났다"로 발견 사항을 열지 않고, 리포트 숫자가 바뀌었다는 이유로 수리를 완료로 닫지 않습니다.

받아들이는 증명 네 가지이며, 시도하는 순서대로입니다.

1. `tid`가 속성의 측정 ID이고 `en`이 기대한 이벤트인 `/g/collect` 요청이 `200`이나 `204`로 응답한 것
2. 이번 실행이 시작한 세션에서 DebugView가 그 이벤트와 매개변수를 보여 주는 것
3. 실시간 리포트가 분 단위 창 안에서 그 이벤트를 보여 주는 것
4. 서버 측 전송이면 `validationMessages`가 빈 `/debug/mp/collect` 응답

Admin API read-back은 설정을 증명하지 수집을 증명하지 않습니다. `/mp/collect`의 `2xx`는 요청이 접수됐다는 뜻이지 이벤트가 존재한다는 뜻이 아닙니다.

## `/g/collect`

- 엔드포인트는 `google-analytics.com/g/collect`와 `analytics.google.com/g/collect`입니다. "`200 OK`나 `204 No Content` 상태 코드는 전송 성공을 뜻합니다."
- 네트워크 패널이나 프록시에서 엔드포인트로 걸러 잡고, 세 가지를 기록합니다. 쿼리가 붙은 URL, 응답 상태, 시각입니다.
- 엔드포인트 선택이 중요합니다. 서드파티나 프록시 호스트로 간 요청은 Google로 간 요청과 다른 발견 사항입니다. 게이트웨이나 Partytown 구성은 호스트를 의도적으로 바꾸기 때문입니다.
- 캡처는 페이지 로드 하나나 상호작용 하나로 제한합니다. 재생 루프는 속성의 이벤트 물량을 부풀려 다음 관측을 신뢰할 수 없게 만듭니다.

쿼리 문자열에는 히트를 식별하고 설명하는 필드가 실립니다. 이것은 관측된 필드이며 공개된 계약이 아닙니다.

| Field | Observed meaning |
|---|---|
| `tid` | 측정 ID(`G-`) |
| `en` | 이벤트 이름, 예를 들어 `page_view` |
| `cid` | 클라이언트 식별자 |
| `ep.*` / `epn.*` | 이벤트 매개변수의 문자열·숫자 형태 |
| `seg` | 세션 참여 플래그 |
| `_p` | 페이지 로드 식별자 |
| `gcs` | 저장 동의 상태 |
| `gcd` | 항상 전송되는 동의 상태 |

관측값으로 적습니다. 공식 페이지가 이 필드를 공개하지 않으므로, 불일치를 API 위반이라고 부르지 않고 필드 철자에 검증을 걸지 않습니다. 형제 필드가 있는데 특정 필드가 없으면 스키마 판정이 아니라 관측과 그 출처를 기록합니다.

## DebugView

- "DebugView를 쓰려면 디버그 모드를 켜야 합니다." `gtag('config', 'G-12345ABCDE', { debug_mode: true })`로 켜거나 Google Analytics Debugger 확장을 설치합니다.
- "매개변수를 `false`로 두어도 디버그 모드는 꺼지지 않습니다." 매개변수를 빼는 것이 끄는 유일한 방법입니다. 운영에 남은 `debug_mode: false`도 디버그 트래픽을 계속 흘립니다.
- 디버그 세션은 디버그가 켜진 페이지를 쓰는 동안에만 나타납니다. 디버그 모드 없이 먼저 연 페이지는 절대 나타나지 않습니다.
- DebugView 안의 기기·브라우저 필터는 실제로 도착한 이벤트를 가립니다. 이벤트가 없다고 보고하기 전에 필터를 지웁니다.
- 디버그 트래픽은 나중에 개발자 트래픽 필터로 제외하므로, 릴리스 빌드에 디버그 모드를 켜 둔 채 두지 않습니다.

## Tag Assistant

- Tag Assistant(`tagassistant.google.com` 또는 확장)는 로드된 태그, 실행 순서, Consent 이벤트를 보여 줍니다. "어느 태그가 실행됐나"와 동의 순서에 맞는 도구입니다.
- 물량이나 시각 도구가 아닙니다. 태그가 있고 실행되는지 확인한 뒤 이벤트 수준 세부는 `/g/collect`나 DebugView로 봅니다.

## Realtime

- 실시간은 지난 5분에서 30분의 이벤트를 보여 주고, "공식 서비스 수준 목표 없이 최선 노력"으로 동작합니다. 데스크톱 카드는 700행까지입니다.
- 빠른 존재 확인과 DebugView 뒤의 두 번째 확인으로 씁니다. 임계값 적용과 짧은 창이 숫자를 바꾸므로 개수로 쓰지 않습니다.
- 대응하는 `/g/collect` 관측 없이 실시간 히트가 나타나면 요청이 없었던 것이 아니라 캡처가 그 요청을 놓친 것입니다.

## Measurement Protocol validation

- 운영 엔드포인트는 `POST https://www.google-analytics.com/mp/collect`(EU는 `https://region1.google-analytics.com/mp/collect`)이고, `api_secret`은 쿼리 문자열로, `client_id`는 본문으로 갑니다.
- 프로토콜은 "이벤트가 잘못돼도 HTTP 오류 코드를 돌려주지 않으므로", `2xx`는 접수가 아니고 그 근거로 요청을 재시도하지 않습니다.
- `https://www.google-analytics.com/debug/mp/collect`로 검증합니다. `validationMessages`를 돌려주고, 빈 배열이 통과입니다. 메시지 코드에는 `VALUE_INVALID`, `VALUE_REQUIRED`, `NAME_INVALID`, `NAME_RESERVED`, `VALUE_OUT_OF_BOUNDS`, `EXCEEDED_MAX_ENTITIES`, `NAME_DUPLICATED`가 있습니다.
- 검증 서버는 `api_secret`을 검증하지 않으므로, 깨끗한 `validationMessages`가 시크릿이 맞다는 증명은 아닙니다.
- 지킬 한도입니다. 요청당 이벤트 25개, 이벤트당 매개변수 25개, 본문 130 kB 미만, 소급 72시간까지입니다. 이벤트는 클라이언트 세션과 합쳐지려면 48시간 안에 Google에 닿아야 합니다.
- `api_secret`을 출력하지 않습니다. 클라이언트 측 코드에서 찾은 `api_secret`은 자체 심각도를 가진 보안 발견 사항이며, 어떤 보고서에서도 앞 4글자까지만 보여 줍니다.

## The diagnose order

이 순서를 걷고, 증상을 설명하는 첫 원인에서 멈춥니다. 더 싼 시험이라고 앞으로 건너뛰지 않습니다.

1. **요청이 아예 없음.** 태그가 로드되지 않습니다. 스니펫 누락, 번들러가 떨어뜨림, 스니펫 위의 이벤트 호출, 빌드가 지워 버림입니다. 근거: 어떤 페이지 로드에도 `/g/collect`가 없습니다.
2. **측정 ID가 틀림.** 페이지가 이 속성의 스트림이 아닌 `tid`를 보내거나, 옛 태그가 계속 실행되거나, 테스트 ID가 운영에 들어갔습니다. 근거: 요청은 있는데 `tid`가 스트림 측정 ID와 다릅니다.
3. **동의 거부.** 기본값이 저장을 막고 업데이트가 오지 않거나, 기본값이 태그 뒤에 도착합니다. 근거: `gcs`가 저장 거부를 보이는 요청, 또는 배너를 수락할 때까지 요청이 없습니다.
4. **CSP나 네트워크 차단.** `connect-src`나 `script-src-elem` 누락, 시험 브라우저의 확장, 호출을 떨어뜨리는 프록시입니다. 근거: 차단된 호스트를 이름으로 적은 콘솔 CSP 위반입니다.
5. **태그나 페이지뷰 중복.** 스니펫 둘, 프레임워크 컴포넌트와 수동 스니펫의 공존, 자동 히스토리 추적과 수동 `page_view`의 공존, `transaction_id` 없는 `purchase`입니다. 근거: 한 번의 이동에서 같은 `en`과 같은 `cid`를 가진 요청 둘입니다.
6. **필터나 추천.** 내부 트래픽·개발자 트래픽 필터, 빈 호스트 이름을 막는 호스트 이름 필터, 자기 추천, 만료된 `_gl` 링커 매개변수입니다. 근거: 요청은 도착하는데 리포트가 그 트래픽을 다른 곳에 붙이거나 빠뜨립니다.
7. **처리 지연.** 요청이 올바르고 도착했으며 표준 리포트가 아직 처리하지 못했습니다. 지연은 지연으로 보고하고 완료로 닫지 않습니다. 근거: 기대한 `tid`에 `200`/`204`가 있고 리포트는 24시간에서 48시간 지연됩니다.

반복 규칙은 `rules/ga-workflow.md`와 같습니다. 원인마다 세 번 시도, 확인 수단은 새 전송 관측, 점검을 약화하는 수리는 금지입니다.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| `/g/collect` 요청이 `200`이나 `204`로 응답하면 전송 성공이고, 표준 리포트는 24~48시간, 실시간은 수 분 안에 나타납니다 | <https://developers.google.com/analytics/devguides/collection/ga4/troubleshoot> |
| DebugView는 디버그 모드가 필요하고 `debug_mode`를 `false`로 두어도 꺼지지 않습니다 | <https://support.google.com/analytics/answer/7201382> |
| 실시간은 지난 5~30분을 덮고 SLO 없이 최선 노력이며 카드당 700행까지입니다 | <https://support.google.com/analytics/answer/9271392> |
| 가장 이른 Consent 이벤트가 페이지 기본값이고 가장 늦은 것이 업데이트입니다 | <https://developers.google.com/tag-platform/security/guides/consent-debugging> |
| Measurement Protocol은 잘못된 이벤트에도 HTTP 오류 코드를 돌려주지 않습니다 | <https://developers.google.com/analytics/devguides/collection/protocol/ga4/validating-events> |
| `/debug/mp/collect`는 `VALUE_INVALID`, `NAME_RESERVED` 같은 코드가 든 `validationMessages`를 돌려주고 `api_secret`은 검증하지 않습니다 | <https://developers.google.com/analytics/devguides/collection/protocol/ga4/validating-events> |
| `api_secret`은 비공개이고 클라이언트 코드에 노출해서는 안 되며, 요청은 `measurement_id`와 `client_id`를 받습니다 | <https://developers.google.com/analytics/devguides/collection/protocol/ga4/sending-events> |
| 요청당 이벤트 25개, 이벤트당 매개변수 25개, 본문 130 kB 상한, 소급 72시간 | <https://developers.google.com/analytics/devguides/collection/protocol/ga4/reference> |
| 개발자 트래픽 필터는 디버그 모드로 보낸 이벤트를 제외하고 적용에 24~36시간이 걸립니다 | <https://support.google.com/analytics/answer/13296662> |
| 공식 페이지가 `/g/collect` 쿼리 매개변수를 문서화하지 않습니다 | <https://developers.google.com/analytics/devguides/collection/ga4/>를 2026-11-08에 직접 검색했으나 매개변수 레퍼런스 페이지가 없었습니다 |

### Evidence grade

상태 코드, 디버그 모드 규칙, 실시간 창, 검증 엔드포인트와 코드, 요청 한도는 위 페이지를 2026-11-08에 읽은 `MEASURED`입니다. 일곱 단계 진단 순서, 증명 사다리 네 단, 필드 표는 `LOCAL`입니다. 순서와 사다리는 이 패키지의 설계이고, 필드 표는 공식 레퍼런스가 없어 관측 트래픽을 기록한 것입니다. 공식 `/g/collect` 매개변수 페이지가 없다는 사실 자체가 2026-11-08 검색의 결과이며, 그런 페이지가 영원히 생기지 않는다는 주장이 아닙니다.
