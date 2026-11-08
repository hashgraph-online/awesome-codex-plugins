# 설치 레시피

`install`에서, 그리고 `audit`이나 `diagnose`에서 발견 사항이 스니펫, 프레임워크, SPA 페이지 뷰, CSP, 로딩 비용에 관한 것이면 이 파일을 읽습니다. 사실에는 날짜가 붙어 있으므로 변동 사실(`volatile` 표시)에 의존하기 전에 다시 확인합니다.

## Contents

- 1. GTM or a direct Google tag
- 2. Snippet forms
- 3. Framework recipes
- 4. SPA page views
- 5. Content Security Policy
- 6. First-party serving and performance
- Sources

## 1. GTM or a Direct Google Tag

| Situation | Choose |
|---|---|
| Google이나 제3자 제품 여럿, 잦은 태그 변경, 비개발자의 태그 편집 | GTM(`GTM-` 컨테이너) |
| 변경이 드문 Google 제품 하나(예: GA4만 또는 Ads만) | 직접 Google 태그(`gtag/js?id=G-...`)가 더 단순할 수 있습니다 |
| 사이트가 이미 둘 중 하나를 불러옴 | 유지합니다. 같은 ID에 다른 것을 더하지 않습니다 |

- Google: "If your site platform or Content Management System permits it, Google Tag Manager should be your first choice", 그러나 제품 하나에 변경이 드물면 Google 태그가 "may be the fastest and easiest method"입니다.
- "You should avoid installing redundant tags or tag management systems." 페이지당 컨테이너 하나, "the best practice is to set up one container per web domain"입니다.
- 컨테이너 ID 접두사가 컨테이너가 실행할 수 있는 것을 정합니다(`volatile`, 2026-07-09 이후). `GTM-` 컨테이너는 모든 태그 유형을 허용하고, `G-`나 `AW-` ID로 불러온 컨테이너는 "is limited to Google tags"입니다.
- `G-`, `AW-`, `DC-` ID를 `gtm.js` 경로로 불러오는 것은 "is an unsupported implementation"입니다. `GTM-` ID와 `gtag('config')` 없이 `gtm.js`를 쓰거나, `gtag/js?id=<ID>`와 `gtag('config', '<ID>')`를 씁니다.
- `gtag('config')`는 폐기되었습니다. "Use the Google Tag Manager UI to configure tag settings and destinations, or use `gtag('set')` for setting in-page parameters." 기존 설정은 계속 작동합니다. 2026-10-08 이후 `gtm.js`는 "will initialize on container load, regardless of any gtag('config') commands"이고, config 명령은 dataLayer에 `gtag.config` 이벤트로 나타나며 와일드카드 Custom Event 트리거가 이를 잡습니다(`volatile`).

## 2. Snippet Forms

컨테이너의 설치 대화상자(Admin > Install Google Tag Manager)나 Tag Manager API `snippet` 메서드에서 스니펫을 복사합니다. Google은 살아 있는 세 가지 형태를 안내하며, 기억으로 쓰는 에이전트는 보통 이전 형태를 만듭니다.

### Current form (Install dialog, one block, `volatile`)

```html
<!-- Google Tag Manager -->
<script async src="https://www.googletagmanager.com/gtm.js?id=GTM-XXXXXXX"></script>
<script>
window.dataLayer = window.dataLayer || [];function gtag(){dataLayer.push(arguments);}gtag('js', new Date());
</script>
<!-- End Google Tag Manager -->
```

- "Copy the first block of code and paste it as high in the `<head>` tag as possible." 이 형태에는 `<noscript>` 부분이 없습니다.
- 로더가 `async`라서 인라인 줄은 보통 `gtm.js` 실행 전에 돕니다. 사이트가 순서를 보장해야 하면(동의 기본값, 페이지 수준 푸시) 그 스크립트를 이 블록 위에 둡니다.

### Previous form (two parts, still supported)

```html
<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','GTM-XXXXXXX');</script>
<!-- End Google Tag Manager -->
```

```html
<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-XXXXXXX"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->
```

- "If you already have your website tagged with the previous version of the snippet, you do not need to retag your website." noscript 부분은 "as high in the `<body>` tag as possible"에 둡니다.
- IIFE의 네 번째 인수가 dataLayer 이름을 바꾸고, 로더가 `&l=<name>`을 붙입니다. 다른 스크립트가 이미 `dataLayer`를 차지했을 때만 사용자 이름을 씁니다.
- CSP nonce 형태(§5)는 이 형태 위에 만듭니다.

### Environment form

환경 스니펫(Admin > Environments > Get Snippet)은 로더와 noscript URL에 `&gtm_auth=<token>&gtm_preview=env-<n>&gtm_cookies_win=x`를 더합니다. "Reset Link"는 설치된 스니펫을 무효로 만듭니다. Google: 환경은 "designed for use with non-production environments"이며 프로덕션은 표준 스니펫을 씁니다. `gtm_auth`는 비밀로 취급합니다(`rules/safety-gates.md` §3).

### Placement rules

- `<head>` 안 순서: 동의 기본값(`references/consent.md` §2) -> 컨테이너 로드에 필요한 페이지 수준 `dataLayer.push` 값 -> 컨테이너 스니펫 -> 나머지 전부.
- 컨테이너마다 페이지마다 로더 하나. 레이아웃에 스니펫을 넣고 페이지, CMS 플러그인, 다른 컨테이너 안의 태그에 또 넣지 않습니다.

## 3. Framework Recipes

| Framework | Where | How | Notes |
|---|---|---|---|
| Next.js App Router | `app/layout.tsx` | `import { GoogleTagManager, sendGTMEvent } from '@next/third-parties/google'`; `<html><GoogleTagManager gtmId="GTM-XXXXXXX" /><body>...</body></html>` | Props: `gtmId` 또는 `gtmScriptUrl`, `dataLayer`, `dataLayerName`, `auth`, `preview`, `nonce`. "fetches the original inline script after hydration"(`afterInteractive`)이며 noscript를 렌더링하지 않고 ID가 서버 HTML에 없으므로 점검에는 렌더링된 확인이 필요합니다. 이벤트는 `sendGTMEvent({ event: '...', ... })`로 넣습니다. |
| Next.js Pages Router | `pages/_app.tsx` | 앱 루트 안에 같은 컴포넌트 | 같은 주의 사항 |
| Next.js with consent defaults | `app/layout.tsx` | `gtag('consent','default',...)` 호출을 담은 `<Script id="consent-default" strategy="beforeInteractive">`를 `GoogleTagManager` 앞에 둡니다 | `beforeInteractive` 스크립트는 초기 HTML에 들어갑니다 |
| Nuxt | `nuxt.config.ts` | `@nuxt/scripts`: `scripts.registry.googleTagManager: { id: 'GTM-XXXXXXX' }` 또는 `useScriptGoogleTagManager({ id })` | 옵션에 `l`, `auth`, `preview`, `defaultConsent`(`gtm.js` 전에 대기), `trigger`(기본 `onNuxtReady`)가 있습니다. `proxy.dataLayer.push(...)`로 넣습니다 |
| Astro | `src/layouts/*.astro` `<head>` | 스니펫을 `is:inline`으로 붙여 넣습니다. `@astrojs/partytown`을 쓰면 `type="text/partytown"`과 `partytown({ config: { forward: ['dataLayer.push'] } })`를 씁니다 | `forward`가 없으면 메인 스레드의 푸시가 워커에 도달하지 않습니다 |
| SvelteKit | `src/app.html` `<head>` | `%sveltekit.head%` 위에 스니펫을 붙여 넣습니다 | 컴포넌트에서 `window.dataLayer.push`로 넣습니다 |
| Vite or React SPA | `index.html` `<head>` | 스니펫을 붙여 넣습니다 | SPA 규칙(§4)을 더합니다 |
| TanStack Start, Remix, React Router | 루트 라우트의 문서 `<head>` | 루트 문서에 `<script>` 요소로 스니펫을 렌더링합니다(인라인 부분은 `dangerouslySetInnerHTML`) | 서버 렌더링이라 서버가 보낸 HTML 확인이 작동합니다 |
| WordPress | 테마 `header.php`의 `wp_head()` 시작 뒤, 또는 플러그인 하나 | 방법 하나만 씁니다. 플러그인(예: Site Kit by Google)이나 테마 중 하나이고 둘 다 아닙니다 | `gtm-detect.sh`와 서버가 보낸 페이지에서 다른 플러그인의 두 번째 로더를 확인합니다 |
| Static HTML | 모든 페이지의 `<head>` | 공용 include에 스니펫을 붙여 넣습니다 | |

- 모든 프레임워크 설치를 서버가 보낸 페이지(`scripts/gtm-site-check.sh`)에서, 클라이언트가 주입하는 로더(Next.js 컴포넌트, Nuxt Scripts)는 렌더링된 브라우저에서 검증합니다.
- Shopify 결제와 다른 샌드박스 픽셀 런타임은 제한된 워커에서 사용자 픽셀을 실행합니다. 그곳의 GTM은 페이지 수준 설치가 아닙니다. 표준 레시피 밖으로 보고 그 사실을 밝힙니다. [INFERENCE from the platform's sandbox description]

## 4. SPA Page Views

- GA4 향상된 측정은 "each time the page loads or the browser history state is changed by the active site"마다 `page_view`를 보내며 `pushState`, `popState`, `replaceState`를 듣습니다. 브라우저 기록 부분은 Page views 옵션의 고급 설정입니다.
- 경로 변경 `page_view`의 원천을 정확히 하나 고릅니다.
  - 향상된 측정 기록 이벤트를 켜고, History Change나 사용자 경로 이벤트에 GTM page_view 태그를 두지 않습니다. (가장 단순합니다.)
  - 향상된 측정 기록 이벤트를 끄고, History Change 트리거나 라우터가 넣는 사용자 `virtual_page_view` dataLayer 이벤트에 GA4 이벤트 태그 `page_view` 하나를 둡니다.
- 증명: 렌더링된 브라우저에서 경로 변경마다 `en=page_view`인 `/g/collect` 요청 하나.

## 5. Content Security Policy

- nonce를 인식하는 컨테이너 코드(nonce 전파가 있는 이전 형태):

```html
<script nonce='{SERVER-GENERATED-NONCE}'>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;var n=d.querySelector('[nonce]');
n&&j.setAttribute('nonce',n.nonce||n.getAttribute('nonce'));f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','GTM-XXXXXXX');</script>
```

- GTM은 "will then propagate the nonce to any scripts that it adds to the page"입니다. `'unsafe-inline'`은 권장하지 않는 대체 수단입니다. 현재 단일 블록 형태에는 스크립트가 둘이고 둘 다 nonce가 필요합니다.
- GTM 최소값: `script-src-elem https://www.googletagmanager.com`, `img-src https://www.googletagmanager.com`, `connect-src https://www.googletagmanager.com https://www.google.com`. GA4를 쓰면 `img-src https://*.google-analytics.com`과 `connect-src https://*.google-analytics.com`을 더합니다. Google 최상위 도메인마다 따로 나열하며, CSP는 호스트 오른쪽에 와일드카드를 두지 않습니다.
- Preview 모드는 `script-src-elem`과 `style-src`에 `https://tagmanager.google.com`, `style-src`에 `https://fonts.googleapis.com`, `img-src`에 `https://ssl.gstatic.com https://www.gstatic.com`, `font-src`에 `https://fonts.gstatic.com data:`를 더합니다. 디버그 세션은 `tagassistant.google.com`도 쓰므로 Preview를 돌리는 환경에서 허용합니다.
- GTM은 서비스 워커를 등록할 수 있습니다. Google CSP 표는 이를 위해 `frame-src https://www.googletagmanager.com`을 요구합니다(`volatile`).
- Custom JavaScript 변수는 "evaluate to `undefined` in the presence of a CSP unless the `'unsafe-eval'` directive is given"입니다. `'unsafe-eval'`을 더하기보다 사용자 템플릿을 권합니다.
- 컨테이너의 제3자 태그마다 자기 호스트가 필요합니다. 렌더링된 Preview 세션의 CSP 위반 보고서에서 읽습니다.

## 6. First-Party Serving and Performance

- 광고주용 Google tag gateway는 사이트 자체 도메인의 경로(예: `/metrics/`)로 CDN이나 오리진을 통해 GTM을 제공합니다(`volatile`, Cloudflare, Akamai, Fastly, CloudFront, GCP). 경로는 `/`가 아니고 최대 100자입니다. noscript 스니펫은 지원하지 않습니다. Next.js에서는 `gtmScriptUrl="/metrics/?id=GTM-XXXXXXX"`를 씁니다. 설정은 CDN이나 DNS 구성을 바꾸므로 `rules/safety-gates.md`의 승인 등급입니다.
- 서버 측 태깅은 별도의 태깅 서버입니다. `references/container-design.md` §8을 봅니다.
- 비용: "Google Tag Manager limits container size to 300 KB and warns about container size after it's reached 70% of the size limit"이며 컨테이너 중앙값은 약 50 KB, 라이브러리는 압축 약 33 KB입니다. `gtm.js`는 `cache-control: private, max-age=900`으로 제공됩니다(2026-11-08 관측).
- web.dev: "Use only one container per page", 필수가 아닌 태그는 `Window Loaded` 뒤에 발화시키고, 이미지 픽셀이 가장 싸고 그다음 사용자 템플릿, 그다음 Custom HTML입니다. Preview 모드는 느리므로 Preview의 Web Vitals를 프로덕션과 비교하지 않습니다.
- GTM으로 UX 기능을 불러오지 않습니다. "some users block tag managers. Using a tag manager to implement UX features may result in a broken website for some of your users."

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| 현재와 이전 스니펫 형태, 배치, 재태깅 불필요 | <https://support.google.com/tagmanager/answer/14847097> |
| 도메인당 컨테이너 하나 | <https://support.google.com/tagmanager/answer/6103576> |
| GTM 대 Google 태그, 중복 태그 시스템 회피, 컨테이너 ID 접두사 | <https://developers.google.com/tag-platform/devguides/prerequisites>, <https://support.google.com/tagmanager/answer/17070049> |
| `gtm.js`의 비 GTM ID 미지원, `gtag('config')` 폐기, 2026-10-08 변경 | <https://support.google.com/tagmanager/answer/17231523>, <https://developers.google.com/tag-platform/gtagjs/reference>, <https://support.google.com/tagmanager/answer/4620708> |
| 환경과 그 스니펫 | <https://support.google.com/tagmanager/answer/6311518> |
| Next.js 컴포넌트 props와 동작 | <https://nextjs.org/docs/app/guides/third-party-libraries>, <https://github.com/vercel/next.js/blob/canary/packages/third-parties/src/google/gtm.tsx> |
| Nuxt Scripts GTM 옵션 | <https://scripts.nuxt.com/scripts/tracking/google-tag-manager> |
| Partytown forward 설정 | <https://docs.astro.build/en/guides/integrations-guide/partytown/>, <https://partytown.qwik.dev/google-tag-manager/> |
| 향상된 측정 기록의 페이지 뷰 | <https://support.google.com/analytics/answer/9216061> |
| CSP nonce 스니펫, 호스트, Custom JavaScript 변수 | <https://developers.google.com/tag-platform/security/guides/csp> |
| Google tag gateway | <https://developers.google.com/tag-platform/tag-manager/gateway/setup-guide?setup=manual> |
| 컨테이너 크기, 페이지당 컨테이너 하나, 태그 유형별 비용, 태그 관리자를 통한 UX | <https://web.dev/articles/tag-best-practices> |

### Evidence grade

2026-11-08에 읽은 Google, Vercel, Nuxt, Astro 공식 문서와 관측한 응답 헤더 하나입니다. SvelteKit, TanStack Start, Remix, WordPress, Shopify 행은 각 프레임워크의 문서 head 관례를 따르며 이번 실행에서 다시 읽지 않았습니다.
