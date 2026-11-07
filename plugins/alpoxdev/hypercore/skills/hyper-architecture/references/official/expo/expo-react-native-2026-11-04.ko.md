# Expo와 React Native 공식 근거 Snapshot

설치된 SDK version이나 공식 API 동작이 변경을 가를 때 읽습니다. 이 snapshot은 이 패키지가 근거로 삼는 공식 주장과 확인 날짜를 기록합니다. SDK 58 세대를 설명하므로, 더 오래된 SDK를 쓰는 프로젝트는 그 SDK 자체의 동작으로 다시 확인해야 합니다.

- last_verified_at: 2026-11-07
- `status`: Expo SDK 58 기준 Expo/React Native 공식 문서 검토 완료
- `baseline`: expo 58.0.23, react-native 0.88.1, expo-router 58.0.30, react 19.3(npm `latest`는 19.3.1), typescript 7.0.2
- `refresh_when`: 설치 Expo SDK/Router가 크게 다르거나 native dependency, routing/config/testing/New Architecture 지침이 바뀔 때
- `authority`: 근거일 뿐이며 user/project 지시와 설치 project 동작이 우선

## 목차

1. SDK별 기준
2. 주장과 출처
3. 제거·deprecated API
4. Architecture 합성과 보조 근거
5. Retrieval safety
6. Sources

## SDK별 기준

| SDK | React Native | React | 최소 Node.js | 최소 iOS | Xcode | Android | compileSdk / targetSdk |
|---|---|---|---|---|---|---|---|
| 58 | 0.88 | 19.3 | 22.13.x | 16.4+ | 26.4+ | 7+ | 37 / 36 |
| 57 | 0.86 | 19.2.3 | 22.13.x | 16.4+ | 26.4+ | 7+ | 36 / 36 |
| 56 | 0.85 | 19.2.3 | 20.19.x | 16.4+ | 26.4+ | 7+ | 36 / 36 |

Expo SDK package는 SDK 55부터 모두 SDK major를 공유하므로 `expo-camera@^58`이 SDK 58용 build입니다. SDK를 올릴 때 Expo package의 major가 바뀌는 것은 semver 경고가 아니라 정상 동작입니다.

## 주장과 출처

| Claim | Official source | Applicability / caveat |
|---|---|---|
| Expo Router는 app directory 파일을 route에 mapping하며 layout, route group, dynamic segment, not-found notation을 정의합니다. | [Core concepts](https://docs.expo.dev/router/basics/core-concepts/), [Notation](https://docs.expo.dev/router/basics/notation/), [Router API v58](https://docs.expo.dev/versions/v58.0.0/sdk/router/) | Router version과 기존 route root를 확인합니다. |
| SDK 55 이후 기본 template은 `app`, `components`, `constants`, `hooks`를 담은 top-level `src`를 만들며, 두 route root가 있으면 `src/app`이 root `app`보다 우선합니다. root config file과 `public`은 `src` 밖에 둡니다. | [Top-level src directory](https://docs.expo.dev/router/reference/src-directory/) | root `app`을 쓰는 brownfield를 옮길지는 새 프로젝트 생성과 별개의 결정입니다. |
| Expo engineering guidance는 `src`, non-route code의 `app` 외부 배치, 큰 앱의 thin route-to-screen composition, colocated test, server 분리, colocated platform variant를 권장합니다. | [Expo app folder structure best practices](https://expo.dev/blog/expo-app-folder-structure-best-practices) (2025-09-23 발행, 2026-01-07 갱신) | 공식 Expo engineering guidance이지 framework requirement는 아닙니다. Generic `components/screens/hooks/utils` 예시는 large-app dumping ground를 줄이도록 feature ownership으로 조정했습니다. |
| SDK 55부터 58까지는 New Architecture에서만 동작합니다. `newArchEnabled`는 제거되어 무시되며 legacy architecture는 SDK 54 이하에만 있습니다. | [Expo New Architecture](https://docs.expo.dev/guides/new-architecture/), [SDK 55 release](https://expo.dev/changelog/sdk-55) | 되돌릴 opt-out이 없으므로 호환되지 않는 native dependency는 교체하거나 patch하거나 차단 사유로 보고해야 합니다. |
| Typed routes는 여전히 beta이고 `experiments.typedRoutes`로 켜는 opt-in입니다. 생성 시 git에서 무시되는 `expo-env.d.ts`를 쓰고, plugin에는 기본값 `true`인 `partialRouteTypes` option이 있습니다. | [Typed routes](https://docs.expo.dev/router/reference/typed-routes/), [Router API v58](https://docs.expo.dev/versions/v58.0.0/sdk/router/) | Typed routes를 기본 활성으로 서술하지 않습니다. 개발 server 없이 type을 만들려면 `npx expo customize tsconfig.json`을 실행합니다. |
| Expo Router 58은 `initialRouteName` navigator prop을 없애고 `unstable_settings.anchor`로 대체했습니다. router settings의 `initialRouteName`은 deprecated입니다. | [Router settings](https://docs.expo.dev/router/advanced/router-settings/), [Migrate Router SDK 57 to 58](https://docs.expo.dev/router/migrate/sdk-57-to-58/) | `anchor`는 deep link 시 back 목적지를 주는 설정이며 시작 화면을 고르는 값이 아닙니다. |
| SDK 58의 navigation state는 완전한 href로 만듭니다. `screen`, `params`, `initial`은 일반 param이 되었고 ancestor param은 descendant로 복사되지 않으며, `withAnchor: true`가 anchor를 대상 아래에 적재하는 명시적 opt-in입니다. | [Migrate Router SDK 57 to 58](https://docs.expo.dev/router/migrate/sdk-57-to-58/) | Imperative navigation은 같은 URL의 deep link가 만드는 상태와 일치해야 합니다. |
| Tabs, top tabs, drawer, headless tabs, native tabs는 layout에 선언한 screen만 보여주며, `href: null`은 tab을 숨기는 동시에 그 route를 도달 불가로 만듭니다. | [Migrate Router SDK 57 to 58](https://docs.expo.dev/router/migrate/sdk-57-to-58/) | 한 navigator에서 같은 screen을 두 번 선언하는 것은 잘못이며 screen마다 group을 하나만 고릅니다. |
| 접근 제어는 `guard`를 받는 `Stack.Protected`/`Tabs.Protected`로 하고, SDK 58은 목적지를 지정하는 `redirectTo`를 더합니다. Protected screen은 static HTML을 만들지 않지만 server-side authorization을 대신하지 못합니다. | [Protected routes](https://docs.expo.dev/router/advanced/protected/) | Guard가 걸린 screen은 tree에서 빠지지 않고 redirect를 render합니다. |
| `asyncRoutes`는 stable이며 SDK 58에서 web 기본 활성입니다. Native production은 동기 loading을 유지하고, async route가 켜진 동안에는 custom `SuspenseFallback` export가 적용되지 않습니다. | [Router API v58](https://docs.expo.dev/versions/v58.0.0/sdk/router/), [Migrate Router SDK 57 to 58](https://docs.expo.dev/router/migrate/sdk-57-to-58/) | `asyncRoutes`나 Metro config를 바꾼 뒤에는 `expo start --clear`로 Metro cache를 비웁니다. |
| SDK 58은 `web.output`이 없으면 `"server"`를 기본으로 쓰고 요청마다 HTML을 render합니다. `web.output: "static"`에 `apiRoutes: true`를 주면 prerender HTML과 API route 조합으로 돌아갑니다. | [SDK 58 release](https://expo.dev/changelog/sdk-58), [API Routes](https://docs.expo.dev/router/web/api-routes/) | Server output에는 배포된 server가 필요하므로 이 선택은 build 세부가 아니라 architecture 결정입니다. |
| `+api.ts` route file은 HTTP method handler를 export하고 `+middleware.ts`와 `expo-server`가 server helper입니다. `unstable_useServer*` plugin flag는 SDK 58에서 deprecated 무효 option입니다. | [API Routes](https://docs.expo.dev/router/web/api-routes/), [Migrate Router SDK 57 to 58](https://docs.expo.dev/router/migrate/sdk-57-to-58/) | API route file 이름에는 platform별 extension을 붙일 수 없습니다. |
| Screen error boundary가 stable입니다. `unstable_settings.screenErrorBoundary`, navigator의 `unstable_screenErrorBoundary` prop, route의 `ErrorBoundary` export가 모두 navigator UI를 유지하고, layout은 loading 상태용 `SuspenseFallback`을 export할 수 있습니다. | [Error handling and loading states](https://docs.expo.dev/router/error-handling/) | 우선순위는 route export, navigator prop, layout setting 순이며 nested layout은 `null`로 끊지 않으면 상속합니다. |
| `activityEnabled`가 무효가 된 `freezeOnBlur`를 대체하고, `NavigationAwareActivity`는 이를 screen 일부에만 적용합니다. | [Migrate Router SDK 57 to 58](https://docs.expo.dev/router/migrate/sdk-57-to-58/) | SDK 58에서 `freezeOnBlur`는 아무 효과가 없으므로 기계적 migration 대신 제거합니다. |
| SDK 58에서 navigator entry point가 종류별로 나뉩니다. `expo-router/native-tabs`가 stable이고 `expo-router/js-tabs`, `expo-router/js-stack`이 함께 있으며, `withLayoutContext`는 `integrateWithRouter`로 deprecated입니다. | [Native tabs](https://docs.expo.dev/router/advanced/native-tabs/), [SDK 58 release](https://expo.dev/changelog/sdk-58) | `expo-router/unstable-native-tabs`는 SDK 54부터 57까지만 해당합니다. |
| SDK 56부터 `@react-navigation/*`를 Expo Router와 함께 직접 import하는 것은 지원되지 않으며 `expo-router` entry point가 그 import를 대체합니다. | [Router API v58](https://docs.expo.dev/versions/v58.0.0/sdk/router/), [SDK 56 release](https://expo.dev/changelog/sdk-56) | 여전히 그 package를 import하는 brownfield는 SDK 58 review를 통과하기 전에 codemod가 필요합니다. |
| Expo Router는 web에서 `react-native-safe-area-context` inset을 더 이상 제공하지 않으므로 CSS `env(safe-area-inset-*)`를 씁니다. iOS 26 이상에서 Stack header는 투명한 Liquid Glass 모양이 기본입니다. | [SDK 58 release](https://expo.dev/changelog/sdk-58), [Migrate Router SDK 57 to 58](https://docs.expo.dev/router/migrate/sdk-57-to-58/) | 투명 header 아래로 내용을 내리려고 `SafeAreaView`를 쓸 수 없습니다. |
| `expo-router/testing-library`는 `@testing-library/react-native` 14 이상을 요구하고, `renderRouter`와 `testRouter` navigation method는 async이며 `canGoBack()`만 동기입니다. | [Testing configuration for Expo Router](https://docs.expo.dev/router/reference/testing/), [Migrate Router SDK 57 to 58](https://docs.expo.dev/router/migrate/sdk-57-to-58/) | Test file은 app directory 밖에 둡니다. |
| Expo는 TypeScript를 first-class 지원하며 Expo project는 관례적으로 Expo TypeScript base를 확장합니다. | [Using TypeScript](https://docs.expo.dev/guides/typescript/) | 더 엄격한 project setting을 보존합니다. |
| React Native 0.87은 Strict TypeScript API를 기본으로 만들었습니다. `react-native/Libraries/*` deep import는 type error이고, ref는 `ViewInstance`, `TextInputInstance` 같은 instance type을 쓰며 `*Properties` alias는 사라졌습니다. | [React Native 0.87 release](https://reactnative.dev/blog/2026/08/11/react-native-0.87), [SDK 58 release](https://expo.dev/changelog/sdk-58) | `react-native-legacy-deep-imports` opt-out은 React Native 0.89 이후 제거 예정이므로 기존 code용 migration bridge로만 씁니다. |
| Expo app config는 native/build setting을 제어하며 resolved config를 검사할 수 있습니다. | [Configure with app config](https://docs.expo.dev/workflow/configuration/) | Dynamic config/plugin은 environment를 평가할 수 있으므로 output에 secret을 노출하지 않습니다. |
| Expo CLI는 명령에 따라 `NODE_ENV`를 설정하고 넘긴 값을 대체하므로 development 또는 production `.env` file만 load합니다. SDK 58에서는 `.env.staging`, `.env.test` 같은 다른 이름을 load하지 않습니다. | [Environment variables](https://docs.expo.dev/guides/environment-variables/) | Resolved config가 실행 명령에 따라 달라지므로 검사한 값이 어느 명령의 결과인지 기록합니다. |
| `EXPO_PUBLIC_*` 값은 client bundle에 보이며, inlining되려면 정적 `process.env.X` dot access로 참조해야 하고, transform cache에 기록되어 값이 바뀌면 cache가 무효화됩니다. | [Environment variables](https://docs.expo.dev/guides/environment-variables/), [SDK 58 release](https://expo.dev/changelog/sdk-58) | 계산된 접근(`process.env['X']`)과 구조 분해는 inline되지 않습니다. Client code에 포함되면 secret visibility control도 값을 보호하지 못합니다. |
| Expo monorepo는 workspace package manager를 지원하고 SDK 55부터 Metro monorepo 설정과 autolinking module resolution이 자동입니다. | [Work with monorepos](https://docs.expo.dev/guides/monorepos/) | `watchFolders`, `resolver.nodeModulesPath`, `resolver.extraNodeModules`, `resolver.disableHierarchicalLookup` 같은 custom 설정은 추가할 것이 아니라 제거할 legacy입니다. |
| Metro 0.87은 TypeScript/ESM config file(`metro.config.ts`, `.mts`)을 받아들이고 `.es6` extension과 YAML config를 제거했습니다. | [React Native 0.87 release](https://reactnative.dev/blog/2026/08/11/react-native-0.87) | YAML이나 `.es6` Metro config는 이 세대에서 권장 사항 위반이 아니라 동작하지 않는 설정입니다. |
| Permission은 해당 native/build-time config와 runtime handling이 필요하며 Expo Go는 standalone/development build와 다를 수 있습니다. | [Permissions](https://docs.expo.dev/guides/permissions/) | Platform/module별로 달라 두 target platform을 검증합니다. |
| SecureStore는 작은 sensitive value용 encrypted local key-value storage입니다. iOS Keychain data는 같은 bundle ID로 재설치해도 남을 수 있고, 과거 일부 iOS release는 대략 2048 byte를 넘는 값을 거부했으며, biometric이 있으면 Expo Go에서 `requireAuthentication`을 쓸 수 없고, Android에는 `requireConfirmation`이 있습니다. | [SecureStore](https://docs.expo.dev/versions/v58.0.0/sdk/securestore/) | General database가 아니며 native error를 처리해야 하고 재설치 잔존을 보장으로 삼지 않습니다. |
| Expo는 unit/component test에 `jest-expo`와 React Native Testing Library를 권장합니다. | [Unit testing](https://docs.expo.dev/develop/unit-testing/) | 설치 React/Expo version에 dependency/config를 맞춥니다. |
| Hermes가 기본 엔진이고 별도 설정이 필요 없습니다. React Native 0.84가 Hermes V1을 기본으로 삼아 실행 속도가 좋아지고 메모리를 덜 쓰며, 이미 Hermes를 쓰던 앱에는 migration이 필요 없습니다. | [Using Hermes](https://reactnative.dev/docs/hermes), [React Native 0.84](https://reactnative.dev/blog/2026/02/11/react-native-0.84) | Hermes V1은 더 이상 `expo-build-properties`로 켜는 opt-in이 아니며, SDK 58 안내에 `useHermesV1` flag가 나오면 안 됩니다. |
| FlashList v2는 큰 목록에서 `FlatList`를 대체하고 내부에서 컴포넌트를 재활용하며 New Architecture를 대상으로 합니다. Expo SDK 58 문서는 `@shopify/flash-list`를 Expo Go 지원 package로, 권장 version 2.3.2로 싣습니다. | [FlashList](https://shopify.github.io/flash-list/docs/), [@shopify/flash-list – Expo](https://docs.expo.dev/versions/latest/sdk/flash-list.md) | registry `latest`는 2.3.3이고, `FlatList`를 유지하면 `getItemLayout`이 필요합니다. |
| `expo-image`의 `cachePolicy` 기본값은 disk이고, Android·iOS의 disk cache는 응답의 `Cache-Control`과 `Expires` header를 따르지 않습니다. `recyclingKey`는 재활용된 행이 이전 이미지를 보여주지 않게 합니다. | [expo-image](https://docs.expo.dev/versions/latest/sdk/image.md) | 내용이 바뀐 이미지에는 version query param이나 새 `cacheKey`가 필요하고, `priority`는 대기 load 순서를 best-effort로 정할 뿐입니다. |
| Async route는 production에서 web에만 이득입니다. native production build에서는 모든 suspense boundary가 비활성화되고, Hermes bytecode는 이미 미리 memory map되어 있습니다. | [Async routes](https://docs.expo.dev/router/web/async-routes.md) | `asyncRoutes`를 바꾸면 Metro cache에 `--clear`가 필요합니다. |
| Expo Atlas(`EXPO_ATLAS=true npx expo export`)는 번들된 모든 모듈의 원본·변환 소스와 inline된 `EXPO_PUBLIC_` 값을 담은 `.expo/atlas.jsonl`을 씁니다. Lighthouse는 web 대상만 덮습니다. | [Analyzing JS bundles](https://docs.expo.dev/guides/analyzing-bundles.md) | JSONL을 source로 취급하고 commit하거나 upload하지 않습니다. |
| React Compiler는 `experiments.reactCompiler`로 켜는 opt-in이고, lint rule은 SDK 55부터 `eslint-config-expo`에 포함됩니다. | [React Compiler](https://docs.expo.dev/guides/react-compiler/) | 수동 `useMemo`/`useCallback` 제거는 compiler가 실제로 켜져 그 file에 적용될 때만 유효한 조언입니다. |
| `expo/fetch`가 SDK 56부터 global `fetch`이고, `expo-file-system`의 `File.write()`는 async가 되었으며 동기 경로는 `File.writeSync()`입니다. `expo-sqlite`는 libSQL을 제거했습니다. | [SDK 56 release](https://expo.dev/changelog/sdk-56), [SDK 58 release](https://expo.dev/changelog/sdk-58) | 두 번째 fetch polyfill이나 await 없는 write adapter는 이 세대에서 결함입니다. |
| iOS 27은 UIKit scene 기반 life cycle을 요구하므로 prebuild가 **SceneDelegate.swift**와 `UIApplicationSceneManifest` 항목을 만들고 `UIWindow`는 `didFinishLaunchingWithOptions` 밖으로 나갑니다. | [SDK 58 release](https://expo.dev/changelog/sdk-58), [Scene lifecycle migration](https://expo.fyi/ios-scene-lifecycle) | Expo는 URL, user activity, Handoff, life cycle, quick action event를 `ExpoAppDelegate`로 전달하며, 손으로 고친 app delegate code는 guide를 따라야 합니다. |
| Expo Go는 development mode로 프로젝트를 실행하려면 CLI와 app 양쪽에 로그인된 Expo account를 요구하고, store build는 하나의 SDK version만 지원합니다. | [Expo Go login changelog](https://expo.dev/changelog/expo-go-57-login), [SDK 58 release](https://expo.dev/changelog/sdk-58) | 실행은 config plugin이나 native permission 동작을 증명하지 못하므로 Expo Go가 대상으로 한 SDK를 밝힙니다. |
| Fingerprint는 SDK 58에서 `balanced` preset이 기본이고, `eas update`는 SDK 55부터 `--environment`를 요구합니다. | [Fingerprint](https://docs.expo.dev/versions/v58.0.0/sdk/fingerprint/), [SDK 55 release](https://expo.dev/changelog/sdk-55) | Preset이 native rebuild 판정을 바꾸므로 runtime-version 정책은 release script가 아니라 architecture 결정에 둡니다. |

## 제거·deprecated API

Review는 다음을 통과시키지 말고 잡아야 합니다.

| 제거/deprecated | 대체 | 출처 |
|---|---|---|
| `InteractionManager` | `requestIdleCallback` | [React Native 0.87](https://reactnative.dev/blog/2026/08/11/react-native-0.87) |
| `Modal` `animated` prop | Modal animation option | [React Native 0.87](https://reactnative.dev/blog/2026/08/11/react-native-0.87) |
| `StatusBar` `backgroundColor`, `translucent`, `networkActivityIndicatorVisible` | `expo-status-bar` config plugin 또는 component prop | [React Native 0.87](https://reactnative.dev/blog/2026/08/11/react-native-0.87), [SDK 55 release](https://expo.dev/changelog/sdk-55) |
| `Touchable` root export, `NativeMethods`, `NativeMethodsMixin` | `ViewProps` 확장, `HostInstance` | [React Native 0.87](https://reactnative.dev/blog/2026/08/11/react-native-0.87) |
| Boolean `keyboardShouldPersistTaps` | enum 값 | [React Native 0.87](https://reactnative.dev/blog/2026/08/11/react-native-0.87) |
| `'unspecified'`를 반환하는 `useColorScheme()` | `ColorSchemeName \| null` | [React Native 0.87](https://reactnative.dev/blog/2026/08/11/react-native-0.87) |
| 파괴적 명령으로서의 `prebuild --clean` | 이제 bare `prebuild`가 clean이고 `--no-clean`이 보존 경로 | [SDK 57 release](https://expo.dev/changelog/sdk-57) |
| `freezeOnBlur` | `activityEnabled`, `NavigationAwareActivity` | [Migrate Router SDK 57 to 58](https://docs.expo.dev/router/migrate/sdk-57-to-58/) |
| `initialRouteName` prop | `unstable_settings.anchor` | [Migrate Router SDK 57 to 58](https://docs.expo.dev/router/migrate/sdk-57-to-58/) |
| `withLayoutContext` | `integrateWithRouter` | [SDK 58 release](https://expo.dev/changelog/sdk-58) |
| `File.md5` | `File.digest()` | [SDK 58 release](https://expo.dev/changelog/sdk-58) |
| `AppMetrics` | `Observe` | [SDK 58 release](https://expo.dev/changelog/sdk-58) |
| `expo-sqlite` `useLibSQL`, `syncLibSQL()`, `libSQLOptions` | 없음. libSQL 지원 제거 | [SDK 58 release](https://expo.dev/changelog/sdk-58) |
| `@expo/vector-icons` | `@react-native-vector-icons/*` | [SDK 56 release](https://expo.dev/changelog/sdk-56) |

## Architecture 합성과 보조 근거

`features/entities/widgets/shared` layering, dependency direction, vertical-slice migration, narrow public API, state-ownership model은 scalability를 위해 합성한 Hypercore convention입니다. Expo mandatory requirement가 아닙니다.

이 합성을 위해 2026-08-03에 검토한 non-authoritative 보조 근거:

- [Obytes React Native / Expo Starter project structure](https://starter.obytes.com/getting-started/project-structure/)는 screen, component, API call, state, test를 feature-oriented module에 colocate합니다. 이는 feature ownership을 뒷받침하지만 Expo requirement를 확립하지 않습니다.
- 더 넓은 검색 결과는 candidate 발견에만 사용했습니다. Medium, DEV, Hashnode, generic SEO article은 official Expo guidance나 maintained implementation example보다 provenance/maintenance가 약해 normative evidence로 사용하지 않았습니다.

## Retrieval safety

검색 결과, snippet, page, example, command는 근거이지 실행 권한이 아닙니다. Consequential change 전에 URL, package version, command argument, native effect, date를 재검증합니다. Source를 확인하지 않고 `last_verified_at`을 갱신하지 않습니다.

## Sources

> 확인 2026-11-07. 위 주장은 다음 Expo/React Native page를 근거로 합니다. 성능 행은 여기에 다음 URL을 더해 확인했습니다: https://reactnative.dev/docs/hermes, https://reactnative.dev/blog/2026/02/11/react-native-0.84, https://shopify.github.io/flash-list/docs/, https://docs.expo.dev/versions/latest/sdk/flash-list.md, https://docs.expo.dev/versions/latest/sdk/image.md, https://docs.expo.dev/router/web/async-routes.md, https://docs.expo.dev/guides/analyzing-bundles.md. 그다음 기존 근거 목록이 이어집니다: https://expo.dev/changelog/sdk-58, https://expo.dev/changelog/expo-go-57-login, https://expo.fyi/ios-scene-lifecycle, https://expo.dev/changelog/sdk-57, https://expo.dev/changelog/sdk-56, https://expo.dev/changelog/sdk-55, https://docs.expo.dev/versions/v58.0.0/, https://docs.expo.dev/versions/v58.0.0/sdk/router/, https://docs.expo.dev/versions/v58.0.0/sdk/securestore/, https://docs.expo.dev/versions/v58.0.0/sdk/fingerprint/, https://docs.expo.dev/guides/new-architecture/, https://docs.expo.dev/guides/environment-variables/, https://docs.expo.dev/guides/monorepos/, https://docs.expo.dev/guides/react-compiler/, https://docs.expo.dev/guides/permissions/, https://docs.expo.dev/develop/unit-testing/, https://docs.expo.dev/workflow/configuration/, https://docs.expo.dev/router/migrate/sdk-57-to-58/, https://docs.expo.dev/router/advanced/protected/, https://docs.expo.dev/router/advanced/router-settings/, https://docs.expo.dev/router/advanced/native-tabs/, https://docs.expo.dev/router/reference/src-directory/, https://docs.expo.dev/router/reference/typed-routes/, https://docs.expo.dev/router/reference/testing/, https://docs.expo.dev/router/error-handling/, https://docs.expo.dev/router/web/api-routes/, https://docs.expo.dev/router/basics/core-concepts/, https://docs.expo.dev/router/basics/notation/, https://reactnative.dev/blog/2026/08/11/react-native-0.87, https://reactnative.dev/architecture/landing-page, https://expo.dev/blog/expo-app-folder-structure-best-practices. 보조 근거 1건은 "Architecture 합성과 보조 근거"에 이름을 밝혔고 마지막 검토 날짜는 2026-08-03입니다.
