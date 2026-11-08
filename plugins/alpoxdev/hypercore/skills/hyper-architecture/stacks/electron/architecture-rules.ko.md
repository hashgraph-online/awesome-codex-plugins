# Electron Architecture 규칙

> finding을 분류하거나 규칙을 적용하기 전에 읽습니다. 이 파일은 규칙 분류, 권한 순서, 목표 구조, blocking gate, migration 정책을 소유합니다.

## 규칙 분류

- **official**: 설치한 version에 대해 Electron, electron-vite, Electron Forge, electron-builder, Vite, React, Tailwind CSS, TanStack이 문서화한 동작.
- **hypercore-default**: 이 패키지의 더 엄격한 기본값. 채택하거나, 기록된 project 결정으로 대체할 수 있습니다.
- **Safety**: 신뢰 경계를 지키는 `hypercore-default` 규칙. touched work를 block하며, 위험을 명시적으로 받아들이지 않는 한 완화하지 않습니다.

우선순위는 사용자와 project 권한, 설치 project 증거(manifest, lockfile, `electron.vite.config.*` 또는 `forge.config.*`, `webPreferences`), 적용 가능한 공식 동작, hypercore-default입니다.

## 신뢰 모델

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

Renderer는 모든 byte가 app 안에서 출하되더라도 web content입니다. dependency, rendering된 문서, remote content가 script를 주입할 수 있습니다. 그래서 모든 권한은 main에 있고, 모든 IPC handler는 누가 호출했고 무엇을 넘겼는지 검사합니다.

## 목표 구조

전체 tree는 `rules/electron/project-structure.md`에 있습니다. 요약하면 `src/main/`, `src/preload/`, `src/renderer/`, `src/shared/`, block 셋을 가진 `electron.vite.config.ts` 하나(또는 Vite config 셋을 가진 Forge config), 그리고 `tsconfig.node.json`과 `tsconfig.web.json`입니다. Dependency는 `src/shared/`를 향해 안쪽으로 향하고, renderer는 main이나 preload code를 import하지 않습니다.

## Blocking gate

다음 touched work는 block하거나 수정합니다.

1. **renderer 경계를 약화함**: 기록되고 받아들여진 위험이 없는데 `contextIsolation: false`, `sandbox: false`, `nodeIntegration: true`, `webSecurity: false`, `allowRunningInsecureContent`, `experimentalFeatures`, `enableBlinkFeatures`를 씀.
2. **raw bridge를 노출함**: preload가 `ipcRenderer`, 범용 `invoke(channel, …)`, `@electron-toolkit/preload`의 `electronAPI`, 또는 `IpcRendererEvent`를 전달하는 listener wrapper를 노출함.
3. **IPC input을 신뢰함**: handler가 `senderFrame` origin 검사나 runtime schema parse를 건너뜀.
4. **production을 `file://`로 load함**: 패키징한 빌드의 `loadFile`이나 `file://` URL, 또는 경로 이탈 검사가 없는 `protocol.handle` callback을 씀.
5. **navigation을 열어 둠**: `will-navigate` origin 검사가 없거나, 기본 거부 `setWindowOpenHandler`가 없거나, 검사하지 않은 URL로 `shell.openExternal`을 호출함.
6. **permission을 기본으로 허용함**: content를 load하는 session에 permission 요청 handler가 없거나, 모든 permission을 허용함.
7. **secret을 renderer로 옮김**: renderer code, renderer storage, `VITE_`/`RENDERER_VITE_` 변수에 token, key, credential을 두거나, 동기 `safeStorage` API에 새 code를 씀.
8. **패키징한 load 환경에서 browser history를 씀**: protocol handler에 test한 `index.html` fallback이 없음.
9. **renderer plugin을 잘못된 build에 둠**: `@tailwindcss/vite`, `@tanstack/router-plugin/vite`, `@vitejs/plugin-react`를 renderer block 밖에 두거나, router plugin을 React plugin 뒤에 둠.
10. **sandboxed preload를 깨뜨림**: sandbox 상태에서 ESM 또는 externalize된 preload를 쓰거나, Electron 45에서 제거된 Node shim에 의존함.
11. **hardened fuse 없이 출하함**: 또는 signing 뒤에 fuse를 바꿈.
12. **main process를 block함**: utility process나 worker에 속하는 긴 CPU 또는 I/O 작업을 main에 둠.
13. **실행하지 않은 검증을 주장함**: build를 type check로 보고하거나, 보안이나 packaging 변경을 개발 서버에서만 검증함.

## 확장 가능한 기본값

- Window class마다 preload 계약 하나. `src/shared/ipc/api.ts`로 typing하고 한 번만 구현합니다.
- React와 `window.desktop` 사이에 renderer adapter(`platform/desktop.ts`) 하나. feature code는 adapter type에 의존하므로 test가 fake를 주입합니다.
- renderer root마다 `QueryClient` 하나, history 하나, router 하나. tab이 독립적인 location을 소유하면 tab마다 memory router 하나를 둡니다.
- `src/main/ipc/`에 domain마다 handler file 하나. 하나의 `registerIpc()`에서 등록합니다.
- Packager 하나, dev/prod URL 관례 하나.

## Brownfield 정책

1. touched code의 blocking gate는 고치거나 완료를 막습니다.
2. 건드리지 않은 도달 가능한 code의 blocking gate(다른 곳에서 쓰는 raw `ipcRenderer` bridge, 다른 window의 `sandbox: false`)는 file과 gate를 함께 보고합니다. 요청한 작업이 그것에 의존하거나 사용자가 요청하면 고칩니다.
3. 건드리지 않은 code의 `hypercore-default` 차이는 범위가 정해진 migration 단계로 기록하고, repository 전면 refactor로 확장하지 않습니다.
4. 공식 electron-vite template으로 만든 project는 첫날 gate 1, 2, 4를 실패하는 것이 정상입니다. template 부채로 보고하고 sandbox와 preload를 먼저, 그다음 protocol 순서로 고칩니다.

## Migration 정책

한 번에 domain 하나씩 옮깁니다. 그 channel과 schema를 `src/shared/ipc/`에 추가하고, preload surface를 이름 붙은 function으로 바꾸고, main에 sender와 input 검사를 추가하고, renderer 호출을 adapter로 바꾸고, 그 test를 갱신한 뒤 type check와 패키징한 빌드의 smoke test 하나를 돌리고 나서 다음 domain으로 넘어갑니다. Bridge 전체를 한 변경으로 교체하지 않습니다. 제거한 preload method는 그 화면이 실행될 때만 실패합니다.

## 완료 gate

모든 blocking gate가 통과하거나 file과 gate를 함께 보고합니다. hypercore-default 차이는 이유를 밝혀야 출하합니다. 검증 증거는 두 project의 type check, test 실행, production build이며, 보안이나 packaging 작업에는 패키징한 빌드의 smoke test 하나가 추가됩니다. 성능 주장에는 before와 after 수치가 더 필요합니다.

## Sources

> 확인 2026-11-08. 이 서술은 `references/official/electron/electron-2026-11-08.md`를 재진술한 것입니다.

| Claim | Source |
|---|---|
| Renderer 기본값, security checklist, sender 검증 | https://www.electronjs.org/docs/latest/tutorial/security |
| Sandboxed preload 범위와 45에서 제거된 shim | https://www.electronjs.org/docs/latest/tutorial/sandbox, https://www.electronjs.org/docs/latest/breaking-changes |
| 좁은 `contextBridge` 노출과 `{}`로 도착하는 `ipcRenderer` | https://www.electronjs.org/docs/latest/api/context-bridge, https://www.electronjs.org/docs/latest/tutorial/context-isolation |
| Custom protocol과 경로 이탈 검사 | https://www.electronjs.org/docs/latest/api/protocol |
| Signing 전에 뒤집는 fuse | https://www.electronjs.org/docs/latest/tutorial/fuses |
| Main process blocking과 utility process | https://www.electronjs.org/docs/latest/tutorial/performance, https://www.electronjs.org/docs/latest/api/utility-process |
| 공식 template의 `sandbox: false`, `electronAPI`, `loadFile` | https://github.com/alex8088/quick-start |
| 신뢰 모델 문구, adapter, brownfield와 migration 순서 | 공식 Electron 요구가 아니라 이 패키지의 관례 |
