# 보안

> renderer를 신뢰할 수 없는 웹 콘텐츠로 취급하고, 모든 권한을 main 프로세스에 두고, custom protocol로 앱을 서비스하고, 서명 전에 fuse를 뒤집습니다.

`references/official/electron/electron-2026-11-08.md`의 페이지가 밝히는 규칙에는 `official` 표기를, 이 패키지가 기본값을 정한 규칙에는 `hypercore-default` 표기를 붙입니다. 대괄호 안 숫자는 Electron 보안 checklist의 항목 번호입니다.

## 1. `webPreferences` 기준선

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

- `official` — 기본값과 같더라도 보안 key 네 개를 명시적으로 씁니다. 검토자가 볼 수 있게 하고, 복사한 코드 조각이 조용히 하나를 끄지 못하게 하려는 것입니다. `contextIsolation`을 끄거나 `nodeIntegration`을 켜면 sandbox도 함께 꺼집니다 [3].
- `official` — `allowRunningInsecureContent`, `experimentalFeatures`, `enableBlinkFeatures`는 절대 설정하지 않습니다 [8, 9, 10]. `webSecurity`를 끄면 `allowRunningInsecureContent`도 강제로 켜집니다 [6].
- `hypercore-default` — 새 앱에서는 `ready` 전에 `app.enableSandbox()`를 부릅니다. 나중에 `sandbox: false`로 만든 창도 sandbox 상태로 남습니다 [4].

## 2. 콘텐츠와 navigation

- `official` — 안전한 콘텐츠만 엽니다. 패키징한 앱은 custom protocol에서, remote 콘텐츠는 HTTPS로만 엽니다 [1, 18].
- `official` — 앱 scheme을 `ready` 전에 한 번 등록합니다. `protocol.registerSchemesAsPrivileged([{ scheme: 'app', privileges: { standard: true, secure: true, supportFetchAPI: true } }])`를 쓰고, `ready` 뒤에 `protocol.handle('app', …)`로 파일을 서비스합니다. `standard`는 상대 URL 해석과 웹 storage를 줍니다. 오래된 `register*Protocol`과 `intercept*Protocol` 계열은 deprecated입니다.
- `official` — `protocol.handle` callback은 요청 경로를 renderer 출력 폴더 기준으로 해석하고 그 밖으로 나가는 경로를 거부합니다(`path.relative` 결과가 `..`로 시작). 그 검사가 없는 handler는 디스크 전체를 서비스합니다.
- `official` — `file://` 페이지는 브라우저보다 넓은 권한을 받습니다. `GrantFileProtocolExtraPrivileges` fuse가 켜져 있으면 모든 파일에 닿을 수 있습니다. production 빌드는 `loadFile`이 아니라 custom protocol에서 엽니다 [18].
- `official` — Content-Security-Policy를 응답 header로 설정합니다. `session.defaultSession.webRequest.onHeadersReceived`나 `protocol.handle` 응답에서 넣습니다. `<meta http-equiv>` tag는 header를 설정할 수 없는 곳에서만 쓰는 대체 수단입니다 [7].
- `official` — `app.on('web-contents-created')`에서 navigation을 제한합니다. `will-navigate`에서는 `new URL(url).origin`을 허용 목록과 비교하고(`startsWith`는 절대 쓰지 않음), `setWindowOpenHandler`는 기본적으로 `{ action: 'deny' }`로 거부합니다 [13, 14].
- `official` — `shell.openExternal`에는 URL을 파싱해 protocol(`https:`와 필요한 mail scheme)과 host를 허용 목록과 확인한 뒤에만 넘깁니다. 그곳에 신뢰할 수 없는 입력이 들어가면 명령 실행이 될 수 있습니다 [15].
- `official` — `<webview>`를 쓰지 않습니다. 기존 앱이 어쩔 수 없이 쓸 때는 `will-attach-webview`에서 옵션을 검증하고 `allowpopups`를 절대 설정하지 않습니다 [11, 12]. 새로 넣는 embedded 콘텐츠는 `WebContentsView`를 씁니다. `BrowserView`는 Electron 30부터 deprecated입니다.

### 개발·운영 URL

- `hypercore-default` — 개발에서는 electron-vite나 Forge가 주는 Vite 개발 서버 URL(`ELECTRON_RENDERER_URL` 또는 Forge가 주입한 상수)을 열고, production에서는 `app://…/index.html`을 엽니다. `app.isPackaged`나 빌드 시점 mode로 고르고 renderer가 준 값으로 고르지 않습니다. navigation 허용 목록에는 개발 빌드에서만 개발 origin을 넣습니다.

## 3. permission과 session

- `official` — Electron은 기본적으로 모든 permission 요청을 승인합니다. 콘텐츠를 여는 모든 session에 `setPermissionRequestHandler`(와 `setPermissionCheckHandler`)를 설치하고, 제품이 앱 origin에 실제로 필요로 하는 permission만 허용합니다 [5].
- `official` — Electron 45부터 화면 캡처는 `display-capture`로 요청하고 `media`는 camera와 microphone만 뜻합니다. 화면 공유를 위해 `media`를 허용하던 handler는 이제 `display-capture`를 허용해야 합니다.
- `hypercore-default` — 앱이 신뢰할 수 없는 remote 콘텐츠를 꼭 열어야 한다면 그 콘텐츠 전용 `session.fromPartition()`과 전용 permission handler를 씁니다. 로그인 cookie를 들고 있는 앱 기본 session에는 절대 넣지 않습니다.

## 4. IPC 노출

- `official` — Electron API, 특히 `ipcRenderer`를 renderer에 노출하지 않습니다. 동작마다 좁은 함수 하나를 노출합니다 [20].
- `official` — 모든 IPC 메시지의 송신자를 `event.senderFrame`과 origin 허용 목록으로 검증합니다 [17].
- 런타임 input 파싱을 포함한 전체 IPC 계약은 `rules/electron/processes-and-ipc.md`에 있습니다.

## 5. secret

- `official` — `safeStorage`는 main 프로세스에서만 돕니다. Electron 45에서 동기 `encryptString`/`decryptString`/`isEncryptionAvailable`이 deprecated이고 46에서 제거됩니다. `isAsyncEncryptionAvailable`, `encryptStringAsync`, `decryptStringAsync`를 쓰고 결과가 `shouldReEncrypt`를 알리면 다시 암호화합니다.
- `official` — Linux에서 `basic_text` backend는 하드코딩된 password를 뜻하며 보호가 아닙니다. `getSelectedStorageBackend()`로 확인하고 보고합니다. macOS에서는 안정적인 code signature가 있어야 update마다 Keychain 재입력을 막을 수 있습니다.
- `hypercore-default` — token과 API key는 main에 두고 `safeStorage`로 저장 시점에 암호화합니다. 인증이 필요한 요청은 main에서 `net.fetch`(Chromium 네트워크 stack, proxy 인식)로 하거나 앱 `session`을 받은 utility process에서 합니다. renderer는 데이터를 받고 token은 받지 않습니다. renderer의 `import.meta.env` 값(`VITE_` 또는 `RENDERER_VITE_` 접두사)은 공개된 빌드 시점 문자열입니다.

## 6. fuse와 패키지 무결성

`official` — fuse는 패키징 시점에, code signing 전에 `@electron/fuses`나 Forge의 fuses plugin으로 뒤집습니다 [19]. 강화 조합은 다음과 같습니다.

| Fuse | Set to | Why |
|---|---|---|
| `RunAsNode` | off | `ELECTRON_RUN_AS_NODE`가 바이너리를 Node로 바꾸는 것을 막음 |
| `EnableNodeOptionsEnvironmentVariable` | off | `NODE_OPTIONS` 주입을 막음 |
| `EnableNodeCliInspectArguments` | off | production에서 `--inspect` 접속을 막음 |
| `GrantFileProtocolExtraPrivileges` | off | 앱을 custom protocol에서 서비스함 |
| `EnableCookieEncryption` | on | cookie store를 암호화함(단방향. macOS에서는 서명 필요) |
| `EnableEmbeddedAsarIntegrityValidation` | on | 변조된 `app.asar`에서 종료함(macOS, Electron 30부터 Windows) |
| `OnlyLoadAppFromAsar` | on | 무결성 검증과 함께 써서 검증된 코드만 load |

- `official` — `RunAsNode`를 끄면 `child_process.fork`가 깨집니다. `utilityProcess.fork`를 씁니다.
- `official` — 지원하는 Electron major(최근 세 개)에 머물고, breaking-changes 페이지를 보며 한 major씩 올립니다 [16].

## Review gate

다음에 해당하면 변경을 거부하거나 고칩니다.

1. `contextIsolation: false`, `sandbox: false`, `nodeIntegration: true`, `webSecurity: false`, `allowRunningInsecureContent`, `experimentalFeatures`, `enableBlinkFeatures` 중 하나가 기록되고 수용된 위험 없이 나타납니다.
2. production renderer가 `file://`나 `loadFile`로 열리거나, `protocol.handle` callback에 경로 이탈 검사가 없습니다.
3. CSP가 없거나 `unsafe-eval`을 포함하거나, `script-src`가 앱에 필요 없는 remote origin을 허용합니다.
4. `will-navigate`나 `setWindowOpenHandler`가 없거나, 문자열 접두사로 비교하거나, 기본 허용입니다.
5. `shell.openExternal`이 파싱하지 않았거나 검사하지 않은 URL을 받습니다.
6. 콘텐츠를 여는 session에 permission request handler가 없거나, handler가 모든 것을 허용합니다.
7. credential이 renderer 코드, renderer storage, `VITE_` 접두사 변수에 닿거나, 새 코드가 동기 `safeStorage` API를 씁니다.
8. release 빌드가 강화 fuse 조합 없이 나가거나, 서명 뒤에 fuse를 뒤집습니다.

## Sources

> 확인 2026-11-08. Electron 45 문서 집합을 기준으로 했습니다.

| Claim | Source |
|---|---|
| 20개 항목 checklist, 그 기본값, 송신자 검증 | https://www.electronjs.org/docs/latest/tutorial/security |
| sandbox 기본값과 `app.enableSandbox()` | https://www.electronjs.org/docs/latest/tutorial/sandbox |
| `registerSchemesAsPrivileged`, `protocol.handle`, 경로 이탈 예시, deprecated 계열 | https://www.electronjs.org/docs/latest/api/protocol |
| 45에서 화면 캡처용 `media`를 대체한 `display-capture` | https://www.electronjs.org/docs/latest/breaking-changes |
| permission handler와 partition | https://www.electronjs.org/docs/latest/api/session |
| `safeStorage` async API, deprecation, backend, 서명 주의 | https://www.electronjs.org/docs/latest/api/safe-storage |
| Chromium 네트워크 stack을 쓰는 `net.fetch` | https://www.electronjs.org/docs/latest/api/net |
| fuse 이름, 기본값, 서명 전 뒤집기 | https://www.electronjs.org/docs/latest/tutorial/fuses |
| ASAR 무결성 지원 platform과 불일치 시 종료 | https://www.electronjs.org/docs/latest/tutorial/asar-integrity |
| `BrowserView` 대신 `WebContentsView` 사용(deprecated) | https://www.electronjs.org/docs/latest/breaking-changes |
| 개발·운영 URL 선택, remote 콘텐츠용 별도 partition, main에 두는 token | 이 패키지의 규약이며 공식 Electron 요구 사항이 아님 |
