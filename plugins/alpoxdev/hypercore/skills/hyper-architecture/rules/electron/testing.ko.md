# 테스트

> 각 프로세스를 실제로 도는 런타임에서 테스트합니다. main과 preload는 Node에서 Electron을 mock해, renderer는 DOM에서 가짜 desktop 어댑터로, 앱 전체는 end to end로 확인합니다.

규칙은 `references/official/electron/electron-2026-11-08.md`의 페이지가 그대로 진술하면 `official`, 이 패키지가 기본값을 고르면 `hypercore-default`로 표시합니다.

## 1. Layers

| Layer | Tool | Environment | Proves |
|---|---|---|---|
| shared contract | Vitest | `node` | schema가 맞는 입력을 받고 틀린 입력을 거부합니다. channel 이름이 고유합니다 |
| main handlers and services | Vitest | `node`, `electron` mock | sender 검사가 모르는 origin을 거부하고, 입력 parse가 잘못된 입력을 거부하며, 서비스 로직이 동작합니다 |
| renderer features and routes | Vitest + Testing Library | `jsdom` 또는 `happy-dom` | 가짜 `DesktopApi` 상대의 render, 이벤트, loader, Query 동작 |
| whole app | Playwright `_electron` 또는 WebdriverIO | 빌드한 앱 | 창이 열리고, preload 브리지가 있고, IPC 왕복이 되고, 이동 가드가 동작합니다 |

- `official` — Electron은 자체 테스트 러너를 유지하지 않습니다. 테스트 페이지에서 WebdriverIO, Selenium, Playwright를 살펴봅니다.
- `official` — Vitest environment는 `node`, `jsdom`, `happy-dom`, `edge-runtime`입니다. Browser Mode는 environment가 아니라 별도 project입니다. `happy-dom`은 더 빠르고 API가 적습니다.
- `hypercore-default` — 모든 것에 environment 하나를 쓰지 말고 프로세스마다 Vitest project를 설정합니다(`main`은 `node`, `renderer`는 `jsdom`). 그래야 Node 전역이 우연히 있어서 renderer 테스트가 통과하는 일이 없습니다.

## 2. Unit and component tests

- `hypercore-default` — main 테스트에서 `electron`은 handler를 잡아 두는 가짜 `ipcMain`을 돌려주는 helper 하나로 mock하고, 잡은 handler를 `senderFrame.origin`을 직접 정한 가짜 이벤트로 부릅니다. 새 handler마다 허용 origin과 거부 origin을 모두 테스트합니다.
- `hypercore-default` — renderer 테스트는 router context나 `platform/desktop.ts` 모듈로 가짜 `DesktopApi`를 넣습니다. `window`에 진짜 브리지를 할당하지 않습니다. 테스트마다 `retry: false`인 새 `QueryClient`를 만듭니다.
- `hypercore-default` — push 구독 테스트는 unmount가 unsubscribe 함수를 부르는지 확인합니다.

## 3. End-to-end tests

- `official` — Playwright는 CDP로 Electron을 실험적으로 지원합니다(`_electron`, Electron 21 이상). `electron.launch({ args: ['.'] })`는 `ElectronApplication`을 돌려주고, `app.evaluate(({ app }) => …)`는 main 프로세스에서 돌며, `firstWindow()`는 첫 페이지를 돌려줍니다. API가 실험적이므로 Playwright 버전을 고정합니다.
- `official` — `EnableNodeCliInspectArguments` fuse가 꺼져 있으면 Playwright 실행이 timeout으로 끝납니다. end-to-end 테스트는 패키징하지 않은 빌드(`electron-vite build` 후 `out/main/index.js` 실행)나 테스트 전용 패키지로 돌리고, 릴리스 빌드는 강화 fuse를 유지합니다.
- `official` — native 대화상자는 가로채지지 않습니다. `app.evaluate(({ dialog }) => …)` 안에서 stub합니다.
- `official` — ChromeDriver는 자기 인자(`--enable-automation`, `--remote-debugging-port=0`, 때로 `data:,`)를 더합니다. WebdriverIO 설정에서 엄격한 argv 파싱 전에 걸러 냅니다.
- `hypercore-default` — 보안이나 패키징을 건드린 작업에는 end-to-end smoke 테스트 하나가 필요합니다. 창이 custom protocol에서 로드되고, renderer에서 `window.require`와 `window.process`가 undefined이며, IPC 호출 하나가 봉투를 돌려줍니다.

## 4. Static gates

- `official` — electron-vite는 Vite처럼 변환만 합니다. 타입 검사는 `tsconfig.node.json`과 `tsconfig.web.json`에 `tsc --noEmit`을 돌려 따로 합니다(`rules/setup/typescript.md`).
- `hypercore-default` — `electron-vite build`가 통과한 것은 테스트 결과도 타입 검사도 아닙니다. 개발 실행이 통과한 것은 패키징 결과가 아닙니다. 패키징 작업은 패키징한 빌드에서 검증합니다.

## Review gate

1. 새 IPC handler에 거부 sender와 거부 입력 테스트가 없습니다.
2. renderer 테스트가 실제 `window.desktop`에 닿거나 `QueryClient` 하나를 공유합니다.
3. end-to-end 테스트가 실행하려고 릴리스 fuse를 완화했습니다.
4. 보안이나 패키징 변경을 개발 서버에서만 검증했습니다.
5. 빌드 결과를 타입 검사라고 보고했습니다.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| Electron의 테스트 도구 조사, ChromeDriver 인자, Playwright의 실험적 지원 | https://www.electronjs.org/docs/latest/tutorial/automated-testing |
| Playwright `_electron` API, Electron 21 이상, inspect fuse timeout, 대화상자 stubbing | https://playwright.dev/docs/api/class-electron |
| Vitest environment와 project로서의 Browser Mode | https://vitest.dev/guide/environment, https://vitest.dev/guide/browser/ |
| Vite와 electron-vite가 타입 검사 없이 변환만 함 | https://vite.dev/guide/features#transpile-only, https://electron-vite.org/guide/typescript |
| 출하 앱에서 프로세스별 Vitest project와 Playwright end to end | surveyed projects: https://github.com/CherryHQ/cherry-studio, https://github.com/cawa-93/vite-electron-builder |
| handler 테스트 쌍, 가짜 어댑터 주입, smoke 테스트 집합 | 이 패키지의 관례, 공식 요구 사항 아님 |
