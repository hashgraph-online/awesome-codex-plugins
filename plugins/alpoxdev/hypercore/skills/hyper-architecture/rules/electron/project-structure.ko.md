# 프로젝트 구조

> 프로세스마다 폴더 하나, 공유 계약 폴더 하나, 블록 세 개를 가진 빌드 설정 하나, 두 런타임에 맞춘 tsconfig 파일 두 개.

`references/official/electron/electron-2026-11-08.md`의 페이지가 밝히는 규칙에는 `official` 표기를, 이 패키지가 기본값을 정한 규칙에는 `hypercore-default` 표기를 붙입니다.

## 1. 대상 배치

```text
electron.vite.config.ts        main, preload, renderer blocks (or forge.config.ts + three vite.*.config.mts)
electron-builder.yml           packaging, when electron-builder is the packager
tsconfig.json                  references only
tsconfig.node.json             src/main, src/preload, src/shared — Node and Electron types
tsconfig.web.json              src/renderer, src/shared — DOM types, no Node types
resources/                     icons and files shipped outside app.asar (asarUnpack)
src/
  main/
    index.ts                   lifecycle only: single-instance lock, protocol, windows, registerIpc()
    windows/                   one file per window: BrowserWindow options, load URL, navigation guards
    ipc/                       one handler file per domain, plus sender.ts and index.ts (registerIpc)
    services/<domain>/         main-side domain logic the handlers call (store, fs, net, safeStorage)
    workers/                   utilityProcess entry points for long CPU or I/O work
  preload/
    index.ts                   contextBridge.exposeInMainWorld — the only file the renderer can reach
  shared/
    ipc/                       channels.ts, schemas.ts, api.ts (DesktopApi), result.ts
    types/                     domain types used across processes
  renderer/
    index.html
    src/
      main.tsx                 createRoot, QueryClientProvider, RouterProvider
      router.tsx               QueryClient, hash history, createRouter, Register
      main.css                 @import "tailwindcss"; @theme; @source
      routes/                  TanStack Router file routes (__root.tsx, index.tsx, …)
      routeTree.gen.ts         generated, never edited
      features/<domain>/       components, query options, hooks for one domain
      platform/desktop.ts      the only renderer file that reads window.desktop
      components/              shared UI with no IPC and no domain logic
      env.d.ts                 Window augmentation
```

- `official` — electron-vite의 기본 entry는 `src/main/index.ts`, `src/preload/index.ts`, `src/renderer/index.html`이고 renderer root는 `src/renderer`입니다. 그래서 이 배치는 entry를 덮어쓸 필요가 없습니다. Electron Forge의 `vite-typescript` template은 대신 `src/main.ts`, `src/preload.ts`, `src/renderer.ts`를 flat하게 두고 `vite.*.config.mts` 파일 세 개를 씁니다. Forge 프로젝트에서는 그 형태를 유지하고 같은 소유권 규칙을 적용합니다.
- `hypercore-default` — 의존성은 `shared`를 향해 안쪽으로 흐릅니다. `main`, `preload`, `renderer`는 `shared`를 import할 수 있고, `shared`는 이들 중 어느 것도 import하지 않으며, `renderer`는 `main`이나 `preload`를 import하지 않습니다(`shared/ipc/api.ts`를 타입으로만 import하는 것이 다리 계약입니다). feature끼리 import하지 않습니다.
- `hypercore-default` — 작은 앱은 더 평평하게 둘 수 있습니다(`services/` 없음, `workers/` 없음, `features/` 없음). 빈 계층을 미리 만들지 않습니다. 프로세스 폴더와 `shared/ipc/`는 선택 사항이 아닙니다.
- `hypercore-default` — 창이 여러 개인 앱은 창마다 `src/renderer/` 아래에 자기 HTML entry를 두고 `src/main/windows/` 아래에 자기 파일을 둡니다. 창이 더 좁은 계약을 필요로 하는 경우가 아니면 하나의 preload 계약을 함께 씁니다.

## 2. 빌드 설정

- `official` — `electron.vite.config.ts`에는 `main`, `preload`, `renderer` 블록 세 개가 있습니다. renderer 전용 plugin(`@vitejs/plugin-react`, `@tailwindcss/vite`, `@tanstack/router-plugin/vite`)은 `renderer.plugins`에만 둡니다. root 수준 plugin이나 별도 `vite.config.ts`는 기대한 방식으로 renderer 빌드에 닿지 않습니다.
- `official` — electron-vite의 renderer preset은 production에서 `base: './'`를 설정합니다. 그래서 내보낸 asset URL이 상대 경로가 되고 `index.html`을 서비스하는 origin에서 해석됩니다.
- `official` — electron-vite renderer는 `RENDERER_VITE_`와 `VITE_` 접두사 변수를, preload는 `PRELOAD_VITE_`를, main은 `MAIN_VITE_`를 노출합니다. 모두 빌드 시점에 인라인되며 secret이 아닙니다.
- `official` — sandbox preload는 CommonJS 번들 하나여야 합니다. 의존성을 external로 빼지 말고 번들에 넣고(electron-vite의 isolated build 또는 preload에서 의존성 external 옵션을 끔) `sandbox: true`를 유지합니다. 외부 모듈을 싣겠다고 sandbox를 끄는 것은 해결책이 아닙니다.
- `hypercore-default` — `@shared` alias 하나를 블록 세 개와 tsconfig 파일 두 개에 똑같이 두어 공유 모듈이 모든 번들과 타입 검사에서 같은 경로로 해석되게 합니다.
- `hypercore-default` — 저장소마다 개발·운영 URL 관례를 하나 고릅니다. electron-vite의 `process.env.ELECTRON_RENDERER_URL` 또는 Forge의 `MAIN_WINDOW_VITE_DEV_SERVER_URL`과 `MAIN_WINDOW_VITE_NAME`입니다. 둘을 섞으면 production에서 URL이 `undefined`로 남습니다.

## 3. 시작 template은 기준선이 아닙니다

- `official` — 공식 electron-vite `react-ts` template은 `sandbox: false`를 설정하고 raw `ipcRenderer.send`, `sendSync`, `invoke`, `on`을 포함한 `@electron-toolkit/preload`의 `electronAPI`를 노출합니다. production도 `loadFile`로 엽니다.
- `hypercore-default` — 그 template으로 만든 프로젝트는 배치는 유지하되 세 가지를 고칩니다. 번들한 preload와 함께 `sandbox: true`를 쓰고, `electronAPI` 대신 이름 붙인 함수를 노출하는 preload를 쓰고, `loadFile` 대신 custom protocol을 씁니다. 각 항목을 받아들인 기본값이 아니라 `rules/electron/security.md`의 지적으로 취급합니다.
- `hypercore-default` — community starter를 채택하기 전에 마지막 push 날짜와 Electron major를 확인합니다. 지원하는 세 major 밖의 Electron에 고정된 starter는 기준선이 아니라 이관 작업입니다.

## 4. 생성 파일과 소유 파일

| Path | Owner | Rule |
|---|---|---|
| `src/renderer/src/routeTree.gen.ts` | `@tanstack/router-plugin` | regenerate, never edit; excluded from lint and format |
| `out/`, `dist/`, `release/` | electron-vite, electron-builder, Forge | build output, gitignored |
| `src/shared/ipc/*` | the team | every change compiles in all three tsconfig projects |
| `src/preload/index.ts` | the team | security review on every change |
| `electron-builder.yml`, `forge.config.ts` | the team | fuse and signing settings reviewed in `rules/electron/packaging.md` |

## Review gate

1. renderer 파일이 `src/main/`, `src/preload/`, `electron`, `node:*`에서 import합니다.
2. `src/shared/`가 프로세스별 런타임을 import합니다.
3. renderer plugin이 renderer 빌드 블록 밖에 있습니다.
4. preload를 external로 빼거나 sandbox 상태에서 ESM으로 내보냈거나, 의존성을 싣겠다고 `sandbox: false`를 설정했습니다.
5. 타입 검사가 모든 프로세스에 tsconfig 하나를 돌리거나, renderer tsconfig가 Node 타입을 포함합니다.
6. 개발·운영 URL 관례 두 개가 함께 있습니다.

## Sources

> 확인 2026-11-08.

| Claim | Source |
|---|---|
| electron-vite 기본 entry, renderer root, config 블록 세 개, env 접두사 | https://electron-vite.org/guide/dev, https://electron-vite.org/guide/env-and-mode |
| production에서 renderer `base: './'` | https://github.com/alex8088/electron-vite/blob/master/src/plugins/electron.ts |
| sandbox 단일 번들 preload의 전제 조건인 isolated build | https://electron-vite.org/guide/isolated-build |
| sandbox preload는 CommonJS여야 함 | https://www.electronjs.org/docs/latest/tutorial/esm |
| `react-ts` template의 `sandbox: false`, `electronAPI`, `loadFile` | https://github.com/alex8088/quick-start/tree/master/packages/create-electron/template, https://github.com/alex8088/electron-toolkit/blob/master/packages/preload/src/index.ts |
| Forge `vite-typescript` 배치와 주입 URL 상수 | https://github.com/electron/forge/tree/main/packages/template/vite/tmpl, https://www.electronforge.io/config/plugins/vite |
| 프로세스 간 `src/shared`와 tsconfig 파일 두 개라는 일반 관례 | 조사한 프로젝트: https://github.com/CherryHQ/cherry-studio, https://github.com/chatboxai/chatbox, https://github.com/alex8088/quick-start |
| 안쪽 의존 규칙, `platform/desktop.ts` adapter, template 수정 정책 | 이 패키지의 규약이며 공식 Electron 요구 사항이 아님 |
