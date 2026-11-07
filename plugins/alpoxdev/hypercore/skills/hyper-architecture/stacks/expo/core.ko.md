`hyper-architecture`의 Expo 스택 가이드입니다. `rules/stack-detection.ko.md`가 대상을 Expo로 라우팅하면 이 파일을 읽고, 이 파일이 그 대상의 작업을 맡습니다.

- 범위: React Native, Expo, Expo Router, TypeScript로 확장 가능한 Android/iOS 앱 architecture를 생성·검토·refactor할 때 사용합니다. project structure, routing, feature boundary, native config, data/state, platform code, validation을 포함합니다. Expo 없는 bare React Native, web-only React, 문서 요약에는 사용하지 않습니다.
- 실행 조건: Expo 프로젝트 또는 Expo 프로젝트 생성 요청이 필요하며, 최신 API 주장은 공식 Expo/React Native 문서와 로컬 package 확인이 필요할 수 있습니다.

@architecture-rules.ko.md
@../../rules/expo/project-structure.ko.md
@../../rules/expo/routing-and-navigation.ko.md
@../../rules/expo/data-state-and-boundaries.ko.md
@../../rules/expo/native-platform-and-security.ko.md
@../../references/official/expo/expo-react-native-2026-11-04.ko.md
@../../rules/expo/testing-and-validation.ko.md

# Expo Architecture

> 공식 framework 동작과 Hypercore convention을 구분하면서 Android/iOS용 React Native + Expo + TypeScript architecture를 생성하고 강제합니다.

<output_language>

사용자-facing 산출물, 보고서, 계획, handoff note, validation note는 기본적으로 한국어로 작성합니다. code identifier, command, path, schema key, package/API 이름, 인용문은 필요한 원문 언어를 유지합니다.

</output_language>

<purpose>

- Expo Router, strict TypeScript, feature boundary, 명시적 native-platform seam을 중심으로 Expo 앱을 bootstrap하거나 refactor합니다.
- route file을 얇게 유지하고 성장하는 제품 코드를 하나의 전역 기술 bucket이 아니라 domain/feature별로 구성합니다.
- secret, permission, native config, storage, Android/iOS 차이를 명시적 gate로 보호합니다.
- 최신 공식 지침을 적용하기 전에 설치된 Expo SDK와 프로젝트 근거로 architecture를 검증합니다.

</purpose>

<routing_rule>

Android/iOS를 대상으로 하는 Expo managed 또는 Expo prebuild 프로젝트의 architecture setup, implementation, review, remediation에 사용합니다.

Expo 없는 bare React Native, generic web React, architecture 영향이 없는 단일 visual component, deployment-only 작업, 문서 요약에는 사용하지 않습니다. Brownfield 앱에서는 사용자가 migration을 요청하거나 safety/correctness 문제로 변경이 필요한 경우가 아니면 작동 중인 project convention을 보존합니다.

</routing_rule>

<instruction_contract>

| Field | Contract |
|---|---|
| Intent | 앱이 성장해도 route, feature, data, native, platform boundary를 이해할 수 있는 확장 가능하고 testable한 Expo architecture를 만듭니다. |
| Trigger | app setup, folder structure, Expo Router, state/data flow, native config, platform divergence, test, architecture review가 포함된 Expo/React Native/TypeScript 작업. |
| Scope | touched app config, TypeScript source, route tree, feature/shared module, test, architecture validation note. 광범위 native 재생성과 dependency 교체는 명시적 scope가 필요합니다. |
| Authority | user/project 지시가 이 스킬보다 우선합니다. 설치 package/config 근거가 project 동작을 결정합니다. API 사실은 공식 Expo/React Native 문서가, convention은 프로젝트가 채택하지 않는 한 권고가 우선합니다. |
| Evidence | 먼저 `package.json`, app config, router entry, TypeScript/Metro/Babel config, native directory, 기존 source/test, lockfile을 조사합니다. Version drift가 중요하면 날짜가 있는 공식 reference를 사용합니다. |
| Tools | capability 기반 inspect/read/search/edit/execute를 사용합니다. command/path를 검증하고 network install, credential, EAS 작업, commit된 native directory의 `prebuild` 실행, signing, publish/deploy/production effect를 gate합니다. |
| Loop | 제한된 verify-repair loop를 사용합니다. 관련 check를 실행하고 관찰된 실패만 고치며 최대 2회 repair 후 멈춥니다. Critical type, route, native-config, safety guard를 모두 통과한 변경만 유지합니다. |
| Output | project-local architecture 구현 또는 review와 decision, changed files, check, source/version caveat, residual risk를 담은 간결한 한국어 보고서. |
| Verification | project-defined format/lint/type/test와 touched surface에 맞는 Expo diagnostic/platform check를 실행하고 config/route 변경 시 resolved behavior를 검사합니다. |
| Stop condition | project mode와 SDK를 확인하고 applicable critical gate 통과, 변경 검증, residual risk 기록 후 완료합니다. 권한 부족, unsafe native effect, unresolved package incompatibility, 필수 검증 불가 시 block합니다. |

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
- "Expo 로그인 화면의 문구 하나만 바꿔줘." 빠른 boundary check만 하고 architecture churn을 강제하지 않습니다.
- "Expo 앱을 스토어에 배포해줘." architecture/config review에만 사용하며 배포 승인과 실행은 deployment workflow가 담당합니다.

</activation_examples>

<trigger_conditions>

요청에 Expo나 React Native 앱, Expo Router, app folder나 route boundary, native config, platform별 code, 앱 data/state 배치가 나오고, 하는 일이 setup, 구현, review, remediation이면 활성화합니다.

이미 운영 중이거나 커지는 Expo 프로젝트의 structure, routing, import, platform seam을 바꿔야 하거나, review 요청이 change set으로 끝나는 경우에도 활성화합니다.

요청보다 프로젝트 판정을 먼저 합니다. 로컬 파일에서 Expo나 Expo prebuild가 확인되지 않고 사용자가 Expo 앱 생성을 요청하지도 않았다면 이 스킬로 routing하지 않습니다. 나머지 제외 대상은 `<routing_rule>`에 있습니다.

</trigger_conditions>

<skill_architecture>

| 구성 | 역할 | 읽는 조건 |
|---|---|---|
| `stacks/expo/core.ko.md` | trigger, contract, workflow, gate, validation | 항상 |
| `stacks/expo/architecture-rules.ko.md` | rule class와 blocking gate | finding을 분류하기 전 |
| `rules/expo/project-structure.ko.md` | folder, ownership, import, migration, scale profile | folder나 import를 바꿀 때 |
| `rules/expo/routing-and-navigation.ko.md` | Expo Router layout, group, param, protected screen, route thinness | route를 바꿀 때 |
| `rules/expo/data-state-and-boundaries.ko.md` | server/client state, DTO, transport, persistence, dependency direction | data 흐름을 바꿀 때 |
| `rules/expo/native-platform-and-security.ko.md` | app config, permission, secret, storage, native toolchain, EAS, native code | config나 platform code를 건드릴 때 |
| `rules/expo/testing-and-validation.ko.md` | check 순서와 완료 근거 | 완료를 주장하기 전 |
| `references/official/expo/expo-react-native-2026-11-04.ko.md` | 날짜가 고정된 공식 SDK/API 사실, SDK별 기준, 제거 API | 현재 SDK 주장이 변경을 가를 때 |

</skill_architecture>

<loop_policy>

change set마다 loop는 한 번만 돌립니다. check를 실행하고 실패를 읽고 실패한 것만 고친 뒤 다시 실행합니다. 한 round는 repair 한 번과 그 재실행이며, 두 round 뒤에 끝냅니다. critical type, route, native-config, safety gate를 모두 통과한 변경만 남기고, 통과하지 못하면 실패한 check를 밝히고 끝내며 검증됐다고 주장하지 않습니다. 구조가 만족스러워질 때까지 refactor를 반복하는 loop도, 스스로 점수를 매기는 loop도 없습니다. 근거는 기록한 command 출력과 resolved config이고, 계획을 다시 읽는 것이 아닙니다.

</loop_policy>

<language_and_translation_default>

사용자에게 보이는 글은 기본적으로 한국어로 씁니다. 보고서, 결정, caveat, residual risk가 여기 해당합니다. code identifier, command, path, package/API 이름, 인용한 원문은 원래 형태를 유지합니다. 이 패키지는 영문/한글 쌍(`X.md` ↔ `X.ko.md`)으로 관리하므로 한 번에 한 언어판만 읽고, 규칙이 바뀌면 양쪽을 함께 고칩니다.

</language_and_translation_default>

<reference_routing>

- finding을 분류하거나 규칙을 적용하기 전에 `stacks/expo/architecture-rules.ko.md`를 읽습니다.
- folder, import, module ownership, migration 순서를 바꿀 때 `rules/expo/project-structure.ko.md`를 읽습니다.
- route tree, layout, group, param을 바꿀 때 `rules/expo/routing-and-navigation.ko.md`를 읽습니다.
- server state, client state, persistence, dependency 방향을 바꿀 때 `rules/expo/data-state-and-boundaries.ko.md`를 읽습니다.
- app config, permission, secret, storage, native code, platform file을 건드릴 때 `rules/expo/native-platform-and-security.ko.md`를 읽습니다.
- 요청이 끊김, 느린 시작, 목록 스크롤 비용, 메모리, 앱 크기, 번들 크기, "최적화"를 말하면 `rules/expo/performance.ko.md`를 읽습니다.
- 작업이 lint, format, type-check, tsconfig, package manager 고정, CI 검사 순서를 다루면 `rules/setup/typescript.ko.md`를 읽습니다.
- 완료를 주장하기 전에 `rules/expo/testing-and-validation.ko.md`를 읽습니다.
- 설치된 SDK나 공식 API 동작이 변경을 가를 때 `references/official/expo/expo-react-native-2026-11-04.ko.md`를 읽고 `last_verified_at`을 설치 버전과 맞춰 봅니다.

</reference_routing>

<support_file_read_order>

한 번에 한 언어판만, 다음 순서로 읽습니다. 경로는 이 스킬 directory 기준입니다.

1. rule class와 blocking gate는 `stacks/expo/architecture-rules.ko.md`에서 읽습니다.
2. 변경이 건드리는 topic의 rule file은 `<reference_routing>`으로 골라 읽습니다.
3. 현재 SDK/API 동작이 결정에 영향을 줄 때만 `references/official/expo/expo-react-native-2026-11-04.ko.md`를 읽습니다.
4. 구현을 마치기 전에 `rules/expo/testing-and-validation.ko.md`를 읽습니다.

</support_file_read_order>

<workflow>

| Phase | Task | Output |
|---|---|---|
| 0 | 로컬 파일에서 Expo SDK, React Native, Router, TypeScript, package manager, workspace mode, managed/CNG인지 committed `ios/`·`android/`인지, route root(`src/app` 또는 `app`), alias, project command, `web.output`과 API route 존재 여부, 요청에 install·`prebuild`·EAS·credential·signing·store effect가 필요한지 확인 | Scope decision |
| 1 | route, feature, shared module, state/data, native config, test, dependency direction inventory | Architecture map |
| 2 | finding을 Official, Safety, Hypercore convention으로 분류 | Prioritized plan |
| 3 | target boundary와 최소 migration slice 정의, user work 보존 | Change set |
| 4 | 안전하고 reversible한 변경 구현 및 affected callsite/test/config 갱신 | Integrated architecture |
| 5 | focused/project check 실행과 resolved behavior 검사 | Verification evidence |
| 6 | decision, version/source, result, residual risk를 한국어로 보고 | Handoff |

</workflow>

<required>

- Route는 `src/app`을 선호하고 non-route code는 그 밖에 둡니다. SDK 55 이후 기본 template이 `src/app`, `src/components`, `src/constants`, `src/hooks`를 만들고, 두 route root가 있으면 `src/app`이 root `app`보다 우선합니다.
- 성장은 `src/features/<domain>`과 좁은 `src/shared/*`로 조직하고 domain behavior를 전역 `components`, `hooks`, `utils`, `services` bucket에 쌓지 않습니다.
- route file은 composition 중심으로 유지하고 business rule/reusable data access는 feature/application layer에 둡니다.
- TypeScript strict를 유지하고 untrusted runtime data를 boundary에서 검증하며 `any`와 unchecked cast를 피합니다. React Native 0.88에서는 Strict TypeScript API가 기본이므로 `react-native/Libraries/*` deep import와 `*Properties` type alias를 쓰지 않습니다.
- server state, client UI state, form state, persisted device state를 ownership/lifecycle별로 분리합니다.
- `EXPO_PUBLIC_*`를 public으로 취급하고 작은 secret만 secure platform-backed storage에 저장하며 server secret을 bundle하지 않습니다.
- 실제 동작이 다를 때 `.ios.ts(x)`/`.android.ts(x)` 또는 작은 adapter로 platform divergence를 명시합니다.
- package version을 추측하지 않고 설치 SDK와 `expo install` compatibility를 따릅니다. SDK 55부터 모든 Expo package가 SDK major를 공유하므로 SDK 58의 `expo-camera@^58`은 정상입니다.
- 수동 `useMemo`/`useCallback`/`React.memo` 제거는 `experiments.reactCompiler`가 켜져 있고 그 file이 적용 범위에 있을 때만 권합니다.

</required>

<forbidden>

- project command, package, native capability, API contract, environment variable 조작.
- project scale/convention 조사 없이 universal folder template 강제.
- domain feature가 route file을 import하거나 UI가 infrastructure 내부를 import하거나 cycle을 만드는 broad barrel 사용.
- source, app config `extra`, `EXPO_PUBLIC_*`, log, AsyncStorage, client bundle에 secret 저장.
- 명시적 승인 없는 package install, EAS build/update/submit, signing, store publish.
- commit된 `ios/`·`android/` directory에 명시적 승인 없이 `prebuild`를 실행하는 것. SDK 57부터 bare `prebuild`가 두 directory를 지우고 다시 생성하므로 보존 경로는 `--no-clean`과 diff 검토입니다.
- Expo Go 성공을 development/standalone build, permission, config plugin, native module 동작의 증거로 취급. Expo Go는 CLI와 app 양쪽 로그인된 Expo account를 요구하고 store에서는 한 SDK version만 지원하므로, 실행을 근거로 인용하기 전에 대상 SDK를 밝힙니다.
- Swift Package Manager(`npx react-native spm`), `experiments.noxcturnalTransformWorker`, `expo-location/next` 같은 실험 경로를 기본 지원 설정처럼 채택.
- 검증된 incremental boundary 없는 unbounded refactor/migration.

</forbidden>

<validation>

- [ ] Expo mode, SDK, React Native, Router, package manager, platform, native-directory ownership을 식별했습니다.
- [ ] SDK 세대를 기억이 아니라 날짜가 있는 reference 기준(SDK 58: react-native 0.88, react 19.3, expo-router 58)으로 밝혔습니다.
- [ ] Reference의 제거 API 표에 있는 API를 새로 도입하거나 review 대상 code에 그대로 두지 않았습니다.
- [ ] positive 3개, negative 2개, boundary 1개 이상의 trigger example이 유지됩니다.
- [ ] route file은 얇고 non-route module은 `app`/`src/app` 밖에 있습니다.
- [ ] dependency direction과 feature/shared ownership이 명확하며 cycle/unsafe barrel이 없습니다.
- [ ] route 접근 제어는 navigator의 protected-screen API를 쓰며 그것이 유일한 authorization이 아닙니다.
- [ ] runtime input, environment, persistence, permission, secure storage가 boundary rule을 따릅니다.
- [ ] `web.output`, API route, `asyncRoutes`가 실제 hosting model과 일치합니다.
- [ ] 동작/config가 다르면 Android/iOS 변경을 각각 확인했습니다.
- [ ] relevant typecheck, lint, test, Expo diagnostic, resolved config, build check를 실행했거나 불가 사유를 기록했습니다.
- [ ] 영문/한글 파일의 trigger, authority, workflow, safety, completion 의미가 동등합니다.
- [ ] 최신 공식 주장은 날짜가 있는 reference를 인용하며 source date가 미래가 아닙니다.
- [ ] 완료 기록은 `Claim -> Risk -> Evidence -> Verification -> Result -> Caveat`와 ship/iterate/caveated ship/block 결정을 포함합니다.

</validation>
