# Security

> Treat the renderer as untrusted web content, keep every privilege in the main process, serve the app from a custom protocol, and flip the fuses before signing.

Rules are labelled `official` when a page in `references/official/electron/electron-2026-11-08.md` states them, and `hypercore-default` when this package chose the default. The numbers in brackets are the item numbers of Electron's security checklist.

## 1. `webPreferences` baseline

```ts
// src/main/windows/main-window.ts
new BrowserWindow({
  show: false,
  webPreferences: {
    preload: join(__dirname, '../preload/index.js'),
    contextIsolation: true,   // default since 12 [3]
    sandbox: true,            // default since 20 [4]
    nodeIntegration: false,   // default since 5 [2]
    webSecurity: true,        // [6]
  },
})
```

- `official` — Write the four security keys explicitly even though they match the defaults, so a reviewer sees them and a copied snippet cannot silently turn one off. Turning `contextIsolation` off or `nodeIntegration` on also disables the sandbox [3].
- `official` — Never set `allowRunningInsecureContent`, `experimentalFeatures`, or `enableBlinkFeatures` [8, 9, 10]. Disabling `webSecurity` also forces `allowRunningInsecureContent` on [6].
- `hypercore-default` — Call `app.enableSandbox()` before `ready` in a new app, so a window created later with `sandbox: false` is still sandboxed [4].

## 2. Content and navigation

- `official` — Load only secure content: the packaged app from a custom protocol, remote content over HTTPS only [1, 18].
- `official` — Register the app scheme once, before `ready`, with `protocol.registerSchemesAsPrivileged([{ scheme: 'app', privileges: { standard: true, secure: true, supportFetchAPI: true } }])`, then serve files with `protocol.handle('app', …)` after `ready`. `standard` gives relative URL resolution and web storage; the older `register*Protocol` and `intercept*Protocol` family is deprecated.
- `official` — The `protocol.handle` callback resolves the requested path against the renderer output folder and rejects any path that escapes it (`path.relative` result starting with `..`). A handler without that check serves the whole disk.
- `official` — `file://` pages get privileges beyond a browser's; with the `GrantFileProtocolExtraPrivileges` fuse on they can reach every file. Load the production build from the custom protocol, not `loadFile` [18].
- `official` — Set a Content-Security-Policy as a response header through `session.defaultSession.webRequest.onHeadersReceived` or in the `protocol.handle` response; a `<meta http-equiv>` tag is the fallback only where headers cannot be set [7].
- `official` — Limit navigation in `app.on('web-contents-created')`: handle `will-navigate` by comparing `new URL(url).origin` with an allowlist (never `startsWith`), and deny `setWindowOpenHandler` by default with `{ action: 'deny' }` [13, 14].
- `official` — Pass a URL to `shell.openExternal` only after parsing it and checking its protocol (`https:` and the mail scheme you need) and host against an allowlist; untrusted input there can become command execution [15].
- `official` — Do not use `<webview>`. When an existing app must, verify its options in `will-attach-webview` and never set `allowpopups` [11, 12]. New embedded content uses `WebContentsView`; `BrowserView` is deprecated since Electron 30.

### Development and production URLs

- `hypercore-default` — In development load the Vite dev server URL that electron-vite or Forge provides (`ELECTRON_RENDERER_URL` or the Forge-injected constant); in production load `app://…/index.html`. Choose by `app.isPackaged` or the build-time mode, never by a renderer-supplied value, and allow the dev origin in the navigation allowlist only in development builds.

## 3. Permissions and sessions

- `official` — Electron approves every permission request by default. Install `setPermissionRequestHandler` (and `setPermissionCheckHandler`) on every session that loads content, granting only the permissions the product needs for the app origin [5].
- `official` — Since Electron 45 screen capture is requested as `display-capture`, and `media` means camera and microphone only; a handler that granted `media` for screen sharing must now grant `display-capture`.
- `hypercore-default` — Load untrusted remote content, if the app must, in its own `session.fromPartition()` with its own permission handler, never in the app's default session that holds the login cookies.

## 4. IPC exposure

- `official` — Do not expose Electron APIs, especially `ipcRenderer`, to the renderer; expose one narrow function per operation [20].
- `official` — Validate the sender of all IPC messages through `event.senderFrame` and an origin allowlist [17].
- The full IPC contract, including runtime input parsing, lives in `rules/electron/processes-and-ipc.md`.

## 5. Secrets

- `official` — `safeStorage` runs in the main process only. In Electron 45 the synchronous `encryptString`/`decryptString`/`isEncryptionAvailable` are deprecated, and they are removed in 46: use `isAsyncEncryptionAvailable`, `encryptStringAsync`, and `decryptStringAsync`, and re-encrypt when the result reports `shouldReEncrypt`.
- `official` — On Linux the `basic_text` backend means a hardcoded password, not protection; check `getSelectedStorageBackend()` and report it. On macOS a stable code signature keeps the Keychain from re-prompting after each update.
- `hypercore-default` — Tokens and API keys stay in main, encrypted at rest with `safeStorage`; authenticated requests run from main with `net.fetch` (Chromium's network stack, proxy-aware) or from a utility process given the app `session`. The renderer receives data, never the token. Renderer `import.meta.env` values (`VITE_` or `RENDERER_VITE_` prefixes) are public build-time strings.

## 6. Fuses and package integrity

`official` — Fuses are flipped at package time, before code signing, with `@electron/fuses` or Forge's fuses plugin [19]. Hardened set:

| Fuse | Set to | Why |
|---|---|---|
| `RunAsNode` | off | blocks `ELECTRON_RUN_AS_NODE` turning the binary into Node |
| `EnableNodeOptionsEnvironmentVariable` | off | blocks `NODE_OPTIONS` injection |
| `EnableNodeCliInspectArguments` | off | blocks `--inspect` attach in production |
| `GrantFileProtocolExtraPrivileges` | off | the app is served from a custom protocol |
| `EnableCookieEncryption` | on | encrypts the cookie store (one-way; needs signing on macOS) |
| `EnableEmbeddedAsarIntegrityValidation` | on | terminates on a modified `app.asar` (macOS, and Windows from Electron 30) |
| `OnlyLoadAppFromAsar` | on | pair with integrity validation so only validated code loads |

- `official` — Turning `RunAsNode` off breaks `child_process.fork`; use `utilityProcess.fork`.
- `official` — Stay on a supported Electron major (the latest three) and upgrade one major at a time against the breaking-changes page [16].

## Review gate

Reject or correct the change when:

1. Any of `contextIsolation: false`, `sandbox: false`, `nodeIntegration: true`, `webSecurity: false`, `allowRunningInsecureContent`, `experimentalFeatures`, or `enableBlinkFeatures` appears without a recorded, accepted risk.
2. The production renderer loads through `file://` or `loadFile`, or the `protocol.handle` callback has no path-escape check.
3. No CSP is set, or it contains `unsafe-eval`, or `script-src` allows a remote origin the app does not need.
4. `will-navigate` or `setWindowOpenHandler` is missing, compares with a string prefix, or allows by default.
5. `shell.openExternal` receives an unparsed or unchecked URL.
6. A session that loads content has no permission request handler, or the handler grants everything.
7. A credential reaches renderer code, renderer storage, or a `VITE_`-prefixed variable, or the synchronous `safeStorage` API is used in new code.
8. A release build ships without the hardened fuse set, or flips fuses after signing.

## Sources

> Checked 2026-11-08 against the Electron 45 documentation set.

| Claim | Source |
|---|---|
| The 20-item checklist, its defaults, and sender validation | https://www.electronjs.org/docs/latest/tutorial/security |
| Sandbox default and `app.enableSandbox()` | https://www.electronjs.org/docs/latest/tutorial/sandbox |
| `registerSchemesAsPrivileged`, `protocol.handle`, the path-escape example, and the deprecated family | https://www.electronjs.org/docs/latest/api/protocol |
| `display-capture` replacing `media` for screen capture in 45 | https://www.electronjs.org/docs/latest/breaking-changes |
| Permission handlers and partitions | https://www.electronjs.org/docs/latest/api/session |
| `safeStorage` async API, deprecation, backends, and signing note | https://www.electronjs.org/docs/latest/api/safe-storage |
| `net.fetch` on Chromium's network stack | https://www.electronjs.org/docs/latest/api/net |
| Fuse names, defaults, and flipping before signing | https://www.electronjs.org/docs/latest/tutorial/fuses |
| ASAR integrity platforms and termination on mismatch | https://www.electronjs.org/docs/latest/tutorial/asar-integrity |
| `BrowserView` deprecated in favour of `WebContentsView` | https://www.electronjs.org/docs/latest/breaking-changes |
| Development versus production URL choice, a separate partition for remote content, and tokens kept in main | this package's convention, not an official Electron requirement |
