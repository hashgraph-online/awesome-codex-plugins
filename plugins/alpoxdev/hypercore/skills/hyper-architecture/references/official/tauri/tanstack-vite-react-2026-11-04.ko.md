# TanStack, Vite, React 공식 문서 스냅샷 (2026-11-04)

- last_verified_at: 2026-11-04
- applies_to: TanStack Router v1, TanStack Query v5, Vite 8.3 현재 문서, React 19.3 문서
- source_priority: 정본 guide/reference page > 공식 example > package registry metadata
- refresh_when: 나열된 package의 major 변경, Router file-routing/plugin API 변경, Query cache/testing API 변경, Tauri 정적 프런트엔드 계약 변경, Vite build/base 기본값 변경

이 파일은 버전에 민감한 API와 런타임 사실에만 사용합니다. 프로젝트 및 사용자 지시가 항상 우선합니다. Tauri 전용 신뢰 및 패키징 경계는 `tauri-v2-2026-11-04.ko.md`에 기록합니다.

## 목차

- 패키지 스냅샷
- TanStack Router 사실
- TanStack Query 사실
- Vite 사실
- React 사실
- 프로젝트 구조 근거
- 통합 주의사항
- Sources

## 패키지 스냅샷

다음 npm `latest` metadata는 2026-11-04에 확인했고 `vite`와 `@tanstack/react-query` 행은 2026-11-07에 다시 확인했습니다. 이는 registry 상태의 근거이며 dependency upgrade 지시가 아닙니다.

| Package | 확인 버전 | Registry |
|---|---:|---|
| `@tanstack/react-router` | `1.170.46` | <https://registry.npmjs.org/@tanstack/react-router/latest> |
| `@tanstack/router-plugin` | `1.168.48` | <https://registry.npmjs.org/@tanstack/router-plugin/latest> |
| `@tanstack/react-query` | `5.107.1` | <https://registry.npmjs.org/@tanstack/react-query/latest> |
| `@tanstack/zod-adapter` | `1.167.0` | <https://registry.npmjs.org/@tanstack/zod-adapter/latest> |
| `vite` | `8.3.6` | <https://registry.npmjs.org/vite/latest> |
| `@vitejs/plugin-react` | `6.2.1` | <https://registry.npmjs.org/@vitejs/plugin-react/latest> |
| `react` | `19.3.1` | <https://registry.npmjs.org/react/latest> |
| `zod` | `4.6.7` | <https://registry.npmjs.org/zod/latest> |

## TanStack Router 사실

- File-based routing은 TanStack Query가 아니라 TanStack Router가 소유합니다. Vite build에서 `@tanstack/router-plugin/vite`를 구성해 route file을 탐색하고 route tree를 생성하며, Query는 비동기 data cache와 freshness를 소유합니다.
- File-based routing이 권장 기본값입니다. 생성된 `routeTree.gen.ts`는 build output이므로 source route와 plugin config를 수정합니다.
- Vite config에서 `tanstackRouter()`를 React plugin 앞에 두어 React transform 전에 route generation이 실행되게 합니다.
- `1.168.48`의 plugin option은 `target`, `autoCodeSplitting`, route directory/token/generated tree option, formatting/HMR option입니다. `enableRouteGeneration`은 제거되었고 route generation은 항상 실행되므로 이를 넘기는 것은 죽은 설정입니다.
- `createRouter`는 생성된 route tree를 받습니다. 앱 전체 type safety를 위해 `Register.router`를 declaration merge합니다.
- `createRootRouteWithContext<T>()`와 router context를 사용해 단일 `QueryClient`와 좁은 desktop API interface 같은 dependency를 명시합니다. Loader와 `beforeLoad`에서는 React hook을 호출할 수 없습니다.
- Router loader는 context, params, 검증된 search dependency, abort controller를 받습니다. Loading에 영향을 주는 search 값은 `loaderDeps`에 둡니다.
- `beforeLoad` route guard는 navigation UX만 제어합니다. 모든 Tauri command 또는 remote endpoint가 독립적으로 authorization을 강제해야 합니다.
- Root pending, error, not-found UI를 정의합니다. 누락된 resource에만 `notFound()`를 던지고 permission, command, network 실패는 error로 유지합니다.
- Preloading은 추측적 실행입니다. Loader와 preload에서 write, prompt, privileged native side effect를 실행하지 않습니다.
- Zod v4에서는 schema를 `validateSearch`에 직접 넘깁니다. Zod v3는 `@tanstack/zod-adapter`의 `zodValidator`가 필요하므로 한 route tree에서 두 관례를 섞지 않습니다.

출처:

- <https://tanstack.com/router/v1/docs/framework/react/guide/creating-a-router>
- <https://tanstack.com/router/v1/docs/framework/react/guide/router-context>
- <https://tanstack.com/router/v1/docs/framework/react/routing/file-based-routing>
- <https://tanstack.com/router/v1/docs/framework/react/guide/data-loading>
- <https://tanstack.com/router/v1/docs/framework/react/guide/preloading>
- <https://tanstack.com/router/v1/docs/framework/react/guide/not-found-errors>
- <https://tanstack.com/router/v1/docs/framework/react/guide/authenticated-routes>
- <https://tanstack.com/router/latest/docs/framework/react/guide/search-params>
- <https://raw.githubusercontent.com/TanStack/router/main/packages/router-plugin/CHANGELOG.md>

## TanStack Query 사실

- Router의 문서화된 Query 통합은 하나의 `QueryClient`를 router context에 두고, critical route data에 `ensureQueryData(queryOptions)`를 호출하며, `QueryClientProvider` 아래 component에서 같은 options를 `useSuspenseQuery`로 읽습니다.
- Query가 freshness를 소유하면 Router preload stale time을 `0`으로 두어 loader가 실행되고 Query가 cache freshness를 결정하게 합니다.
- `ensureQueryData`는 cached data를 반환하거나 없으면 fetch합니다. 명시하지 않으면 stale revalidation은 자동이 아닙니다. `prefetchQuery`는 throw하지 않으므로 critical loader의 유일한 gate로 부적합합니다.
- Query key는 top-level serializable array이며 query function이 사용하는 모든 변수를 포함해야 합니다.
- Query function은 data를 resolve하거나 throw/reject해야 합니다. `AbortSignal`을 받지만 이를 Tauri `invoke`에 전달하는 것만으로 native command가 취소되지는 않습니다. Native cancellation은 명시적인 cooperative protocol이 필요합니다.
- Query data는 기본적으로 stale이며 mount, focus, reconnect 시 refetch할 수 있습니다. Desktop 프로젝트는 `staleTime`, refetch, retry, invalidation 정책을 의도적으로 선택해야 합니다.
- Mutation/fetch filter는 이전보다 좁아졌습니다. `QueryClient.isMutating`/`useIsMutating`은 `status`를, `QueryClient.isFetching`/`useIsFetching`은 `fetchStatus`를 받지 않습니다. 상태 문자열 대신 남은 mutation/fetch identity field로 filter합니다.
- 테스트는 격리된 QueryClient를 사용하고 예상 error case에서는 retry를 비활성화합니다.

출처:

- <https://tanstack.com/router/v1/docs/framework/react/guide/external-data-loading>
- <https://tanstack.com/query/v5/docs/reference/QueryClient>
- <https://tanstack.com/query/latest/docs/framework/react/guides/important-defaults>
- <https://tanstack.com/query/latest/docs/framework/react/guides/query-keys>
- <https://tanstack.com/query/latest/docs/framework/react/guides/query-functions>
- <https://tanstack.com/query/latest/docs/framework/react/guides/query-cancellation>
- <https://tanstack.com/query/v5/docs/framework/react/guides/testing>
- <https://raw.githubusercontent.com/TanStack/query/main/packages/react-query/CHANGELOG.md>

## Vite 사실

- 기본적으로 `VITE_` 접두사가 있는 환경값만 `import.meta.env`를 통해 노출되며 모두 문자열입니다. 비밀값을 넣어서는 안 됩니다. Tauri의 `TAURI_ENV_*`처럼 build tool 접두사를 함께 노출하면 renderer에 닿는 범위가 넓어지므로 추가 prefix는 public-input 결정으로 취급합니다.
- `base`는 생성되는 asset URL을 제어합니다. Embedded 배포에서 relative base를 지원하지만 선택한 값은 Tauri packaged asset origin 및 lazy chunk와 함께 검증해야 합니다.
- 제한된 remote-device debugging이 필요한 경우가 아니면 dev server를 loopback에 유지합니다. `strictPort: true`는 Tauri의 고정 `devUrl`이 잘못된 port를 조용히 바라보는 일을 방지합니다. 광범위한 `allowedHosts` 또는 CORS 설정을 피합니다.
- Vite는 TypeScript를 transpile하지만 type-check하지 않습니다. Type check를 별도로 실행합니다.
- Vite 기본 build target은 release에 따라 바뀌며 API polyfill을 제공하지 않습니다. 가장 오래 지원하는 system WebView에 맞춰 target을 선택하고 테스트합니다.
- Vite 8은 `build.rolldownOptions`를 사용하며 `build.rollupOptions`는 deprecated alias입니다. Vite 8.2는 최상위 `input` option을, Vite 8.3은 최상위 `tsconfig` option을 추가했으며 둘은 `build` 안이 아니라 밖에 있습니다. Bundler option을 편집하기 전에 설치 버전을 검사합니다.
- Vite 8.2부터 JavaScript에서 참조하는 asset은 `import.meta.ROLLDOWN_FILE_URL_*` URL로 emit됩니다. Upgrade 뒤에는 packaged entry, lazy chunk, non-root route asset URL이 Tauri asset origin에서 여전히 해석되는지 다시 확인합니다.

출처:

- <https://vite.dev/guide/env-and-mode>
- <https://vite.dev/config/shared-options#base>
- <https://vite.dev/config/server-options>
- <https://vite.dev/config/build-options#build-target>
- <https://vite.dev/guide/features#transpile-only>
- <https://raw.githubusercontent.com/vitejs/vite/main/packages/vite/CHANGELOG.md>
- <https://vite.dev/blog/announcing-vite8-1>

## React 사실

- Vite SPA는 하나의 명시적 `createRoot` bootstrap을 소유하며, 필요한 provider 아래에 `RouterProvider`를 mount합니다.
- 개발 중 `StrictMode`를 유지합니다. Effect 재실행으로 드러난 중복 Tauri listener는 StrictMode를 제거할 이유가 아니라 cleanup 누락 또는 비멱등 setup 결함입니다.
- Effect는 외부 시스템 동기화에만 사용하고 등록을 되돌려야 하면 항상 listener cleanup을 반환합니다. 사용자가 시작한 native command는 event handler에 둡니다.
- Lazy feature에는 loading 및 rendering-error UI를 함께 둡니다. Error Boundary는 async callback 또는 event handler 실패를 잡지 않으므로 command 실패는 promise/event 경로에서 처리합니다.
- Shared mutable external store에는 stable subscription과 cached immutable snapshot을 갖춘 `useSyncExternalStore`만 사용합니다.
- React 19.3은 Trusted Types API를 통합했으므로 packaged app은 모든 script sink를 점검한 뒤 CSP에 `require-trusted-types-for 'script'`를 검토할 수 있습니다. 점검 없이 켜면 DOM script 주입 지점이 깨집니다.
- React 19.3은 transition을 하나의 render로 얽지 않고 독립적으로 render하므로 여러 transition이 겹칠 때 pending UI를 다시 확인합니다. `<ViewTransition />`과 `addTransitionType`은 이 계열에서 안정 API입니다.

출처:

- <https://react.dev/reference/react-dom/client/createRoot>
- <https://react.dev/reference/react-dom/client/hydrateRoot>
- <https://react.dev/reference/react/StrictMode>
- <https://react.dev/reference/react/useEffect>
- <https://react.dev/reference/react/lazy>
- <https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary>
- <https://react.dev/reference/react/useSyncExternalStore>
- <https://raw.githubusercontent.com/facebook/react/main/CHANGELOG.md>

## 프로젝트 구조 근거

- Tauri 공식 프로젝트 구조는 선택적인 JavaScript project를 repository top level에, Cargo/Tauri project를 `src-tauri/`에 둡니다. `tauri.conf.json`, capability, icon, `lib.rs`, 얇은 desktop `main.rs`를 문서화하지만 `src/` 아래 React folder는 규정하지 않습니다.
- TanStack Router의 file naming 계약은 `__root`, `$`, `_`, `-`, route group `(folder)`, `index`, `route`에 routing 의미를 부여합니다. 특히 `-`는 함께 둔 file/folder를 route generation에서 제외하고 `(folder)`는 URL segment를 추가하지 않고 route를 정리합니다.
- React legacy file-structure FAQ는 단일 layout을 규정하지 않고 feature/route 기준 및 file type 기준 grouping을 일반적인 접근으로 설명하며 deep nesting을 피하고 함께 변경되는 file을 colocate하라고 권합니다. 해당 page는 legacy이므로 current React API 요구사항이 아니라 비교 조직 근거로만 사용합니다.
- Redux의 current code-structure FAQ는 Redux application에 feature/domain folder를 권장합니다. 이 스킬은 Redux를 요구하지 않으며, cohesive `modules/<domain>/` 소유권의 비교 근거로 feature-folder 결과만 사용합니다.

출처:

- <https://v2.tauri.app/start/project-structure/>
- <https://tanstack.com/router/latest/docs/framework/react/routing/file-naming-conventions>
- <https://legacy.reactjs.org/docs/faq-structure.html>
- <https://redux.js.org/faq/code-structure/>

**도출한 규약:** 공식/generated routing surface는 `routes/`에 유지하고, nontrivial screen composition에는 `pages/`, cohesive domain capability에는 `modules/`, 재사용되는 business-agnostic UI에만 `components/`를 추가합니다. 이 이름과 dependency rule은 vendor mandate가 아니라 Hypercore 규약입니다. 모든 layer를 scaffold하거나 repository-specific contract 없이 경쟁하는 `features/`와 `modules/` 용어를 함께 사용하지 않습니다.

## 통합 주의사항

- Tauri는 이 정확한 Vite SPA stack을 공식적으로 보증하지 않습니다. Production build와 packaged-WebView smoke test를 통과해야 하는 통합으로 취급합니다.
- TanStack, Vite, React 문서로 Tauri security behavior를 추론하지 않습니다. Native trust boundary는 `tauri-v2-2026-11-04.ko.md`를 사용합니다.
- Official fact를 Hypercore convention으로 바꾸거나 그 반대로 표현하지 않습니다. 공식 문서가 규정하지 않는 directory layout 및 typed adapter 위치는 repository convention입니다.

## Sources

> 링크 확인 2026-11-04.

| 주장 | 출처 |
|---|---|
| Package snapshot 버전 | 위 Package snapshot 표의 registry URL |
| Router와 Query 사실 | 위 섹션의 TanStack 출처 목록 (`tanstack.com/router/...`, `tanstack.com/query/...`, package CHANGELOG) |
| Vite 사실 | 위 섹션의 Vite 출처 목록 (`vite.dev/...`, Vite CHANGELOG) |
| React 사실 | 위 섹션의 React 출처 목록 (`react.dev/...`, React CHANGELOG) |
| 프로젝트 구조 비교 근거 | <https://v2.tauri.app/start/project-structure/>; <https://legacy.reactjs.org/docs/faq-structure.html>; <https://redux.js.org/faq/code-structure/> |
| 도출한 `routes/`/`pages/`/`modules/`/`components/` 관례 | 이 저장소의 관례; 외부 출처 없음 |