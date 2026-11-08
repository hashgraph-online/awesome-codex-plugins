# Renderer: React, Tailwind CSS v4, TanStack Router와 Query

> renderer는 sandbox에 갇힌 웹 앱입니다. React가 그려 내고, Tailwind v4는 renderer 빌드에서만 스타일을 입히며, TanStack Router는 hash 또는 memory history로 경로를 잇고, TanStack Query는 모든 IPC 읽기를 하나의 desktop 어댑터 뒤에서 캐시합니다.

규칙은 `references/official/electron/electron-2026-11-08.md`의 페이지가 그대로 진술하면 `official`, 이 패키지가 기본값을 고르면 `hypercore-default`로 표시합니다.

## 1. Bootstrap

- `official` — `src/renderer/src/main.tsx`에서 `createRoot`를 하나 두고, `StrictMode` 안에서 `RouterProvider` 위에 `QueryClientProvider`를 놓습니다. 개발 모드에서도 StrictMode를 유지합니다. effect 재실행으로 IPC 리스너가 중복된다면 unsubscribe가 빠진 것이지, `StrictMode`를 뺄 이유가 아닙니다.
- `hypercore-default` — `src/renderer/src/router.tsx`가 `QueryClient` 하나, history 인스턴스 하나, router 하나를 소유합니다. 다른 곳에서는 만들지 않습니다.

```tsx
// src/renderer/src/router.tsx
import { QueryClient } from '@tanstack/react-query'
import { createHashHistory, createRouter } from '@tanstack/react-router'
import { routeTree } from './routeTree.gen'
import { desktop } from './platform/desktop'

export const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, refetchOnWindowFocus: false, networkMode: 'always' } },
})

export const router = createRouter({
  routeTree,
  history: createHashHistory(),
  context: { queryClient, desktop },
  defaultPreloadStaleTime: 0,
})

declare module '@tanstack/react-router' {
  interface Register { router: typeof router }
}
```

## 2. TanStack Router

- `official` — TanStack Router는 기본으로 browser history를 씁니다. hash history는 `index.html`로 다시 쓰는 서버가 없는 환경에 맞고, memory history는 위치를 메모리에 둡니다. 인스턴스를 `createRouter({ routeTree, history })`로 넘깁니다.
- `official` — 패키징한 renderer에는 깊은 경로를 다시 쓰는 서버가 없습니다. `file://` 아래에서 `/settings` 같은 browser-history 경로는 `file:///…/index.html/settings`가 되어 새로고침이나 새 창에서 깨집니다. custom protocol을 써도 깊은 browser-history 경로를 새로고침하면 protocol handler에 없는 파일을 요청합니다.
- `hypercore-default` — 단일 창 앱에는 `createHashHistory()`를 씁니다. 앱이 독립된 위치를 여러 개 소유하면(Cherry Studio가 출하하는 패턴) 탭이나 패널마다 `createMemoryHistory()` router를 하나씩 둡니다. browser history는 `protocol.handle` 콜백이 모르는 경로를 `index.html`로 돌려보내고 그 폴백을 테스트할 때만 남깁니다.
- `official` — `@vitejs/plugin-react` 앞에 `tanstackRouter({ target: 'react', autoCodeSplitting: true })`를 두고, 둘 다 `renderer.plugins` 안에 넣습니다. 플러그인은 `routesDirectory`(기본 `./src/routes`)와 `generatedRouteTree`(기본 `./src/routeTree.gen.ts`)를 electron-vite의 `renderer.root`가 아니라 프로세스 작업 디렉터리에서 풉니다. 그래서 `join(import.meta.dirname, 'src/renderer/src/routes')` 같은 절대 경로를 넘깁니다. override가 없으면 `ENOENT … scandir '<repo>/src/routes'`로 실패합니다. `routeTree.gen.ts`는 생성물입니다. route 파일을 고치고 tree는 고치지 않습니다.
- `official` — `beforeLoad` 가드와 redirect는 이동만 제어합니다. 주입된 스크립트가 가드 route를 거치지 않고 preload API를 부를 수 있으므로, main-process handler마다 자기 작업을 스스로 승인합니다.
- `official` — route loader와 preload는 예측 실행입니다. 쓰기, 프롬프트, 대화상자 열기, native 부수 효과를 일으켜서는 안 됩니다. loader 출력을 바꾸는 검증된 search 값은 `loaderDeps`에 넣고, 의미 있는 route 계층마다 `pendingComponent`, `errorComponent`, `notFoundComponent`를 정의합니다.

## 3. TanStack Query over IPC

- `hypercore-default` — `src/renderer/src/platform/desktop.ts`만 renderer에서 `window.desktop`을 읽습니다. `{ ok: false }` 결과를 throw된 `DesktopError`로 바꿔 `queryFn`이 Query가 요구하듯 reject하게 하고, 타입이 붙은 메서드만 노출합니다.
- `official` — `queryFn`은 데이터를 resolve하거나 throw해야 합니다. query key는 `queryFn`이 쓰는 모든 입력을 담은 직렬화 가능한 배열입니다.
- `hypercore-default` — `features/<domain>/` 아래 도메인마다 `queryOptions`를 한 번 정의합니다. route loader는 component가 `useSuspenseQuery`로 읽는 것과 같은 옵션으로 `ensureQueryData`를 부릅니다. mutation은 desktop 어댑터를 부르고 영향받은 key만 무효화합니다.
- `official` — Query는 기본적으로 데이터를 stale로 보고 mount, window focus, reconnect 때 다시 가져옵니다. renderer에서 `focusManager`가 `visibilitychange`를 듣습니다. 그래서 desktop 창에서는 alt-tab마다 IPC 읽기가 다시 돌 수 있습니다. 웹 기본값을 그대로 두지 말고 query마다 `staleTime`과 `refetchOnWindowFocus`를 의도적으로 고릅니다. focus 재조회를 원하면 main이 preload로 밀어 주는 `BrowserWindow` `focus`·`blur` 이벤트로 `focusManager.setEventListener`를 구동합니다.
- `official` — Query의 기본 `networkMode: 'online'`은 Chromium이 offline을 보고하는 동안 query를 멈춥니다. 네트워크가 필요 없는 `queryFn`에는 `'always'`가 문서화된 모드입니다. IPC 기반 query는 `'always'`를 쓰고, 원격 API에 닿는 query는 `'online'`을 유지합니다.
- `official` — IPC 호출에 `AbortSignal`을 넘겨도 main의 작업은 취소되지 않습니다. native 취소에는 별도 채널이 필요합니다(취소 메시지나 main이 지켜보는 `MessagePort`).
- `hypercore-default` — main이 밀어 주는 데이터(파일 watcher, 다운로드 진행률, 업데이트 상태)는 preload의 `on*` 구독 하나를 effect에서 걸어 `queryClient.setQueryData`나 `invalidateQueries`로 Query에 넣고, unsubscribe 함수를 반환합니다. 같은 데이터를 `refetchInterval`로 또 폴링하지 않습니다.
- `hypercore-default` — 테스트는 테스트마다 `retry: false`와 가짜 desktop 어댑터로 새 `QueryClient`를 만들고, 실제 `window.desktop`은 건드리지 않습니다.

## 4. Tailwind CSS v4

- `official` — `tailwindcss`와 `@tailwindcss/vite`를 설치하고, renderer Vite 플러그인에 `tailwindcss()`를 더하며, renderer CSS 진입 파일에 `@import "tailwindcss";`를 넣습니다. 버전 4에는 `tailwind.config.js`도 PostCSS 설정도 필요 없습니다. 테마 값은 CSS에서 `@theme`, 플러그인은 `@plugin`, 사용자 variant는 `@custom-variant`로 둡니다.
- `official` — 플러그인은 renderer 빌드에만 속합니다. `electron.vite.config.ts`에서는 `renderer.plugins`입니다. 루트나 `main`에 붙인 플러그인은 renderer를 훑지 않고 Node 빌드만 느리게 합니다.
- `official` — 자동 소스 탐지는 `.gitignore`에 걸린 경로와 `node_modules`를 건너뜁니다. renderer 루트 밖의 class 출처(워크스페이스 UI 패키지, `node_modules` 컴포넌트 라이브러리)는 `@source`로 등록하고, fixture는 `@source not`으로 제외합니다.
- `official` — Tailwind v4는 Safari 16.4, Chrome 111, Firefox 128을 대상으로 합니다. 지원하는 모든 Electron major가 훨씬 최신 Chromium을 출하하므로 v3 호환 모드나 추가 PostCSS 단계가 필요 없습니다.
- `hypercore-default` — dark mode는 `@custom-variant dark (&:where(.dark, .dark *));`와, main이 preload로 알려 주는 OS 테마(`nativeTheme`)에서 `<html>`에 붙는 class로 구현합니다. 그러면 창 배경, 타이틀 바, CSS가 서로 맞습니다.
- `hypercore-default` — 디자인 토큰은 `main.css`의 `@theme` 블록 하나에 둡니다. 공유 컴포넌트 라이브러리는 자체 CSS를 갖고 `@source`로 끌어옵니다. class를 복사해 오지 않습니다.

## Review gate

1. renderer 파일이 `platform/desktop.ts` 밖에서 `window.desktop`을 읽거나 `electron` 또는 `node:*`를 import합니다.
2. router가 browser history를 쓰는데 프로덕션은 `file://`이나, 테스트한 `index.html` 폴백이 없는 protocol handler로 로드합니다.
3. router 플러그인이 React 플러그인 뒤에 오거나, 둘 중 하나 또는 Tailwind가 `renderer.plugins` 밖에 있습니다.
4. `QueryClient`나 router가 둘 이상 있거나, loader와 component가 다른 query 옵션을 씁니다.
5. `queryFn`이 `{ ok: false }` 봉투를 데이터로 반환하고 throw하지 않습니다.
6. IPC를 부르는 query의 window-focus 재조회 정책이 이유 설명 없이 웹 기본값으로 남아 있습니다.
7. push 구독에 unsubscribe가 없거나, 밀어 주는 데이터를 또 폴링합니다.
8. `@tailwindcss/vite`와 함께 `tailwind.config.js`나 PostCSS Tailwind 단계가 이전 메모 없이 남아 있습니다.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| Browser, hash, memory history와 `createRouter`로 인스턴스 넘기기 | https://tanstack.com/router/latest/docs/framework/react/guide/history-types |
| Router 플러그인 순서, `routesDirectory`, `generatedRouteTree` | https://tanstack.com/router/latest/docs/framework/react/installation/with-vite |
| loader, preload, guard, route 상태 동작 | https://tanstack.com/router/v1/docs/framework/react/guide/data-loading, https://tanstack.com/router/v1/docs/framework/react/guide/authenticated-routes |
| Query 기본값, `focusManager`, network 모드, query key, query 함수 | https://tanstack.com/query/latest/docs/framework/react/guides/important-defaults, https://tanstack.com/query/latest/docs/reference/focusManager, https://tanstack.com/query/latest/docs/framework/react/guides/network-mode, https://tanstack.com/query/latest/docs/framework/react/guides/query-keys |
| electron-vite renderer 안에서 `routesDirectory`가 작업 디렉터리에서 풀리는 문제 | https://github.com/TanStack/router/issues/1170 |
| Tailwind v4 Vite 설치, CSS 우선 설정, 브라우저 대상 | https://tailwindcss.com/docs/installation/using-vite, https://tailwindcss.com/docs/theme, https://tailwindcss.com/docs/compatibility |
| 소스 탐지와 `@source` | https://tailwindcss.com/docs/detecting-classes-in-source-files |
| dark mode custom variant | https://tailwindcss.com/docs/dark-mode |
| `file://`에서 browser-history route가 깨지는 문제, 탭별 memory router, desktop에서 hash history | surveyed apps: https://github.com/CherryHQ/cherry-studio, https://github.com/chatboxai/chatbox |
| desktop 어댑터, 봉투를 throw로 바꾸는 규칙, push를 캐시에 넣는 패턴, 토큰 위치 | 이 패키지의 관례, 공식 요구 사항 아님 |
