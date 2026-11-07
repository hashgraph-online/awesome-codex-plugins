# 성능

> intent preload를 켜고, 라우트 컴포넌트는 라우터가 분할하게 두며, 캐시 최신성은 정확히 한 계층이 소유합니다.

규칙은 날짜가 붙은 스냅숏에서 연 페이지가 그대로 진술하면 `official`, 이 패키지가 기본값으로 고르면 `hypercore-default`로 표시합니다. 순서는 흔한 영향 순이며 측정으로 매긴 순위가 아닙니다.

## Measure first

| 목표 | 명령 또는 도구 |
|---|---|
| 프로덕션 빌드 | Start 플러그인을 거치는 `vite build` |
| 프로덕션 서버 미리보기 | `vite preview` 또는 프로젝트의 프로덕션 시작 명령 |
| 파일별 transform 시간 | `vite --debug plugin-transform` |
| 번들 구성 | 프로덕션 빌드에 붙인 Rolldown 호환 visualizer |
| 내비게이션과 라우트 타이밍 | TanStack Router devtools와 프로덕션 빌드의 Performance 패널 |
| 필드 Core Web Vitals | `useReportWebVitals` 또는 동등한 RUM hook |
| 랩 Core Web Vitals | 프로덕션 배포에 대한 `lhci autorun` |

라우트 loader와 preload는 클라이언트에서 실행되므로 개발 서버 수치로는 아무것도 알 수 없습니다. 프로덕션 서버로 프로덕션 빌드를 측정하고, 개발 서버에 대한 랩 Lighthouse 실행은 근거가 아닙니다.

## Rules

1. `official` — 앱 같은 내비게이션에는 라우터의 `defaultPreload: 'intent'`를 씁니다. 기본값은 `false`이고 `'intent'`는 hover나 touch 시작에 발동합니다. intent와 viewport preloading은 50ms `defaultPreloadDelay` 뒤에 시작하고 touch intent는 즉시 발동합니다.
2. `official` — TanStack Query가 캐시 최신성을 소유하면 `defaultPreloadStaleTime: 0`을 둡니다. 그렇지 않으면 preload 데이터가 30초 동안 신선해 Query의 staleness 규칙을 가립니다.
3. `official` — loader를 손으로 분할하지 말고 파일 기반 라우팅 플러그인으로 라우트 컴포넌트에 `autoCodeSplitting`을 켭니다. `component`, `errorComponent`, `pendingComponent`, `notFoundComponent`를 분할하고, loader, validator, `beforeLoad`, context, link는 의도적으로 중요 경로에 남깁니다. loader를 분할하면 이미 있는 async 경계 위에 청크 fetch가 하나 더 붙기 때문입니다.
4. `official` — loader의 prefetch는 `queryClient.query({ ...options, staleTime: 'static' })`로 합니다. `prefetchQuery`, `fetchQuery`, `ensureQueryData`와 그 infinite 변형은 폐기됐고 다음 메이저에서 제거됩니다.
5. `official` — 서버 쪽 `QueryClient`에 0이 아닌 기본 `staleTime`을 주어 prefetch마다 값을 넘기지 않게 합니다.
6. `official` — 컴포넌트가 브라우저 API를 필요로 하지만 데이터는 서버에서 가져올 수 있는 라우트에는 `ssr: false`로 내리지 말고 `ssr: 'data-only'`를 씁니다. `'data-only'`는 서버에서 `beforeLoad`와 `loader`를 계속 실행합니다.
7. `official` — 스트리밍을 hydration 실패 원인으로 지목하기 전에 `<Scripts />`가 루트 라우트의 `<body>` 안에 있는지 확인합니다. 이것이 없으면 응답은 끝까지 완성되지만 페이지가 hydration되지 않습니다.
8. `official` — `defaultStaleTime`은 `0`으로 두고, 측정상 비싸고 안정적인 데이터에만 라우트별 `staleTime`을 줍니다. 그 밖의 loader 데이터는 이후 재사용에 즉시 stale이고, `gcTime`과 `preloadGcTime`은 5분이며 `staleReloadMode`는 `'background'`가 기본입니다.
9. `official` — 측정된 깜빡임이나 지연이 말하지 않는 한 `defaultPendingMs`(1000)와 `defaultPendingMinMs`(500)를 기본값으로 둡니다. 이 값은 pending UI가 언제 나타나 얼마나 머무는지를 정하고 데이터 최신성과는 무관합니다.
10. `official` — `defaultStreamHandler`나 `renderRouterToStream`을 쓰면 스트리밍 SSR은 자동입니다. 그 위에 수동 스트리밍 배관을 더하지 않습니다.
11. `official` — React Compiler가 초기 로드를 개선한다고 주장하지 않습니다. 갱신 성능을 목표로 하고 컴포넌트와 hook만 메모이즈하며 메모이제이션은 컴포넌트 사이에서 공유되지 않습니다. 수동 `useMemo`/`useCallback`/`memo` 삭제는 그 파일에서 컴파일러가 실제로 도는 경우에만 허용합니다.
12. `official` — 컴파일러 lint 규칙(`react-hooks`의 `recommended`/`recommended-latest`, 또는 oxlint `react` 플러그인 동등 규칙)을 켜고, 보고는 "이 컴포넌트는 최적화되지 않는다"로 읽습니다. 빌드 실패로 읽지 않습니다. oxlint에서 `rules-of-hooks`는 `correctness`가 아니라 `pedantic`에 있습니다.
13. `hypercore-default` — 75백분위에서 LCP 2.5초 이하, INP 200밀리초 이하, CLS 0.1 이하를 게이트로 두고 모바일과 데스크톱을 따로 보고하며 스크립트와 이미지 크기 예산을 CI에 둡니다.

## Do not

- `defaultPreload`를 `false`로 두고 느린 내비게이션의 원인을 라우터로 돌리지 않습니다.
- preload 데이터와 TanStack Query가 함께 최신성을 결정하게 두지 않습니다. 한 계층이 소유합니다.
- loader를 별도 청크로 손수 분할하거나 async 경계 앞에 청크 fetch를 붙이지 않습니다.
- 새 코드에 `prefetchQuery`, `fetchQuery`, `ensureQueryData`를 쓰지 않습니다.
- 서버 fetch를 지킬 수 있는 곳에서 `ssr: false`를 쓰지 않습니다.
- `defaultStreamHandler` 위에 스트리밍 래퍼를 더하지 않고, `<Scripts />`를 확인하기 전에 hydration 실패를 쫓지 않습니다.
- 수치를 좋게 보이게 하려고 전역 `staleTime`을 0보다 크게 두지 않습니다. 오래된 데이터는 정확성 결정입니다.
- 30초 preload 신선도 기본값을 성능 개선으로 인용하지 않습니다. Query와 맞춰야 하는 기본값입니다.

## Checklist

- [ ] 프로덕션 빌드와 내비게이션 트레이스, CWV 측정으로 기준선을 기록했습니다.
- [ ] 앱 같은 내비게이션이면 `defaultPreload`가 `'intent'`이고 지연 값은 기본입니다.
- [ ] TanStack Query가 캐시를 소유하는 곳에서 `defaultPreloadStaleTime`이 `0`입니다.
- [ ] `autoCodeSplitting`이 켜져 있고 loader가 중요 라우트 설정에 남아 있습니다.
- [ ] loader prefetch가 `staleTime: 'static'`과 함께 `queryClient.query(...)`를 쓰고 서버 `QueryClient`에 기본 `staleTime`이 있습니다.
- [ ] 컴포넌트는 브라우저가 필요하고 데이터는 아닌 경우 선택적 SSR이 `'data-only'`를 씁니다.
- [ ] `<Scripts />`가 루트 라우트의 `<body>` 안에 있습니다.
- [ ] 측정마다 레버 하나만 바꾸고 전후 수치를 기록했습니다.

## Sources

> Checked 2026-11-07. 아래 사실과 URL은 성능 조사 레인의 TanStack 항목에서 가져왔습니다. 레인은 2026-11-07에 각 페이지를 열었고 출처 id를 괄호에 남겼습니다.

| Claim | Source |
|---|---|
| `defaultPreload`, `'intent'` 시점, `defaultPreloadDelay`, Query와의 `defaultPreloadStaleTime` 조정 (L-22) | https://tanstack.com/router/latest/docs/guide/preloading.md |
| 라우터 옵션 기본값: `defaultPreload: false`, `defaultPreloadStaleTime` 30초, `defaultPendingMs` 1000, `defaultPendingMinMs` 500, `staleReloadMode` (L-23) | https://tanstack.com/router/latest/docs/api/router/RouterOptionsType.md |
| `autoCodeSplitting` 적용 범위와 loader를 중요 경로에 두는 이유 (L-24) | https://tanstack.com/router/latest/docs/guide/code-splitting.md |
| 선택적 SSR `ssr: true \| false \| 'data-only'`와 `defaultSsr` (L-25) | https://tanstack.com/start/latest/docs/framework/react/guide/selective-ssr.md |
| 자동 스트리밍 SSR과 `<Scripts />` hydration 요구 (L-26) | https://tanstack.com/router/latest/docs/guide/ssr.md |
| `queryClient.query({ staleTime: 'static' })` prefetch 방식과 폐기된 prefetch API (L-27) | https://tanstack.com/query/latest/docs/framework/react/guides/prefetching.md |
| loader `staleTime` 0, `gcTime`과 `preloadGcTime` 5분, `staleReloadMode` (L-28) | https://tanstack.com/router/latest/docs/guide/data-loading.md |
| React Compiler 1.0 안정성, 갱신 성능 범위, Meta 수치 (L-01, L-02) | https://react.dev/blog/2025/10/07/react-compiler-1, https://react.dev/learn/react-compiler/introduction |
| 컴파일러 선행 Babel 순서, lint는 최적화 건너뜀, `panicThreshold` (L-03, L-04) | https://react.dev/learn/react-compiler/installation, https://react.dev/reference/react-compiler/configuration |
| 컴파일러 lint 규칙 이름과 프리셋 (L-65) | https://raw.githubusercontent.com/facebook/react/main/packages/eslint-plugin-react-hooks/README.md |
| oxlint `react` 플러그인 규칙과 카테고리 매핑 (L-66) | https://oxc.rs/docs/guide/usage/linter/rules.html |
| 75백분위 Core Web Vitals 임계값, 기기별 구분 (L-67) | https://web.dev/articles/vitals |
| CI 하네스로서의 Lighthouse CI와 예산 권고 (L-68) | https://raw.githubusercontent.com/GoogleChrome/lighthouse-ci/main/README.md |
