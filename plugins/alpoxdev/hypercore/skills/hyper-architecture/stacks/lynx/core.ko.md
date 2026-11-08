`hyper-architecture` 안의 Lynx stack guide입니다. `rules/stack-detection.md`가 target을 Lynx로 routing하면 이 파일을 읽고, 그때부터 이 파일이 해당 target의 작업을 소유합니다.

- Scope: ReactLynx로 rendering하고 Lynx dual-thread engine 위에서 Rspeedy로 build하는 Lynx application을 만들거나, 감사하거나, 재구성하거나, 검토할 때 사용합니다. folder 구조, main thread/background 분리, element와 CSS, host data, native module, host app embedding, engine version compatibility, test, 성능이 대상입니다. React DOM app, React Native나 Expo app, 또는 `react` dependency만 있고 `@lynx-js/react`가 없는 repository에는 사용하지 않습니다.
- Runtime needs: target의 `package.json`, `lynx.config.*`, `tsconfig.json`, 그리고 repository에 있다면 native host project가 필요합니다. 현재 version 주장에는 `references/official/lynx/lynx-2026-11-07.md`의 날짜가 있는 snapshot이 필요할 수 있고, 측정한 성능 주장에는 device나 Lynx DevTool session이 필요합니다.

@architecture-rules.md
@../../rules/lynx/project-structure.md
@../../rules/lynx/threading.md
@../../rules/lynx/ui-and-data.md
@../../rules/lynx/native-and-platform.md
@../../rules/lynx/testing.md
@../../rules/lynx/performance.md
@../../references/official/lynx/lynx-2026-11-07.md

# Lynx Architecture

> code를 바꾸기 전에 dual-thread 경계, bundle layer, host 계약, engine version 하한이 명시된 ReactLynx architecture를 강제합니다.

<output_language>

사용자에게 보이는 산출물, 보고, 계획, handoff note, validation note는 기본으로 한국어로 작성합니다. code identifier, command, path, package name, API name, `'main thread'` 같은 directive, source 발췌는 필요한 형태 그대로 유지합니다.

</output_language>

<purpose>

- 두 실행 thread와 각 thread에서 허용되는 API, 둘 사이의 경계를 touched file마다 명시합니다.
- main-thread bundle을 기능이 허용하는 만큼 first-frame critical path에서 작게 유지합니다.
- native host를 계약 상대로 다룹니다. `engineVersion`, `initData`, `globalProps`, native module은 다른 interface와 같은 기준으로 검토합니다.
- 공식 Lynx 동작과 이 package의 관례를 구분하고, 확인하지 못한 topic은 단정하지 않고 미확인으로 표시합니다.

</purpose>

<routing_rule>

Lynx target의 setup, 구현, 검토, 교정에 이 guide를 사용합니다.

target에 `@lynx-js/react`나 `@lynx-js/rspeedy` dependency가 없고 `lynx.config.ts`, `lynx.config.js`, `lynx.config.mjs`도 없으면 사용하지 않습니다. architecture 경계를 넘지 않는 copy-only 수정이나, 사용자가 공식 Lynx 기본값만 원한다고 밝힌 경우에도 사용하지 않습니다. 후자에서는 hypercore-default 규칙이 선택 finding으로 완화됩니다.

Lynx repository 안의 router library, state library, native host app은 Lynx target의 일부이며 두 번째 framework가 아닙니다.

</routing_rule>

<instruction_contract>

| Field | Contract |
|---|---|
| Intent | thread 분리, bundle layer, host 계약, version 하한을 검토 가능하게 유지하고 app이 커져도 안정적인 Lynx architecture를 만듭니다. |
| Trigger | folder 구조, `main-thread:` handler, native module, host embedding, `engineVersion`, test, bundle과 runtime 성능을 다루는 Lynx/ReactLynx 작업. |
| Scope | touched `src/` code, `lynx.config.ts`, `tsconfig.json`, test config, 변경에 필요한 host integration file, 그리고 대응 rule file. |
| Authority | 사용자와 project 지시가 이 guide보다 우선합니다. 공식 Lynx 문서가 API 사실을 정합니다. 설치된 package version과 `lynx.config.ts`가 project 동작을 정합니다. Hypercore 관례는 project가 채택하기 전까지 권고입니다. |
| Evidence | manifest, `lynx.config.ts`, `tsconfig.json`, entry file, touched source와 test를 읽습니다. version이나 config key가 결정을 좌우하면 날짜가 있는 snapshot을 사용합니다. |
| Tools | 읽기, 검색, 편집, project 자체 script. package install, native host 변경, device install, host application에 닿는 build는 gate합니다. |
| Loop | 검토 또는 교정 1회, 그 뒤 아래 gate에 대한 verify-repair를 최대 2회. 변경은 touched scope 안이고 해당 gate를 통과할 때만 유지합니다. |
| Output | `official`과 `hypercore-default` label이 붙은 한국어 finding 또는 구현 요약, 변경 file, 검증 증거, 남은 위험. |
| Verification | project 자체 command로 type check, test, production build. 성능 주장에는 before/after 수치가 추가로 필요합니다. |
| Stop condition | stack을 확인했고 적용 가능한 gate가 통과했거나 blocker로 보고됐으며 증거를 기록했을 때 멈춥니다. |

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

- `Lynx 로그인 버튼 문구만 바꿔줘.` 변경과 boundary 확인만 적용하고 재구성하지 않습니다.
- `Use official Lynx defaults only, not the extra hypercore conventions.` guide는 그대로 적용하되 hypercore-default 엄격도는 완화됩니다.

</activation_examples>

<trigger_conditions>

target이 Lynx package이거나, 요청이 ReactLynx, Rspeedy, `lynx.config.*`, `main-thread:` handler, `engineVersion`, Lynx native host embedding을 지목하고, 작업이 setup, 구현, 검토, 교정일 때 활성화합니다.

argument는 규칙이 아니라 범위를 바꿉니다.

| Argument | Meaning |
|---|---|
| missing | 요청받았거나 touched인 범위를 검토하고 고칩니다. 건드리지 않은 drift는 backlog로 보고할 수 있습니다. |
| `전체 수정` | 감지된 Lynx app 전체에 대해 모든 entry, feature folder, test config를 포함해 전면 교정합니다. |
| `full fix` / `fix all` | `전체 수정`과 같습니다. |
| `공식 기본만` / `official defaults only` | `전체 수정`을 함께 요청하지 않았다면 hypercore-default 관례를 선택 finding으로 낮춥니다. |

</trigger_conditions>

<skill_architecture>

- Core (`stacks/lynx/core.md`): trigger, 계약, gate 순서, workflow, 검증, stop condition.
- Rules: `stacks/lynx/architecture-rules.md`와 `reference_routing`이 연결하는 topic file.
- References: `references/official/lynx/lynx-2026-11-07.md`가 날짜가 있는 version, config, template 사실을 담습니다.
- Assets: `assets/evals/lynx-cases.jsonl`이 trigger와 동작 case를 담습니다.
- Setup과 performance는 별도 track입니다. `rules/setup/typescript.md`가 tooling 기준선을, `rules/lynx/performance.md`가 측정 기반 성능 작업을 소유합니다.

</skill_architecture>

<loop_policy>

- 요청당 검토 또는 교정은 1회입니다.
- 교정 후 Step 3의 gate와 touched check에 대해 verify-repair를 최대 2회 수행합니다. 변경은 touched scope 안이고 통과할 때만 유지합니다.
- 성능 주장은 `rules/lynx/performance.md`의 measure-change-measure loop를 따르며, refactor를 정당화하려고 architecture loop에 들어오지 않습니다.

</loop_policy>

<language_and_translation_default>

finding, 교정 요약, validation note는 한국어로 작성합니다. identifier, path, package name, directive, `official`과 `hypercore-default` label은 원형 그대로 유지해 보고가 rule file과 1:1로 대응하게 합니다. `stacks/lynx/core.ko.md`는 이 파일을 section 단위로 mirror하며, 여기서 규칙을 바꾸면 같은 편집에서 그쪽도 바꿉니다.

</language_and_translation_default>

<reference_routing>

편집 전에 `stacks/lynx/architecture-rules.md`를 읽습니다. 그다음 touched surface를 소유한 file 하나를 엽니다.

| Touched surface | File |
|---|---|
| Entry file, folder 소유권, `source.entry`, multi-entry, web target 배치, host embedding 경계 | `rules/lynx/project-structure.md` |
| `'main thread'`와 `'background only'` directive, `main-thread:` binding, `runOnMainThread`/`runOnBackground`, `useMainThreadRef`, shared module, thread 사이를 넘는 값 | `rules/lynx/threading.md` |
| Element, CSS와 layout 차이, event, `<list>`, `initData`/`globalProps`, 검증된 routing 선택지 | `rules/lynx/ui-and-data.md` |
| Native module, iOS와 Android와 HarmonyOS host app integration, `engineVersion` 결합, web target 상태 | `rules/lynx/native-and-platform.md` |
| Rstest/Vitest 설정, testing-library, type checking | `rules/lynx/testing.md` |
| 측정 기반 성능 작업: DevTool Trace, IFR, list recycling, lazy bundle, `optimizeBundleSize`, `firstScreenSyncTiming`, cross-thread traffic | `rules/lynx/performance.md` |
| Target의 TypeScript 쪽 lint, format, tsconfig, package manager 기준선 | `rules/setup/typescript.md` |
| 규칙 뒤의 version, config key, template 사실 | `references/official/lynx/lynx-2026-11-07.md` |

setup track은 `rules/setup/typescript.md`를 통해 oxlint와 Prettier를 표준으로 삼습니다. 공식 Lynx template은 `rslint` variant에서 Rslint를 제공하고 Prettier config는 전혀 두지 않으므로, Rslint를 유지하는 project는 그 결정을 기록해야 합니다. 기록이 없으면 setup file을 따릅니다.

</reference_routing>

<support_file_read_order>

1. `stacks/lynx/architecture-rules.md`로 규칙 분류와 blocking gate를 확인합니다.
2. `reference_routing` 순서로 touched surface의 topic file을 읽습니다.
3. tooling이 범위에 있으면 `rules/setup/typescript.md`를 읽습니다.
4. version, config key, template 사실이 결정을 좌우하면 `references/official/lynx/lynx-2026-11-07.md`를 읽습니다.

</support_file_read_order>

<workflow>

| Step | Task | Output |
|---|---|---|
| 1 | target이 Lynx package임을 확인하고 version을 읽습니다 | Scope 결정 |
| 2 | touched surface의 rule file을 읽습니다 | 최소 증거 집합 |
| 3 | 계획한 변경을 critical gate에 대조합니다 | file path가 붙은 finding |
| 3.5 | touched scope 안에서 위험이 낮은 자동 교정을 적용합니다 | 편집 또는 backlog item |
| 4 | 아래 순서로 구현하고 검증합니다 | 변경 file과 증거 |

Step 1 — project 확인.

```bash
jq -r '.dependencies, .devDependencies | keys[]?' package.json | grep -E '@lynx-js/(react|rspeedy|types|lynx-ui|web-core)'
ls lynx.config.ts lynx.config.js lynx.config.mjs 2>/dev/null
jq -r '.engines.node? // empty' package.json
grep -n 'engineVersion\|pluginReactLynx\|pluginTypeCheck\|source:' lynx.config.ts
grep -n 'isolatedModules\|jsxImportSource\|noEmit' tsconfig.json src/tsconfig.json
```

Lynx 신호가 없으면 Lynx 규칙을 강제하지 말고 정상 경로로 되돌립니다.

Step 3 — critical gate. 건드리지 않은 code에 같은 pattern이 있어도 blocking gate는 실패입니다.

1. `pluginReactLynx`의 `engineVersion`이 실제 출시 host가 실행하는 가장 낮은 engine version 이하입니다. 더 높은 version을 선언한 bundle은 구형 host에서 fatal error 10204로 실패하므로, 이 값은 build 취향이 아니라 배포 제약입니다. 하한은 default가 아니라 host project에서 확인합니다.
2. 모든 `main-thread:` binding에 `'main thread';`가 첫 statement로 있고, capture는 JSON-serializable이며 read-only이고, main-thread function이 중첩되지 않습니다.
3. `NativeModules`, `lynx.getJSModule`, `lynx.createSelectorQuery`, `fetch`, timer, `requestAnimationFrame`이 render body나 module top level에 나타나지 않습니다. effect, event handler, `'background only'` function에 둡니다.
4. Cross-thread 호출은 `runOnMainThread`/`runOnBackground`를 쓰고 동기 반환을 가정하지 않습니다.
5. `useLayoutEffect`를 layout 이후 동기 측정 hook으로 쓰지 않습니다.
6. virtualized feed는 고정 viewport, `list-type`, `span-count`, `scroll-orientation`, `key`와 일치하는 `item-key`를 갖춘 `<list>`입니다.
7. Type checking이 `pluginTypeCheck()`로 연결되어 있습니다. `rspeedy build`가 통과해도 type에 대한 증거는 아닙니다.
8. `isolatedModules: true`와 `jsxImportSource: "@lynx-js/react"`가 있습니다.
9. application code에 `document`, `window`, DOM, History API가 나타나지 않습니다.
10. 새 project는 deprecated `create-rspeedy` shim이 아니라 `@lynx-js/create-lynx`로 scaffold합니다.

Step 3.5 — 자동 교정. 국소적이고 되돌릴 수 있으며 위험이 낮으면 바로 적용합니다.

- render body의 `NativeModules`나 `fetch` 호출을 effect 또는 `'background only'` function으로 옮깁니다.
- 이미 `main-thread:`로 binding된 handler에 `'main thread';` directive를 추가합니다.
- inline arrow event handler를 function reference로 바꾸고, closure로 읽던 값을 `dataset`으로 옮깁니다.
- `<list>`의 필수 attribute를 채우고 `item-key`를 `key`에 맞춥니다.
- `pluginTypeCheck()` 또는 빠진 `isolatedModules`/`jsxImportSource` 설정을 추가합니다.
- touched `main-thread:` handler 이름을 그 handler가 맡은 상호작용이 드러나게 바꿉니다.

전면 migration은 자동 적용하지 않습니다. app 전체 thread 분리, 출시 host에 영향을 주는 `engineVersion` 변경, native host 편집, bundle 구조 변경, project가 유지하기로 결정한 lint migration이 해당합니다.

Step 4 — 구현 순서.

1. 감지, version, host engine 하한을 확인합니다.
2. Entry와 folder 소유권을 정리합니다.
3. Thread 분리와 directive를 정리합니다.
4. UI, list, host data 경계를 정리합니다.
5. Native module과 host integration 경계를 정리합니다.
6. Type checking과 test를 정리합니다.
7. 성능은 마지막에 lever 하나씩 측정하며 바꿉니다.

</workflow>

<required>

- 증명된 Lynx target과, 설치 증거로 밝힌 `@lynx-js/react`, `@lynx-js/rspeedy`, host engine version.
- Entry에 `root.render` 호출 지점이 하나이고 feature code가 그 밖에 있습니다.
- touched handler, effect, native call마다 명시된 thread.
- 출시 host의 최저 version으로 정당화된 `engineVersion`.
- Type checking과 touched 화면당 최소 하나의 render + event test.
- finding마다 `official` 또는 `hypercore-default` label, 미확인 topic은 미확인으로 명시한 보고.

</required>

<forbidden>

- `@lynx-js/react`, `@lynx-js/rspeedy`, `lynx.config.*` 신호가 없는 target에 Lynx 규칙을 적용하는 것.
- 출시 host 하한을 확인하지 않고 CSS나 API 기능을 쓰려고 `engineVersion`을 올리는 것. 실패는 build error가 아니라 device에서의 fatal 10204입니다.
- `'3.2'` default를 target version으로 취급하는 것.
- Render body에서 native module, `fetch`, selector query API를 호출하는 것.
- Application code에서 `document`, `window`, `<Link>`, History API를 쓰는 것.
- Production build before/after 측정 없이 성능 개선을 주장하는 것.
- hypercore-default folder 배치, native wrapper 경계, lint 기준선을 공식 Lynx 동작으로 제시하는 것.
- 새 project를 deprecated `create-rspeedy` package로 scaffold하는 것.

</forbidden>

<validation>

- [ ] `package.json`과 `lynx.config.*`로 stack 감지를 확인했습니다.
- [ ] Engine, `@lynx-js/react`, `@lynx-js/rspeedy`, Node version을 설치 증거에서 읽었습니다.
- [ ] `engineVersion`이 출시 host 최저 version과 일치하고 10204 위험을 기록했습니다.
- [ ] Entry file이 유일한 `root.render` 지점이고 feature code가 그 밖에 있습니다.
- [ ] touched handler와 native call마다 thread가 명시됐고 필요한 곳에 directive가 있습니다.
- [ ] `main-thread:` capture가 JSON-serializable이고 read-only입니다.
- [ ] touched 화면의 UI와 list 규칙을 확인했습니다.
- [ ] Native module 호출이 하나의 adapter 뒤에 있고 background-thread 규칙을 지킵니다.
- [ ] `pluginTypeCheck()`와 `isolatedModules`가 설정됐고 type check가 통과합니다.
- [ ] touched 화면에 render test와 event test가 있습니다.
- [ ] 성능 작업이 측정을 명시하고 before/after 수치를 기록했습니다.
- [ ] finding에 `official` 또는 `hypercore-default` label이 있고 미확인 topic은 그렇게 표시했습니다.

</validation>

## Sources

> 확인 2026-11-07. 이 서술은 이 패키지의 날짜가 있는 snapshot `references/official/lynx/lynx-2026-11-07.md`를 재진술한 것이며, 그 파일이 2026-11-07에 읽은 Lynx 문서, `@lynx-js/create-lynx` 0.2.1 template tarball, npm registry metadata를 인용합니다.

| Claim | Source |
|---|---|
| Dual-thread runtime, directive, `main-thread:` binding, background-only API 집합 | https://lynxjs.org/guide/scripting-runtime/main-thread-runtime.md, https://lynxjs.org/react/thinking-in-reactlynx.md, https://lynxjs.org/api/react/Document.directives.md, https://lynxjs.org/react/main-thread-script.md |
| `engineVersion` default `'3.2'`와 구형 host에서의 fatal 10204 | https://lynxjs.org/guide/compatibility.md, https://lynxjs.org/rspeedy/plugin.md |
| `pluginTypeCheck()`, `isolatedModules`, JSX import source | https://lynxjs.org/rspeedy/typescript.md |
| Template file 집합, entry file, deprecated `create-rspeedy` shim | https://registry.npmjs.org/@lynx-js%2Fcreate-lynx/-/create-lynx-0.2.1.tgz, https://registry.npmjs.org/create-rspeedy |
| `<list>` attribute와 고정 viewport 요구 | https://lynxjs.org/api/elements/built-in/list.md |
| Folder 배치, native wrapper 경계, lint 기준선 | 공식 Lynx 요구가 아니라 이 패키지의 관례 |
