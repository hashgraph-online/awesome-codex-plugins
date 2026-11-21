# Vite + TanStack Router 공식 문서 스냅숏 (2026-11-04 기준)

> 버전에 민감한 Vite 8 + TanStack Router 아키텍처 판단에 쓰는 공식 문서 사실 모음입니다.

last_verified_at: 2026-11-04
checked_at: 2026-11-04
patch_checked_at: 2026-11-07 (stable_versions의 `vite`와 `@tanstack/react-query`, 아래 React Compiler 네이티브 경로 상태)
library_ids: `/websites/vite_dev`, `/tanstack/router`
stable_versions: vite 8.3.6, @vitejs/plugin-react 6.2.1, @tanstack/react-router 1.170.46, @tanstack/router-plugin 1.168.48, @tanstack/react-query 5.107.1, @tanstack/router-core 1.171.39, zod 4.6.7
source_priority: 공식 Vite 문서, Vite 8 릴리스 글, `vitejs/vite`와 `vitejs/vite-plugin-react` 체인지로그, 공식 TanStack Router·TanStack Query 문서, npm 레지스트리.

## 현재 공식 Vite 사실

- Vite 8은 esbuild와 Rollup 대신 Rolldown과 Oxc 기반 도구를 씁니다. Rolldown이 개발 의존성 최적화와 프로덕션 빌드의 단일 번들러이고, Oxc가 자바스크립트 변환과 압축을 맡습니다.
- `esbuild` 옵션은 deprecated이고 내부에서 `oxc` 옵션으로 변환됩니다. `build.rollupOptions`는 `build.rolldownOptions`의 deprecated 별칭이고, `worker.rollupOptions`는 `worker.rolldownOptions`의 deprecated 별칭이며, `build.commonjsOptions`는 no-op입니다. `optimizeDeps.esbuildOptions`는 `optimizeDeps.rolldownOptions`로 대체되어 deprecated입니다.
- `build.rollupOptions.output.manualChunks`의 객체형은 제거되었고 함수형은 deprecated입니다. 둘 다 Rolldown의 `output.codeSplitting`이 대체합니다.
- Vite 8은 Node.js 20.19+ 또는 22.12+를 요구하고 ESM으로만 배포됩니다.
- `build.target` 기본값은 특수 값 `'baseline-widely-available'`이고, 이 메이저에서는 `['chrome111', 'edge111', 'firefox114', 'safari16.4', 'ios16.4']`로 해석됩니다. 구형 브라우저를 지원해야 하는 프로젝트는 `build.target`을 직접 지정해야 합니다.
- Vite는 `VITE_` 접두사가 붙은 env 변수만 `import.meta.env`를 통해 클라이언트 코드에 노출합니다. `DB_PASSWORD`처럼 접두사가 없는 값은 브라우저 코드에 노출되지 않습니다.
- `import.meta.env` 값은 애플리케이션 코드가 파싱하지 않는 한 문자열입니다.
- `vite-env.d.ts`에서 `ImportMetaEnv`를 확장해 env 타입을 붙일 수 있고, `vite/client` 타입이 asset import, `import.meta.env`, HMR API의 타입 선언을 제공합니다.
- 설정 파일 자체에서 env 값이 필요하면 `loadEnv(mode, process.cwd(), '')`를 씁니다. 설정용으로 모든 env 값을 읽었다고 해서 그 값이 클라이언트 코드에 안전한 것은 아닙니다.
- `defineConfig`가 표준 설정 헬퍼입니다. 아키텍처가 의존하는 `resolve.alias`, 플러그인, 서버 옵션, 빌드 옵션은 명시적으로 둡니다. `resolve.tsconfigPaths`(기본 `false`)도 있지만, 문서는 더 저렴하고 명시적인 `resolve.alias`를 대안으로 제시합니다.
- `server.forwardConsole`은 `@vercel/detect-agent`로 AI 코딩 에이전트가 감지되면 `true`, 아니면 `false`가 기본입니다. 브라우저 런타임 에러와 `console.*` 출력을 개발 서버 터미널로 넘깁니다.
- `public/` 자산은 정적 공개 자산으로 제공됩니다. `src/lib`나 `src/services` 같은 애플리케이션 소스 구성은 프로젝트 관례이지 공식 Vite 요구사항이 아닙니다.

## 현재 공식 @vitejs/plugin-react 사실

- `@vitejs/plugin-react` 6.x는 `vite: ^8.0.0`을 peer dependency로 선언합니다. Vite 7 이하에서는 동작하지 않습니다.
- Vite 8이 React Refresh 변환을 Oxc로 처리하므로 plugin-react 6은 Babel에 의존하지 않습니다. 플러그인의 Babel 옵션은 6.0.0에서 제거되었습니다.
- Babel 변환이 여전히 필요한 프로젝트는 플러그인 옵션이 아니라 `react()` 옆에 `@rolldown/plugin-babel`을 붙입니다.
- React Compiler 지원은 `oxc-transform-react`를 설치하고 `react({ compiler: true })`를 쓰거나, `reactCompilerPreset()`과 `@rolldown/plugin-babel`을 조합합니다.
- 네이티브 `compiler` 경로는 **experimental**입니다. 플러그인 README가 그렇게 표시하고, `@vitejs/plugin-react` 6.2.0 기준 `oxc-transform-react >=0.152.0 <0.157.0`을 peer로 선언합니다. 그 표시가 바뀌기 전까지 프로덕션에는 `reactCompilerPreset()`을 우선합니다. (2026-11-07 재확인.)
- `compiler.reportDiagnostics`가 deprecated된 `compiler.logDiagnostics`(6.1.2)를 대체합니다. `refreshInclude`와 `refreshExclude`는 브라우저에서 실행되지 않는 파일의 Fast Refresh를 건너뜁니다. 플러그인의 `main` README에는 아직 `logDiagnostics`가 적혀 있으므로 체인지로그가 기준입니다.

## 현재 공식 TanStack Router 사실

- Vite에서는 TanStack Router 플러그인을 `@tanstack/router-plugin/vite`에서 설정하고 `@vitejs/plugin-react` / `react()`보다 앞에 둡니다.
- 공식 Vite 예시는 `tanstackRouter({ target: 'react', autoCodeSplitting: true })` 다음에 `react()`를 두는 형태입니다.
- `@tanstack/router-plugin` 1.168.48의 peer dependency는 `@tanstack/react-router: ^1.170.46`입니다. 플러그인과 라우터는 짝을 맞춰 올립니다.
- 플러그인이 파일 기반 라우팅, 라우트 트리 생성, 라우트 단위 코드 스플리팅을 켭니다.
- `autoCodeSplitting`의 기본값은 `false`이고, 다음 메이저(v2)에서 `true`가 될 예정이라고 문서에 적혀 있습니다.
- 생성 라우트 트리 포맷 옵션이 문서화되어 있습니다. `quoteStyle` 기본 `single`, `semicolons` 기본 `false`, `addExtensions` 기본 `false`입니다.
- `routeTree.gen.ts`는 소스 라우트 파일에서 생성됩니다. 아키텍처 작업은 생성 산출물을 손으로 고치지 않고 소스 라우트와 설정을 고치며, 이 파일 경로는 린터와 포매터에서 제외합니다.
- React 라우터 설정은 `./routeTree.gen`에서 `routeTree`를 import하고 `createRouter({ routeTree, ... })`로 라우터를 만든 뒤 `RouterProvider`에 넘깁니다.
- 파일 라우트는 `export const Route = createFileRoute(...)({ ... })` 같은 exported route 객체를 씁니다.
- search params는 `validateSearch`로 검증합니다. Zod v4에서는 스키마를 `validateSearch`에 직접 넘기고 `.catch()`가 타입 추론을 유지합니다. Zod v3에서는 `@tanstack/zod-adapter`의 `zodValidator`와 `fallback`을 씁니다. 어댑터의 현재 peer dependency는 `zod: ^3.23.8`이라 Zod 4 프로젝트를 덮지 않습니다.
- `search.strict`(라우터 옵션, 기본 `false`)는 `validateSearch`가 반환하지 않는 search param을 제거합니다.
- route loader는 자체 캐시를 가집니다. 기본 `staleTime`은 `0`, preload 데이터는 30초 동안 신선하고, `gcTime`과 `preloadGcTime` 기본값은 5분, `staleReloadMode` 기본값은 `'background'`이며 `shouldReload`로 재로드를 막을 수 있습니다. TanStack Query가 캐시를 소유하면 라우터에 `defaultPreloadStaleTime: 0`을 두도록 문서가 권합니다.
- TanStack Query용으로 문서화된 loader 형태는 `queryClient.query({ ...queryOptions, staleTime: 'static' })`와 `useSuspenseQuery`의 조합이고 `ensureQueryData`가 아닙니다.
- `<ScrollRestoration />` 컴포넌트는 동작하지만 deprecated입니다. `scrollRestoration` 라우터 옵션은 그대로 유효합니다.
- `basepath`(라우터 옵션, 기본 `/`)는 라우터를 하위 경로에 마운트합니다.
- `@tanstack/router-core` 1.171.16(배포 완료, 최신 안정 1.171.39)부터 `RouterState`에 `loadedAt`, `isTransitioning`, `statusCode`, `redirect`가 없고, `RouteMatch.status`에 `'redirected'`가 없으며, `RouterCore`가 `getMatch()`, `updateMatch()`, `cancelMatch()`를 노출하지 않습니다.
- `@tanstack/react-router-ssr-query` 1.167.3은 `setupRouterSsrQueryIntegration({ router, queryClient })`로 SSR 스트리밍을 연결하고, `wrapQueryClient: false`로 자체 provider 래핑을 건너뛸 수 있습니다.
- route loader는 비공개 백엔드 경계가 아닙니다. loader 코드와 라우트 모듈을 클라이언트에서 닿는 코드로 취급하고, 비밀 값, DB 클라이언트, 파일 시스템 접근, 권한이 필요한 SDK는 실제 백엔드/API 경계 뒤에 둡니다.

## 현재 공식 TanStack Query 사실

- `fetchQuery`, `prefetchQuery`, `ensureQueryData`와 infinite query 변형들이 deprecated이며 다음 메이저에서 제거됩니다.
- `queryClient.query(options)`가 `fetchQuery`를 대체하고, `queryClient.query({ ...options, staleTime: 'static' })`가 `ensureQueryData`를 대체하며, `queryClient.infiniteQuery(...)`가 infinite 변형을 대체합니다.
- `query()`는 기본적으로 재시도를 끄고(`retry: false`) fetch 에러로 reject합니다. `enabled`, `refetchOn*`, `throwOnError`, `suspense`, `placeholderData`처럼 observer 전용인 옵션은 받지 않습니다.
- `prefetchQuery` 마이그레이션 안내는 `queryClient.query(options)`를 쓰고 에러는 `.catch(noop)`로 삼키라는 것입니다.
- `staleTime`은 `number | 'static'`을 받고, `'static'`이면 데이터가 절대 stale이 되지 않습니다.

## Hypercore 해석

- `src/lib/<domain>/`과 `src/services/<domain-or-provider>/`는 소유권과 런타임 경계를 드러내는 Hypercore/저장소 로컬 관례입니다. 공식 Vite나 TanStack Router 요구사항이 아닙니다.
- 손댄 공유 루트에 `src/lib/foo.ts`나 `src/services/foo.ts` 같은 direct leaf 파일을 명시적 프로젝트 예외 없이 추가하지 않습니다.
- Vite SPA에서는 공개 클라이언트 API 래퍼를 Services에 둡니다. 이 스킬에서는 TanStack Start 서버 함수(`createServerFn`, `useServerFn`, Start middleware API)를 도입하지 않습니다.

## Sources

> 확인 2026-11-04. `vite`와 `@tanstack/react-query` 버전 행, React Compiler 네이티브 경로 상태는 2026-11-07에 다시 확인했습니다.

- `https://vite.dev/guide/migration`
- `https://vite.dev/blog/announcing-vite8`
- `https://vite.dev/config/build-options`
- `https://vite.dev/config/shared-options`
- `https://vite.dev/config/server-options`
- `https://vite.dev/guide/env-and-mode`
- `https://raw.githubusercontent.com/vitejs/vite-plugin-react/main/packages/plugin-react/CHANGELOG.md`
- `https://registry.npmjs.org/@vitejs/plugin-react/latest`
- `https://registry.npmjs.org/@tanstack/react-router/latest`
- `https://registry.npmjs.org/@tanstack/router-plugin/latest`
- `https://registry.npmjs.org/@tanstack/react-query/latest`
- `https://registry.npmjs.org/@tanstack/zod-adapter/latest`
- `https://registry.npmjs.org/@tanstack/react-router-ssr-query/latest`
- `https://tanstack.com/router/latest/docs/installation/with-vite`
- `https://tanstack.com/router/latest/docs/api/file-based-routing`
- `https://tanstack.com/router/latest/docs/guide/search-params`
- `https://tanstack.com/router/latest/docs/guide/data-loading`
- `https://tanstack.com/router/latest/docs/guide/external-data-loading`
- `https://tanstack.com/router/latest/docs/guide/scroll-restoration`
- `https://tanstack.com/router/latest/docs/api/router/RouterOptionsType`
- `https://raw.githubusercontent.com/TanStack/router/main/packages/router-core/CHANGELOG.md`
- `https://tanstack.com/query/latest/docs/framework/react/reference/QueryClient`