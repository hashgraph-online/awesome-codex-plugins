Stack guide inside `hyper-architecture` for Lynx. Read it when `rules/stack-detection.md` routes a target to Lynx; from then on this file owns that target's work.

- Scope: Use this guide when building, auditing, restructuring, or reviewing a Lynx application that renders with ReactLynx and builds with Rspeedy on the Lynx dual-thread engine — folder structure, the main-thread/background split, elements and CSS, host data, native modules, host-app embedding, engine-version compatibility, testing, or performance. Do not use it for React DOM apps, React Native or Expo apps, or a repository whose only React signal is a `react` dependency with no `@lynx-js/react`.
- Runtime needs: The target's `package.json`, `lynx.config.*`, `tsconfig.json`, and the native host project when one is in the repository. Current version claims may need the dated snapshot in `references/official/lynx/lynx-2026-11-07.md`, and a device or Lynx DevTool session for any measured performance claim.

@architecture-rules.md
@../../rules/lynx/project-structure.md
@../../rules/lynx/threading.md
@../../rules/lynx/ui-and-data.md
@../../rules/lynx/native-and-platform.md
@../../rules/lynx/testing.md
@../../rules/lynx/performance.md
@../../references/official/lynx/lynx-2026-11-07.md

# Lynx Architecture

> Enforce a ReactLynx architecture whose dual-thread boundary, bundle layering, host contract, and engine-version floor are explicit before any code changes.

<output_language>

Default user-facing deliverables, reports, plans, handoff notes, and validation notes to Korean. Preserve code identifiers, commands, paths, package names, API names, directives such as `'main thread'`, and source excerpts in their required form.

</output_language>

<purpose>

- Keep the two execution threads, their allowed APIs, and the boundary between them explicit in every touched file.
- Keep the main-thread bundle on the first-frame critical path as small as the feature allows.
- Treat the native host as a contract partner: `engineVersion`, `initData`, `globalProps`, and native modules are reviewed like any other interface.
- Tell official Lynx behavior apart from this package's conventions, and mark unverified topics as unverified rather than asserting them.

</purpose>

<routing_rule>

Use this guide for setup, implementation, review, or remediation of a Lynx target.

Do not use it when the target has no `@lynx-js/react` or `@lynx-js/rspeedy` dependency and no `lynx.config.ts`, `lynx.config.js`, or `lynx.config.mjs`; when the request is a copy-only edit that crosses no architecture boundary; or when the user asks for official Lynx defaults only, in which case the hypercore-default rules relax to optional findings.

A router library, a state library, or a native host app inside a Lynx repository is part of the Lynx target, not a second framework.

</routing_rule>

<instruction_contract>

| Field | Contract |
|---|---|
| Intent | Produce a Lynx architecture whose thread split, bundle layers, host contract, and version floor are reviewable and stable as the app grows. |
| Trigger | Lynx or ReactLynx work involving folder structure, `main-thread:` handlers, native modules, host embedding, `engineVersion`, testing, or bundle and runtime performance. |
| Scope | Touched `src/` code, `lynx.config.ts`, `tsconfig.json`, test config, host integration files that the change requires, and the matching rule files. |
| Authority | User and project instructions outrank this guide. Official Lynx documentation controls API facts. Installed package versions and `lynx.config.ts` control project behavior. Hypercore conventions are recommendations until the project adopts them. |
| Evidence | Read the manifest, `lynx.config.ts`, `tsconfig.json`, the entry file, and the touched source and tests. Use the dated snapshot when a version or config key decides the change. |
| Tools | Read, search, edit, and the project's own scripts. Gate package installs, native host changes, device installs, and any build that reaches a host application. |
| Loop | One review or remediation pass, then at most two verify-repair rounds against the gates below. A change stays only when it is inside the touched scope and passes those gates. |
| Output | Korean findings or implementation summary with `official` and `hypercore-default` labels, changed files, verification evidence, and remaining risk. |
| Verification | Type check, tests, and a production build with the project's own commands; a measured performance claim also needs a before/after number. |
| Stop condition | Stop when the stack is confirmed, the applicable gates pass or are reported as blockers, and the evidence is recorded. |

</instruction_contract>

<activation_examples>

Positive:

- `이 Lynx 앱 구조랑 main thread 코드 경계 정리해줘.`
- `Review this ReactLynx app's dual-thread split before we add more screens.`
- `Lynx 번들 크기랑 first screen 성능을 DevTool Trace로 재고 개선해줘.`
- `Audit our Lynx host integration: engineVersion, initData, and native modules.`
- `Rspeedy 프로젝트에 Rstest 테스트 기준을 세워줘.`

Negative:

- `Design a React DOM dashboard with Vite.`
- `Refactor this Expo app's route tree.`

Boundary:

- `Lynx 로그인 버튼 문구만 바꿔줘.` Apply the change and a boundary check only; do not restructure.
- `Use official Lynx defaults only, not the extra hypercore conventions.` The guide still applies, but hypercore-default strictness relaxes.

</activation_examples>

<trigger_conditions>

Activate when the target is a Lynx package or the request names ReactLynx, Rspeedy, `lynx.config.*`, `main-thread:` handlers, `engineVersion`, or Lynx native-host embedding, and the work is setup, implementation, review, or remediation.

Arguments change scope, not the rules.

| Argument | Meaning |
|---|---|
| missing | Review and fix the requested or touched scope. Untouched drift may be reported as backlog. |
| `전체 수정` | Full remediation across the whole detected Lynx app, including every entry, feature folder, and test config. |
| `full fix` / `fix all` | Same as `전체 수정`. |
| `공식 기본만` / `official defaults only` | Downgrade hypercore-default conventions to optional findings unless `전체 수정` was also requested. |

</trigger_conditions>

<skill_architecture>

- Core (`stacks/lynx/core.md`): trigger, contract, gate order, workflow, verification, stop condition.
- Rules: `stacks/lynx/architecture-rules.md` plus the topic files mapped in `reference_routing`.
- References: `references/official/lynx/lynx-2026-11-07.md` holds the dated version, config, and template facts.
- Assets: `assets/evals/lynx-cases.jsonl` holds trigger and behavior cases.
- Setup and performance tracks are separate: `rules/setup/typescript.md` owns the tooling baseline and `rules/lynx/performance.md` owns measured performance work.

</skill_architecture>

<loop_policy>

- One review or remediation pass per request.
- After remediation, at most two verify-repair rounds against the gates in Step 3 and the touched checks. A change stays only when it is inside the touched scope and passes.
- A performance claim follows the measure-change-measure loop in `rules/lynx/performance.md`; it never enters the architecture loop to justify a refactor.

</loop_policy>

<language_and_translation_default>

Write findings, remediation summaries, and validation notes in Korean. Keep identifiers, paths, package names, directives, and the labels `official` and `hypercore-default` in their source form so a report maps one-to-one onto the rule files. `stacks/lynx/core.ko.md` mirrors this file section by section; a rule changed here is changed there in the same edit.

</language_and_translation_default>

<reference_routing>

Read `stacks/lynx/architecture-rules.md` before editing. Then open the one file that owns the touched surface.

| Touched surface | File |
|---|---|
| Entry files, folder ownership, `source.entry`, multi-entry, web target layout, host embedding boundary | `rules/lynx/project-structure.md` |
| `'main thread'` and `'background only'` directives, `main-thread:` bindings, `runOnMainThread`/`runOnBackground`, `useMainThreadRef`, shared modules, what may cross threads | `rules/lynx/threading.md` |
| Elements, CSS and layout differences, events, `<list>`, `initData`/`globalProps`, routing options | `rules/lynx/ui-and-data.md` |
| Native modules, host app integration on iOS and Android and HarmonyOS, `engineVersion` coupling, web target status | `rules/lynx/native-and-platform.md` |
| Rstest/Vitest setup, testing-library, type checking | `rules/lynx/testing.md` |
| Measured performance work: DevTool Trace, IFR, list recycling, lazy bundles, `optimizeBundleSize`, `firstScreenSyncTiming`, cross-thread traffic | `rules/lynx/performance.md` |
| Lint, format, tsconfig, and package-manager baseline for the TypeScript side of the target | `rules/setup/typescript.md` |
| Version, config-key, and template facts behind a rule | `references/official/lynx/lynx-2026-11-07.md` |

The setup track standardizes on oxlint plus Prettier through `rules/setup/typescript.md`. The official Lynx template ships Rslint in its `rslint` variant and no Prettier config at all, so a project that keeps Rslint needs a recorded decision; absent one, follow the setup file.

</reference_routing>

<support_file_read_order>

1. `stacks/lynx/architecture-rules.md` for rule classes and blocking gates.
2. The topic file for the touched surface, in `reference_routing` order.
3. `rules/setup/typescript.md` when tooling is in scope.
4. `references/official/lynx/lynx-2026-11-07.md` when a version, config key, or template fact decides the change.

</support_file_read_order>

<workflow>

| Step | Task | Output |
|---|---|---|
| 1 | Prove the target is a Lynx package and read its versions | Scope decision |
| 2 | Load the rule files for the touched surface | Minimal evidence set |
| 3 | Judge planned changes against the critical gates | Findings with file paths |
| 3.5 | Apply low-risk auto-remediations inside the touched scope | Edits or backlog items |
| 4 | Implement in the order below, then verify | Changed files and evidence |

Step 1 — project validation.

```bash
jq -r '.dependencies, .devDependencies | keys[]?' package.json | grep -E '@lynx-js/(react|rspeedy|types|lynx-ui|web-core)'
ls lynx.config.ts lynx.config.js lynx.config.mjs 2>/dev/null
jq -r '.engines.node? // empty' package.json
grep -n 'engineVersion\|pluginReactLynx\|pluginTypeCheck\|source:' lynx.config.ts
grep -n 'isolatedModules\|jsxImportSource\|noEmit' tsconfig.json src/tsconfig.json
```

If no Lynx signal is present, stop and route back to the normal path instead of forcing Lynx rules.

Step 3 — critical gates. A blocking gate fails even when untouched code shows the same pattern.

1. `engineVersion` in `pluginReactLynx` is at or below the lowest engine version the shipping host actually runs. A bundle that declares a higher version fails fatally with error 10204 on an older host, so the value is a deployment constraint, not a build preference. Confirm the host floor from the host project, not from the default.
2. Every `main-thread:` binding has `'main thread';` as the first statement, only JSON-serializable captures, read-only captures, and no nested main-thread functions.
3. `NativeModules`, `lynx.getJSModule`, `lynx.createSelectorQuery`, `fetch`, timers, and `requestAnimationFrame` never appear in a render body or module top level; they live in effects, event handlers, or `'background only'` functions.
4. Cross-thread calls use `runOnMainThread`/`runOnBackground` and never assume a synchronous return.
5. No `useLayoutEffect` used as a synchronous-after-layout measurement hook.
6. Any virtualized feed is a `<list>` with a fixed viewport, `list-type`, `span-count`, `scroll-orientation`, and `item-key` matching `key`.
7. Type checking is wired through `pluginTypeCheck()`; a green `rspeedy build` proves nothing about types.
8. `isolatedModules: true` and `jsxImportSource: "@lynx-js/react"` are present.
9. `document`, `window`, and DOM or History APIs do not appear in application code.
10. New projects are scaffolded with `@lynx-js/create-lynx`, not the deprecated `create-rspeedy` shim.

Step 3.5 — auto-remediation. Apply directly when local, reversible, and low-risk.

- Move a `NativeModules` or `fetch` call out of a render body into an effect or a `'background only'` function.
- Add the `'main thread';` directive to a handler already bound with `main-thread:`.
- Replace an inline arrow event handler with a function reference, and a closure read with `dataset`.
- Add the required `<list>` attributes and align `item-key` with `key`.
- Add `pluginTypeCheck()` or the missing `isolatedModules`/`jsxImportSource` setting.
- Rename a touched `main-thread:` handler so its name states the interaction it serves.

Do not auto-apply broad migrations: a whole-app thread split, `engineVersion` changes that affect shipped hosts, native host edits, bundle architecture changes, or a lint migration the project has decided against.

Step 4 — implementation order.

1. Confirm detection, versions, and the host engine floor.
2. Fix entry and folder ownership.
3. Fix the thread split and directives.
4. Fix UI, list, and host-data boundaries.
5. Fix native module and host integration boundaries.
6. Fix type checking and tests.
7. Measure and change performance last, one lever at a time.

</workflow>

<required>

- A proven Lynx target, with the `@lynx-js/react`, `@lynx-js/rspeedy`, and host engine versions named from installed evidence.
- One `root.render` call site at the entry, with feature code outside it.
- An explicit thread split for every touched handler, effect, and native call.
- An `engineVersion` justified by the lowest shipping host version.
- Type checking and at least one render-plus-event test for touched screens.
- A report labeling each finding `official` or `hypercore-default`, with unverified topics named as unverified.

</required>

<forbidden>

- Applying Lynx rules to a target with no `@lynx-js/react`, `@lynx-js/rspeedy`, or `lynx.config.*` signal.
- Raising `engineVersion` to unlock a CSS or API feature without checking the shipped host floor; the failure is a fatal 10204 on the device, not a build error.
- Treating the `'3.2'` default as a target version.
- Calling native modules, `fetch`, or the selector query API from a render body.
- Using `document`, `window`, `<Link>`, or the History API in application code.
- Claiming a performance gain without a production-build before/after measurement.
- Presenting the hypercore-default folder layout, native-wrapper boundary, or lint baseline as official Lynx behavior.
- Scaffolding a new project with the deprecated `create-rspeedy` package.

</forbidden>

<validation>

- [ ] Stack detection confirmed from `package.json` and `lynx.config.*`.
- [ ] Engine, `@lynx-js/react`, `@lynx-js/rspeedy`, and Node versions read from installed evidence.
- [ ] `engineVersion` matches the lowest shipping host version and the 10204 risk is recorded.
- [ ] Entry file is the only `root.render` call site and feature code lives outside it.
- [ ] Every touched handler and native call has an explicit thread and a directive where required.
- [ ] `main-thread:` captures are JSON-serializable and read-only.
- [ ] UI and list rules checked for touched screens.
- [ ] Native module calls sit behind one adapter and the background-thread rule holds.
- [ ] `pluginTypeCheck()` and `isolatedModules` are configured; type check passes.
- [ ] Touched screens have a render and an event test.
- [ ] Performance work names its measurement and records before and after numbers.
- [ ] Findings are labeled `official` or `hypercore-default`, and unverified topics are named as such.

</validation>

## Sources

> Checked 2026-11-07. These statements restate the package's dated snapshot, `references/official/lynx/lynx-2026-11-07.md`, which cites the Lynx documentation, the `@lynx-js/create-lynx` 0.2.1 template tarball, and npm registry metadata read on 2026-11-07.

| Claim | Source |
|---|---|
| Dual-thread runtime, directives, `main-thread:` bindings, and the background-only API set | https://lynxjs.org/guide/scripting-runtime/main-thread-runtime.md, https://lynxjs.org/react/thinking-in-reactlynx.md, https://lynxjs.org/api/react/Document.directives.md, https://lynxjs.org/react/main-thread-script.md |
| `engineVersion` default `'3.2'` and the fatal 10204 outcome on an older host | https://lynxjs.org/guide/compatibility.md, https://lynxjs.org/rspeedy/plugin.md |
| `pluginTypeCheck()`, `isolatedModules`, and the JSX import source | https://lynxjs.org/rspeedy/typescript.md |
| Template file set, entry file, and the deprecated `create-rspeedy` shim | https://registry.npmjs.org/@lynx-js%2Fcreate-lynx/-/create-lynx-0.2.1.tgz, https://registry.npmjs.org/create-rspeedy |
| `<list>` attributes and the fixed-viewport requirement | https://lynxjs.org/api/elements/built-in/list.md |
| Folder layout, native-wrapper boundary, and lint baseline | this package's convention, not an official Lynx requirement |
