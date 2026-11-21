# 탑재 방식

`install` 모드에서 이 참조를 읽습니다. 탑재 방식의 순서, 프레임워크별 레시피, `gtag('config')` 변경, Partytown 주의 사항, 두 가지 선택 경로를 소유합니다.

> 영어판: [`install-methods.md`](install-methods.md)

## Contents

- Method order
- The `gtag('config')` change
- Framework recipes
- Partytown caveat
- Optional paths: tag gateway and server-side tagging

## Method order

사이트에 맞는 첫 번째 방식을 고르고, 뒤 방식을 왜 버렸는지 밝힙니다.

1. **이미 있는 GTM 컨테이너.** 페이지가 이미 `gtm.js`를 불러오면 측정을 그 컨테이너 안에서 처리하고 태그를 하나 더 붙이지 않습니다. Google 안내서는 이렇게 씁니다. "If you are installing a Google tag for the first time, we recommend using Google Tag Manager." 그 태그를 이름으로 적는 데서 이 스킬의 컨테이너 작업은 끝납니다. 컨테이너 항목 생성과 수정은 자체 승인이 붙는 별도 변경이므로, 이번 실행은 컨테이너에 데이터를 넣는 페이지 코드를 맡고 컨테이너 태그는 넘길 항목으로 적습니다. 동의 기본값 순서, 페이지뷰 출처 하나, CSP 항목, `dataLayer` 푸시입니다.
2. **프레임워크 공식 통합.** 프레임워크가 지원 컴포넌트나 모듈을 내면 손으로 쓴 스니펫 대신 그것을 씁니다. `@next/third-parties/google`, `@nuxt/scripts`, WordPress의 Site Kit, Shopify의 Google & YouTube 채널이 해당합니다.
3. **평범한 Google 태그 스니펫.** 위 어느 것도 없으면 `gtag.js`로 내려갑니다. 스니펫은 "여는 `<head>` 태그 바로 뒤"에 두고, 이벤트 호출은 스니펫 아래에 둡니다. Google은 스니펫 위에 놓인 이벤트의 데이터를 처리하지 않습니다.

방식을 가르는 제약입니다.

- `gtag.js`는 "서드파티나 커스텀 태그를 지원하지 않고 Google 서비스로만 데이터를 보낼 수 있습니다." 정적 사이트 생성기, CMS, 코드 기반 구성에는 맞고 여러 업체를 받아야 하는 컨테이너에는 틀립니다.
- `G-` 같은 목적지 접두사에 묶인 컨테이너는 "Google 태그로 제한됩니다." 여러 업체를 다루는 일은 이 스킬 범위 밖이므로 그렇다고 밝히고 멈춥니다.
- 측정 ID(`G-`와 문자·숫자 조합)는 목적지 ID와 같은 값이며 속성 ID가 아닙니다.

## The `gtag('config')` change

Google 레퍼런스는 이렇게 못 박습니다. "The `gtag('config')` command is deprecated. Use the Google Tag Manager UI to configure tag settings and destinations, or use `gtag('set')` for setting in-page parameters." 같은 페이지는 `gtag('config')`가 들어 있는 기존 스니펫이 "하위 호환을 위해 계속 동작한다"고 적고, 설치 페이지는 하드코딩한 옵션이 설정을 "페이지나 이벤트 생명주기의 특정 시점에 고정한다"는 이유를 밝힙니다.

출처와 날짜: <https://developers.google.com/tag-platform/gtagjs/reference>, 2026-11-08 확인.

새 탑재에 주는 의미입니다.

- 새 `gtag('config', 'G-...', {...})` 옵션 블록을 손으로 더하지 않습니다. 페이지가 필요로 하는 `gtag('set', ...)` 호출을 쓰고, 태그 UI로 옮겨 간 설정은 위치와 함께 보고서에 UI 단계로 적습니다.
- 프레임워크 래퍼는 내부에서 여전히 `gtag('config', ...)`를 낼 수 있습니다. Next.js `@next/third-parties/google`은 `GoogleAnalytics` 컴포넌트 안에서 `gtag('config', '<gaId>' [, {'debug_mode': true}])`를 호출합니다. 그 호출은 패키지의 계약이지 애플리케이션 코드에 베낄 패턴이 아닙니다.
- 기존 `gtag('config')` 스니펫은 발견 사항이 아닙니다. 이전은 선택이며, 손으로 쓴 옵션이 결함의 원인일 때만 권합니다.

## Framework recipes

모든 레시피는 같은 두 의무로 끝납니다. 동의 기본값이 모든 페이지의 모든 측정 명령보다 앞서고, 페이지뷰 출처가 정확히 하나입니다.

### Next.js App Router

```tsx
// app/layout.tsx
import { GoogleAnalytics } from '@next/third-parties/google';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>{children}</body>
      <GoogleAnalytics gaId="G-XXXXXXXXXX" />
    </html>
  );
}
```

- 이벤트: `sendGAEvent('event', 'buttonClicked', { value: 'xyz' })`. 컴포넌트가 마운트되기 전에 부르면 경고합니다.
- 컨테이너를 쓸 때: `<GoogleTagManager gtmId="GTM-XXXXXXX" />`와 `sendGTMEvent({ event: 'buttonClicked', value: 'xyz' })`. `gtmId`는 `gtmScriptUrl`이 태그 게이트웨이 경로를 가리키면 생략할 수 있습니다.
- 페이지뷰: 이 패키지는 브라우저 히스토리 상태가 바뀔 때 Analytics가 페이지뷰를 수집하는 것에 기댑니다. 그래서 향상된 측정의 히스토리 옵션이 켜져 있어야 하고, 그 옆에서 수동 `page_view` 호출이 돌면 안 됩니다.
- nonce: 컴포넌트는 `nonce` 속성을 받습니다. CSP를 쓰면 요청 nonce를 넘깁니다.

### Next.js Pages Router

같은 컴포넌트를 `pages/_app.js`에 한 번만 답니다.

```jsx
import { GoogleAnalytics } from '@next/third-parties/google';

export default function App({ Component, pageProps }) {
  return (
    <>
      <Component {...pageProps} />
      <GoogleAnalytics gaId="G-XXXXXXXXXX" />
    </>
  );
}
```

### React or Vite SPA

1. Google 태그 스니펫을 `index.html`의 여는 `<head>` 바로 뒤에 둡니다.
2. 페이지뷰 출처를 하나 고릅니다. 향상된 측정의 히스토리 옵션을 켜 두고 손으로는 아무것도 보내지 않거나, 페이지 로드와 히스토리 페이지뷰를 모두 끄고 경로가 바뀔 때마다 `page_title`과 `page_location`을 붙여 `page_view`를 직접 보냅니다.
3. 둘을 함께 두지 않습니다. 라우터 리스너와 히스토리 옵션이 동시에 있으면 진단 순서에 나오는 중복 집계입니다.
4. 경로가 바뀔 때 스크롤을 되돌려 참여 시간이 맞는 가상 페이지에 붙게 합니다.

### TanStack Start

TanStack에는 Google Analytics 패키지가 없습니다. 라우터를 구독해 페이지뷰를 직접 보냅니다.

```ts
router.subscribe('onResolved', (event) => {
  if (event.toLocation.pathname === event.fromLocation?.pathname) return;
  gtag('event', 'page_view', {
    page_title: document.title,
    page_location: window.location.href,
  });
});
```

`onResolved`는 분석과 다른 명령형 통합에 문서가 권하는 훅입니다. 이 구독을 두면 향상된 측정의 히스토리 옵션은 꺼야 합니다.

### Nuxt

`@nuxt/scripts`는 `googleAnalytics` 레지스트리 항목을 냅니다.

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['@nuxt/scripts'],
  scripts: {
    registry: {
      googleAnalytics: { id: 'G-XXXXXXXXXX', trigger: 'onNuxtReady' },
    },
  },
});
```

- `useScriptGoogleAnalytics()`와 그 `proxy.gtag(...)`로 이벤트를 모듈을 거쳐 보냅니다.
- 모듈의 퍼스트파티 모드는 기본으로 스크립트를 묶고 프록시합니다. 점검이 프록시 경로를 결함이라고 부르기 전에 의도된 설정인지 확인합니다.
- SPA 경로 변경에는 `useScriptEventPage`를 쓰고 `page_referrer`를 이어 붙여 `page_view`를 보내며, 히스토리 옵션은 끕니다.

### Astro

Astro는 공식 Analytics 통합을 문서에 두지 않습니다. 지원되는 두 형태입니다.

```astro
<script is:inline>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
</script>
<script is:inline async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
```

- 또는 하이드레이션되는 아일랜드에 UI 프레임워크 컴포넌트를 렌더합니다.
- `is:inline`은 스크립트를 묶거나 가공하지 않게 유지합니다. 번들된 스크립트는 순서가 바뀌어 `dataLayer`보다 먼저 실행될 수 있습니다.
- 다중 페이지 이동은 전체 페이지 로드이므로 페이지 로드 페이지뷰로 충분하고 히스토리 옵션은 필요 없습니다.

### Static HTML

모든 페이지 템플릿의 여는 `<head>` 바로 뒤에 스니펫을 붙이고, 이벤트 호출은 그 아래에, 동의 기본값은 그 위에 둡니다. 빌드 단계가 없으므로 CSP 항목은 서버나 CDN 헤더 설정에 넣습니다.

### WordPress

공식 Google 플러그인인 Site Kit을 씁니다. 코드 수정 없이 속성과 컨테이너를 연결합니다. 플러그인이 돌 수 없는 사이트에서는 테마 수준 스니펫이 대체 수단이며, Site Kit이 함께 켜져 있으면 수집이 중복됩니다.

### Shopify

Google & YouTube 판매 채널을 씁니다. 테마 수정 없이 속성을 연결하고 이커머스 이벤트를 추적합니다. `theme.liquid` 직접 수정은 대체 수단이며 채널과 함께 돌면 안 됩니다.

## Partytown caveat

Partytown은 서드파티 스크립트를 웹 워커로 옮기고, 그 때문에 전송되는 내용이 달라집니다.

- "the automatic Google Analytics 4 `user_engagement` event … is not sent when GA4 runs in Partytown."
- 페이지 종료 핸들러(`pagehide`, `visibilitychange`, `beforeunload`)는 워커에서 "신뢰할 수 없습니다".
- 메인 스레드의 `dataLayer` 호출이 태그에 닿으려면 `forward: ["dataLayer.push"]`가 필요합니다.

이 손실을 보고서에 적고, 빠진 참여 시간을 태그 결함으로 보고하지 않습니다.

## Optional paths: tag gateway and server-side tagging

둘 다 선택 사항입니다. 요청이 퍼스트파티 스크립트 제공이나 서버 컨테이너를 요구할 때만 권하고, 기본 탑재로 제시하지 않습니다.

- **Google tag gateway**는 사이트 자체 도메인에서 CDN, 로드 밸런서, 웹 서버를 통해 태그를 제공하고 일부 측정 요청을 그 퍼스트파티 도메인으로 보냅니다. 자동 경로는 스크립트를 스스로 구성하고, 안내 경로는 "수동 재태깅이 필요하며", 기존 스크립트 소스를 모두 새 측정 경로로 바꿔야 합니다. 그러지 않으면 "브라우저가 계속 Google에서 스크립트를 직접 요청합니다". 동의 모드를 쓰면 자동 스크립트 설정을 꺼야 합니다.
- **서버 측 태깅**은 `server_container_url` 구성 매개변수로 이벤트를 Google 대신 자체 컨테이너로 보냅니다. Google은 가장 오래 견디는 구성을 위해 게이트웨이와 서버 측 태깅을 함께 쓰라고 권합니다.
- 둘 다 요청이 가는 곳을 바꾸므로, 수집 증명은 새 경로에서 요청을 잡아야 합니다.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| 첫 탑재에는 GTM이 Google의 권장이고, `gtag.js`는 Google 서비스로만 데이터를 보냅니다 | <https://developers.google.com/tag-platform/gtagjs>, <https://developers.google.com/analytics/devguides/collection/ga4/tag-options> |
| `gtag('config')`는 폐기됐고 기존 스니펫은 계속 동작하며, 하드코딩 옵션은 설정을 생명주기 한 지점에 고정합니다 | <https://developers.google.com/tag-platform/gtagjs/reference>, <https://developers.google.com/tag-platform/gtagjs/install> |
| Next.js는 App·Pages Router용 `GoogleAnalytics`, `GoogleTagManager`, `sendGAEvent`, `sendGTMEvent`를 냅니다 | <https://nextjs.org/docs/app/guides/third-party-libraries>, <https://nextjs.org/docs/pages/guides/third-party-libraries> |
| Next.js `GoogleAnalytics` 컴포넌트는 `gtag('config', ...)`를 냅니다 | <https://github.com/vercel/next.js/blob/canary/packages/third-parties/src/google/ga.tsx> |
| TanStack Router는 분석용으로 `router.subscribe('onResolved', ...)`를 문서에 둡니다 | <https://tanstack.com/router/latest/docs/framework/react/guide/router-events> |
| `@nuxt/scripts`는 퍼스트파티 모드가 있는 `googleAnalytics` 레지스트리 항목을 냅니다 | <https://scripts.nuxt.com/scripts/google-analytics> |
| Astro는 `is:inline`과 Partytown으로 클라이언트 스크립트를 다루고 공식 Analytics 통합은 없습니다 | <https://docs.astro.build/en/guides/client-side-scripts/>, <https://docs.astro.build/en/guides/integrations-guide/partytown/> |
| Site Kit과 Shopify Google & YouTube 채널이 공식 노코드 경로입니다 | <https://wordpress.org/plugins/google-site-kit/>, <https://help.shopify.com/en/manual/reports-and-analytics/google-analytics/google-analytics-setup> |
| Partytown은 자동 `user_engagement` 이벤트를 보내지 않고 페이지 종료 핸들러를 신뢰할 수 없게 만듭니다 | <https://partytown.qwik.dev/trade-offs/> |
| 태그 게이트웨이는 퍼스트파티 도메인에서 태그를 제공하고, 안내 경로는 수동 재태깅이 필요합니다 | <https://developers.google.com/tag-platform/tag-manager/gateway>, <https://support.google.com/tagmanager/answer/16061406> |
| `server_container_url`은 이벤트를 자체 서버 컨테이너로 보냅니다 | <https://developers.google.com/tag-platform/tag-manager/server-side/intro> |

### Evidence grade

인용 문장, 컴포넌트 속성, 엔드포인트 동작은 위 페이지를 2026-11-08에 읽은 `MEASURED`입니다. 방식 순서와 옮겨 간 설정을 UI 단계로 적으라는 지시는 이 패키지가 폐기 안내 위에서 세운 `LOCAL` 설계입니다. Vite, Astro, 정적 HTML 레시피는 프레임워크별 Google 페이지가 아니라 스니펫 배치 규칙과 단일 페이지뷰 규칙을 조합한 것입니다.
