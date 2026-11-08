Stack guide inside `hyper-architecture` for Electron. Read it when `rules/stack-detection.md` routes a target to Electron; from then on this file owns that target's work.

- Scope: Use this guide when building, auditing, restructuring, or reviewing an Electron desktop application whose renderer uses React and TypeScript with Tailwind CSS v4, TanStack Router file-based routing, and TanStack Query, built with electron-vite or Electron Forge's Vite plugin — process boundaries, the preload bridge and typed IPC, window and protocol setup, security settings and fuses, renderer routing and data, packaging, signing, updates, testing, or performance. Do not use it for a Tauri app, a browser-only Vite app, NW.js, or a documentation summary with no project work.
- Runtime needs: The target's `package.json` and lockfile, `electron.vite.config.*` or `forge.config.*`, the packager config, `src/main/`, `src/preload/`, and the renderer entry. Version claims use the dated snapshot in `references/official/electron/electron-2026-11-08.md`; packaging and performance claims need a packaged build.

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

> Keep every privilege in the main process, give the sandboxed renderer one typed and validated preload API, serve it from a custom protocol, and verify on a packaged build.

<output_language>

Default user-facing deliverables, reports, plans, handoff notes, and validation notes to Korean. Preserve code identifiers, commands, paths, package names, API names, config keys, fuse names, and source excerpts in their required form.

</output_language>

<purpose>

- Keep the main, preload, and renderer processes, and the `src/shared/` contract between them, explicit in every touched file.
- Treat the renderer as untrusted web content: no Node, no raw IPC, no secrets, sandboxed and context-isolated.
- Make the renderer stack (React, Tailwind CSS v4, TanStack Router, TanStack Query) work under a packaged load: renderer-only plugins, hash or memory history, IPC-aware Query policy.
- Tell official vendor behavior apart from this package's conventions, and name unverified topics as unverified.

</purpose>

<routing_rule>

Use this guide for setup, implementation, review, or remediation of an Electron target.

Do not use it when the target has no `electron` dependency and no `electron.vite.config.*`, `forge.config.*`, or `electron-builder.*` file; when `src-tauri/tauri.conf.json` is also present in the same target (a conflict that stops routing); or when the request is a copy-only edit that crosses no boundary.

A renderer built with Vite and TanStack Router, a Hono or other API client inside the renderer, and a `utilityProcess` worker are parts of the Electron target, not second frameworks. A missing layer (no router, no Query, no Tailwind) is an adoption step, not a violation.

</routing_rule>

<instruction_contract>

| Field | Contract |
|---|---|
| Intent | Produce an Electron architecture whose process boundaries, IPC contract, security settings, and renderer stack are reviewable and stay safe as the app grows. |
| Trigger | Electron work on folder layout, main/preload/renderer split, `contextBridge`, IPC, windows, protocol, `webPreferences`, fuses, renderer routing or data, Tailwind setup, packaging, updates, tests, or performance. |
| Scope | Touched `src/main/`, `src/preload/`, `src/shared/`, `src/renderer/` code, the build config, the packager config, tsconfig files, tests, and the matching rule files. |
| Authority | User and project instructions outrank this guide. Vendor documentation controls API facts; the installed versions control project behavior. `hypercore-default` rules are recommendations until adopted, except Safety rules, which block touched work. |
| Evidence | Read the manifest and lockfile, the build and packager configs, every `BrowserWindow` `webPreferences`, the preload, the IPC handlers, the renderer entry and router. Use the dated snapshot when a version decides the change. |
| Tools | Read, search, edit, and the project's own scripts. Gate dependency installs, packaging, signing, notarization, publishing, and anything that reaches users. |
| Loop | One review or remediation pass, then at most two verify-repair rounds against the gates below. A change stays only when it is inside the touched scope and passes. |
| Output | Korean findings or implementation summary with `official`, `hypercore-default`, and Safety labels, changed files, verification evidence, and remaining risk. |
| Verification | `tsc --noEmit` on both tsconfig projects, the test run, a production build, and a packaged smoke test for security or packaging work; a performance claim also needs before and after numbers. |
| Stop condition | Stop when the stack is confirmed, the applicable gates pass or are reported as blockers, and the evidence is recorded. |

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

- `Electron 설정 화면 문구만 바꿔줘.` Apply the change and a boundary check only.
- `공식 기본만 적용해줘.` The guide still applies; hypercore-default rules relax to optional findings, Safety rules stay blocking.

</activation_examples>

<trigger_conditions>

Activate when the target is an Electron package or the request names Electron, electron-vite, Electron Forge, electron-builder, `contextBridge`, `ipcMain`, preload, fuses, or `BrowserWindow`, and the work is setup, implementation, review, or remediation.

| Argument | Meaning |
|---|---|
| missing | Review and fix the requested or touched scope; untouched drift may be reported as backlog. |
| `전체 수정` / `full fix` | Full remediation across every window, the whole preload surface, every IPC domain, and the packager config, in the migration order. |
| `공식 기본만` / `official defaults only` | Downgrade hypercore-default conventions to optional findings unless `전체 수정` was also requested; Safety rules stay blocking. |

</trigger_conditions>

<skill_architecture>

- Core (`stacks/electron/core.md`): trigger, contract, gate order, workflow, verification, stop condition.
- Rules: `stacks/electron/architecture-rules.md` plus the topic files mapped in `reference_routing`.
- References: `references/official/electron/electron-2026-11-08.md` holds dated version, API, and tooling facts.
- Assets: `assets/evals/electron-cases.jsonl` holds trigger and behavior cases.
- Setup and performance tracks: `rules/setup/typescript.md` owns the tooling baseline; `rules/electron/performance.md` owns measured performance work.

</skill_architecture>

<loop_policy>

- One review or remediation pass per request.
- After remediation, at most two verify-repair rounds against the gates in Step 3 and the touched checks.
- A performance claim follows the measure-change-measure loop in `rules/electron/performance.md`; it never justifies an architecture refactor.

</loop_policy>

<language_and_translation_default>

Write findings, remediation summaries, and validation notes in Korean. Keep identifiers, paths, package names, config keys, fuse names, and the labels `official`, `hypercore-default`, and Safety in their source form. `stacks/electron/core.ko.md` mirrors this file section by section; a rule changed here is changed there in the same edit.

</language_and_translation_default>

<reference_routing>

Read `stacks/electron/architecture-rules.md` before editing. Then open the file that owns the touched surface.

| Touched surface | File |
|---|---|
| Folder layout, build config blocks, tsconfig split, aliases, starter-template debt, generated files | `rules/electron/project-structure.md` |
| Process ownership, utility processes, IPC patterns, the preload contract, typed and validated handlers, ESM rules | `rules/electron/processes-and-ipc.md` |
| `webPreferences`, custom protocol, CSP, navigation, `shell.openExternal`, permissions, secrets, fuses | `rules/electron/security.md` |
| React bootstrap, TanStack Router history and plugin, TanStack Query over IPC, Tailwind CSS v4 | `rules/electron/renderer.md` |
| Packager choice, fuses at package time, signing, notarization, updates, package contents | `rules/electron/packaging.md` |
| Unit, component, and end-to-end tests; static gates | `rules/electron/testing.md` |
| Measured startup, main-process blocking, bundle and package weight | `rules/electron/performance.md` |
| Lint, format, tsconfig, and package-manager baseline | `rules/setup/typescript.md` |
| Version, API, and tooling facts behind a rule | `references/official/electron/electron-2026-11-08.md` |

</reference_routing>

<support_file_read_order>

1. `stacks/electron/architecture-rules.md` for rule classes, trust model, and blocking gates.
2. The topic file for the touched surface, in `reference_routing` order; `rules/electron/security.md` whenever `webPreferences`, the preload, or a handler is touched.
3. `rules/electron/testing.md` before claiming validation.
4. `references/official/electron/electron-2026-11-08.md` when a version or API fact decides the change.

</support_file_read_order>

<workflow>

| Step | Task | Output |
|---|---|---|
| 1 | Prove the target is Electron, read versions, the build tool, and the packager | Scope decision |
| 2 | Load the rule files for the touched surface | Minimal evidence set |
| 3 | Judge planned changes against the blocking gates | Findings with file paths |
| 3.5 | Apply low-risk auto-remediations inside the touched scope | Edits or backlog items |
| 4 | Implement in the order below, then verify | Changed files and evidence |

Step 1 — project validation.

```bash
jq -r '(.dependencies // {}) + (.devDependencies // {}) | to_entries[] | select(.key | test("^(electron|electron-vite|electron-builder|electron-updater|@electron-forge/|@electron/fuses|@tailwindcss/vite|tailwindcss|@tanstack/react-(router|query)|@tanstack/router-plugin|vite|@vitejs/plugin-react)")) | "\(.key) \(.value)"' package.json
jq -r '.main // empty' package.json
ls electron.vite.config.* forge.config.* electron-builder.* src-tauri/tauri.conf.json 2>/dev/null
grep -rn 'contextIsolation\|sandbox\|nodeIntegration\|webSecurity\|loadFile\|loadURL\|protocol.handle' src/main
grep -rn 'exposeInMainWorld\|electronAPI\|ipcRenderer' src/preload
grep -rn 'createHashHistory\|createMemoryHistory\|createBrowserHistory\|createRouter' src/renderer
```

Read the installed version from the lockfile when the manifest uses a range. If `src-tauri/tauri.conf.json` is also present, stop and report the conflict. If no Electron signal is present, stop and route back.

Step 3 — apply the blocking gates in `stacks/electron/architecture-rules.md`. A gate fails even when untouched code shows the same pattern in the touched file.

Step 3.5 — auto-remediation. Apply directly when local, reversible, and low-risk:

- Write `contextIsolation: true`, `sandbox: true`, `nodeIntegration: false`, and `webSecurity: true` explicitly on a touched window.
- Replace a touched raw `ipcRenderer` exposure with named functions and add the `Window` type augmentation.
- Add the `senderFrame` check and a schema parse to a touched handler.
- Strip `IpcRendererEvent` from a listener wrapper and return an unsubscribe function.
- Switch the router to `createHashHistory()` when production loads `file://` or a protocol handler without fallback.
- Move `@tailwindcss/vite`, the router plugin, or the React plugin into `renderer.plugins`, router plugin first, with absolute route paths.
- Add `networkMode: 'always'` and an explicit focus-refetch policy to IPC-backed queries.

Do not auto-apply broad migrations: replacing the whole preload surface, switching packagers, changing the dev/prod URL convention, enabling fuses on an app that has never shipped with them, or anything that changes signing or updates.

Step 4 — implementation order.

1. Confirm detection, versions, build tool, packager, and the Electron support window.
2. Fix `webPreferences`, the custom protocol, navigation, and permission handlers.
3. Fix the preload contract and `src/shared/ipc/`.
4. Fix main handlers: sender checks, schema parsing, services, utility processes.
5. Fix the renderer: adapter, router history and plugin, Query policy, Tailwind setup.
6. Fix packaging: fuses, signing settings, update path.
7. Fix type checking and tests, then run the packaged smoke test.
8. Measure and change performance last, one lever at a time.

</workflow>

<required>

- A proven Electron target with Electron, build-tool, and packager versions named from installed evidence, and the Electron major checked against the supported three.
- Explicit secure `webPreferences` on every touched window.
- A preload exposing named functions only, typed by `src/shared/ipc/`.
- A sender check and runtime input parse in every touched IPC handler.
- A custom protocol for the packaged renderer, with a path-escape check.
- Renderer plugins in the renderer build only, and a history choice that works under the packaged load.
- A report labeling each finding `official`, `hypercore-default`, or Safety, with unverified topics named as unverified.

</required>

<forbidden>

- Applying Electron rules to a target without an Electron signal, or mixing Tauri rules into an Electron target.
- Turning off `contextIsolation` or the sandbox, or turning on `nodeIntegration`, to make a feature or dependency work.
- Exposing `ipcRenderer`, a generic invoke bridge, or `@electron-toolkit/preload`'s `electronAPI` to the renderer.
- Passing a renderer-supplied URL to `shell.openExternal` or `loadURL` without parsing and an allowlist check.
- Putting a credential where renderer code can read it.
- Treating the official electron-vite template's `sandbox: false` as an accepted default.
- Claiming a performance or packaging result from the dev server.
- Signing, notarizing, publishing, or releasing without an explicit request.
- Presenting a hypercore-default layout or IPC convention as official Electron behavior.

</forbidden>

<validation>

- [ ] Stack detection confirmed from `package.json` and the build or packager config; no Tauri conflict.
- [ ] Electron, electron-vite or Forge, packager, React, Router, Query, and Tailwind versions read from installed evidence.
- [ ] Every touched window has explicit secure `webPreferences`.
- [ ] Production loads from a custom protocol with a path-escape check and a CSP.
- [ ] Navigation, new windows, `shell.openExternal`, and permissions are restricted.
- [ ] The preload exposes named functions only and is a sandbox-compatible CommonJS bundle.
- [ ] Every touched handler checks the sender and parses its input.
- [ ] Renderer plugins sit in the renderer block, router plugin before React, with absolute route paths.
- [ ] The router history works under the packaged load; Query has an IPC-aware focus and network policy.
- [ ] Release config flips the hardened fuses before signing.
- [ ] Both tsconfig projects type check; tests pass; a packaged smoke test ran for security or packaging work.
- [ ] Performance work records before and after numbers from a packaged build.
- [ ] Findings are labeled, and unverified topics are named as such.

</validation>

## Sources

> Checked 2026-11-08. These statements restate the package's dated snapshot, `references/official/electron/electron-2026-11-08.md`, which cites the Electron 45 documentation, electron-vite, Electron Forge, electron-builder, TanStack, and Tailwind documentation, and npm registry metadata read on 2026-11-08.

| Claim | Source |
|---|---|
| Process model, sandbox, context isolation, and the preload `require` scope | https://www.electronjs.org/docs/latest/tutorial/process-model, https://www.electronjs.org/docs/latest/tutorial/sandbox |
| Security checklist, custom protocol, and fuses | https://www.electronjs.org/docs/latest/tutorial/security, https://www.electronjs.org/docs/latest/api/protocol, https://www.electronjs.org/docs/latest/tutorial/fuses |
| IPC patterns and `contextBridge` limits | https://www.electronjs.org/docs/latest/tutorial/ipc, https://www.electronjs.org/docs/latest/api/context-bridge |
| electron-vite layout and config blocks | https://electron-vite.org/guide/dev |
| TanStack Router history types and Vite plugin | https://tanstack.com/router/latest/docs/framework/react/guide/history-types, https://tanstack.com/router/latest/docs/framework/react/installation/with-vite |
| Tailwind CSS v4 Vite setup | https://tailwindcss.com/docs/installation/using-vite |
| The official template's defaults | https://github.com/alex8088/quick-start |
| Folder layout, adapter, typed IPC contract, and auto-remediation list | this package's convention, not an official requirement |
