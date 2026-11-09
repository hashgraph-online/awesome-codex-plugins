# Project Structure

> One folder per process, one shared contract folder, one build config with three blocks, and two tsconfig files that match the two runtimes.

Rules are labelled `official` when a page in `references/official/electron/electron-2026-11-08.md` states them, and `hypercore-default` when this package chose the default.

## 1. Target layout

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

- `official` — electron-vite's default entries are `src/main/index.ts`, `src/preload/index.ts`, and `src/renderer/index.html`, with the renderer root at `src/renderer`, so this layout needs no entry overrides. Electron Forge's `vite-typescript` template instead uses flat `src/main.ts`, `src/preload.ts`, `src/renderer.ts` with three `vite.*.config.mts` files; keep that shape in a Forge project and apply the same ownership rules to it.
- `hypercore-default` — Dependencies point inward to `shared`: `main` and `preload` and `renderer` may import `shared`; `shared` imports none of them; `renderer` never imports `main` or `preload` (type-only imports of `shared/ipc/api.ts` are the bridge contract). Features never import each other.
- `hypercore-default` — A small app may stay flatter (no `services/`, no `workers/`, no `features/`); do not scaffold empty layers. The process folders and `shared/ipc/` are not optional.
- `hypercore-default` — A multi-window app gives each window its own HTML entry under `src/renderer/` and its own file under `src/main/windows/`, all sharing the one preload contract unless a window needs a narrower one.

## 2. Build configuration

- `official` — `electron.vite.config.ts` has three blocks: `main`, `preload`, `renderer`. Renderer-only plugins (`@vitejs/plugin-react`, `@tailwindcss/vite`, `@tanstack/router-plugin/vite`) go in `renderer.plugins` only; a root-level plugin or a separate `vite.config.ts` does not reach the renderer build the way you expect.
- `official` — electron-vite's renderer preset sets `base: './'` in production, so emitted asset URLs are relative and resolve from whatever origin serves `index.html`.
- `official` — An electron-vite renderer exposes `RENDERER_VITE_` and `VITE_` prefixed variables, the preload `PRELOAD_VITE_`, and main `MAIN_VITE_`; all of them are inlined at build time and are not secrets.
- `official` — A sandboxed preload must be one CommonJS bundle. Bundle its dependencies instead of externalizing them (electron-vite's isolated build or the dependency-externalizing option turned off for the preload) and keep `sandbox: true`; turning the sandbox off to load an external module is not the fix.
- `hypercore-default` — Mirror one `@shared` alias in all three blocks and in both tsconfig files, so a shared module resolves identically in every bundle and in the type checker.
- `hypercore-default` — Choose one dev/prod URL convention per repository: electron-vite's `process.env.ELECTRON_RENDERER_URL`, or Forge's `MAIN_WINDOW_VITE_DEV_SERVER_URL` and `MAIN_WINDOW_VITE_NAME`. Mixing them leaves `undefined` URLs in production.

## 3. Starter templates are not a baseline

- `official` — The official electron-vite `react-ts` template sets `sandbox: false` and exposes `@electron-toolkit/preload`'s `electronAPI`, which includes raw `ipcRenderer.send`, `sendSync`, `invoke`, and `on`. It also loads production through `loadFile`.
- `hypercore-default` — A project scaffolded from that template keeps its layout but fixes the three points: `sandbox: true` with a bundled preload, a named-function preload instead of `electronAPI`, and a custom protocol instead of `loadFile`. Treat each as a `rules/electron/security.md` finding, not as an accepted default.
- `hypercore-default` — Before adopting a community starter, check its last push date and its Electron major; a starter pinned to an Electron major outside the supported three is a migration, not a baseline.

## 4. Generated and owned files

| Path | Owner | Rule |
|---|---|---|
| `src/renderer/src/routeTree.gen.ts` | `@tanstack/router-plugin` | regenerate, never edit; excluded from lint and format |
| `out/`, `dist/`, `release/` | electron-vite, electron-builder, Forge | build output, gitignored |
| `src/shared/ipc/*` | the team | every change compiles in all three tsconfig projects |
| `src/preload/index.ts` | the team | security review on every change |
| `electron-builder.yml`, `forge.config.ts` | the team | fuse and signing settings reviewed in `rules/electron/packaging.md` |

## Review gate

1. A renderer file imports from `src/main/`, `src/preload/`, `electron`, or `node:*`.
2. `src/shared/` imports a process-specific runtime.
3. A renderer plugin sits outside the renderer build block.
4. The preload is externalized or emitted as ESM while sandboxed, or `sandbox: false` was set to make a dependency load.
5. The type check runs one tsconfig over all processes, or the renderer tsconfig includes Node types.
6. Two dev/prod URL conventions coexist.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| electron-vite default entries, renderer root, three config blocks, and env prefixes | https://electron-vite.org/guide/dev, https://electron-vite.org/guide/env-and-mode |
| Renderer `base: './'` in production | https://github.com/alex8088/electron-vite/blob/master/src/plugins/electron.ts |
| Isolated build as the prerequisite for a sandboxed single-bundle preload | https://electron-vite.org/guide/isolated-build |
| Sandboxed preload must be CommonJS | https://www.electronjs.org/docs/latest/tutorial/esm |
| The `react-ts` template's `sandbox: false`, `electronAPI`, and `loadFile` | https://github.com/alex8088/quick-start/tree/master/packages/create-electron/template, https://github.com/alex8088/electron-toolkit/blob/master/packages/preload/src/index.ts |
| Forge `vite-typescript` layout and injected URL constants | https://github.com/electron/forge/tree/main/packages/template/vite/tmpl, https://www.electronforge.io/config/plugins/vite |
| `src/shared` across processes and two tsconfig files as the common convention | surveyed projects: https://github.com/CherryHQ/cherry-studio, https://github.com/chatboxai/chatbox, https://github.com/alex8088/quick-start |
| The inward dependency rule, the `platform/desktop.ts` adapter, and the fix-the-template policy | this package's convention, not an official Electron requirement |
