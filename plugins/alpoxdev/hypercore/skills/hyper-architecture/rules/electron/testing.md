# Testing

> Test each process in the runtime it ships in: main and preload under Node with Electron mocked, the renderer under a DOM with a fake desktop adapter, and the packaged app end to end.

Rules are labelled `official` when a page in `references/official/electron/electron-2026-11-08.md` states them, and `hypercore-default` when this package chose the default.

## 1. Layers

| Layer | Tool | Environment | Proves |
|---|---|---|---|
| shared contract | Vitest | `node` | schemas accept and reject the right inputs; channel names are unique |
| main handlers and services | Vitest | `node`, `electron` mocked | sender check rejects an unknown origin, input parse rejects bad input, service logic |
| renderer features and routes | Vitest + Testing Library | `jsdom` or `happy-dom` | render, events, loader and Query behavior against a fake `DesktopApi` |
| whole app | Playwright `_electron` or WebdriverIO | built app | windows open, preload bridge exists, IPC round trip, navigation guards |

- `official` — Electron maintains no test runner of its own; its testing page surveys WebdriverIO, Selenium, and Playwright.
- `official` — Vitest environments are `node`, `jsdom`, `happy-dom`, and `edge-runtime`; Browser Mode is a separate project, not an environment. `happy-dom` is faster with fewer APIs.
- `hypercore-default` — Configure Vitest projects per process (`main` with `node`, `renderer` with `jsdom`) instead of one environment for everything, so a renderer test cannot pass because Node globals happened to exist.

## 2. Unit and component tests

- `hypercore-default` — Mock `electron` in main tests through one helper that returns a fake `ipcMain` capturing handlers; call the captured handler with a fake event whose `senderFrame.origin` you control. Test both an allowed and a rejected origin for every new handler.
- `hypercore-default` — Renderer tests inject a fake `DesktopApi` through router context or the `platform/desktop.ts` module, never by assigning a real bridge to `window`. Create a fresh `QueryClient` per test with `retry: false`.
- `hypercore-default` — A test for a push subscription asserts that unmount calls the unsubscribe function.

## 3. End-to-end tests

- `official` — Playwright has experimental Electron support through CDP (`_electron`, Electron 21 and later). `electron.launch({ args: ['.'] })` returns an `ElectronApplication`; `app.evaluate(({ app }) => …)` runs in the main process; `firstWindow()` returns the first page. Pin the Playwright version because the API is experimental.
- `official` — Playwright launches time out when the `EnableNodeCliInspectArguments` fuse is off. Run end-to-end tests against the unpackaged build (`electron-vite build` then launch `out/main/index.js`) or a test-only package, and keep the hardened fuses on the release build.
- `official` — Native dialogs are not intercepted; stub them inside `app.evaluate(({ dialog }) => …)`.
- `official` — ChromeDriver adds its own arguments (`--enable-automation`, `--remote-debugging-port=0`, sometimes `data:,`); filter them before strict argv parsing in a WebdriverIO setup.
- `hypercore-default` — One end-to-end smoke test is required for touched security or packaging work: the window loads from the custom protocol, `window.require` and `window.process` are undefined in the renderer, and one IPC call returns its envelope.

## 4. Static gates

- `official` — electron-vite, like Vite, only transpiles; type checking runs separately with `tsc --noEmit` over `tsconfig.node.json` and `tsconfig.web.json` (`rules/setup/typescript.md`).
- `hypercore-default` — A green `electron-vite build` is not a test result and not a type check. A green dev run is not a packaging result; packaging work is verified on a packaged build.

## Review gate

1. A new IPC handler has no test for a rejected sender and a rejected input.
2. Renderer tests reach a real `window.desktop` or share one `QueryClient`.
3. End-to-end tests relax a release fuse to launch.
4. A security or packaging change was verified only in the dev server.
5. A build is reported as type checking.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| Electron's testing survey, ChromeDriver arguments, and Playwright as experimental | https://www.electronjs.org/docs/latest/tutorial/automated-testing |
| Playwright `_electron` API, Electron 21+, the inspect-fuse timeout, and dialog stubbing | https://playwright.dev/docs/api/class-electron |
| Vitest environments and Browser Mode as a project | https://vitest.dev/guide/environment, https://vitest.dev/guide/browser/ |
| Vite and electron-vite transpile without type checking | https://vite.dev/guide/features#transpile-only, https://electron-vite.org/guide/typescript |
| Per-process Vitest projects with Playwright end to end in shipped apps | surveyed projects: https://github.com/CherryHQ/cherry-studio, https://github.com/cawa-93/vite-electron-builder |
| The handler test pair, fake adapter injection, and the smoke-test set | this package's convention, not an official requirement |
