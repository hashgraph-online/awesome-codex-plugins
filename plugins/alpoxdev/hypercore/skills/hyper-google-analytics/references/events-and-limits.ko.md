# 이벤트와 한도

이벤트 설계 질문, 이커머스 질문, 발견 사항이 의존하는 한도에서 이 참조를 읽습니다. 이벤트 분류, 권장·이커머스 이벤트, 공개된 한도, 이름 규칙, 핵심 이벤트 수치를 소유합니다.

> 영어판: [`events-and-limits.md`](events-and-limits.md)

## Contents

- Event categories
- Recommended events
- Ecommerce events
- Limits
- Naming and reserved prefixes
- Key events

## Event categories

| Category | Where it comes from | Examples |
|---|---|---|
| 자동 수집 | Google Analytics 태그를 설정하면 기본으로 수집됩니다 | `first_visit`, `session_start`, `user_engagement` |
| 향상된 측정 | Analytics에서 스위치를 켜면 수집됩니다 | `page_view`, `scroll`, `click`, `view_search_results`, `video_*`, `file_download`, `form_start`, `form_submit` |
| 권장 | 업종별 표준 이름입니다 | `login`, `sign_up`, `purchase`, `generate_lead` |
| 맞춤 | 구현자가 정의한 이름입니다 | 위 목록에 없는 모든 이름 |

- 맞춤 이름보다 권장 이름을 먼저 씁니다. 권장 이름은 내장 리포트를 켜고, 맞춤 이름은 맞춤 디멘션만 채웁니다.
- 맞춤 이벤트 이름은 대소문자를 구분하고, 문자로 시작해야 하며, 문자·숫자·밑줄만 쓸 수 있습니다.
- 태그 스니펫 위에 놓인 이벤트 호출은 버려집니다. Google은 "Google 태그 스니펫 위에 놓인 이벤트의 데이터를 처리하지 않습니다".

## Recommended events

권장 이벤트는 모든 속성, 온라인 판매, 리드 생성, 게임으로 묶입니다. 리드 생성 묶음(`qualify_lead`, `working_lead`, `close_convert_lead`, `close_unconvert_lead`, `disqualify_lead`)은 리드 리포트에 속합니다.

- 문서에 있는 매개변수 이름을 씁니다. 이름을 바꾼 매개변수를 가진 권장 이벤트는 그 매개변수를 기대하는 리포트를 채우지 못합니다.
- 권장 이벤트는 이름과 스키마이지, 그 속성에 리포트가 켜져 있다는 보장이 아닙니다.

## Ecommerce events

점검에서 확인할 퍼널 순서는 `view_item_list`, `select_item`, `view_item`, `add_to_cart` 또는 `add_to_wishlist`, `view_cart`, `begin_checkout`, `add_shipping_info`, `add_payment_info`, `purchase`, `refund`입니다.

구매를 쓸 수 있는지 가르는 매개변수 둘입니다.

- `transaction_id`는 `purchase`에 필요하고 "구매에 중복 이벤트가 생기는 것을 막아 줍니다". 이것이 없는 `purchase`는 재시도된 호출을 두 번 셀 수 있습니다.
- `currency`는 "3자리 ISO 4217 형식" 값입니다. 통화가 빠지거나 틀리면 이벤트 수는 기록되지만 Google Ads로 나가지 않으므로, 조용히 망가진 매출 지표가 Analytics에서는 정상으로 보입니다.
- `value`는 "모든 항목의 `(price * quantity)` 합"이며 배송비와 세금은 뺍니다.
- `items` 배열은 원소 200개까지이고, 각 항목에 `item_id`나 `item_name`이 필요하며 `quantity`는 "기본값 1"입니다.
- `purchase`는 `ecommerce_purchase`를, `refund`는 `ecommerce_refund`를 대체했습니다. 옛 이름은 발견 사항입니다.
- `in_app_purchase`는 앱 스트림에서 자동 수집되므로 손으로 보내면 이벤트가 중복됩니다.

아이템 수준 맞춤 매개변수에는 문서화된 충돌이 있습니다.

| Path | Item custom parameters |
|---|---|
| 태그(gtag.js와 GTM) | 27 |
| Measurement Protocol | 10 |

한 숫자를 골라 해소하지 않습니다. 사이트가 쓰는 경로를 기록하고, 페이로드가 두 경로를 모두 통과해야 하면 낮은 값을 안전한 상한으로 둡니다.

## Limits

표준 속성이며 수집 한도 페이지 기준입니다.

| Item | Limit |
|---|---|
| 이벤트 이름 | 40자. 40자를 넘는 이름을 핵심 이벤트로 표시하면 `_c` 접미사를 잃어 핵심 이벤트로 보고되지 않습니다 |
| 이벤트당 매개변수 | 25개 |
| 매개변수 이름 | 40자 |
| 매개변수 값 | 100자. 예외는 `page_title` 300, `page_referrer` 420, `page_location` 1,000 |
| 사용자 속성 | 속성당 25개, 이름 24자, 값 36자 |
| User-ID | 256자 |
| 서로 다른 이벤트 | 앱 사용자당 하루 500개. 웹은 무제한 |
| 세션 | 사용자당 하루 2,000개 |
| 핵심 이벤트 | 사용자당 하루 10,000개 |
| 이벤트 | 사용자당 하루 100,000개 |
| 이벤트 범위 맞춤 측정기준 | 50개 |
| 사용자 범위 맞춤 측정기준 | 25개 |
| 아이템 범위 맞춤 측정기준 | 10개 |
| 맞춤 측정항목 | 50개 |
| 계산 측정항목 | 5개 |
| 속성당 핵심 이벤트 | 30개 |

- Google Analytics는 "다음 한도를 넘는 이벤트, 이벤트 매개변수, 사용자 속성을 기록하지 않습니다". 그래서 26번째 매개변수는 잘리는 것이 아니라 없습니다. 매개변수를 조용히 잃은 이벤트는 이벤트 수가 늘어도 실제 발견 사항입니다.
- 맞춤 측정기준을 삭제해도 자리는 48시간이 지나야 비웁니다.
- Analytics 360은 이 한도를 올립니다. 이벤트당 매개변수 100개, 사용자 속성 100개, 매개변수 값 500자, 핵심 이벤트 50개입니다. 한도를 인용하기 전에 속성 판을 읽습니다.

## Naming and reserved prefixes

맞춤 이름이 쓸 수 없는 예약 접두사는 `_`, `firebase_`, `ga_`, `google_`, `gtag.`입니다. 웹 속성은 `query_id`도 예약합니다.

- Measurement Protocol 예약 이름에는 `session_start`, `first_visit`, `user_engagement`, `error`가 있고, `screen_view`, `ad_impression`, `in_app_purchase`는 앱 전용입니다.
- 예약 접두사로 시작하는 이름은 거부되거나 바뀌므로, 쓴 그대로 리포트에 닿지 않습니다. 의도한 이름과 어긴 예약 규칙을 함께 보고합니다.

## Key events

- "전환"은 2024년 3월 27일에 "핵심 이벤트"로 이름이 바뀌었습니다. 아직 전환이라고 부르는 문서나 코드 주석은 이름 변경 이전의 것이며, 보고서는 현재 이름을 쓰고 옛 이름은 한 번만 덧붙입니다.
- 이제 "전환"은 광고 제품과 공유하는 행동을 뜻하므로, GA4 발견 사항에서 두 단어는 바꿔 쓸 수 없습니다.
- 표준 속성은 핵심 이벤트 30개까지, Analytics 360은 50개까지입니다.
- `purchase`, `first_open`, `in_app_purchase`, `app_store_subscription_convert`, `app_store_subscription_renew`는 자동으로 표시됩니다.
- 이벤트를 핵심 이벤트로 표시하는 것은 "만든 시점부터의 리포트에 영향을 주고 과거 데이터를 바꾸지 않으며", 반영에 최대 24시간이 걸립니다. read-back을 과거가 바뀌었다는 증명으로 보고하지 않습니다.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| 이벤트 분류 네 가지와 스니펫 위 이벤트가 버려진다는 규칙 | <https://developers.google.com/analytics/devguides/collection/ga4/events> |
| 권장 이벤트는 모든 속성, 온라인 판매, 리드 생성, 게임으로 묶입니다 | <https://support.google.com/analytics/answer/9267735> |
| `purchase`는 `transaction_id`가 필요하고, `currency`는 ISO 4217이며, `value`는 배송비·세금을 빼고, `items`는 200개까지입니다 | <https://developers.google.com/analytics/devguides/collection/ga4/reference/events>, <https://developers.google.com/analytics/devguides/collection/ga4/ecommerce> |
| 아이템 맞춤 매개변수는 태그에서 27개, Measurement Protocol에서 10개입니다 | <https://support.google.com/analytics/answer/9267744>, <https://developers.google.com/analytics/devguides/collection/protocol/ga4/sending-events> |
| 이벤트 이름 40자, 매개변수 25개, 값 100자에 `page_title` 300, `page_referrer` 420, `page_location` 1,000, 사용자 속성 25개 | <https://support.google.com/analytics/answer/9267744> |
| 맞춤 측정기준 자리는 사용자 범위 25개, 이벤트 범위 50개, 아이템 범위 10개이고 삭제 48시간 뒤에 풀립니다 | <https://support.google.com/analytics/answer/14240153> |
| 예약 접두사 `_`, `firebase_`, `ga_`, `google_`, `gtag.`와 웹의 `query_id` | <https://support.google.com/analytics/answer/13316687> |
| 전환이 2024년 3월 27일 핵심 이벤트로 이름을 바꿨습니다 | <https://support.google.com/analytics/answer/13420269> |
| 표준 속성 핵심 이벤트 30개, 360은 50개, 자동 표시 다섯 개, 과거 데이터를 바꾸지 않는다는 점 | <https://support.google.com/analytics/answer/13128484> |
| 360은 매개변수 100개, 사용자 속성 100개, 값 500자, 핵심 이벤트 50개로 올립니다 | <https://support.google.com/analytics/answer/11202874> |

### Evidence grade

모든 한도, 매개변수 이름, 접두사, 날짜, 인용은 위 페이지를 2026-11-08에 읽은 `MEASURED`입니다. 두 경로를 함께 쓰는 페이로드가 낮은 아이템 매개변수 상한을 유지한다는 규칙과 점검표로 쓰는 퍼널 순서는 `LOCAL`입니다. 퍼널 순서는 이커머스 페이지에서 왔고 상한 규칙은 이 패키지의 보수적 선택입니다. 아이템 매개변수 충돌은 공식 페이지 둘이 모두 현행이므로 충돌로 보고합니다.
