# 패키징, 서명, 업데이트

> packager는 하나만 고르고, 서명 전에 fuse를 뒤집으며, 릴리스마다 서명과 notarization을 거치고, 업데이트는 packager 자체 업데이트 경로로 내보냅니다.

규칙은 `references/official/electron/electron-2026-11-08.md`의 페이지가 그대로 진술하면 `official`, 이 패키지가 기본값을 고르면 `hypercore-default`로 표시합니다.

## 1. One packager

| Packager | Build tool it pairs with | Config | Updates |
|---|---|---|---|
| electron-builder 26.x | electron-vite (조사한 electron-vite 앱 전부) | `electron-builder.yml` | `electron-updater` |
| Electron Forge 8.x | `@electron-forge/plugin-vite` | `forge.config.ts` | Electron 내장 `autoUpdater`(`update-electron-app`, 정적 저장소 publisher, 업데이트 서버 중 하나) |

- `hypercore-default` — 저장소는 packager를 하나 씁니다. 한 대상에 패키징 설정이 둘(`electron-builder.yml`과 `forge.config.*`) 있으면 발견 사항입니다. 릴리스 스크립트가 부르는 쪽을 남깁니다.
- `official` — Forge 8은 Vite 플러그인을 stable로 올리고 Vite 8을 대상으로 하며, `electron-forge publish`를 `electron-forge release`로 바꿨습니다(`publish`는 deprecated 별칭으로 남음). 문서 사이트에는 아직 옛 "experimental" 배너가 보이지만 8.0.1 릴리스 노트가 더 최신입니다.
- `official` — electron-builder의 기본 문서 URL은 이제 아직 나오지 않은 v27을 설명합니다. 26.x 프로젝트는 `https://www.electron.build/v26/docs/…`를 읽습니다. v27은 키 이름을 바꾸고 `electron-builder migrate-schema`를 제공합니다.
- `official` — 패키징된 `main` 진입 파일은 도구마다 다릅니다. electron-vite는 `out/main/index.js`, Forge는 `.vite/build/main.cjs`를 씁니다. `package.json`의 `main`은 빌드하는 도구와 맞아야 합니다.

## 2. Fuses

- `official` — fuse는 패키징 시점, 코드 서명 전에 뒤집습니다. Forge의 `FusesPlugin`이나 electron-builder의 `electronFuses` 키를 쓰고, 둘 다 `@electron/fuses` 옵션을 넘깁니다. 강화 집합은 `rules/electron/security.md` §6에 있고, Forge 템플릿은 이미 그중 여섯 개를 뒤집습니다.
- `official` — `EnableNodeCliInspectArguments`가 꺼져 있으면 Playwright의 `_electron.launch`가 timeout으로 끝납니다. end-to-end 테스트는 패키징하지 않은 빌드나 테스트 전용 패키지로 돌리고, 릴리스 빌드에서 fuse를 다시 켜서 해결하지 않습니다.

## 3. Signing and notarization

- `official` — macOS 자동 업데이트(Squirrel.Mac)에는 서명된 앱이 필요하고, `safeStorage`는 업데이트 후 Keychain 프롬프트를 피하려고 안정된 서명을 요구합니다.
- `official` — electron-builder는 `mac: { hardenedRuntime: true, notarize: true, entitlements, entitlementsInherit }` 한 번의 실행으로 서명, notarization, staple을 끝냅니다. Electron에는 최소한 `com.apple.security.cs.allow-jit`이 필요합니다. 자격 증명은 환경에서 옵니다. CI에서는 `APPLE_API_KEY`, `APPLE_API_KEY_ID`, `APPLE_API_ISSUER`를 쓰거나 `APPLE_ID`와 앱 전용 암호, `APPLE_TEAM_ID`를 씁니다. 인증서는 `CSC_LINK`와 `CSC_KEY_PASSWORD`로 넘깁니다.
- `hypercore-default` — 서명 자격 증명은 CI secret에만 둡니다. 저장소에도, `electron-builder.yml`에도, `VITE_` 변수에도 나타나지 않습니다. 릴리스의 서명, notarization, 게시는 권한이 필요한 동작이며 이 안내서는 명시적 요청 없이 실행하지 않습니다.

## 4. Updates

- `official` — Electron 내장 `autoUpdater`는 macOS와 Windows만 지원합니다. Linux 업데이트는 패키지 소스에서 옵니다. `update.electronjs.org`에는 공개 GitHub 저장소, GitHub Releases, 서명된 macOS 빌드가 필요합니다.
- `official` — `electron-updater`는 electron-builder와 별개 패키지입니다. 앱 의존성으로 설치하고, `publish`를 설정하고, `autoUpdater.checkForUpdatesAndNotify()`를 부릅니다. 빌드가 `app-update.yml`을 쓰므로 `setFeedURL`은 부르지 않습니다. macOS는 `dmg` 옆에 `zip` 대상이 필요하고, Squirrel.Windows는 지원하지 않습니다(NSIS를 씁니다).
- `official` — electron-builder의 암묵적 CI 게시는 deprecated이고 v27에서 제거됩니다. `--publish always|onTag|onTagOrDraft|never`를 명시적으로 넘깁니다.
- `hypercore-default` — 업데이트 확인은 첫 창이 보인 뒤 main에서 돌고, 상태를 push 채널 하나(`updates.onStatus`)로 renderer에 알립니다. `app.isPackaged`로 감쌉니다.

## 5. What goes into the package

- `official` — electron-vite는 renderer 의존성을 번들하고, 기본값(`build.externalizeDeps`)으로 main과 preload에서는 `dependencies`를 external로 남깁니다. React, TanStack, Tailwind 같은 renderer 전용 라이브러리는 `devDependencies`에 두어 electron-builder가 `app.asar`에 두 번 복사하지 않게 합니다. electron-vite 5부터 `externalizeDepsPlugin`과 `bytecodePlugin` 플러그인은 deprecated이고 `build.externalizeDeps`와 `build.bytecode`가 그 자리를 대신합니다.
- `official` — `asarUnpack`에는 `app.asar` 밖에 있어야 하는 파일(native addon, 자식 프로세스가 실행하는 바이너리)을 나열합니다. 나머지는 패킹 상태로 두어 ASAR 무결성 검사가 덮게 합니다.
- `official` — electron-vite의 `build.bytecode`는 프로덕션에서만 main과 preload 소스를 보호하고, bytecode preload에는 `sandbox: false`가 필요하며, V8 버전과 CPU 아키텍처에 묶입니다. preload bytecode를 얻으려고 renderer sandbox를 포기하지 않습니다.

## Review gate

1. packager가 둘 설정돼 있거나, `package.json`의 `main`이 빌드 도구 출력과 맞지 않습니다.
2. fuse를 서명 뒤에 뒤집거나, 릴리스 설정에서 빠뜨렸거나, 테스트를 통과시키려고 완화했습니다.
3. 서명이나 notarization 자격 증명이 저장소나 renderer가 보는 설정에 있습니다.
4. `electron-updater`가 `setFeedURL`을 쓰거나, macOS 빌드가 업데이트를 기대하면서 `zip` 대상이 없습니다.
5. bytecode 보호를 얻으려고 sandbox를 쓴 preload를 포기했습니다.
6. 26.x 프로젝트가 v27 문서 키를 따릅니다.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| Forge 8의 stable Vite 플러그인, `release` 이름 변경, 오래된 배너 | https://github.com/electron/forge/releases/tag/v8.0.1, https://www.electronforge.io/config/plugins/vite |
| Forge fuse 플러그인과 템플릿 fuse 집합 | https://www.electronforge.io/config/plugins/fuses, https://github.com/electron/forge/tree/main/packages/template/vite/tmpl |
| 서명 전에 fuse를 뒤집기 | https://www.electronjs.org/docs/latest/tutorial/fuses |
| electron-builder v26 설정, `asarUnpack`, `electronFuses`, v27 문서 차이 | https://www.electron.build/v26/docs/configuration |
| electron-builder 서명과 notarization | https://www.electron.build/v26/docs/code-signing-mac |
| `electron-updater` 설정, 대상, provider, 명시적 `--publish` | https://www.electron.build/v26/docs/auto-update, https://www.electron.build/v26/docs/publish |
| 내장 `autoUpdater` 플랫폼, 서명, `update.electronjs.org` | https://www.electronjs.org/docs/latest/api/auto-updater, https://www.electronjs.org/docs/latest/tutorial/updates |
| electron-vite `externalizeDeps`, `bytecode`, deprecated 플러그인 | https://electron-vite.org/guide/dependency-handling, https://electron-vite.org/guide/source-code-protection, https://github.com/alex8088/electron-vite/blob/master/CHANGELOG.md |
| inspect fuse를 끈 상태의 Playwright 실행 timeout | https://playwright.dev/docs/api/class-electron |
| 저장소당 packager 하나, CI 전용 자격 증명, 첫 창 뒤 업데이트 확인 | 이 패키지의 관례, 공식 Electron 요구 사항 아님 |
