# 검증

모든 `verify` 단계 전과 `diagnose`에서 이 파일을 읽습니다. 어떤 검사가 무엇을 증명하는지, 증명처럼 보이지만 아닌 신호가 무엇인지 적습니다. `volatile` 표시가 붙은 사실은 Google 도구와 함께 바뀌므로 의존하기 전에 다시 확인합니다.

## Contents

- 1. Preview and Tag Assistant
- 2. Environments
- 3. Rendered-browser checks
- 4. Failure signatures
- 5. Destination checks
- 6. Google-side audit surfaces
- 7. Publishing and rollback
- Sources

## 1. Preview and Tag Assistant

- 시작: 컨테이너 > Workspace > **Preview**로 Tag Assistant를 엽니다. 사이트 URL을 넣고 **Connect**를 누릅니다. 디버그 뷰는 "will only appear on the same browser that was used to enable preview mode, or for shared users"입니다. Preview는 세션에 묶여 있어 헤드리스 크롤로는 Preview 동작을 단정할 수 없습니다.
- 세션 공유: Tag Assistant > More Actions > **Share** 또는 Versions > More Actions > **Share Preview**. 가져온 디버그 세션은 읽기 전용입니다.
- 이전 버전: Versions > 행 > More Actions > **Preview**.
- 뷰마다 증명하는 것:
  - 이벤트 목록: 이벤트가 "in the order they were fired"로 나옵니다. `<>`는 내장 이벤트입니다.
  - **Tags**: 선택한 이벤트의 Tags Fired와 Tags Not Fired.
  - **Variables**: 그 이벤트 시점의 변수 값.
  - **Data Layer**: 이벤트 뒤의 dataLayer 상태. **API Call**은 그것을 만든 `gtag()`나 `dataLayer.push()`를 보여 줍니다.
  - **Consent**: 가장 이른 동의 이벤트가 기본값, 가장 늦은 것이 업데이트입니다.
  - **Page issues**: CSP 차단과 다른 로드 문제.
- 디버그 매개변수(`volatile`): Tag Assistant는 URL에 `_dbg`를 더합니다. 로더는 `gtm_debug`, `tagassistant.google.com` 리퍼러, `__TAG_ASSISTANT` 쿠키, postMessage 핸드셰이크도 읽습니다. `gtm.js?id=...&gtm_debug=x`를 curl 상태 확인으로 쓰지 않습니다. 2026-11-08에 시험한 모든 컨테이너에서 403을 응답했습니다.
- Tag Assistant Companion은 하나의 Tag Assistant 확장 프로그램으로 합쳐지며 "will be deprecated in the coming months"입니다(`volatile`).
- 쓸 수 없는 것: 모바일 앱과 AMP 컨테이너의 디버그 뷰. "AMP is not currently supported by Tag Assistant"입니다.

## 2. Environments

- 모든 컨테이너에는 **Live**(게시된 버전)와 **Latest**(마지막으로 만든 버전)가 있습니다. 사용자 환경: Admin > Environments > New, Versions > Actions > **Publish To...**로 게시합니다. "When you publish a custom environment, you will not send those changes to the live version of your container."
- 환경 스니펫에는 `gtm_auth`, `gtm_preview=env-<n>`, `gtm_cookies_win=x`가 있습니다. **Reset Link**는 "will invalidate any container snippets that may be installed"입니다. 환경은 비프로덕션 사이트용입니다.
- Live를 건드리지 않고 실제 페이지 로드가 필요한 검증에는 스테이징 환경을 쓰고, 승인 뒤에 같은 버전을 Live에 게시합니다.

## 3. Rendered-Browser Checks

브라우저 자동화 기능이 있으면 씁니다. 페이지마다 다음을 기록합니다.

1. `googletagmanager.com/gtm.js` 요청(횟수, 상태, 컨테이너 ID)과 목적지 요청(GA4의 `/g/collect`, 그 밖의 벤더 호스트).
2. `/g/collect` 요청마다 `tid`(측정 ID), `en`(이벤트 이름), `cid`(클라이언트 ID), 이벤트 매개변수(`ep.*`, `epn.*`), `gcs` 또는 `gcd`(동의 상태). 이 쿼리 이름은 Google 문서가 아니라 관측한 것이므로 `volatile`로 봅니다.
3. 로드 뒤와 동작마다의 `window.dataLayer`, `Object.keys(window.google_tag_manager || {})`. 로더는 `google_tag_manager`를 컨테이너 ID로 만듭니다. 스크립트가 실행됐다는 증거이며 태그가 발화했다는 증거가 아닙니다.
4. 콘솔 오류와 CSP 위반 보고서.

런타임의 브라우저 도구에 맞춰 쓴 전형적인 캡처입니다(Playwright 형태):

```js
page.on('request', r => {
  const u = r.url();
  if (u.includes('googletagmanager.com/gtm.js') || u.includes('/g/collect')) log.push(u);
});
await page.goto(url);
const keys = await page.evaluate(() => Object.keys(window.google_tag_manager || {}));
const dl = await page.evaluate(() => JSON.stringify(window.dataLayer || []));
```

- `/g/collect`는 엉터리 `tid`에도 204를 응답하므로 상태가 아니라 요청 매개변수로 단정합니다.
- Next.js `GoogleTagManager`와 Nuxt Scripts는 수화 뒤에 컨테이너를 불러옵니다. 서버가 보낸 HTML에는 컨테이너 ID가 없고 렌더링된 페이지에는 있습니다.

## 4. Failure Signatures

2026-11-08에 실서비스 엔드포인트에서 관측했습니다(`volatile`).

| Request | Answer | Meaning |
|---|---|---|
| `gtm.js?id=<unknown GTM-ID>` | 200, 약 241 KB, `"resource": {"version":"1", "macros":[], "tags":[]...}` | ID가 틀렸거나 한 번도 게시하지 않은 컨테이너입니다. 밖에서는 둘이 같아 보이므로 Versions 목록(Published 날짜가 있는 행)에서 확인합니다 |
| `gtm.js?id=<published GTM-ID>` | 200, 항목이 있는 `"tags":[{` | 컨테이너를 제공했습니다. `resource.version`은 컨테이너 형식 버전(예: `44`)이며 게시된 버전 번호가 아닙니다 |
| 소문자 컨테이너 ID | 200, 빈 컨테이너 | ID는 대소문자를 구분합니다 |
| 알 수 없는 ID에 `gtm_auth`와 `gtm_preview` | 404 | 없는 컨테이너의 환경 스니펫입니다 |
| 게시된 컨테이너에 틀린 `gtm_auth`와 `gtm_preview` | 403 | 오래됐거나 초기화된 환경 스니펫입니다(`gtm_auth`만으로는 무시됩니다) |
| `id` 없는 `gtm.js` | 400 | 깨진 스니펫입니다 |
| `ns.html?id=<any>` | 200, 실제와 가짜 ID에 같은 작은 본문 | noscript iframe은 아무것도 증명하지 않습니다 |

틀린 컨테이너 ID는 404를 주지 않습니다. 평범한 `gtm.js` 요청의 404는 프록시, CDN, 호스트 재작성을 가리킵니다. `scripts/gtm-site-check.sh --check-loader`가 `loaderResourceVersion`과 `loaderEmpty`를 보고하는 이유입니다.

중복 설치: 렌더링된 네트워크 로그에서 ID마다 `gtm.js?id=` 요청 수를 세고, `document.querySelectorAll('script[src*="googletagmanager.com/gtm.js"]')`를 나열하고, `rm` 없이 `Object.keys(window.google_tag_manager)`를 읽습니다. 거기에 컨테이너 ID가 둘이면 한 페이지에 컨테이너가 둘입니다.

다른 서명:

- 광고 차단기: `gtm.js` 요청이 없거나 `ERR_BLOCKED_BY_CLIENT`, `window.google_tag_manager`가 undefined, `/g/collect` 없음, 나머지 페이지는 정상. 차단기를 끄고 시험하고 그 사실을 밝힙니다.
- CSP: Tag Assistant의 Page issues, 콘솔의 위반 보고서, `'unsafe-eval'` 없이 `undefined`로 평가되는 Custom JavaScript 변수.
- 전부 거부하는 `gtag('policy')`: `Arguments(3) ['policy', ...`로 시작하는 dataLayer 항목. `read_event_data`, `read_container_data`, `configure_google_tags`를 허용하지 않으면 측정 핑이 멈춥니다.
- 로드 뒤의 `dataLayer = []`: 이후 푸시가 보이지 않고 dataLayer 뷰가 갱신을 멈춥니다.
- Tag Assistant의 "no tags found"는 광고 차단기, CSP, 방화벽이나 프록시, Tag Assistant가 연결된 뒤 로드된 태그(**Retry** 클릭), iframe, AMP에서 나올 수 있습니다. 설치가 깨졌다는 증거가 아닙니다.

## 5. Destination Checks

- GA4 DebugView(Admin > Data display > DebugView)는 디버그 기기의 이벤트를 몇 초 안에 보여 줍니다. Preview와 Tag Assistant는 시험 브라우저에 디버그 모드를 켜고, `debug_mode: true`는 다른 곳에서 켜며 매개변수를 지워야 꺼집니다. 분석 동의가 없었으면 이벤트가 DebugView에 보이지 않습니다.
- GA4 실시간은 몇 분 안에 이벤트를 보여 줍니다. 표준 보고서는 24~48시간 걸리며 검증 근거가 아닙니다.
- 다른 벤더: 벤더 자체 디버거나 테스트 이벤트 뷰를 쓰고 그 이벤트 ID를 기록합니다.

## 6. Google-Side Audit Surfaces

- **Tag Diagnostics**(Google tag > Tag quality > View diagnostics): 상태는 Excellent, Good, Needs attention, Urgent, No recent data입니다. Google 태그가 이전에 감지됐고 최근 48시간에 없으면 Urgent입니다. 진단에는 순서가 틀린 config나 동의 설치, 레거시 Universal Analytics 태그, 누락된 거래 ID, 리소스를 차단하는 CSP, 페이지에서 너무 낮은 태그 위치, 태그 게이트웨이 없이 제한된 데이터가 포함됩니다(`volatile` 목록).
- **Tag coverage**(Google tag > Admin > Tools > Tag coverage): 도메인과 경로 기준 최대 10,000페이지, 상태는 Not tagged, No recent activity(30일), Tagged입니다. 60일 동안 신호가 없는 페이지는 빠지고 상태는 24시간 늦을 수 있습니다. 리디렉트, 후행 슬래시, URL 대소문자, 낮은 트래픽이 잘못된 "not tagged" 행을 만듭니다.

## 7. Publishing and Rollback

- 게시: **Submit** > Publish and Create Version > Workspace Changes 검토 > Version Name and Description > 선택적 환경 > **Publish**. 승인 등급 동작입니다(`rules/safety-gates.md` §1).
- 실서비스 롤백: Versions > 이전 버전 > Actions > **Publish**. 역시 승인 등급입니다.
- 초안만 롤백: Versions > Actions > **Set as Latest Version**. 게시 전까지 Live는 바뀌지 않습니다.
- Request Approval은 Tag Manager 360에만 있습니다. 버전 목록의 Published 열이 감사 기록입니다.
- 게시한 뒤에는 항상 `gtm-site-check.sh --check-loader`를 다시 실행하고 `gtm.js`가 이제 바뀐 태그를 제공하는지(예: 새 태그의 유형이나 이벤트 이름이 응답에 나타남) 확인합니다.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| Preview, 공유, 이전 버전, 지원하지 않는 컨테이너 | <https://support.google.com/tagmanager/answer/6107056>, <https://support.google.com/tagmanager/answer/15212893> |
| Tag Assistant 뷰와 API Call | <https://support.google.com/tagmanager/answer/15212503> |
| `_dbg`, 문제 해결 원인, AMP | <https://support.google.com/tagassistant/answer/10039345> |
| Companion 지원 종료 | <https://support.google.com/tagmanager/answer/16463290> |
| 환경과 그 스니펫 | <https://support.google.com/tagmanager/answer/6311518> |
| 게시, 버전, 롤백, 360 승인 | <https://support.google.com/tagmanager/answer/6107163> |
| Tag Diagnostics | <https://support.google.com/tagmanager/answer/14681508> |
| Tag coverage | <https://support.google.com/tagmanager/answer/12270036> |
| CSP Page issues와 Custom JavaScript 변수 | <https://developers.google.com/tag-platform/security/guides/csp> |
| `gtag('policy')`의 측정 중단 | <https://developers.google.com/tag-platform/tag-manager/templates/policies> |
| dataLayer 재초기화 | <https://developers.google.com/tag-platform/tag-manager/datalayer> |
| DebugView와 `debug_mode` | <https://support.google.com/analytics/answer/7201382> |
| 보고서 지연과 네트워크 확인 | <https://developers.google.com/analytics/devguides/collection/ga4/troubleshoot> |
| 요청 캡처 API 형태 | <https://playwright.dev/docs/network> |
| `gtm.js` 상태와 본문 서명, `gtm_debug=x` 403, `/g/collect` 204, `google_tag_manager` 키 | execution checks against the live endpoints, 2026-11-08 |

### Evidence grade

2026-11-08에 읽은 Google 공식 문서와 그날 네트워크 하나에서 관측한 실서비스 엔드포인트 기록입니다. 실패 서명 표와 `/g/collect` 매개변수 이름은 관측이며 문서화된 계약이 아닙니다. 결과가 앞뒤가 맞지 않으면 다시 확인합니다.
