Stack guide inside `hyper-architecture` for Expo. Read it when `rules/stack-detection.md` routes a target to Expo; from then on this file owns that target's work.

- Scope: Use this skill when creating, reviewing, or refactoring scalable Android and iOS app architecture with React Native, Expo, Expo Router, and TypeScript, including project structure, routing, feature boundaries, native configuration, data/state, platform code, and validation. Do not use for bare React Native projects without Expo, web-only React apps, or docs-only summaries.
- Runtime needs: Requires an Expo project or an explicit request to create one; current API claims may require official Expo and React Native documentation plus local package inspection.

@architecture-rules.md
@../../rules/expo/project-structure.md
@../../rules/expo/routing-and-navigation.md
@../../rules/expo/data-state-and-boundaries.md
@../../rules/expo/native-platform-and-security.md
@../../references/official/expo/expo-react-native-2026-11-04.md
@../../rules/expo/testing-and-validation.md

# Expo Architecture

> Create and enforce scalable React Native + Expo + TypeScript architecture for Android and iOS while separating official framework behavior from Hypercore conventions.

<output_language>

Default user-facing deliverables, reports, plans, handoff notes, and validation notes to Korean. Preserve code identifiers, commands, paths, schema keys, package names, API names, and source excerpts in their required language.

</output_language>

<purpose>

- Bootstrap or refactor Expo applications around Expo Router, strict TypeScript, feature boundaries, and explicit native-platform seams.
- Keep route files thin and organize growing product code by domain/feature rather than by one global technical bucket.
- Protect secrets, permissions, native configuration, storage, and Android/iOS divergence with explicit gates.
- Validate architecture against the installed Expo SDK and project evidence before applying current official guidance.

</purpose>

<routing_rule>

Use this skill for architecture setup, implementation, review, or remediation in Expo-managed or Expo prebuild projects targeting Android and iOS.

Do not use it for bare React Native without Expo, generic web React, a single visual component with no architecture impact, deployment-only work, or documentation-only summaries. For brownfield apps, preserve working project conventions unless the user requests migration or a safety/correctness issue requires change.

</routing_rule>

<instruction_contract>

| Field | Contract |
|---|---|
| Intent | Produce a scalable, testable Expo architecture whose route, feature, data, native, and platform boundaries remain understandable as the app grows. |
| Trigger | Expo/React Native/TypeScript work involving app setup, folder structure, Expo Router, state/data flow, native configuration, platform divergence, testing, or architecture review. |
| Scope | Touched app configuration, TypeScript source, route tree, feature/shared modules, tests, and architecture validation notes; broad native regeneration and dependency replacement require explicit scope. |
| Authority | User and project instructions outrank this skill. Installed package/config evidence controls project behavior. Official Expo/React Native docs control API facts; Hypercore conventions are recommendations unless adopted by the project. |
| Evidence | Inspect `package.json`, app config, router entry, TypeScript/Metro/Babel config, native directories, existing source/tests, and lockfile first. Use dated official references when version drift matters. |
| Tools | Use capability-based inspect/read/search/edit/execute. Validate commands and paths. Gate network installs, credentials, EAS operations, any `prebuild` run on committed native directories, signing, publication, deployment, and production effects. |
| Loop | Use a bounded verify-repair loop: run relevant checks, repair only observed failures, and stop after two repair passes. Keep changes only when critical type, route, native-config, and safety guards pass. |
| Output | A project-local architecture implementation or review, plus a concise Korean report of decisions, changed files, checks, source/version caveats, and residual risks. |
| Verification | Run project-defined format/lint/type/test checks plus Expo diagnostics and platform checks relevant to touched surfaces; inspect resolved config and route behavior when changed. |
| Stop condition | Finish when project mode and SDK are identified, applicable critical gates pass, changes are verified, and residual risk is recorded; block on missing authority, unsafe native effects, unresolved package incompatibility, or unavailable required verification. |

</instruction_contract>

<activation_examples>

Positive:
- "React Native + Expo + TypeScript로 iOS/Android 앱 구조를 확장 가능하게 세팅해줘."
- "Expo Router 앱의 routes, features, API, state 경계를 리팩터링해줘."
- "Audit this Expo app for scalable architecture and platform-boundary violations."
- "EAS 환경과 iOS/Android 설정까지 고려해서 Expo 프로젝트 구조를 잡아줘."

Negative:
- "Bare React Native CLI 앱의 native module architecture를 설계해줘."
- "이 React 웹 컴포넌트의 CSS만 고쳐줘."
- "Expo 문서를 요약만 해줘."

Boundary:
- "Expo 로그인 화면의 문구 하나만 바꿔줘." Apply only a quick boundary check; do not force architecture churn.
- "Expo 앱을 스토어에 배포해줘." Use this skill only for architecture/config review; deployment authorization and execution belong to the deployment workflow.

</activation_examples>

<trigger_conditions>

Activate when the request names an Expo or React Native app, Expo Router, the app folder or a route boundary, native configuration, platform-specific code, or the layout of app data and state, and the work is setup, implementation, review, or remediation.

Activate also when a shipped or growing Expo project needs its structure, routing, imports, or platform seams changed, including review requests that end in a change set.

The project test runs before the request test. When local files show neither Expo nor Expo prebuild and the user did not ask to create an Expo app, do not route here. The remaining exclusions are in `<routing_rule>`.

</trigger_conditions>

<skill_architecture>

| Part | Role | Load condition |
|---|---|---|
| `stacks/expo/core.md` | Trigger, contract, workflow, gates, validation | Always |
| `stacks/expo/architecture-rules.md` | Rule classes and blocking gates | Before classifying a finding |
| `rules/expo/project-structure.md` | Folders, ownership, imports, migration, scale profiles | When changing folders or imports |
| `rules/expo/routing-and-navigation.md` | Expo Router layouts, groups, params, protected screens, route thinness | When changing routes |
| `rules/expo/data-state-and-boundaries.md` | Server and client state, DTOs, transport, persistence, dependency direction | When changing data flow |
| `rules/expo/native-platform-and-security.md` | App config, permissions, secrets, storage, native toolchain, EAS, native code | When touching config or platform code |
| `rules/expo/testing-and-validation.md` | Check order and completion evidence | Before claiming completion |
| `references/official/expo/expo-react-native-2026-11-04.md` | Dated official SDK and API facts, per-SDK baseline, removed APIs | When a current SDK claim decides the change |

</skill_architecture>

<loop_policy>

One bounded loop per change set: run the checks, read the failures, repair only what failed, and re-run. One round is one repair and its re-run, and the loop ends after two rounds. A change stays only when the critical type, route, native-config, and safety gates pass; otherwise the loop ends with the failing check named and nothing claimed as verified. There is no loop that keeps refactoring until the structure feels right and no self-scoring loop. Evidence is the recorded command output and the resolved config, not a restatement of the plan.

</loop_policy>

<language_and_translation_default>

Deliver user-facing text in Korean by default: the report, decisions, caveats, and residual risks. Keep code identifiers, commands, paths, package and API names, and quoted source lines in their original form. This package is maintained as English/Korean pairs (`X.md` ↔ `X.ko.md`); read one language version per run and update both when a rule changes.

</language_and_translation_default>

<reference_routing>

- Before classifying any finding or enforcing a rule, read `stacks/expo/architecture-rules.md`.
- When changing folders, imports, module ownership, or migration order, read `rules/expo/project-structure.md`.
- When changing the route tree, layouts, groups, or params, read `rules/expo/routing-and-navigation.md`.
- When changing server state, client state, persistence, or the direction of a dependency, read `rules/expo/data-state-and-boundaries.md`.
- When touching app config, permissions, secrets, storage, native code, or platform files, read `rules/expo/native-platform-and-security.md`.
- When the request names jank, slow startup, list scroll cost, memory, app size, bundle size, or "최적화", read `rules/expo/performance.md`.
- When the work involves lint, format, type-check, tsconfig, package manager pinning, or the CI check order, read `rules/setup/typescript.md`.
- Before claiming completion, read `rules/expo/testing-and-validation.md`.
- When the installed SDK or an official API behavior decides the change, read `references/official/expo/expo-react-native-2026-11-04.md` and compare its `last_verified_at` with the installed version.

</reference_routing>

<support_file_read_order>

Read one language version per run, in this order. Paths are relative to this skill directory.

1. Read `stacks/expo/architecture-rules.md` for rule classes and blocking gates.
2. Read the rule files for the topics the change touches, choosing them with `<reference_routing>`.
3. Read `references/official/expo/expo-react-native-2026-11-04.md` only when current SDK/API behavior affects a decision.
4. Read `rules/expo/testing-and-validation.md` before implementation completion.

</support_file_read_order>

<workflow>

| Phase | Task | Output |
|---|---|---|
| 0 | Confirm the project facts from local files: Expo SDK, React Native, Router, TypeScript, package manager, workspace mode, managed/CNG versus committed `ios/` and `android/`, route root (`src/app` or `app`), aliases, project commands, `web.output` and whether API routes exist, and whether the request needs installs, `prebuild`, EAS, credentials, signing, or store effects | Scope decision |
| 1 | Inventory routes, features, shared modules, state/data, native config, tests, and dependency direction | Architecture map |
| 2 | Classify findings as Official, Safety, or Hypercore convention | Prioritized plan |
| 3 | Define target boundaries and the smallest migration slice; preserve user work | Change set |
| 4 | Implement safe reversible changes and update affected callsites/tests/config | Integrated architecture |
| 5 | Run focused then project-level checks and inspect resolved behavior | Verification evidence |
| 6 | Report decisions, versions/sources, results, and residual risks in Korean | Handoff |

</workflow>

<required>

- Prefer `src/app` for routes and keep non-route code outside it: the SDK 55+ default template ships `src/app`, `src/components`, `src/constants`, and `src/hooks`, and `src/app` outranks a root `app` when both exist.
- Organize growth by `src/features/<domain>` and narrowly scoped `src/shared/*`; avoid dumping domain behavior into global `components`, `hooks`, `utils`, or `services` buckets.
- Keep route files composition-oriented; business rules/expo and reusable data access belong to feature/application layers.
- Keep TypeScript strict, validate untrusted runtime data at boundaries, and avoid `any` and unchecked casts. On React Native 0.88 the Strict TypeScript API is the default: no `react-native/Libraries/*` deep imports and no `*Properties` type aliases.
- Separate server state, client UI state, form state, and persisted device state by ownership and lifecycle.
- Treat `EXPO_PUBLIC_*` as public; store small secrets only in secure platform-backed storage and never bundle server secrets.
- Make platform divergence explicit with `.ios.ts(x)` / `.android.ts(x)` or a small adapter when behavior truly differs.
- Use the installed SDK and `expo install` compatibility rather than guessing package versions; from SDK 55 every Expo package shares the SDK major, so `expo-camera@^58` on SDK 58 is expected.
- Recommend removing manual `useMemo`/`useCallback`/`React.memo` only when `experiments.reactCompiler` is enabled and the file is in its scope.

</required>

<forbidden>

- Inventing project commands, packages, native capabilities, API contracts, or environment variables.
- A universal folder template applied without inspecting project scale and existing conventions.
- Domain features importing route files, UI importing infrastructure internals, or broad barrel files that create cycles.
- Secrets in source, app config `extra`, `EXPO_PUBLIC_*`, logs, AsyncStorage, or client bundles.
- Running package installs, EAS builds/updates/submits, signing, or store publication without explicit authorization.
- Running `prebuild` on committed `ios/`/`android/` directories without explicit authorization. Bare `prebuild` clears and regenerates both directories since SDK 57, so the preserving path is `--no-clean` plus a diff review.
- Treating Expo Go success as proof that development/standalone builds, permissions, config plugins, or native modules work. Expo Go also requires a signed-in Expo account in both the CLI and the app, and only one SDK version is supported from the stores, so name the SDK it targets before citing a run as evidence.
- Adopting an experimental path as the default supported setup: Swift Package Manager (`npx react-native spm`), `experiments.noxcturnalTransformWorker`, or `expo-location/next`.
- Unbounded refactoring or migration without a verified incremental boundary.

</forbidden>

<validation>

- [ ] Expo mode, SDK, React Native, Router, package manager, platforms, and native-directory ownership are identified.
- [ ] The SDK generation is named against the dated reference baseline (SDK 58: react-native 0.88, react 19.3, expo-router 58) rather than a remembered version.
- [ ] No removed API from the reference's removed-API table is introduced or left untouched in reviewed code.
- [ ] At least 3 positive, 2 negative, and 1 boundary trigger examples remain present.
- [ ] Route files are thin and non-route modules do not live under `app`/`src/app`.
- [ ] Dependency direction and feature/shared ownership are explicit; cycles and unsafe barrels are absent.
- [ ] Route access control uses the navigator's protected-screen API and is not the only authorization.
- [ ] Runtime inputs, environment, persistence, permissions, and secure storage follow boundary rules.
- [ ] `web.output`, API routes, and `asyncRoutes` are consistent with the app's actual hosting model.
- [ ] Android/iOS changes are checked independently where behavior or config differs.
- [ ] Relevant typecheck, lint, tests, Expo diagnostics, resolved config, and build checks ran or are explicitly reported as unavailable.
- [ ] English/Korean skill files retain equivalent trigger, authority, workflow, safety, and completion semantics.
- [ ] Current official claims cite the dated reference; source dates are not in the future.
- [ ] Completion records `Claim -> Risk -> Evidence -> Verification -> Result -> Caveat` and decides ship, iterate, caveated ship, or block.

</validation>
