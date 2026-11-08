Electron을 위한 `hyper-architecture` 안의 stack guide입니다. `rules/stack-detection.md`가 target을 Electron으로 routing하면 이 파일을 읽고, 그때부터 이 파일이 해당 target의 작업을 소유합니다.

- Scope: React와 TypeScript, Tailwind CSS v4, TanStack Router file-based routing, TanStack Query로 renderer를 만들고 electron-vite 또는 Electron Forge의 Vite plugin으로 build하는 Electron desktop application을 만들거나, 감사하거나, 재구성하거나, 검토할 때 사용합니다. process 경계, preload bridge와 typed IPC, window와 protocol 설정, 보안 설정과 fuse, renderer routing과 data, packaging, signing, update, test, 성능이 대상입니다. Tauri app, browser-only Vite app, NW.js, 또는 project 작업이 없는 문서 요약에는 사용하지 않습니다.
- Runtime needs: target의 `package.json`과 lockfile, `electron.vite.config.*` 또는 `forge.config.*`, packager config, `src/main/`, `src/preload/`, renderer entry가 필요합니다. version 주장에는 `references/official/electron/electron-2026-11-08.md`의 날짜가 있는 snapshot을 사용하고, packaging과 성능 주장에는 패키징한 빌드가 필요합니다.

@architecture-rules.md
@../../rules/electron/project-structure.md
@../../rules/electron/processes-and-ipc.md
@../../rules/electron/security.md
@../../rules/electron/renderer.md
@../../rules/electron/packaging.md
@../../rules/electron/testing.md
@../../rules/electron/performance.md
@../../references/official/electron/electron-2026-11-08.md

# Electron Architecture

> 모든 권한을 main process에 두고, sandboxed renderer에는 typed이고 검증된 preload API 하나만 주며, custom protocol로 제공하고, 패키징한 빌드에서 확인합니다.

<output_language>

사용자에게 보이는 산출물, 보고, 계획, handoff note, validation note는 기본으로 한국어로 작성합니다. code identifier, command, path, package name, API name, config key, fuse 이름, source 발췌는 필요한 형태 그대로 유지합니다.

</output_language>

<purpose>

- main, preload, renderer process와 그 사이의 `src/shared/` 계약을 touched file마다 명시합니다.
- renderer를 신뢰하지 않는 web content로 다룹니다. Node도, raw IPC도, secret도 없고, sandbox와 context isolation을 켠 상태입니다.
- renderer stack(React, Tailwind CSS v4, TanStack Router, TanStack Query)이 패키징한 빌드의 load 환경에서 동작하게 만듭니다. renderer 전용 plugin, hash 또는 memory history, IPC를 인식하는 Query 정책을 씁니다.
- 공식 vendor 동작과 이 패키지의 관례를 구분하고, 확인하지 못한 topic은 미확인으로 표시합니다.

</purpose>

<routing_rule>

Electron target의 setup, 구현, 검토, 교정에 이 guide를 사용합니다.

target에 `electron` dependency가 없고 `electron.vite.config.*`, `forge.config.*`, `electron-builder.*` file도 없으면 사용하지 않습니다. 같은 target에 `src-tauri/tauri.conf.json`이 함께 있으면 routing을 멈추는 충돌이므로 사용하지 않습니다. architecture 경계를 넘지 않는 copy-only 수정에도 사용하지 않습니다.

Vite와 TanStack Router로 만든 renderer, renderer 안의 Hono 또는 다른 API client, `utilityProcess` worker는 Electron target의 일부이며 두 번째 framework가 아닙니다. 빠진 layer(router 없음, Query 없음, Tailwind 없음)는 위반이 아니라 채택 단계입니다.

</routing_rule>

<instruction_contract>

| Field | Contract |
|---|---|
| Intent | process 경계, IPC 계약, 보안 설정, renderer stack을 검토 가능하게 유지하고 app이 커져도 안전한 Electron architecture를 만듭니다. |
| Trigger | folder 배치, main/preload/renderer 분리, `contextBridge`, IPC, window, protocol, `webPreferences`, fuse, renderer routing이나 data, Tailwind 설정, packaging, update, test, 성능을 다루는 Electron 작업. |
| Scope | touched `src/main/`, `src/preload/`, `src/shared/`, `src/renderer/` code, build config, packager config, tsconfig file, test, 그리고 대응 rule file. |
| Authority | 사용자와 project 지시가 이 guide보다 우선합니다. Vendor 문서가 API 사실을 정하고, 설치된 version이 project 동작을 정합니다. `hypercore-default` 규칙은 채택하기 전까지 권고이며, Safety 규칙은 touched work를 block합니다. |
| Evidence | manifest와 lockfile, build와 packager config, 모든 `BrowserWindow` `webPreferences`, preload, IPC handler, renderer entry와 router를 읽습니다. version이 변경을 좌우하면 날짜가 있는 snapshot을 사용합니다. |
| Tools | 읽기, 검색, 편집, project 자체 script. dependency install, packaging, signing, notarization, publishing, 사용자에게 닿는 작업은 gate합니다. |
| Loop | 검토 또는 교정 1회, 그 뒤 아래 gate에 대한 verify-repair를 최대 2회. 변경은 touched scope 안이고 해당 gate를 통과할 때만 유지합니다. |
| Output | `official`, `hypercore-default`, Safety label이 붙은 한국어 finding 또는 구현 요약, 변경 file, 검증 증거, 남은 위험. |
| Verification | 두 tsconfig project에 대한 `tsc --noEmit`, test 실행, production build, 그리고 보안이나 packaging 작업에는 패키징한 빌드의 smoke test. 성능 주장에는 before와 after 수치가 추가로 필요합니다. |
| Stop condition | stack을 확인했고 적용 가능한 gate가 통과했거나 blocker로 보고됐으며 증거를 기록했을 때 멈춥니다. |

</instruction_contract>

<activation_examples>

Positive:

- `Electron 앱 main·preload·renderer 경계랑 IPC 구조 잡아줘.`
- `Audit this Electron app's preload bridge and ipcMain handlers before release.`
- `Electron + React + Tailwind v4 + TanStack Router·Query로 새 데스크톱 앱 구조 셋업해줘.`
- `패키징하면 TanStack Router 화면이 하얘져. 원인 찾아서 고쳐줘.`
- `Harden our Electron release build: fuses, CSP, custom protocol.`

Negative:

- `Review the capability files of our Tauri app.`
- `Electron 보안 문서 요약만 해줘.`

Boundary:

- `Electron 설정 화면 문구만 바꿔줘.` 변경과 boundary check만 적용합니다.
- `공식 기본만 적용해줘.` 이 guide는 여전히 적용되고, hypercore-default 규칙이 선택 finding으로 완화되며 Safety 규칙은 blocking으로 남습니다.

</activation_examples>

<trigger_conditions>

target이 Electron package이거나 요청이 Electron, electron-vite, Electron Forge, electron-builder, `contextBridge`, `ipcMain`, preload, fuse, `BrowserWindow`를 지목하고 작업이 setup, 구현, 검토, 교정일 때 활성화합니다.

| Argument | Meaning |
|---|---|
| missing | 요청받았거나 touched 범위의 scope를 검토하고 고칩니다. 건드리지 않은 drift는 backlog로 보고해도 됩니다. |
| `전체 수정` / `full fix` | migration 순서대로 모든 window, preload surface 전체, 모든 IPC domain, packager config를 전면 교정합니다. |
| `공식 기본만` / `official defaults only` | `전체 수정`을 함께 요청하지 않았다면 hypercore-default 관례를 선택 finding으로 낮춥니다. Safety 규칙은 blocking으로 남습니다. |

</trigger_conditions>

<skill_architecture>

- Core (`stacks/electron/core.md`): trigger, 계약, gate 순서, workflow, 검증, stop condition.
- Rules: `stacks/electron/architecture-rules.md`와 `reference_routing`에 mapping된 topic file.
- References: `references/official/electron/electron-2026-11-08.md`가 날짜가 있는 version, API, tooling 사실을 담습니다.
- Assets: `assets/evals/electron-cases.jsonl`이 trigger와 behavior case를 담습니다.
- Setup과 성능 track: `rules/setup/typescript.md`가 tooling 기준선을, `rules/electron/performance.md`가 측정 기반 성능 작업을 소유합니다.

</skill_architecture>

<loop_policy>

- 요청마다 검토 또는 교정을 1회 합니다.
- 교정 뒤 Step 3의 gate와 touched check에 대한 verify-repair를 최대 2회 합니다.
- 성능 주장은 `rules/electron/performance.md`의 measure-change-measure loop를 따르며, architecture refactor의 근거가 되지 않습니다.

</loop_policy>

<language_and_translation_default>

finding, 교정 요약, validation note는 한국어로 작성합니다. identifier, path, package name, config key, fuse 이름, `official`, `hypercore-default`, Safety label은 원래 형태로 유지합니다. `stacks/electron/core.ko.md`는 이 파일을 section별로 mirror하며, 여기서 바뀐 규칙은 같은 편집에서 그쪽도 바뀝니다.

</language_and_translation_default>

<reference_routing>

편집 전에 `stacks/electron/architecture-rules.md`를 읽습니다. 그다음 touched surface를 소유한 file을 엽니다.

| Touched surface | File |
|---|---|
| Folder 배치, build config block, tsconfig 분리, alias, starter template 부채, 생성 file | `rules/electron/project-structure.md` |
| Process 소유권, utility process, IPC pattern, preload 계약, typed이고 검증된 handler, ESM 규칙 | `rules/electron/processes-and-ipc.md` |
| `webPreferences`, custom protocol, CSP, navigation, `shell.openExternal`, permission, secret, fuse | `rules/electron/security.md` |
| React bootstrap, TanStack Router history와 plugin, IPC 위의 TanStack Query, Tailwind CSS v4 | `rules/electron/renderer.md` |
| Packager 선택, package 시점의 fuse, signing, notarization, update, package 내용 | `rules/electron/packaging.md` |
| Unit, component, end-to-end test, static gate | `rules/electron/testing.md` |
| 측정 기반 startup, main process blocking, bundle과 package 무게 | `rules/electron/performance.md` |
| Lint, format, tsconfig, package manager 기준선 | `rules/setup/typescript.md` |
| 규칙 뒤의 version, API, tooling 사실 | `references/official/electron/electron-2026-11-08.md` |

</reference_routing>

<support_file_read_order>

1. 규칙 분류, 신뢰 모델, blocking gate는 `stacks/electron/architecture-rules.md`에서 확인합니다.
2. touched surface의 topic file을 `reference_routing` 순서로 읽습니다. `webPreferences`, preload, handler를 건드리면 항상 `rules/electron/security.md`를 읽습니다.
3. 검증을 주장하기 전에 `rules/electron/testing.md`를 읽습니다.
4. version이나 API 사실이 변경을 좌우하면 `references/official/electron/electron-2026-11-08.md`를 읽습니다.

</support_file_read_order>

<workflow>

| Step | Task | Output |
|---|---|---|
| 1 | target이 Electron임을 증명하고 version, build tool, packager를 읽습니다 | Scope 결정 |
| 2 | touched surface의 rule file을 읽습니다 | 최소 증거 집합 |
| 3 | 계획한 변경을 blocking gate에 대조합니다 | file path가 붙은 finding |
| 3.5 | touched scope 안에서 위험이 낮은 자동 교정을 적용합니다 | 편집 또는 backlog item |
| 4 | 아래 순서로 구현하고 검증합니다 | 변경 file과 증거 |

Step 1 — project 확인.

```bash
jq -r '(.dependencies // {}) + (.devDependencies // {}) | to_entries[] | select(.key | test("^(electron|electron-vite|electron-builder|electron-updater|@electron-forge/|@electron/fuses|@tailwindcss/vite|tailwindcss|@tanstack/react-(router|query)|@tanstack/router-plugin|vite|@vitejs/plugin-react)")) | "\(.key) \(.value)"' package.json
jq -r '.main // empty' package.json
ls electron.vite.config.* forge.config.* electron-builder.* src-tauri/tauri.conf.json 2>/dev/null
grep -rn 'contextIsolation\|sandbox\|nodeIntegration\|webSecurity\|loadFile\|loadURL\|protocol.handle' src/main
grep -rn 'exposeInMainWorld\|electronAPI\|ipcRenderer' src/preload
grep -rn 'createHashHistory\|createMemoryHistory\|createBrowserHistory\|createRouter' src/renderer
```

manifest에 range가 있으면 설치 version을 lockfile에서 읽습니다. `src-tauri/tauri.conf.json`이 함께 있으면 멈추고 충돌을 보고합니다. Electron 신호가 없으면 멈추고 routing을 되돌립니다.

Step 3 — `stacks/electron/architecture-rules.md`의 blocking gate를 적용합니다. touched file에 건드리지 않은 code가 같은 pattern을 보여도 gate는 실패입니다.

Step 3.5 — 자동 교정. 국소적이고 되돌릴 수 있으며 위험이 낮으면 바로 적용합니다.

- touched window에 `contextIsolation: true`, `sandbox: true`, `nodeIntegration: false`, `webSecurity: true`를 명시합니다.
- touched 범위의 raw `ipcRenderer` 노출을 이름 붙은 function으로 바꾸고 `Window` type augmentation을 추가합니다.
- touched handler에 `senderFrame` 검사와 schema parse를 추가합니다.
- listener wrapper에서 `IpcRendererEvent`를 제거하고 unsubscribe function을 반환합니다.
- production이 `file://` 또는 fallback 없는 protocol handler로 load하면 router를 `createHashHistory()`로 바꿉니다.
- `@tailwindcss/vite`, router plugin, React plugin을 `renderer.plugins`로 옮기고, router plugin을 먼저 두며 route path를 absolute로 만듭니다.
- IPC 기반 query에 `networkMode: 'always'`와 명시적인 focus refetch 정책을 추가합니다.

전면 migration은 자동 적용하지 않습니다. preload surface 전체 교체, packager 변경, dev/prod URL 관례 변경, fuse를 한 번도 켠 적 없는 app에 fuse를 켜는 일, signing이나 update를 바꾸는 일이 해당합니다.

Step 4 — 구현 순서.

1. 감지, version, build tool, packager, Electron 지원 window를 확인합니다.
2. `webPreferences`, custom protocol, navigation, permission handler를 정리합니다.
3. Preload 계약과 `src/shared/ipc/`를 정리합니다.
4. Main handler를 정리합니다. sender 검사, schema parse, service, utility process를 다룹니다.
5. Renderer를 정리합니다. adapter, router history와 plugin, Query 정책, Tailwind 설정을 다룹니다.
6. Packaging을 정리합니다. fuse, signing 설정, update 경로를 다룹니다.
7. Type checking과 test를 정리하고 패키징한 빌드의 smoke test를 실행합니다.
8. 성능은 마지막에 lever 하나씩 측정하며 바꿉니다.

</workflow>

<required>

- 설치 증거로 Electron, build tool, packager version을 밝힌 증명된 Electron target과, 지원 중인 세 major에 대한 Electron major 확인.
- touched window마다 명시된 안전한 `webPreferences`.
- `src/shared/ipc/`에서 type을 정의한, 이름 붙은 function만 노출하는 preload.
- touched IPC handler마다 sender 검사와 runtime input parse.
- 경로 이탈 검사를 갖춘, 패키징한 renderer용 custom protocol.
- renderer build에만 있는 renderer plugin과, 패키징한 load 환경에서 동작하는 history 선택.
- finding마다 `official`, `hypercore-default`, Safety 중 하나를 붙이고 미확인 topic은 미확인으로 명시한 보고.

</required>

<forbidden>

- Electron 신호가 없는 target에 Electron 규칙을 적용하는 것, 또는 Electron target에 Tauri 규칙을 섞는 것.
- 기능이나 dependency를 동작시키려고 `contextIsolation`이나 sandbox를 끄거나 `nodeIntegration`을 켜는 것.
- `ipcRenderer`, 범용 invoke bridge, `@electron-toolkit/preload`의 `electronAPI`를 renderer에 노출하는 것.
- renderer가 준 URL을 parse와 허용 목록 검사 없이 `shell.openExternal`이나 `loadURL`로 넘기는 것.
- renderer code가 읽을 수 있는 곳에 credential을 두는 것.
- 공식 electron-vite template의 `sandbox: false`를 받아들인 기본값으로 취급하는 것.
- 개발 서버에서 성능이나 packaging 결과를 주장하는 것.
- 명시적인 요청 없이 signing, notarization, publishing, release를 하는 것.
- hypercore-default 배치나 IPC 관례를 공식 Electron 동작으로 제시하는 것.

</forbidden>

<validation>

- [ ] `package.json`과 build 또는 packager config로 stack 감지를 확인했고 Tauri 충돌이 없습니다.
- [ ] Electron, electron-vite 또는 Forge, packager, React, Router, Query, Tailwind version을 설치 증거에서 읽었습니다.
- [ ] touched window마다 명시적인 안전한 `webPreferences`가 있습니다.
- [ ] Production이 경로 이탈 검사와 CSP를 갖춘 custom protocol로 load합니다.
- [ ] Navigation, 새 window, `shell.openExternal`, permission이 제한됩니다.
- [ ] Preload가 이름 붙은 function만 노출하고 sandbox 호환 CommonJS bundle입니다.
- [ ] touched handler마다 sender를 검사하고 input을 parse합니다.
- [ ] Renderer plugin이 renderer block에 있고 router plugin이 React보다 앞에 있으며 route path가 absolute입니다.
- [ ] Router history가 패키징한 load 환경에서 동작하고, Query에 IPC를 인식하는 focus와 network 정책이 있습니다.
- [ ] Release config가 signing 전에 hardened fuse를 켭니다.
- [ ] 두 tsconfig project의 type check가 통과하고, test가 통과하며, 보안이나 packaging 작업에는 패키징한 빌드의 smoke test를 실행했습니다.
- [ ] 성능 작업이 패키징한 빌드의 before와 after 수치를 기록했습니다.
- [ ] finding에 label이 붙었고 미확인 topic은 그렇게 표시했습니다.

</validation>

## Sources

> 확인 2026-11-08. 이 서술은 이 패키지의 날짜가 있는 snapshot `references/official/electron/electron-2026-11-08.md`를 재진술한 것이며, 그 파일이 Electron 45 문서, electron-vite, Electron Forge, electron-builder, TanStack, Tailwind 문서, 그리고 2026-11-08에 읽은 npm registry metadata를 인용합니다.

| Claim | Source |
|---|---|
| Process model, sandbox, context isolation, preload의 `require` 범위 | https://www.electronjs.org/docs/latest/tutorial/process-model, https://www.electronjs.org/docs/latest/tutorial/sandbox |
| Security checklist, custom protocol, fuse | https://www.electronjs.org/docs/latest/tutorial/security, https://www.electronjs.org/docs/latest/api/protocol, https://www.electronjs.org/docs/latest/tutorial/fuses |
| IPC pattern과 `contextBridge` 제한 | https://www.electronjs.org/docs/latest/tutorial/ipc, https://www.electronjs.org/docs/latest/api/context-bridge |
| electron-vite 배치와 config block | https://electron-vite.org/guide/dev |
| TanStack Router history type과 Vite plugin | https://tanstack.com/router/latest/docs/framework/react/guide/history-types, https://tanstack.com/router/latest/docs/framework/react/installation/with-vite |
| Tailwind CSS v4 Vite 설정 | https://tailwindcss.com/docs/installation/using-vite |
| 공식 template의 기본값 | https://github.com/alex8088/quick-start |
| Folder 배치, adapter, typed IPC 계약, 자동 교정 목록 | 공식 요구가 아니라 이 패키지의 관례 |
