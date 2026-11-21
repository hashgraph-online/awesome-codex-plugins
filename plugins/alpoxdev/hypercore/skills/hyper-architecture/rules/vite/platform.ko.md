# 플랫폼 설정

> Vite + TanStack Router 프로젝트에서 아키텍처 리뷰가 강제해야 하는 설정 규칙

---

## Vite 8 툴체인

Vite 8(현재 안정 8.3.6)은 Rollup과 esbuild 대신 Rolldown과 Oxc로 동작합니다. Node 20.19+ 또는 22.12+를 요구하고 ESM으로만 배포됩니다.

- 빌드 설정은 새 이름을 씁니다. `build.rollupOptions`(deprecated 별칭) 대신 `build.rolldownOptions`, `esbuild`(deprecated, 자동 변환) 대신 `oxc`, `optimizeDeps.esbuildOptions` 대신 `optimizeDeps.rolldownOptions`, 객체형이 제거되고 함수형이 deprecated된 `output.manualChunks` 대신 Rolldown `output.codeSplitting`입니다. `build.commonjsOptions`는 no-op입니다.
- `build.target` 기본값은 `'baseline-widely-available'`이고 이 메이저에서는 `['chrome111', 'edge111', 'firefox114', 'safari16.4', 'ios16.4']`로 해석됩니다. 구형 브라우저를 지원해야 하는 저장소는 `build.target`을 직접 지정합니다.
- `resolve.tsconfigPaths`(기본 `false`)도 있지만 문서는 더 저렴하고 명시적인 `resolve.alias`를 대안으로 제시합니다. alias는 기존처럼 Vite 설정과 TypeScript 설정 양쪽에 선언합니다.
- `server.forwardConsole`은 `@vercel/detect-agent`로 AI 코딩 에이전트가 감지되면 기본으로 켜지고, 브라우저 런타임 에러와 `console.*` 출력을 개발 서버 터미널로 넘깁니다.
- 라우트 단위 분할은 여전히 라우터 플러그인의 `autoCodeSplitting`이 맡고, 수동 청크 규칙은 `manualChunks`가 아니라 Rolldown `output.codeSplitting`으로 갑니다.
- Vite 8.1의 실험 번들 개발 모드(`experimental.bundledDev: true`)는 이 스킬의 지침에서 켜지 않습니다. 선택 기능이고 서드파티 플러그인 호환성 위험이 남아 있습니다.

---

## Vite Plugin 규칙

플러그인 순서, env 처리, 생성 라우트 트리 경로, 라우터 설정을 바꾸기 전에 API 차이는 `references/official/vite/current-docs-2026-11-04.ko.md`에서 확인합니다.

```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { tanstackRouter } from '@tanstack/router-plugin/vite'

export default defineConfig({
  plugins: [
    // tanstackRouter()는 반드시 react() 보다 앞에 위치합니다
    tanstackRouter({
      target: 'react',
      autoCodeSplitting: true,
    }),
    react(),
  ],
})
```

- `tanstackRouter()`는 명시적으로 유지하고 `target: 'react'`를 전달합니다
- `autoCodeSplitting: true`를 켜야 plugin이 route component를 자동 코드 스플릿합니다. 플러그인 기본값은 `false`이고 다음 메이저에서 `true`가 될 예정이므로 어느 쪽이든 옵션을 명시합니다.
- `tanstackRouter()`는 `react()`보다 먼저 등록합니다 (순서가 잘못되면 조용히 실패)
- router plugin을 중복 추가하지 않습니다
- `@vitejs/plugin-react` 6은 `vite: ^8.0.0`을 선언하고 Babel을 더 이상 싣지 않습니다. React Refresh는 Oxc가 처리합니다. Vite 7 저장소는 plugin-react 5에 남고, Babel 변환이 필요한 프로젝트는 플러그인 옵션이 아니라 `react()` 옆에 `@rolldown/plugin-babel`을 붙입니다.
- React Compiler 지원은 `oxc-transform-react`를 설치한 `react({ compiler: true })` 또는 `reactCompilerPreset()`과 `@rolldown/plugin-babel` 조합입니다. `compiler.reportDiagnostics`를 쓰고(`logDiagnostics`는 deprecated), 브라우저에서 실행되지 않는 파일은 `refreshInclude` / `refreshExclude`로 Fast Refresh에서 뺍니다.
- `@tanstack/router-plugin` 1.168.x의 peer는 `@tanstack/react-router ^1.170.x`입니다. 플러그인과 라우터는 같은 변경에서 함께 올립니다.
- file-convention 옵션 중 hypercore 폴더와 직결되는 것: `routeFileIgnorePrefix` 기본값이 `'-'`이라서 `-components/`, `-hooks/`가 route tree에서 제외됨; `routeToken`/`indexToken`을 커스텀하려면 `tsr.config.json`에 명시

---

## Generated File

- `routeTree.gen.ts`는 generated output입니다
- 수동 편집하지 않습니다
- 라우팅 결과가 이상하면 source route 또는 router config를 수정한 뒤 재생성합니다

`tsr.config.json`을 두는 저장소는 다음 키를 명시해서 plugin과 CLI가 같은 위치를 보도록 유지합니다:

```json
{
  "routesDirectory": "./src/routes",
  "generatedRouteTree": "./src/routeTree.gen.ts"
}
```

`routeToken`, `indexToken`, `routeFilePrefix`, `routeFileIgnorePrefix`는 저장소가 실제로 커스텀할 때만 추가하고 그렇지 않으면 문서화된 기본값에 의존합니다.

생성 트리 포맷 옵션은 `quoteStyle`(기본 `single`), `semicolons`(기본 `false`), `addExtensions`(기본 `false`)입니다. 어떤 값을 쓰든 생성 라우트 트리 경로는 린터와 포매터에서 제외해 둘이 서로 덮어쓰지 않게 합니다.

---

## Router 설정

- router wiring은 `src/router.tsx`에서 명시적으로 유지합니다
- root context 설정은 router/root-route 파일에서 쉽게 찾을 수 있어야 합니다
- 저장소가 SSR 또는 manual rendering을 추가하면 process-global singleton보다 per-request fresh router factory를 선호합니다 (module-level QueryClient는 SSR 요청 간 데이터 leak)
- 표준 `createRouter` 옵션: `defaultPreload: 'intent'`, `defaultPreloadStaleTime: 0`, `scrollRestoration: true`를 명시하고, `Wrap`으로 `QueryClientProvider`를 마운트합니다
- `scrollRestoration: true`는 옵션으로 설정합니다. `<ScrollRestoration />` 컴포넌트는 동작하지만 deprecated입니다.
- `search.strict: true`는 `validateSearch`가 반환하지 않는 search param을 버립니다. 엉뚱한 URL 파라미터가 앱 상태로 들어오면 안 될 때 켭니다. loader 캐시 기본값(`staleTime`, preload 신선도, `gcTime`, `staleReloadMode`, `shouldReload`)은 `rules/vite/routes.md`가 맡습니다.
- 하위 경로에 배포할 때는 Vite `base`와 라우터 `basepath`를 맞춥니다(예: `basepath: import.meta.env.BASE_URL`). 두 값을 맞추는 것은 Hypercore guidance이고, 각 옵션은 따로 문서화되어 있습니다.
- 라우터 상태는 `router.state`(`matches`, `status`, `isLoading`)에서 읽습니다. `@tanstack/router-core` 1.171.16부터 `RouterState`에 `loadedAt`, `isTransitioning`, `statusCode`, `redirect`가 없고, `match.status`에 `'redirected'`가 없으며, `getMatch()`, `updateMatch()`, `cancelMatch()`가 없습니다.

```tsx
// src/router.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createRouter, RouterProvider } from '@tanstack/react-router'
import { routeTree } from './routeTree.gen'

export const createAppRouter = () => {
  // 요청마다 새 QueryClient — SSR 데이터 leak 방지
  const queryClient = new QueryClient()

  return createRouter({
    routeTree,
    context: { queryClient },
    defaultPreload: 'intent',
    defaultPreloadStaleTime: 0,
    scrollRestoration: true,
    Wrap: ({ children }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    ),
  })
}

declare module '@tanstack/react-router' {
  interface Register {
    router: ReturnType<typeof createAppRouter>
  }
}
```

- root route는 `createRootRouteWithContext<{ queryClient: QueryClient }>()` 팩토리 패턴을 써서 nested route까지 context 타입을 유지합니다
- SSR 스트리밍 + TanStack Query를 쓸 때는 같은 factory 안에서 `@tanstack/react-router-ssr-query`의 `setupRouterSsrQueryIntegration({ router, queryClient })`를 연결합니다. 이 패키지(1.167.x)의 peer는 `@tanstack/react-router >= 1.170.33`, `@tanstack/react-query >= 5.102.0`이고, 앱이 이미 `QueryClientProvider`를 직접 마운트한다면 `wrapQueryClient: false`로 자체 provider 래핑을 건너뜁니다.

- App entrypoint는 created router를 `RouterProvider`에 전달합니다. Router setup을 ad-hoc global 뒤에 숨기지 말고 discoverable하게 유지합니다.

---

## Route Token 과 Layout 규칙

- TanStack Router는 `route.tsx`, `posts.route.tsx` 등 `routeToken` 기반 레이아웃을 지원합니다
- hypercore는 shared layout, `beforeLoad`, shared loader 동작에 대해 folder route + `route.tsx`를 선호합니다
- 저장소가 `routeToken` 또는 `indexToken`을 커스텀했다면 `tsr.config.json`에 명시적으로 기록합니다

---

## Env 와 Alias 규칙

- 공개 가능한 클라이언트 설정은 `import.meta.env.VITE_*`를 사용합니다
- secret 값은 클라이언트에서 도달 가능한 route 코드에 두지 않습니다
- path alias는 Vite config와 TypeScript config 양쪽에서 명시적으로 유지합니다
- 중간 이상 규모 앱이면 env typing/runtime validation을 명시적으로 둡니다

---

## 리뷰 체크리스트

- `vite.config.ts`가 `tanstackRouter()`를 `react()`보다 앞에 유지하고 `autoCodeSplitting`을 명시함
- `@vitejs/plugin-react` 6을 Vite 8에서 쓰고, `@tanstack/router-plugin`이 `@tanstack/react-router`와 같은 릴리스임
- 새 빌드 설정이 `esbuild`, `build.rollupOptions`, `manualChunks`가 아니라 `oxc`, `build.rolldownOptions`, `output.codeSplitting`을 씀
- `routeTree.gen.ts`가 수동 편집되지 않고 린터·포매터에서 제외됨
- router 설정이 ad-hoc global 뒤에 숨어 있지 않고 `scrollRestoration`을 옵션으로 설정함
- `tsr.config.json`이 있다면 `routeToken`/`indexToken` 커스터마이징이 문서화되어 있음
- env와 alias 설정이 명시적임

---

## Sources

> 이 파일이 서술하는 Vite와 TanStack Router platform 사실(Rolldown/Oxc 옵션 이름, Node와 ESM 요구사항, `build.target` 기본값, `server.forwardConsole`, `defineConfig`, `react()`보다 앞선 `tanstackRouter()`, plugin-react 6의 peer와 Babel 제거, 포맷 옵션을 포함한 generated output `routeTree.gen.ts`, `routeTree`를 넘겨 구성하는 `createRouter`, `scrollRestoration` 옵션과 deprecated된 `<ScrollRestoration />` 컴포넌트, `search.strict`, `basepath`, `router.state` 표면 변경, `ImportMetaEnv`/`vite/client`, `loadEnv`)은 `references/official/vite/current-docs-2026-11-04.ko.md`에 기록된 dated snapshot에서 왔고, 그 스냅샷이 기록한 자체 검증일은 2026-11-04입니다. 저장소에 맞춘 설정 선택과 `base`/`basepath` 정합 조언은 이 패키지 자체의 guidance입니다. folder route 선호와 alias/env 명시성 요구는 Hypercore/repo-local convention입니다. 이 파일을 위해 페이지를 다시 가져오지 않았습니다. 규칙 문장과 저장소 로컬 경로 확인 2026-11-04. `vite 8.3.6` 현재 안정 수치는 2026-11-07에 스냅숏과 다시 대조했습니다.
