# Processes and IPC

> Keep each Electron process to what it can safely reach, and let the renderer talk to the main process only through one typed, validated, narrow preload API.

Rules are labelled `official` when a page in `references/official/electron/electron-2026-11-08.md` states them, and `hypercore-default` when this package chose the default.

## 1. Process ownership

| Process | Runs on | Owns | Never owns |
|---|---|---|---|
| main (`src/main/`) | Node.js | `app` lifecycle, windows, menus, tray, `protocol`, `session`, `net`, `safeStorage`, file system, OS integration, every IPC handler | UI rendering, React, Tailwind, TanStack |
| preload (`src/preload/`) | renderer context with `require('electron')` only (sandboxed) | the `contextBridge` API object and nothing else | business logic, state, Node modules, secrets |
| renderer (`src/renderer/`) | Chromium, sandboxed and context-isolated | React UI, TanStack Router routes, TanStack Query cache, Tailwind styles | Node APIs, `ipcRenderer`, file paths outside what main hands it, credentials |
| utility process (`src/main/workers/` or `src/utility/`) | Node.js through `utilityProcess.fork` | long CPU or I/O work that would block the main process | windows, UI |
| shared (`src/shared/`) | imported by all of the above | channel names, request and response types, schemas, pure functions | imports from `electron`, Node built-ins, React, or the DOM |

- `official` — The main process hosts the UI thread for the whole app; long CPU or I/O work there freezes every window. Move it to a `utilityProcess` (preferred over `child_process.fork`, which throws when the `runAsNode` fuse is off) or a worker thread.
- `official` — The renderer has no `require` and no Node by default, its sandbox has been on by default since Electron 20, and it talks to main only through IPC.
- `official` — Since Electron 45 a sandboxed preload can `require` only `electron` (`electron/renderer`, `electron/common`); `events`, `timers`, `url`, `Buffer`, and `setImmediate` are gone. Use `EventTarget`, `setTimeout`, `queueMicrotask`, `URL`, `Uint8Array`, and `TextEncoder`, or bundle a polyfill into the preload.
- `official` — A sandboxed preload cannot use ESM imports: it must be CommonJS output, bundled into one file when split across modules. An ESM preload needs `sandbox: false` and the `.mjs` extension, and the `"type": "module"` field is ignored for preloads.
- `official` — An ESM main process (`.mjs` or `"type": "module"`) must `await` anything that has to happen before `ready`: `app.setPath`, `protocol.registerSchemesAsPrivileged`, and `app.enableSandbox()`.
- `hypercore-default` — `src/shared/` is the only folder all three processes import. A file there that imports `electron`, `node:*`, `react`, or touches `window` is a boundary violation, because it drags one process's runtime into another's bundle.

## 2. The four IPC patterns

| Need | Renderer side (inside preload) | Main side | Use |
|---|---|---|---|
| Request with a result | `ipcRenderer.invoke(channel, input)` | `ipcMain.handle(channel, handler)` | `official` recommended default for every read or command |
| Fire and forget | `ipcRenderer.send(channel, input)` | `ipcMain.on(channel, handler)` | telemetry, logs; never for a write whose failure the user must see |
| Push from main | `ipcRenderer.on(channel, listener)` wrapped by the preload | `win.webContents.send(channel, value)` | progress, update status, OS events |
| Renderer to renderer, or a stream | `MessagePort` received in `e.ports[0]` | `MessageChannelMain` plus `webContents.postMessage` | large or high-frequency streams, a utility process talking to a window |

- `official` — `ipcRenderer.sendSync` blocks the renderer and is documented as discouraged; `ipcRenderer.send` plus `event.reply` is a legacy pattern. Neither appears in new code.
- `official` — IPC payloads use the Structured Clone Algorithm. DOM objects, `process.env`, streams, `WebContents`, `BrowserWindow`, and class prototypes do not cross; `Error` crosses with its custom properties lost.
- `hypercore-default` — Return a discriminated result such as `{ ok: true, data } | { ok: false, error: { code, message } }` from handlers instead of throwing, because a thrown `Error` loses its `code` and custom fields on the way to the renderer. The renderer adapter turns `ok: false` back into a thrown `DesktopError` so TanStack Query sees a rejection.

## 3. The preload contract

- `official` — Expose one function per operation with `contextBridge.exposeInMainWorld`. Never expose `ipcRenderer`, `ipcRenderer.on`, `ipcRenderer.send`, or a generic `invoke(channel, ...)`; sending `ipcRenderer` itself yields `{}` since Electron 29.
- `official` — A listener wrapper must strip the `IpcRendererEvent` before calling the renderer's callback, because the event reaches `sender` and therefore `ipcRenderer`.
- `official` — Bridged values are copied and frozen, prototypes are dropped, and `Symbol` values disappear; only functions are proxied.
- `hypercore-default` — The preload returns an unsubscribe function from every `on*` wrapper, so a React effect can clean it up under `StrictMode`.

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

## 4. Typed and validated handlers

- `hypercore-default` — `src/shared/ipc/` holds the channel name constants, the `DesktopApi` interface, and one input schema per channel. Main, preload, and renderer import the same file, so a renamed channel fails the type check in all three.
- `official` — Validate the sender of every IPC message: compare `event.senderFrame` (which may be `null`) against an origin allowlist before doing any work.
- `hypercore-default` — Parse every handler's input with its schema in main, even though the preload is typed. The type annotation is a compile-time promise about your own renderer; the schema is the runtime check against a compromised or injected one.
- `hypercore-default` — Register all handlers from one `registerIpc()` call in `src/main/ipc/`, one file per domain. A typed-IPC library (`@egoist/tipc`, `electron-trpc`) is allowed when the project already uses it; it still needs sender checks and input parsing, and an unmaintained one is a migration finding.

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

Reject or correct the change when:

1. The renderer, or anything the preload exposes, reaches `ipcRenderer`, a generic `invoke(channel)`, `require`, or a Node module.
2. A handler skips the sender check or the runtime input parse.
3. A listener wrapper forwards the `IpcRendererEvent`, or returns no unsubscribe function.
4. `sendSync`, the `remote` module, or a `.send` used where the user must see the failure appears in new code.
5. `src/shared/` imports `electron`, a Node built-in, React, or the DOM.
6. The preload is emitted as ESM while `sandbox` is on, or depends on a Node shim removed in Electron 45.
7. Long CPU or I/O work runs in the main process instead of a utility process or worker.

## Sources

> Checked 2026-11-08 against the Electron 45 documentation set.

| Claim | Source |
|---|---|
| Process roles, the utility process, and TypeScript subpath exports | https://www.electronjs.org/docs/latest/tutorial/process-model |
| Sandboxed preload `require` scope and the shims removed in 45 | https://www.electronjs.org/docs/latest/tutorial/sandbox, https://www.electronjs.org/docs/latest/breaking-changes |
| ESM rules for main and preload | https://www.electronjs.org/docs/latest/tutorial/esm |
| The four IPC patterns, legacy patterns, and structured-clone limits | https://www.electronjs.org/docs/latest/tutorial/ipc, https://www.electronjs.org/docs/latest/tutorial/message-ports |
| `contextBridge` type table, frozen copies, and `ipcRenderer` arriving as `{}` | https://www.electronjs.org/docs/latest/api/context-bridge |
| Wrapping listeners without the event, and validating `senderFrame` | https://www.electronjs.org/docs/latest/tutorial/context-isolation, https://www.electronjs.org/docs/latest/tutorial/security |
| `child_process.fork` failing when `runAsNode` is off | https://www.electronjs.org/docs/latest/tutorial/fuses |
| The `src/shared/ipc/` contract, discriminated results, and schema parsing in main | this package's convention, not an official Electron requirement |
