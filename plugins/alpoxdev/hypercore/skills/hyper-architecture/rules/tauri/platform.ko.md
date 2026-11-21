# 플랫폼 설정: Tauri v2 + Vite + React + TanStack Router + Query

> 렌더러/부트스트랩/설정 검토에 이 규칙을 사용합니다. 먼저 날짜가 기록된 근거를 읽습니다: [Tauri v2 근거](../../references/official/tauri/tauri-v2-2026-11-04.ko.md), [TanStack + Vite + React 근거](../../references/official/tauri/tanstack-vite-react-2026-11-04.ko.md). TanStack Start 프로젝트는 이 규칙의 범위 밖이며, server-owned route tree, loader, SSR data-flow plan을 산출물로 하는 full-stack architecture workflow로 라우팅합니다.

## 분류

| 규칙 | 분류 | 적용 |
|---|---|---|
| TanStack Router Vite 플러그인은 React Vite 플러그인보다 앞선다 | 공식 사실 | 라우트 변환을 진단하기 전에 플러그인 순서를 바로잡는다. |
| `tanstackRouter({ target: 'react', autoCodeSplitting: true })`가 파일 라우트 변환과 라우트 트리 생성을 소유한다 | 공식 사실 | 한 번만 사용하고 생성된 라우트 트리를 수동 편집하지 않는다. |
| TanStack Router는 파일 기반 라우팅을, TanStack Query는 비동기 데이터 cache와 freshness를 소유한다 | 공식 사실 | Query에 파일 라우팅 시스템이 있다고 주장하지 않는다. |
| `build.devUrl`과 `build.frontendDist`는 Tauri v2 설정 키다 | 공식 사실 | 실제 Vite 엔드포인트/출력과 일치시킨다. |
| 공식 Tauri Vite guide는 `port: 5173`, `strictPort: true`, `clearScreen: false`, `host: TAURI_DEV_HOST \|\| false`, `watch.ignored: ['**/src-tauri/**']`, `envPrefix: ['VITE_', 'TAURI_ENV_*']`, `TAURI_ENV_PLATFORM`/`TAURI_ENV_DEBUG` 기반 `target`/`minify`/`sourcemap`을 쓴다 | 공식 사실 | Dev server나 build 값을 바꾸기 전에 프로젝트를 최신 guide와 비교한다. |
| `VITE_*`와 노출된 `TAURI_ENV_*` 값은 렌더러 코드에 도달하고 public 자산은 공개 배포된다 | 공식 사실 | 두 표면 모두에서 비밀을 차단한다. |
| 기본은 loopback host, 엄격한 개발 port, 명시적인 asset-base 결정, 검증된 build target이며, 비루프백 바인딩은 `TAURI_DEV_HOST`를 통한 실기기 개발에서만 허용한다 | Hypercore 관례 + safety policy | 그 밖의 network 노출이나 다른 target/base에는 build evidence와 문서화된 예외가 필요하다. |
| Bootstrap은 한 소유자가 가지며 effect는 외부 작업을 정리한다 | React 공식 사실 + Hypercore 관례 | 중복 mount, 전역 listener, timer를 바로잡는다. |

‘공식 사실’은 2026-11-04에 문서화된 프레임워크 동작을 기록한 것이다. ‘Hypercore 관례’는 기존에 입증된 프로젝트 계약을 대체하지 않는 기본 검토 기준이다.

## Vite 플러그인 구성

파일 기반 라우팅에는 Router Vite 플러그인을 React보다 먼저 사용한다.

```ts
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { tanstackRouter } from '@tanstack/router-plugin/vite'

export default defineConfig({
  plugins: [
    tanstackRouter({ target: 'react', autoCodeSplitting: true }),
    react(),
  ],
})
```

- Router 플러그인은 route source를 발견하고 `routeTree.gen.ts`를 생성한다. Route file과 플러그인 설정은 사람이 작성하는 입력이고 생성된 tree는 도구 출력이다.
- Router 플러그인 등록은 정확히 하나만 유지한다. Route transform이 React가 module을 처리하기 전에 완료되도록 반드시 `react()`보다 앞에 둔다.
- `target: 'react'`는 React Router 통합을 선택한다. `autoCodeSplitting: true`는 대상 route component를 생성된 lazy boundary에 둔다. 이러한 boundary가 보이는 곳에는 loading 및 rendering-error UI를 제공한다.
- `enableRouteGeneration`을 넘기지 않는다. 이 option은 `@tanstack/router-plugin` 1.168에서 제거되었고 route generation은 항상 실행된다. 남아 있는 option은 build 동작을 가리는 죽은 설정이다.
- TanStack Query는 route generator가 아니다. Route와 loader가 공유 data access를 필요로 하면 하나의 `QueryClient`를 타입화된 router context에 둔다. 이후 Query가 cache와 freshness 결정을 소유한다.

## Tauri와 Vite는 같은 앱을 기술해야 한다

Tauri는 v2 config에 지정된 URL과 directory를 실행/로드하며 Vite는 해당 값을 실제로 serve/build해야 한다. 아래 값은 Vite 8 기준 공식 Vite guide를 따른다.

```json
// src-tauri/tauri.conf.json
{
  "build": {
    "beforeDevCommand": "pnpm dev",
    "devUrl": "http://localhost:5173",
    "beforeBuildCommand": "pnpm build",
    "frontendDist": "../dist"
  }
}
```

```ts
// vite.config.ts
import { defineConfig } from 'vite'

const host = process.env.TAURI_DEV_HOST

export default defineConfig({
  clearScreen: false,
  server: {
    port: 5173,
    strictPort: true,
    host: host || false,
    hmr: host ? { protocol: 'ws', host, port: 1421 } : undefined,
    watch: {
      ignored: ['**/src-tauri/**'],
    },
  },
  envPrefix: ['VITE_', 'TAURI_ENV_*'],
  build: {
    target:
      process.env.TAURI_ENV_PLATFORM === 'windows' ? 'chrome105' : 'safari13',
    minify: !process.env.TAURI_ENV_DEBUG,
    sourcemap: !!process.env.TAURI_ENV_DEBUG,
  },
})
```

- **공식 사실:** `devUrl`은 개발에 사용하는 프런트엔드 URL이고 `frontendDist`는 패키지 프런트엔드 directory다. Tauri v2 config reference: <https://v2.tauri.app/reference/config/>; Vite guide: <https://v2.tauri.app/start/frontend/vite/>.
- `devUrl`의 protocol, hostname, port를 Vite server의 실제 address와 동일하게 유지한다. Vite가 조용히 선택한 fallback port를 Tauri가 가리키게 하지 않는다.
- `clearScreen: false`는 Vite가 terminal을 지우지 않게 해 Rust compiler 출력을 계속 볼 수 있게 한다. `watch.ignored: ['**/src-tauri/**']`는 Rust build artifact가 renderer reload를 유발하지 않게 한다. 둘 다 취향이 아니라 공식 guide 값이다.
- `1420`은 `create-tauri-app` template 관례이고 현재 guide 값이 아니다. 이미 1420을 쓰는 프로젝트는 유지할 수 있지만 `devUrl`, `port`, `strictPort`, HMR port가 서로 맞아야 한다.
- 기본은 좁은 loopback host다. Guide의 `host: host || false`는 `TAURI_DEV_HOST`가 설정되기 전까지 기본 loopback address에만 bind하며, 이 variable은 iOS/Android 실기기 개발이 dev server에 접근하는 문서화된 방식이다. 이 variable이 loopback 규칙의 예외다. `0.0.0.0`, LAN interface 또는 무관한 non-loopback development URL 바인딩은 dev server를 의도한 기기 밖에 노출하므로 여전히 명시적 권한이 필요하다.
- `frontendDist`는 `src-tauri/tauri.conf.json`에서 Vite의 실제 `build.outDir`로 해석되어야 한다. Build command와 두 path를 의도적으로 맞추고 `dist`라고 가정하지 말고 해석된 directory를 검사한다.
- 공식 guide는 `base`를 설정하지 않는다. 앱이 custom protocol origin에서 제공되므로 절대 asset path가 보통 동작한다. `base: './'` 같은 relative base는 다른 packaging 전략을 위한 Hypercore 친화적 embedded 선택이지 보편적 기본값이 아니므로 하나를 의도적으로 고르고 production output의 entry, lazy chunk, non-root route URL을 확인한다.
- `target: 'chrome105'`와 `'safari13'`은 Windows WebView2와 macOS/Linux WebKit을 나눈 guide 값이다. 선언된 모든 platform과 가장 오래 지원하는 system WebView에 비추어 정당화해야 하는 출발점으로 취급하며, 고정 `es2021` target은 그 support floor 안에 있는 동안만 유효하다.

## 빌드 target과 output 검사

패키지 렌더러는 로컬 개발에 사용한 browser가 아니라 target platform의 WebView에서 실행된다.

- **공식 사실:** Vite의 `build.target`은 JavaScript/CSS transform target을 제어한다. Tauri의 Vite guide는 platform 인식 target 지침을 제공한다: <https://v2.tauri.app/start/frontend/vite/>; Vite build option: <https://vite.dev/config/build-options>.
- 오래된 browser-target 예시를 현재 support policy로 복사하지 않는다. 설치된 Vite version, Tauri target platform, 가장 오래 지원하는 system WebView를 함께 조정한다.
- Vite 8.2부터 JavaScript에서 참조하는 asset URL이 `import.meta.ROLLDOWN_FILE_URL_*`로 emit된다. Upgrade 뒤 production build를 검사해 entry document, lazy chunk, non-root route의 해당 URL이 packaged asset origin에서 해석되는지 확인한다.
- Target/base 변경 뒤 구성된 frontend output과 참조 asset을 검사한다. URL은 packaged location에서 해석되고, 지원 WebView에 의도치 않은 미지원 syntax가 생성되지 않으며, `frontendDist`에는 entry document가 있어야 한다. non-root 파일 route의 packaged navigation도 검사한다.

## 렌더러 환경과 public-input 경계

| 표면 | 규칙 |
|---|---|
| `import.meta.env.VITE_*` | 렌더러에 보이며 build 시 정적으로 대체된다. 비밀이 아닌 configuration에만 사용한다. |
| `import.meta.env.TAURI_ENV_*` | Guide의 `envPrefix`가 `TAURI_ENV_*`를 나열하기 때문에 노출된다. CLI는 hook command에 `TAURI_ENV_DEBUG`, `TAURI_ENV_PLATFORM`, `TAURI_ENV_PLATFORM_VERSION`, `TAURI_ENV_ARCH`, `TAURI_ENV_FAMILY`, `TAURI_ENV_TARGET_TRIPLE`을 설정하므로 renderer가 build target과 debug 상태를 알게 된다. 가능하면 renderer code에서 쓰지 않고, secret이나 runtime platform 감지로 취급하지 않는다. |
| 그 외 build-time environment variable | 렌더러 코드에 자동 노출되지 않는다. 적절한 runtime boundary에서 validate/consume한다. |
| `public/` | 공개 static input으로 복사/제공된다. credential, private key, internal configuration, license-sensitive data를 두지 않는다. |
| Rust/native configuration | Native secret과 privileged configuration을 renderer bundle 밖에 둔다. 필요할 때 IPC를 통해 authorization-checked 최소 결과만 노출한다. |

Browser fallback으로 renderer configuration을 `process.env`에서 읽지 않는다. Client-side prefix, obfuscation, public asset filename으로 secret을 보호하려 하지 않는다. Vite의 environment와 public-directory 규칙은 <https://vite.dev/guide/env-and-mode> 및 <https://vite.dev/guide/assets>에, `TAURI_ENV_*` 집합은 <https://v2.tauri.app/reference/environment-variables/>에 문서화되어 있다.

## Bootstrap 소유권과 React lifecycle

- `src/main.tsx`는 유일한 React client entry다. `createRoot`, `StrictMode`, `QueryClientProvider`, `RouterProvider`를 소유하며 route, feature component, hot-reload helper가 다른 root를 만들지 않는다.
- 앱 전체에 하나의 `QueryClient`를 만들고 `QueryClientProvider`와 타입화된 router context 양쪽으로 전달한다. Route loader와 `beforeLoad`는 context를 받지만 React hook을 호출할 수 없다.
- 앱은 한 번만 mount한다. 조사하고 격리한 library incompatibility가 문서화되어 있지 않는 한 개발에서 `StrictMode`를 유지한다. 개발 검사는 불순한 render와 불완전한 effect cleanup을 드러낸다.
- Subscribe, listener 등록, timer 시작, object URL 보유, 취소 가능한 async 작업 시작을 하는 effect는 이를 되돌리는 cleanup을 반환한다. API가 지원하면 cleanup에서 unsubscribe, listener 제거, timer 해제, URL revoke, 진행 중 작업 abort/cancel을 한다.
- Visible side effect가 있는 Tauri initialization의 기본 위치는 effect가 아니다. 개발 재실행이 중복 native subscription이나 write를 만들지 않도록 initialization을 idempotent하고 명시적으로 소유하게 한다.

React 참고 자료: [createRoot](https://react.dev/reference/react-dom/client/createRoot), [StrictMode](https://react.dev/reference/react/StrictMode), [useEffect cleanup](https://react.dev/reference/react/useEffect).

## Tauri v1 설정을 그대로 가져오지 않는다

다음 일반적인 v1 key를 무시되는 compatibility debris로 남기지 말고 거부하거나 의도적으로 migration한다.

| Tauri v1 key | Tauri v2 방향 |
|---|---|
| `build.devPath` | `build.devUrl` |
| `build.distDir` | `build.frontendDist` |
| `tauri.allowlist` | capability manifest와 plugin/core permission |
| `tauri.security.csp` | `app.security.csp` |
| `tauri.bundle.identifier` | root `identifier` |

이 항목은 **공식 migration 사실**이다. Blind search-and-replace 대신 v2 configuration schema와 migration guide에서 프로젝트의 정확한 구성을 확인한다: <https://v2.tauri.app/start/migrate/from-tauri-1/> 및 <https://v2.tauri.app/reference/config/>. Permission migration은 native access를 바꿀 수 있으므로 security rule이 요구하는 authority가 필요하다.

## 검토 종료 기준

Platform setup을 수락하기 전에 configuration과 build output에서 다음을 모두 확인한다.

1. `tanstackRouter({ target: 'react', autoCodeSplitting: true })`가 `react()`보다 앞서고, 유일한 route-tree generator이며, 제거된 `enableRouteGeneration` option을 넘기지 않는다.
2. `src/routes`, 생성된 `routeTree.gen.ts`, 타입화된 router context, 하나의 `src/main.tsx`가 명확한 소유권을 가진다.
3. Tauri `devUrl`은 strict한 Vite listener와 같고 `frontendDist`는 Vite가 구성한 `build.outDir`로 해석된다. 1420 같은 guide 밖 port는 의도적이고 일관된 선택이다.
4. Output은 packaged static asset에서 동작하는 base와 지원 WebView로 정당화한 target을 사용한다. Vite 8.2 이상으로 올린 뒤에는 packaged build에서 `import.meta.ROLLDOWN_FILE_URL_*` asset URL을 다시 확인했다.
5. 어떤 secret도 `VITE_*`, 노출된 `TAURI_ENV_*`, `public/`, renderer source에 도달하지 않는다.
6. Query는 async cache/freshness를, Router는 파일 기반 라우팅을 소유하며 loader에 필요한 data는 타입화된 context를 통해 사용할 수 있다.
7. 문서화되고 완료된 migration이 의도적으로 처리하지 않는 한 v1 config key가 남아 있지 않다.

## Sources

> 링크 확인 2026-11-04.

| 주장 | 출처 |
|---|---|
| `devUrl`, `frontendDist`, Tauri v1 -> v2 key 대응, build-hook config key | [tauri-v2-2026-11-04.ko.md](../../references/official/tauri/tauri-v2-2026-11-04.ko.md); <https://v2.tauri.app/reference/config/>; <https://v2.tauri.app/start/frontend/vite/>; <https://v2.tauri.app/start/migrate/from-tauri-1/> |
| 공식 guide의 `5173`, `clearScreen`, `watch.ignored`, `host: TAURI_DEV_HOST`, `envPrefix`, platform 인식 build 값 | <https://v2.tauri.app/start/frontend/vite/> |
| `TAURI_ENV_*` 이름과 hook command 의미 | <https://v2.tauri.app/reference/environment-variables/> |
| Router plugin 순서, `tanstackRouter({ target: 'react', autoCodeSplitting: true })`, 제거된 `enableRouteGeneration`, Router와 Query의 소유권 구분 | [tanstack-vite-react-2026-11-04.ko.md](../../references/official/tauri/tanstack-vite-react-2026-11-04.ko.md); <https://tanstack.com/router/latest/docs/framework/react/routing/file-based-routing>; <https://raw.githubusercontent.com/TanStack/router/main/packages/router-plugin/CHANGELOG.md> |
| `VITE_*` 렌더러 노출, `build.target`, public directory 규칙, Vite 8.2 asset URL 변화 | [tanstack-vite-react-2026-11-04.ko.md](../../references/official/tauri/tanstack-vite-react-2026-11-04.ko.md); <https://vite.dev/guide/env-and-mode>; <https://vite.dev/config/build-options>; <https://raw.githubusercontent.com/vitejs/vite/main/packages/vite/CHANGELOG.md> |
| 하나의 React bootstrap, `StrictMode` 개발 검사, effect cleanup | [tanstack-vite-react-2026-11-04.ko.md](../../references/official/tauri/tanstack-vite-react-2026-11-04.ko.md); <https://react.dev/reference/react-dom/client/createRoot>; <https://react.dev/reference/react/useEffect> |
| Loopback host, strict dev port, 1420 template 관례, 명시적 asset base/target 결정, "Hypercore convention" 분류 | 이 저장소의 규약과 안전 정책; 외부 출처 없음 |