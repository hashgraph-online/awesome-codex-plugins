# Native Platform과 Security

app config, permission, storage, secret, native code, native effect가 있는 dependency, platform file을 건드릴 때 읽습니다. 이 파일은 해당 gate, native toolchain 기준, project mode 판정을 소유합니다.

## Project mode

Native project가 CNG/prebuild로 생성되는지, 의도적으로 commit/관리되는지, 없는지 식별합니다. Config plugin/app config는 project ownership이 지정한 범위에서만 source of truth입니다.

SDK 57부터 bare `expo prebuild`가 `ios/`와 `android/`를 기본으로 지우고 다시 생성하므로, commit된 native directory에 그대로 실행하면 manual 변경이 사라집니다. `prebuild` 자체를 gate 대상 command로 취급하고, commit된 native 프로젝트에는 `--no-clean`과 diff 검토를 요구하며, `prebuild --clean`은 유일한 파괴 경로가 아니라 같은 파괴 동작으로 봅니다.

## Native toolchain 기준

SDK 58 세대의 기준입니다.

- iOS deployment target 16.4 이상, Xcode 26.4 이상, Node.js는 22 line에서 22.13 이상이고 24 line에서 24.3 이상입니다.
- Android 7 이상, `compileSdk` 37, `targetSdk` 36, 최소 Kotlin 2.0이며, AGP 9를 지원하고 AGP 9 opt-out(`android.builtInKotlin=false`, `android.newDsl=false`)을 `gradle.properties`에 둡니다.
- Release build의 R8 minify가 `android.enableMinifyInReleaseBuilds=true`로 기본 활성입니다. Reflection을 쓰는 library는 keep rule이 필요하거나 `expo-build-properties`로 명시적 opt-out을 해야 합니다.
- CocoaPods가 iOS dependency의 기본이자 지원 경로입니다. Swift Package Manager(`npx react-native spm`)는 실험적이고 추가 방식이며 production용이 아니므로 architecture 변경에서 조용히 채택하지 않습니다.
- `expo-modules-core`는 precompiled Android library를 배포합니다. `android.buildExpoModulesCoreFromSource`는 기본값이 아니라 명시적 opt-out입니다.

Commit된 `ios/`에서 `AppDelegate.swift`를 고친 프로젝트는 SDK 58 upgrade 전에 검토가 필요합니다. iOS 27은 UIScene life cycle을 요구하므로 prebuild가 **SceneDelegate.swift**와 `UIApplicationSceneManifest` 항목을 생성하고 `UIWindow`는 `didFinishLaunchingWithOptions` 밖으로 나갑니다. Expo는 URL, user activity, Handoff, life cycle, quick action event를 `ExpoAppDelegate` override와 subscriber로 전달하지만, 손으로 고친 app delegate code는 scene-lifecycle migration guide를 따라야 합니다.

## App configuration

기존 workspace rule이 다르지 않으면 `app.config.ts`, `app.json`, `eas.json`, Metro, TypeScript config는 app root에 둡니다. `npx expo config`로 resolved public config를 검사하되 secret evaluation path를 출력하지 않습니다. Config-plugin/permission 변경은 일반적으로 JavaScript reload/update만이 아니라 새 native build가 필요합니다.

Resolved config는 이제 실행한 command에 따라 달라집니다. Expo CLI는 command에 맞춰 `NODE_ENV`를 설정하고 넘긴 값을 대체하므로 development 또는 production `.env` file만 load하고 `.env.staging`, `.env.test` 같은 이름은 무시합니다. 검사한 값이 어느 command의 결과인지 기록합니다.

| Mode | 우선순위가 높은 순서의 file |
|---|---|
| Development | `.env.development.local`, `.env.local`, `.env.development`, `.env` |
| Production | `.env.production.local`, `.env.local`, `.env.production`, `.env` |

Metro config는 `metro.config.js`, `.ts`, `.mts`를 쓸 수 있습니다. YAML config와 `.es6` extension은 이 세대에서 제거되었고 권장 사항 위반이 아니라 동작하지 않는 설정입니다.

## Permission

Permission을 build-time native declaration/purpose text와 runtime request/denial handling의 두 부분 contract로 취급합니다. User intent 시점에 요청하고 목적을 설명하며 denied/blocked state를 지원하고 fresh-install flow를 시험합니다. Android permission과 iOS usage description을 최소화합니다.

Expo Go는 standalone permission config가 맞다는 증거가 아닙니다. Expo Go는 자체 포함 module의 native permission 선언 단계를 건너뛰고, CLI와 app 양쪽에 로그인된 Expo account를 요구하며, store에서는 하나의 SDK version만 배포합니다. Expo Go로 얻은 실행 결과를 근거로 삼으려면 어떤 SDK를 대상으로 한 실행인지 먼저 밝힙니다.

## Storage와 secret

작은 sensitive value는 adapter를 통해 `expo-secure-store` 또는 근거가 있는 equivalent에 저장합니다. 그 adapter 계약에 네 가지 제약을 넣습니다.

- iOS Keychain data는 같은 bundle ID로 지웠다 다시 설치해도 남을 수 있으므로, 값이 있다는 것이 현재 app instance의 이전 설치를 증명하지 않습니다.
- 기반 platform이 큰 payload를 거부할 수 있습니다. 과거 일부 iOS release는 대략 2048 byte를 넘는 값을 거부했으므로 큰 blob 대신 token이나 참조를 저장합니다.
- Biometric이 있으면 Expo Go에서 face ID usage description이 없어 `requireAuthentication`을 쓸 수 없고, biometric 설정이 바뀌면 보호된 값을 읽을 수 없습니다.
- Android에는 `requireConfirmation`이 있고, 프로젝트가 `SecureStore`를 이미 제외하는 자체 Auto Backup 규칙을 관리한다면 `configureAndroidBackup` plugin option을 꺼야 합니다.

Non-secure storage는 non-sensitive data에만 사용하고 serialization/version migration을 정의합니다. `EXPO_PUBLIC_*`, `extra`, source, log, analytics, error report에 secret을 두지 않습니다.

## Platform seam

명시적 adapter가 있는 shared behavior를 선호합니다. 구현이 실제로 다를 때 `.ios.ts(x)`/`.android.ts(x)`를 사용하고 작은 presentation 차이에는 `Platform.select`를 사용하되 큰 business branch를 숨기지 않습니다. Native-module call은 typed module 뒤에 두어 test와 unsupported platform 동작을 명시합니다.

## Dependency와 native effect

설치 Expo SDK compatibility path를 사용하고 해당 React Native architecture에 대한 package 지원을 확인합니다. SDK 55부터 모든 Expo SDK package가 SDK major를 공유하므로, SDK를 올릴 때 Expo package의 major가 바뀌는 것은 정상입니다. Package install, pod/Gradle 변경, `prebuild`, EAS credential/build/update/submit, signing, push credential, store action은 gated side effect입니다. 필요한 capability/authorization이 없으면 실행했다고 주장하지 말고 blocked check/change를 정확히 제공합니다.

New Architecture에서 동작하지 않는 native dependency에는 fallback이 없습니다. SDK 55부터 58까지는 opt-out이 없으므로 해당 library를 교체하거나 patch하거나, `npx expo-doctor` 출력과 React Native Directory 상태를 붙여 호환성 문제를 blocker로 보고합니다.

## EAS와 전달

- `eas update`는 SDK 55부터 `--environment`를 요구합니다. Flag가 빠진 CI job은 기본값으로 돌지 않고 실패하므로 channel별 environment 매핑은 app의 architecture 결정에 들어갑니다.
- Fingerprint는 SDK 58에서 `balanced` preset이 기본입니다. App config의 `version` 같은 흔한 변경을 무시하고 native module을 package 이름과 version으로 hash하므로, "OTA로 보낼지 rebuild할지"를 정하는 runtime-version 정책은 예전 fingerprint 동작을 물려받지 말고 명시합니다.
- Expo Observe는 startup과 navigation 성능, JavaScript error, native crash를 기록합니다. `shared/observability`의 observability port 구현 하나로 다루고 feature 전반에 흩뿌린 dependency로 만들지 않습니다.

## Sources

> 확인 2026-11-04. 이 서술은 이 패키지의 공식 snapshot `references/official/expo/expo-react-native-2026-11-04.md`를 재진술한 것이며, 그 파일이 다음 URL을 인용합니다: https://expo.dev/changelog/sdk-58, https://expo.dev/changelog/sdk-57, https://expo.dev/changelog/sdk-55, https://docs.expo.dev/guides/new-architecture/, https://docs.expo.dev/guides/environment-variables/, https://docs.expo.dev/guides/permissions/, https://docs.expo.dev/versions/v58.0.0/sdk/securestore/, https://docs.expo.dev/versions/v58.0.0/sdk/fingerprint/, https://reactnative.dev/blog/2026/08/11/react-native-0.87, https://expo.fyi/ios-scene-lifecycle..
