# Electron Architecture Rules

> Read before classifying a finding or enforcing a rule. This file owns the rule classes, the authority order, the target shape, the blocking gates, and the migration policy.

## Rule classes

- **official**: behavior documented by Electron, electron-vite, Electron Forge, electron-builder, Vite, React, Tailwind CSS, or TanStack for the installed versions.
- **hypercore-default**: this package's stricter default, adoptable or replaceable by a recorded project decision.
- **Safety**: a `hypercore-default` rule that protects a trust boundary. It blocks touched work and is never relaxed without an explicitly accepted risk.

Order: user and project authority, installed project evidence (manifest, lockfile, `electron.vite.config.*` or `forge.config.*`, `webPreferences`), applicable official behavior, then hypercore-default.

## Trust model

```text
Renderer (Chromium, sandboxed, context-isolated)          untrusted: may run injected script
  React + TanStack Router (hash history) + TanStack Query + Tailwind v4
  platform/desktop.ts  ->  window.desktop  (typed, narrow)
          |
          | contextBridge: one function per operation
          v
Preload (sandboxed, require('electron') only, CommonJS bundle)
          |
          | ipcRenderer.invoke / on   (channels from src/shared/ipc)
          v
Main (Node)                                                trusted: holds every privilege
  sender check -> schema parse -> service -> { ok, data } | { ok: false, error }
  windows, protocol, session, net, safeStorage, fs, utilityProcess
```

The renderer is web content even when every byte ships inside the app: a dependency, a rendered document, or remote content can inject script. Every privilege therefore lives in main, and every IPC handler checks who called it and what it was given.

## Target shape

`rules/electron/project-structure.md` holds the full tree. In short: `src/main/`, `src/preload/`, `src/renderer/`, `src/shared/`, one `electron.vite.config.ts` with three blocks (or a Forge config with three Vite configs), and `tsconfig.node.json` plus `tsconfig.web.json`. Dependencies point inward to `src/shared/`; the renderer never imports main or preload code.

## Blocking gates

Block or fix touched work that:

1. **Weakens the renderer boundary**: `contextIsolation: false`, `sandbox: false`, `nodeIntegration: true`, `webSecurity: false`, `allowRunningInsecureContent`, `experimentalFeatures`, or `enableBlinkFeatures`, without a recorded, accepted risk.
2. **Exposes a raw bridge**: the preload exposes `ipcRenderer`, a generic `invoke(channel, …)`, `@electron-toolkit/preload`'s `electronAPI`, or a listener wrapper that forwards `IpcRendererEvent`.
3. **Trusts IPC input**: a handler skips the `senderFrame` origin check or the runtime schema parse.
4. **Loads production from `file://`**: `loadFile` or a `file://` URL in a packaged build, or a `protocol.handle` callback without a path-escape check.
5. **Leaves navigation open**: no `will-navigate` origin check, no deny-by-default `setWindowOpenHandler`, or `shell.openExternal` with an unchecked URL.
6. **Grants permissions by default**: a content-loading session without a permission request handler, or one that grants everything.
7. **Moves a secret into the renderer**: a token, key, or credential in renderer code, renderer storage, or a `VITE_`/`RENDERER_VITE_` variable; or new code on the synchronous `safeStorage` API.
8. **Uses browser history under a packaged load** without a tested `index.html` fallback in the protocol handler.
9. **Puts a renderer plugin in the wrong build**: `@tailwindcss/vite`, `@tanstack/router-plugin/vite`, or `@vitejs/plugin-react` outside the renderer block, or the router plugin after the React plugin.
10. **Breaks the sandboxed preload**: an ESM or externalized preload while sandboxed, or a dependency on a Node shim removed in Electron 45.
11. **Ships without the hardened fuses**, or flips fuses after signing.
12. **Blocks the main process** with long CPU or I/O work that belongs in a utility process or worker.
13. **Claims verification it did not run**: a build reported as a type check, or a security or packaging change verified only on the dev server.

## Scalable default

- One preload contract per window class, typed by `src/shared/ipc/api.ts` and implemented once.
- One renderer adapter (`platform/desktop.ts`) between React and `window.desktop`; feature code depends on the adapter type, so tests inject a fake.
- One `QueryClient`, one history, one router per renderer root (one memory router per tab when tabs own independent locations).
- One handler file per domain in `src/main/ipc/`, registered from one `registerIpc()`.
- One packager, one dev/prod URL convention.

## Brownfield policy

1. A blocking gate in touched code is fixed or blocks completion.
2. A blocking gate in untouched reachable code (a raw `ipcRenderer` bridge used elsewhere, `sandbox: false` on another window) is reported with file and gate; it is fixed when the requested work depends on it or the user asks.
3. A `hypercore-default` difference in untouched code is recorded as a bounded migration step, not expanded into a repository-wide refactor.
4. A project scaffolded from the official electron-vite template is expected to fail gates 1, 2, and 4 on day one; report them as template debt and fix them in the order sandbox and preload, then protocol.

## Migration policy

Move one domain at a time: add its channels and schemas to `src/shared/ipc/`, replace its preload surface with named functions, add sender and input checks in main, switch its renderer calls to the adapter, update its tests, then run the type check and one packaged smoke test before the next domain. Never replace the whole bridge in one change; a removed preload method fails only when its screen runs.

## Completion gate

All blocking gates pass or are reported with file and gate. hypercore-default differences ship only with a stated reason. Evidence is the two-project type check, the test run, a production build, and, for security or packaging work, one packaged smoke test; a performance claim also needs before and after numbers.

## Sources

> Checked 2026-11-08. These statements restate `references/official/electron/electron-2026-11-08.md`.

| Claim | Source |
|---|---|
| Renderer defaults, the security checklist, and sender validation | https://www.electronjs.org/docs/latest/tutorial/security |
| Sandboxed preload scope and the shims removed in 45 | https://www.electronjs.org/docs/latest/tutorial/sandbox, https://www.electronjs.org/docs/latest/breaking-changes |
| Narrow `contextBridge` exposure and `ipcRenderer` arriving as `{}` | https://www.electronjs.org/docs/latest/api/context-bridge, https://www.electronjs.org/docs/latest/tutorial/context-isolation |
| Custom protocol and path-escape check | https://www.electronjs.org/docs/latest/api/protocol |
| Fuses flipped before signing | https://www.electronjs.org/docs/latest/tutorial/fuses |
| Main-process blocking and utility processes | https://www.electronjs.org/docs/latest/tutorial/performance, https://www.electronjs.org/docs/latest/api/utility-process |
| The official template's `sandbox: false`, `electronAPI`, and `loadFile` | https://github.com/alex8088/quick-start |
| Trust model wording, the adapter, the brownfield and migration order | this package's convention, not an official Electron requirement |
