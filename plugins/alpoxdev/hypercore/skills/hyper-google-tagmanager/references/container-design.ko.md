# 컨테이너 설계

`configure`에서, 그리고 발견 사항이 dataLayer, 태그, 트리거, 변수, 템플릿, 이커머스, 작업공간, 서버 측 태깅에 관한 것이면 이 파일을 읽습니다. `volatile` 표시가 붙은 사실은 제품과 함께 바뀝니다.

## Contents

- 1. Event plan
- 2. dataLayer contract
- 3. Google tag and GA4 event tags
- 4. Ecommerce
- 5. Triggers and firing control
- 6. Variables, templates, and Custom HTML
- 7. Workspaces, versions, permissions, import, naming
- 8. Server-side tagging
- Sources

## 1. Event Plan

코드나 컨테이너를 건드리기 전에 태그마다 행 하나를 씁니다.

| Event | Trigger | Parameters | Destination | Consent type |
|---|---|---|---|---|
| `purchase` | Custom Event `purchase` | `transaction_id`, `value`, `currency`, `items` | GA4 `G-...` | `analytics_storage` |
| `generate_lead` | 양식 제출, `Form ID`가 `contact`와 같음 | `form_id` | GA4, Google Ads 전환 | `analytics_storage`, `ad_storage`, `ad_user_data` |

- 새 이름을 만들기 전에 Google이 권장하는 이벤트 이름(`purchase`, `add_to_cart`, `generate_lead`, `sign_up`, `login`, `search`, ...)을 씁니다. 이벤트 이름은 대소문자를 구분합니다.
- 이름이나 매개변수에 개인정보를 넣지 않습니다(`rules/safety-gates.md` §4).

## 2. dataLayer Contract

- 컨테이너가 로드되기 전에 dataLayer를 만듭니다. `window.dataLayer = window.dataLayer || [];`입니다. "Only one `dataLayer` object is supported per page." GTM이 로드된 뒤에 `window.dataLayer = []`를 절대 대입하지 않습니다. 태그가 발화를 멈추고 데이터가 사라집니다.
- 이벤트는 `dataLayer.push({ event: 'event_name', key: 'value' })`로 넣습니다. 같은 키를 나중에 푸시하면 값이 덮어써집니다.
- 값은 페이지 로드 사이에 유지되지 않습니다. 컨테이너 로드 시점에 필요한 값은 모든 페이지에서 컨테이너 스니펫 위에 푸시해야 합니다.
- `dataLayer`는 대소문자를 구분합니다(`datalayer.push`는 실패합니다). 키는 따옴표로 감싼 유효한 객체 키여야 하고, 같은 개념에는 페이지 전체에서 이름 하나를 씁니다.
- GTM은 메시지를 먼저 들어온 순서대로 하나씩 처리합니다. 태그나 템플릿 안에서 한 푸시는 대기 중인 메시지 뒤에 대기열로 들어가므로 "any updated data layer values are not guaranteed to be available for the next event"입니다. 그런 값에는 자체 `event`와 Custom Event 트리거를 붙입니다.
- 태그 시퀀싱 설정 태그에서는 값을 `google_tag_manager[{{Container ID}}].dataLayer.set()`로 바꾸고 `push`를 쓰지 않습니다.
- 오래 살아 있는 단일 페이지 앱은 `this.reset()`을 호출하는 푸시 함수로 상태를 지울 수 있습니다.
- Custom HTML 태그로 gtag.js 코드를 배포하거나 동의를 설정하지 않습니다. 네이티브 템플릿과 동의 API를 씁니다.

## 3. Google Tag and GA4 Event Tags

- **Google 태그**(태그 유형 Google Analytics > Google 태그, 태그 ID `G-...`)는 **Initialization - All Pages**에서 발화합니다. 속성을 로드하고 공통 설정을 선언하고 쿠키를 설정하며 자동 수집 이벤트와 향상된 측정 이벤트를 보냅니다.
- **Google Analytics: GA4 이벤트** 태그는 이벤트를 하나씩 보냅니다. 측정 ID와 이벤트 이름, 매개변수가 필요합니다. Google 태그의 ID는 상수 변수로 재사용하는 편이 좋습니다.
- 설정은 두 변수 유형으로 재사용합니다.
  - **Google tag: Configuration settings**: `send_page_view`(기본 `true`), `cookie_domain`(기본 `auto`), `cookie_expires`(기본 `63072000`초), `user_id`(최대 256자), `server_container_url` 같은 구성 수준 키입니다.
  - **Google Tag: Event Settings**: 여러 이벤트 태그가 공유하는 매개변수와 GA4 사용자 속성(속성마다 최대 25개)입니다.
- 목적지(`volatile`, 2026-10-12): 컨테이너는 gtag.js를 로드하지 않고도 Google 목적지로 직접 보낼 수 있고, Settings > Google Destinations에 그 목록이 있습니다. 중앙 설정은 목적지 태그에 적용되며 따로 로드한 Google 태그에는 적용되지 않습니다.
- 2025-04-10 이후 Google Ads나 Floodlight 태그가 있는 컨테이너는 Google 태그를 먼저 로드합니다(`volatile`).

## 4. Ecommerce

이커머스 이벤트마다 먼저 지우고 푸시합니다.

```js
dataLayer.push({ ecommerce: null });  // Clear the previous ecommerce object.
dataLayer.push({
  event: "purchase",
  ecommerce: {
    transaction_id: "T_12345",
    value: 72.05,
    tax: 3.60,
    shipping: 5.99,
    currency: "USD",
    coupon: "SUMMER_SALE",
    items: [{
      item_id: "SKU_12345",
      item_name: "Stan and Friends Tee",
      price: 10.01,
      quantity: 3,
      item_brand: "Google",
      item_category: "Apparel",
      item_variant: "green",
      index: 0
    }]
  }
});
```

- 이벤트 이름: `view_item_list`, `select_item`, `view_item`, `add_to_cart`, `add_to_wishlist`, `view_cart`, `remove_from_cart`, `begin_checkout`, `add_shipping_info`(`shipping_tier`), `add_payment_info`(`payment_type`), `purchase`, `refund`, `view_promotion`, `select_promotion`.
- `purchase`와 `refund`에는 `transaction_id`가 필요합니다(중복 제거). `value`에는 이벤트 수준에서 세 글자 ISO 4217 코드인 `currency`가 필요합니다.
- `items`: 최대 200개이고 각 항목에 `item_id`나 `item_name`이 필요합니다. `quantity` 기본값은 1이며 사용자 항목 매개변수는 최대 27개입니다(문서에 항목당인지 배열당인지 밝혀져 있지 않으므로 항목당으로 계획합니다).
- GTM에서는 이벤트마다 GA4 이벤트 태그 하나에 **Send Ecommerce data**를 켜고(데이터 원본 Data Layer) 그 이벤트 이름의 Custom Event 트리거에 붙입니다. 대안은 Data Layer 변수(`ecommerce.items`, `ecommerce.transaction_id`, ...)를 매개변수에 매핑하는 것입니다.
- `purchase`는 주문마다 한 번만 푸시하고(서버가 확인한 감사 페이지나 결제 성공 뒤), `transaction_id`는 새로고침에도 같은 값을 유지합니다.

## 5. Triggers and Firing Control

- 페이지 로드 순서: **Consent Initialization**(CMP와 동의 기본값) -> **Initialization**(Google 태그) -> **Page View** -> **DOM Ready**(`gtm.dom`) -> **Window Loaded**(`gtm.load`). 필수가 아닌 태그는 Window Loaded에서 발화시킵니다.
- 다른 트리거 유형: 클릭(All Elements, Wait for Tags와 Check Validation이 있는 Just Links), 양식 제출(Wait for Tags, Check Validation), 스크롤 깊이(페이지마다 임계값마다 한 번), 요소 노출(기본 50% 노출, 페이지당 한 번·요소당 한 번·매번 중 선택), YouTube 동영상, 사용자 이벤트(선택적 정규식), 기록 변경(프래그먼트 또는 `pushState`), JavaScript 오류(GTM 로드 뒤 잡히지 않은 오류만), 타이머(`gtm.timer`), 트리거 묶음(모든 구성원이 한 번 이상 발화한 뒤 발화).
- 정규식 `.*`를 쓰는 Custom Event 트리거를 절대 쓰지 않습니다. 2026-10-08 이후 `gtag.config`를 포함해 모든 GTM과 Google 태그 이벤트와 일치합니다.
- 태그는 발화 트리거 중 하나라도 맞으면 발화합니다. 예외(차단 트리거)는 발화를 막습니다. 모든 태그에는 발화 트리거가 최소 하나 필요합니다.
- 발화 옵션: Once per event, Once per page, Unlimited(시퀀싱 전용). 우선순위 숫자는 순서를 보장하지 않습니다("Tags will still fire asynchronously"). 순서가 중요하면 태그 시퀀싱(설정 태그와 정리 태그)을 씁니다.
- 쓰지 않는 태그는 예외로 막지 말고 일시중지하거나 제거합니다. 일시중지는 컨테이너에서 코드를 뺍니다.

## 6. Variables, Templates, and Custom HTML

- 필요할 때 켜는 기본 변수: 클릭, 양식, 기록, 페이지, 스크롤, 유틸리티(Container ID, Container Version, Environment Name, Event, 그리고 2025-12 이후 Analytics Client ID, Session ID, Session Number), 동영상, 노출.
- Data Layer 변수(버전 2)는 `ecommerce.value` 같은 중첩 키를 읽습니다. 조회 테이블과 정규식 테이블은 거의 같은 태그를 대신합니다.
- 사용자 템플릿은 선언한 권한(`inject_script`, `send_pixel`, `access_globals`, `read_data_layer`, `get_cookies`, ...)으로 샌드박스 JavaScript(ECMAScript 5.1과 일부 ES6)를 실행합니다. URL 일치 패턴은 HTTPS를 쓰고 호스트와 경로를 밝혀야 합니다. Custom HTML보다 Community Template Gallery 템플릿을 권합니다.
- Custom HTML은 샌드박스 없이 페이지 스크립트를 실행합니다. 벤더 코드를 검토하고, 큰 라이브러리는 `<script src>`로 불러오고, 벤더 코드가 필요로 할 때만 **Support document.write**를 켭니다. GTM은 Custom HTML을 압축하므로 버전 diff에서 작은따옴표가 큰따옴표로 바뀔 수 있습니다.
- Custom JavaScript 변수는 `'unsafe-eval'` 없는 CSP에서 `undefined`로 평가됩니다(`references/install-recipes.md` §5).
- 태그 유형 제한: 태그가 발화하기 전에 `gtm.allowlist`와 `gtm.blocklist`를 푸시합니다. 차단 목록이 이기고, 어떤 분류를 막으면 `sandboxedScripts`를 허용 목록에 넣지 않는 한 샌드박스 템플릿도 함께 막힙니다. Google은 이제 사용자 템플릿과 템플릿 정책(`gtag('policy', ...)`)을 권합니다. 전부 거부하는 정책은 `read_event_data`, `read_container_data`, `configure_google_tags`를 허용하지 않으면 측정을 멈춥니다.

## 7. Workspaces, Versions, Permissions, Import, Naming

- 작업공간: 표준 계정은 동시 작업공간 3개(기본 하나와 추가 2개)를 허용하고 Tag Manager 360은 무제한입니다. 버전 생성이나 게시가 작업공간을 없애고, 남은 작업공간은 "out of date"로 표시되어 갱신해야 합니다.
- 버전: 버전은 스냅숏입니다. Submit > Publish and Create Version 또는 Create Version only를 씁니다. 승인(Request Approval)은 Tag Manager 360에만 있습니다.
- 컨테이너 권한: No access, Read, Edit(작업공간과 편집, 버전은 불가), Approve(버전, 게시는 불가), Publish. 계정 역할은 Administrator, User입니다. Custom HTML, Custom JavaScript, 사용자 설정에는 2단계 인증을 켭니다.
- 가져오기(Admin > Import Container): **Overwrite**는 기존 태그, 트리거, 변수를 모두 없애고 먼저 버전을 만듭니다. **Merge**는 **Overwrite conflicting** 또는 **Rename conflicting**과 함께 씁니다. 항상 새 작업공간으로 가져오고 View Detailed Changes를 읽으며 Overwrite는 승인 등급으로 취급합니다.
- 크기: GTM은 컨테이너를 300 KB로 제한하고 Size 표시를 보여 줍니다. 70%를 넘으면 조치합니다.
- 이름 규칙: `<type> - <destination> - <detail>`이며 예는 `GA4 - Event - purchase`, 트리거는 `CE - purchase`, 변수는 `DLV - ecommerce.value`입니다. 목적지나 팀별 폴더를 둡니다. 웹 도메인마다 컨테이너 하나, 하나의 경험을 이루는 여러 도메인에는 컨테이너 하나를 씁니다.

## 8. Server-Side Tagging

- 서버 컨테이너는 태깅 서버에서 실행됩니다(자동 프로비저닝이면 Cloud Run, 또는 GCP나 다른 호스트에서 직접). 클라이언트가 들어오는 요청을 받고 태그가 나가는 요청을 보냅니다.
- 비용과 크기(`volatile`): 1 vCPU, 0.5 GB Cloud Run 인스턴스는 월 약 USD 45입니다. Google은 설정 안내에서 인스턴스 최소 2개를, 개요에서 3개를 권하며, 2~10개가 초당 약 35~350 요청을 처리합니다. 기본 배포는 시험용입니다. 만들거나 늘리면 비용이 들므로 승인 등급입니다.
- 도메인: 같은 오리진(`https://www.example.com/metrics`)이 가장 좋고 하위 도메인(`https://metrics.example.com`)이 다음입니다. 기본 `run.app` 도메인은 서버 쿠키를 설정할 수 없습니다.
- 웹 연결: Google 태그의 구성 설정에 `server_container_url`을 더합니다. 2025-06-30 이후 gtag.js와 gtm.js를 웹 컨테이너 클라이언트로 제공합니다(`volatile`).
- 검증은 서버 컨테이너 자체의 Preview(Request, Tags, Variables, Event Data, Console 탭)와 `<server URL>/healthy`의 `ok` 응답으로 합니다. 웹 Preview만으로는 서버 태그 오류가 보이지 않습니다.
- CSP: `img-src`와 `connect-src`에 서버 컨테이너 URL이 필요하고 서비스 워커를 위해 `frame-src`에도 필요합니다. `X-Frame-Options`가 이를 막지 않아야 합니다.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| dataLayer 생성, 객체 하나, FIFO 처리, 지속성, Custom HTML 금지 | <https://developers.google.com/tag-platform/tag-manager/datalayer> |
| GTM의 Google 태그와 GA4 이벤트 태그 | <https://support.google.com/tagmanager/answer/9442095> |
| 이커머스 푸시 형태, `ecommerce: null`, 항목 제한, Send Ecommerce data | <https://developers.google.com/analytics/devguides/collection/ga4/ecommerce?client_type=gtm> |
| 페이지 로드 트리거 순서 | <https://support.google.com/tagmanager/answer/7679319> |
| 트리거 유형과 옵션 | <https://support.google.com/tagmanager/topic/7679108> |
| 태그 시퀀싱과 `dataLayer.set()` | <https://support.google.com/tagmanager/answer/6238868> |
| 발화 옵션과 우선순위 | <https://support.google.com/tagmanager/answer/6279951> |
| 기본 변수 | <https://support.google.com/tagmanager/answer/7182738> |
| 사용자 템플릿과 권한 | <https://developers.google.com/tag-platform/tag-manager/templates> |
| Custom HTML과 document.write | <https://support.google.com/tagmanager/answer/6107167> |
| 허용 목록, 차단 목록, 템플릿 정책 | <https://developers.google.com/tag-platform/tag-manager/restrict>, <https://developers.google.com/tag-platform/tag-manager/templates/policies> |
| 작업공간 | <https://support.google.com/tagmanager/answer/7059647> |
| 버전, 게시, 승인 | <https://support.google.com/tagmanager/answer/6107163> |
| 권한 | <https://support.google.com/tagmanager/answer/6107011> |
| 가져오기와 내보내기 | <https://support.google.com/tagmanager/answer/6106997> |
| 컨테이너 크기 | <https://web.dev/articles/tag-best-practices>, <https://support.google.com/tagmanager/answer/2772488> |
| 릴리스 노트 날짜(2025-04-10, 2025-06-30, 2025-12-11, 2026-10-08, 2026-10-12) | <https://support.google.com/tagmanager/answer/4620708> |
| 서버 측 태깅 | <https://developers.google.com/tag-platform/tag-manager/server-side>, <https://developers.google.com/tag-platform/tag-manager/server-side/cloud-run-setup-guide>, <https://developers.google.com/tag-platform/tag-manager/server-side/custom-domain> |

### Evidence grade

2026-11-08에 읽은 Google 공식 문서입니다. 이름 규칙은 Google의 `<item type> - <app> - <detail>` 예를 각색한 것이고, 이벤트 계획 표는 이 패키지의 설계입니다.
