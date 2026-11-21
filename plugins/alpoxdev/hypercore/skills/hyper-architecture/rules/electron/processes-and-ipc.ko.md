# 프로세스와 IPC

> 각 Electron 프로세스는 안전하게 닿을 수 있는 범위 안에 두고, renderer는 하나의 타입 있고 검증되며 좁은 preload API로만 main 프로세스와 대화하게 합니다.

`references/official/electron/electron-2026-11-08.md`의 페이지가 밝히는 규칙에는 `official` 표기를, 이 패키지가 기본값을 정한 규칙에는 `hypercore-default` 표기를 붙입니다.

## 1. 프로세스 소유권

| Process | Runs on | Owns | Never owns |
|---|---|---|---|
| main (`src/main/`) | Node.js | `app` lifecycle, 창, 메뉴, tray, `protocol`, `session`, `net`, `safeStorage`, 파일 시스템, OS 연동, 모든 IPC handler | UI 렌더링, React, Tailwind, TanStack |
| preload (`src/preload/`) | `require('electron')`만 쓸 수 있는 renderer 컨텍스트(sandbox) | `contextBridge` API 객체뿐 | business logic, 상태, Node module, secret |
| renderer (`src/renderer/`) | sandbox와 context isolation이 켜진 Chromium | React UI, TanStack Router route, TanStack Query cache, Tailwind 스타일 | Node API, `ipcRenderer`, main이 넘겨준 범위 밖의 파일 경로, credential |
| utility process (`src/main/workers/` 또는 `src/utility/`) | `utilityProcess.fork`를 거친 Node.js | main 프로세스를 막을 오래 걸리는 CPU 또는 I/O 작업 | 창, UI |
| shared (`src/shared/`) | 위 프로세스 모두가 import | channel 이름, 요청과 응답 타입, schema, 순수 함수 | `electron`, Node 내장 module, React, DOM에서 오는 import |

- `official` — main 프로세스는 앱 전체의 UI 스레드를 맡습니다. 그곳에서 오래 걸리는 CPU나 I/O 작업을 하면 모든 창이 멈춥니다. 그 작업을 `utilityProcess`(`runAsNode` fuse를 끈 상태에서 오류를 내는 `child_process.fork`보다 선호)나 worker thread로 옮깁니다.
- `official` — renderer에는 기본적으로 `require`도 Node도 없고, sandbox는 Electron 20부터 기본으로 켜져 있으며, main과는 IPC로만 대화합니다.
- `official` — Electron 45부터 sandbox preload는 `electron`(`electron/renderer`, `electron/common`)만 `require`할 수 있습니다. `events`, `timers`, `url`, `Buffer`, `setImmediate`는 없습니다. `EventTarget`, `setTimeout`, `queueMicrotask`, `URL`, `Uint8Array`, `TextEncoder`를 쓰거나 polyfill을 preload에 번들합니다.
- `official` — sandbox preload는 ESM import를 쓸 수 없습니다. CommonJS 출력이어야 하고, 모듈 여러 개로 나뉘면 한 파일로 번들합니다. ESM preload는 `sandbox: false`와 `.mjs` 확장자가 필요하며, `"type": "module"` 필드는 preload에 적용되지 않습니다.
- `official` — ESM main 프로세스(`.mjs` 또는 `"type": "module"`)는 `ready` 전에 끝나야 하는 작업을 `await`해야 합니다. `app.setPath`, `protocol.registerSchemesAsPrivileged`, `app.enableSandbox()`입니다.
- `hypercore-default` — `src/shared/`는 세 프로세스가 모두 import하는 유일한 폴더입니다. 그 안의 파일이 `electron`, `node:*`, `react`를 import하거나 `window`를 건드리면 경계 위반입니다. 한 프로세스의 런타임을 다른 프로세스의 번들로 끌고 들어오기 때문입니다.

## 2. 네 가지 IPC 패턴

| Need | Renderer side (inside preload) | Main side | Use |
|---|---|---|---|
| 결과가 있는 요청 | `ipcRenderer.invoke(channel, input)` | `ipcMain.handle(channel, handler)` | 모든 읽기나 명령의 `official` 권장 기본값 |
| 보내고 끝내기 | `ipcRenderer.send(channel, input)` | `ipcMain.on(channel, handler)` | telemetry, log. 사용자가 실패를 봐야 하는 쓰기에는 쓰지 않음 |
| main에서 밀어 넣기 | preload가 감싼 `ipcRenderer.on(channel, listener)` | `win.webContents.send(channel, value)` | 진행률, update 상태, OS event |
| renderer 사이 또는 stream | `e.ports[0]`로 받은 `MessagePort` | `MessageChannelMain`과 `webContents.postMessage` | 크거나 빈번한 stream, 창과 대화하는 utility process |

- `official` — `ipcRenderer.sendSync`는 renderer를 막으며 문서에서도 권장하지 않습니다. `ipcRenderer.send`와 `event.reply` 조합은 오래된 패턴입니다. 둘 다 새 코드에 넣지 않습니다.
- `official` — IPC payload는 Structured Clone Algorithm을 씁니다. DOM 객체, `process.env`, stream, `WebContents`, `BrowserWindow`, class prototype은 건너오지 못하고, `Error`는 사용자 정의 속성을 잃은 채 건너옵니다.
- `hypercore-default` — handler에서 예외를 던지지 말고 `{ ok: true, data } | { ok: false, error: { code, message } }` 같은 식별 가능한 결과를 돌려줍니다. 던진 `Error`는 renderer로 오는 길에 `code`와 사용자 정의 필드를 잃기 때문입니다. renderer adapter는 `ok: false`를 다시 `DesktopError` throw로 바꿔서 TanStack Query가 거부로 인식하게 합니다.

## 3. preload 계약

- `official` — `contextBridge.exposeInMainWorld`로 동작마다 함수 하나를 노출합니다. `ipcRenderer`, `ipcRenderer.on`, `ipcRenderer.send`, 범용 `invoke(channel, ...)`는 절대 노출하지 않습니다. `ipcRenderer` 자체를 넘기면 Electron 29부터 `{}`가 됩니다.
- `official` — listener wrapper는 renderer callback을 부르기 전에 `IpcRendererEvent`를 걷어내야 합니다. event가 `sender`에, 그래서 `ipcRenderer`에 닿기 때문입니다.
- `official` — bridged 값은 복사되고 동결되며 prototype은 사라지고 `Symbol` 값은 없어집니다. 함수만 proxy로 전달됩니다.
- `hypercore-default` — preload는 모든 `on*` wrapper에서 구독 해제 함수를 돌려줘서 React effect가 `StrictMode`에서 정리할 수 있게 합니다.

```ts
// src/preload/index.ts (bundled to CommonJS)
import { contextBridge, ipcRenderer } from 'electron'
import { channels } from '../shared/ipc/channels'
import type { DesktopApi } from '../shared/ipc/api'

const api: DesktopApi = {
  settings: {
    read: () => ipcRenderer.invoke(channels.settingsRead),
    write: (input) => ipcRenderer.invoke(channels.settingsWrite, input),
  },
  updates: {
    onStatus: (listener) => {
      const wrapped = (_event: Electron.IpcRendererEvent, status: unknown) => listener(status as never)
      ipcRenderer.on(channels.updateStatus, wrapped)
      return () => ipcRenderer.removeListener(channels.updateStatus, wrapped)
    },
  },
}

contextBridge.exposeInMainWorld('desktop', api)
```

```ts
// src/renderer/src/env.d.ts
import type { DesktopApi } from '../../shared/ipc/api'
declare global {
  interface Window { desktop: DesktopApi }
}
```

## 4. 타입과 검증을 갖춘 handler

- `hypercore-default` — `src/shared/ipc/`에 channel 이름 상수, `DesktopApi` interface, channel마다 input schema 하나를 둡니다. main, preload, renderer가 같은 파일을 import하므로 channel 이름을 바꾸면 세 곳의 타입 검사가 모두 실패합니다.
- `official` — 모든 IPC 메시지의 송신자를 검증합니다. 어떤 작업을 하기 전에 `event.senderFrame`(`null`일 수 있음)을 origin 허용 목록과 비교합니다.
- `hypercore-default` — preload가 타입을 갖췄더라도 main에서 handler마다 input을 schema로 파싱합니다. 타입 표기는 자기 renderer에 대한 컴파일 시점 약속이고, schema는 침해되었거나 주입된 renderer에 대항하는 런타임 검사입니다.
- `hypercore-default` — `src/main/ipc/`의 `registerIpc()` 호출 하나에서 모든 handler를 등록하고 도메인마다 파일 하나를 둡니다. 타입 있는 IPC library(`@egoist/tipc`, `electron-trpc`)는 프로젝트가 이미 쓰고 있으면 허용합니다. 그래도 송신자 검사와 input 파싱이 필요하고, 유지보수가 끊긴 library는 이관 지적입니다.

```ts
// src/main/ipc/settings.ts
import { ipcMain } from 'electron'
import { channels } from '../../shared/ipc/channels'
import { settingsInputSchema } from '../../shared/ipc/schemas'
import { assertTrustedSender } from './sender'

export function registerSettingsIpc(store: SettingsStore) {
  ipcMain.handle(channels.settingsRead, (event) => {
    assertTrustedSender(event)
    return { ok: true, data: store.read() } as const
  })
  ipcMain.handle(channels.settingsWrite, (event, raw: unknown) => {
    assertTrustedSender(event)
    const parsed = settingsInputSchema.safeParse(raw)
    if (!parsed.success) return { ok: false, error: { code: 'invalid-input', message: 'Invalid settings' } } as const
    return { ok: true, data: store.write(parsed.data) } as const
  })
}
```

## Review gate

다음에 해당하면 변경을 거부하거나 고칩니다.

1. renderer, 또는 preload가 노출한 무엇이든 `ipcRenderer`, 범용 `invoke(channel)`, `require`, Node module에 닿습니다.
2. handler가 송신자 검사나 런타임 input 파싱을 건너뜁니다.
3. listener wrapper가 `IpcRendererEvent`를 그대로 넘기거나 구독 해제 함수를 돌려주지 않습니다.
4. `sendSync`, `remote` module, 사용자가 실패를 봐야 하는 자리의 `.send`가 새 코드에 있습니다.
5. `src/shared/`가 `electron`, Node 내장 module, React, DOM을 import합니다.
6. preload가 `sandbox`가 켜진 상태에서 ESM으로 내보내졌거나 Electron 45에서 제거된 Node shim에 의존합니다.
7. 오래 걸리는 CPU나 I/O 작업이 utility process나 worker 대신 main 프로세스에서 돕니다.

## Sources

> 확인 2026-11-08. Electron 45 문서 집합을 기준으로 했습니다.

| Claim | Source |
|---|---|
| 프로세스 역할, utility process, TypeScript subpath export | https://www.electronjs.org/docs/latest/tutorial/process-model |
| sandbox preload의 `require` 범위와 45에서 제거된 shim | https://www.electronjs.org/docs/latest/tutorial/sandbox, https://www.electronjs.org/docs/latest/breaking-changes |
| main과 preload의 ESM 규칙 | https://www.electronjs.org/docs/latest/tutorial/esm |
| 네 가지 IPC 패턴, 오래된 패턴, structured clone 한계 | https://www.electronjs.org/docs/latest/tutorial/ipc, https://www.electronjs.org/docs/latest/tutorial/message-ports |
| `contextBridge` 타입 표, 동결된 복사본, `{}`로 도착하는 `ipcRenderer` | https://www.electronjs.org/docs/latest/api/context-bridge |
| event를 걷어내는 listener wrapper와 `senderFrame` 검증 | https://www.electronjs.org/docs/latest/tutorial/context-isolation, https://www.electronjs.org/docs/latest/tutorial/security |
| `runAsNode`가 꺼져 있을 때 실패하는 `child_process.fork` | https://www.electronjs.org/docs/latest/tutorial/fuses |
| `src/shared/ipc/` 계약, 식별 가능한 결과, main에서 schema 파싱 | 이 패키지의 규약이며 공식 Electron 요구 사항이 아님 |
