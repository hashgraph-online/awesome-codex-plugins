# 성능

> 릴리스 빌드만 프로파일하고, JS 스레드, 목록, 이미지 캐시를 먼저 고친 뒤에 다른 것을 건드립니다.

Expo 앱에서 끊김, 느린 시작, 목록 스크롤 성능, 메모리, 앱 크기, 번들 크기, "최적화"를 언급할 때 읽습니다. 이 파일은 런타임 엔진, 목록과 이미지 레버, 애니메이션 비용, 번들 분석 루프를 소유하고, 그 주변의 native 설정은 `rules/expo/native-platform-and-security.md`가 소유합니다.

## 먼저 측정

"개발 모드에서 JavaScript 스레드 성능이 크게 떨어집니다. 성능은 항상 릴리스 빌드에서 시험해야 합니다" [L-42]. 프로파일링 문서도 "Development Mode가 꺼져 있는지 확인"으로 시작합니다 [L-43]. 아래 숫자는 개발 빌드에서 모두 의미가 없습니다.

- Hermes가 기본 엔진이고 별도 설정이 필요 없습니다. React Native **0.84**가 Hermes V1을 기본으로 삼아 "실행 속도가 좋아지고 메모리 사용이 줄었으며", 이미 Hermes를 쓰던 앱에는 migration이 필요 없습니다 [L-44][L-45]. SDK 58에서 엔진은 정해졌으므로 안내에 `useHermesV1` flag가 있으면 낡은 것입니다.
- 프레임 예산은 60fps에서 16.67ms이고, JS 스레드와 UI/main 스레드라는 독립된 두 프레임 레이트가 있습니다. 그래서 UI가 부드러워도 JS 스레드가 막혀 있을 수 있고 그 반대도 가능합니다 [L-42].
- 실제 기기의 릴리스 빌드에서 기록합니다. 콜드 스타트의 interactive 도달 시간, 가장 무거운 목록을 스크롤할 때의 최악 frame drop 구간, 10분 사용 후 메모리 최고점, 설치·다운로드 크기입니다.
- React Native profiler와 platform 자체 도구(Xcode Instruments, Android Studio profiler)로 비용이 JS 스레드, UI 스레드, native 작업 중 어디에 있는지 먼저 귀속시킵니다 [L-43].

번들과 asset 무게는 따로 잽니다.

```bash
EXPO_ATLAS=true npx expo export      # writes .expo/atlas.jsonl
npx expo-atlas                       # opens the graph locally
```

Atlas JSONL은 "번들된 모든 모듈의 원본과 변환된 소스, inline된 `EXPO_PUBLIC_` 환경변수 값까지" 담으므로 이 파일을 source로 취급하고 commit하거나 upload하지 않습니다 [L-48]. Lighthouse는 web 대상만 덮습니다 [L-48].

## 규칙

흔한 영향 순서입니다.

1. **`official` — 미세 최적화보다 먼저 작업을 JS 스레드 밖으로 옮깁니다.** Reanimated worklet과 `useAnimatedStyle` body는 UI 스레드에서 실행되고 shared value는 JS·UI 스레드 사이에서 동기화됩니다 [L-50]. 내장 `Animated`에는 `useNativeDriver: true`를 주고, 결과를 기다리지 않는 전환에는 `LayoutAnimation`을 씁니다 [L-42]. 매 프레임 React state를 갱신하는 gesture가 가장 흔한 끊김 원인입니다.
2. **`official` — 큰 `FlatList`를 FlashList v2로 바꿉니다.** FlashList는 drop-in 대체이면서 "내부에서 컴포넌트를 재활용"하고 New Architecture를 대상으로 하며, SDK 55 이후는 New Architecture만 지원합니다 [L-40]. Expo SDK 58 문서는 `@shopify/flash-list`를 Expo Go에서 지원되는 package로 싣고 권장 version은 2.3.2입니다(registry `latest`는 2.3.3) [L-39][L-70]. `FlatList`를 유지해야 하면 `getItemLayout`을 줍니다 [L-42][L-47].
3. **`official` — `expo-image`를 쓰고 재활용 목록 안에서는 `recyclingKey`를 줍니다.** `expo-image`가 이 SDK의 지원 이미지 컴포넌트이고, `recyclingKey`는 FlashList 재활용이 이전 행의 이미지를 보여주지 않게 하려고 존재합니다 [L-41]. `cachePolicy` 기본값은 `'disk'`이며, Android와 iOS의 disk cache는 응답의 `Cache-Control`이나 `Expires` header를 따르지 않으므로 내용이 바뀐 이미지에는 version query param이나 새 `cacheKey`가 필요합니다 [L-41].
4. **`official` — 운영 번들에서 `console.*`를 제거합니다.** 로깅은 릴리스 빌드에서도 JS 스레드 시간을 쓰고 third-party code 안의 호출도 포함됩니다. 문서가 제시하는 해법은 `transform-remove-console`입니다 [L-42].
5. **`official` — layout이 아니라 `transform`을 animate합니다.** 이미지는 animate된 `width`/`height`가 아니라 `transform: [{ scale }]`로 움직이고, `renderToHardwareTextureAndroid`/`shouldRasterizeIOS`는 메모리 비용이 실제로 크므로 아껴 씁니다 [L-42][L-43].
6. **`official` — 번들 분할을 native 이득으로 팔지 않습니다.** `asyncRoutes`는 stable이고 SDK 58 web에서 기본 활성이지만, native에서는 실험적이고 opt-in이며 개발 전용입니다. "native platform용 production으로 번들할 때 모든 suspense boundary가 비활성화되고 loading state가 없습니다" [L-37]. Hermes bytecode는 이미 미리 memory map되므로 "Hermes Engine을 쓰는 앱은 번들 분할의 이득을 크게 보지 못합니다" [L-37]. 설정 key는 `expo-router` plugin의 `asyncRoutes`이고, 바꾸면 Metro cache에 `--clear`가 필요합니다 [L-37][L-38].
7. **`official` — `EXPO_PUBLIC_*`는 정적 dot 접근으로만 읽습니다.** 값은 build time에 inline되고 배포 번들에 보입니다. `process.env['EXPO_PUBLIC_KEY']`와 `const { EXPO_PUBLIC_X } = process.env`는 "유효하지 않고 inline되지 않습니다" [L-49]. 계산 접근은 조용히 `undefined`를 배포하고 runtime bug처럼 보입니다.
8. **`hypercore-default` — Expo Atlas(export)와 web 빌드의 Lighthouse를 번들 크기 게이트로 삼습니다.** Atlas는 native 번들의 모듈별 graph를 주고, Lighthouse는 web 대상만 덮습니다 [L-48]. 전체 graph가 아니라 변경이 건드린 모듈의 차이를 기록합니다.
9. **`official` — `experiments.reactCompiler`를 의도적으로 켜고, 그 뒤에만 수동 memoization을 걷어냅니다.** Compiler는 초기 로드가 아니라 update 성능을 개선하고, Expo 구현은 "애플리케이션 코드에서만(node module 제외), client 번들 시에만(server rendering에서는 비활성)" 실행됩니다 [L-02][L-36]. 그 범위 밖 file에서 `useMemo`를 지우면 대체 없이 memoization을 잃습니다.

## 하지 말 것

- 개발 빌드에서, 또는 문제가 GPU·메모리 병목인데 시뮬레이터에서 측정하지 않습니다. 개발 모드 JS 시간은 대표값이 아닙니다 [L-42][L-43].
- `useHermesV1` opt-in flag를 추가하지 않습니다. Hermes V1은 React Native 0.84부터 기본입니다 [L-45].
- 긴 feed에 `FlatList`를 두고 "모양이 바뀔 수 있다"는 이유로 migration을 미룬 뒤 `windowSize`/`removeClippedSubviews`만 만지지 않습니다. 재활용을 고치는 것이 먼저입니다 [L-40][L-47].
- FlashList 안에서 `recyclingKey` 없이 `expo-image`를 쓰거나, 서버가 같은 URL의 이미지를 바꿨을 때 disk cache가 다시 받아 오리라 기대하지 않습니다 [L-41].
- `expo-image`의 `priority`를 보장으로 취급하지 않습니다. 대기 중인 load 순서를 best-effort로 정할 뿐입니다 [L-41].
- native production 빌드에 `asyncRoutes`를 켜고 더 빠른 시작이나 loading state를 약속하지 않습니다 [L-37].
- `EXPO_PUBLIC_*`를 bracket 접근이나 구조 분해로 inline하거나, inline된 public 값을 secret으로 취급하지 않습니다 [L-49].
- source와 inline된 환경 값을 담은 `.expo/atlas.jsonl`을 commit하거나 upload하지 않습니다 [L-48].
- `node_modules` 인접 코드나 server-rendered code에서 `useMemo`/`useCallback`/`React.memo`를 지우고 compiler가 덮어 주리라 기대하지 않습니다 [L-36].

## 체크리스트

- [ ] 모든 숫자가 실제 기기의 릴리스 빌드에서 나왔고 엔진과 SDK를 밝혔습니다.
- [ ] 레버를 고르기 전에 비용을 JS 스레드, UI 스레드, native 작업 중 하나로 귀속시켰습니다.
- [ ] 새 `useHermesV1` opt-in이 없고 Hermes V1을 기본으로 다룹니다.
- [ ] 큰 목록이 FlashList v2를 쓰거나, 유지한 `FlatList`에 `getItemLayout`이 있습니다.
- [ ] 재활용 목록의 모든 이미지가 `recyclingKey`를 준 `expo-image`이고, 바뀐 이미지에는 version param이나 `cacheKey`가 있습니다.
- [ ] Gesture 기반 animation이 worklet이나 `useNativeDriver: true`로 돌고, 매 프레임 React state 갱신이 남아 있지 않습니다.
- [ ] 이미지와 layout animation이 `width`/`height`가 아니라 `transform`을 씁니다.
- [ ] 운영 번들에서 `console.*`를 제거했습니다.
- [ ] `asyncRoutes` 주장을 web 대상으로 한정했고 변경 후 Metro cache를 지웠습니다.
- [ ] `EXPO_PUBLIC_*`가 정적 dot 접근이고 `.expo/atlas.jsonl`이 추적되지 않습니다.
- [ ] 주장하는 모든 이득에 같은 빌드 종류와 기기에서 잰 before/after 숫자가 있습니다.
- [ ] 변경이 `stacks/expo/architecture-rules.md`의 게이트와 `rules/setup/typescript.md`의 검사를 모두 통과시킵니다.

## Sources

> 확인 2026-11-07. React Native, Expo, FlashList, Reanimated 서술은 각 프로젝트 자체 문서에서 확인했고 version은 npm registry에서 가져왔습니다.

| 주장 | 출처 |
|---|---|
| 릴리스 빌드에서만 측정, 16.67ms 프레임 예산, 두 프레임 레이트, 문서화된 RN 수정 | [Performance Overview – React Native](https://reactnative.dev/docs/performance) |
| 프로파일링 시 dev mode off, `renderToHardwareTextureAndroid`/`shouldRasterizeIOS` 비용 | [Profiling – React Native](https://reactnative.dev/docs/profiling) |
| Hermes가 기본 엔진 | [Using Hermes – React Native](https://reactnative.dev/docs/hermes) |
| React Native 0.84부터 Hermes V1 기본 | [React Native 0.84](https://reactnative.dev/blog/2026/02/11/react-native-0.84) |
| FlashList v2 재활용과 New Architecture 대상 | [FlashList – Introduction](https://shopify.github.io/flash-list/docs/) |
| Expo Go의 `@shopify/flash-list` 지원과 권장 version | [@shopify/flash-list – Expo](https://docs.expo.dev/versions/latest/sdk/flash-list.md) |
| `expo-image`의 `cachePolicy`, `recyclingKey`, `priority`, `placeholderContentFit` | [expo-image (SDK 58)](https://docs.expo.dev/versions/latest/sdk/image.md) |
| `asyncRoutes` web 기본값, native production 동작, Hermes bytecode 주의 | [Async routes – Expo Router](https://docs.expo.dev/router/web/async-routes.md) |
| `asyncRoutes` 설정 key와 허용 값 | [expo-router API (SDK 58)](https://docs.expo.dev/versions/latest/sdk/router.md) |
| `EXPO_PUBLIC_` inline 규칙 | [Environment variables – Expo](https://docs.expo.dev/guides/environment-variables.md) |
| Expo Atlas export, JSONL 내용, Lighthouse의 web 한정 범위 | [Analyzing JS bundles with Expo Atlas and Lighthouse](https://docs.expo.dev/guides/analyzing-bundles.md) |
| Reanimated worklet과 `useAnimatedStyle`의 UI 스레드 실행 | [Reanimated glossary](https://docs.swmansion.com/react-native-reanimated/docs/fundamentals/glossary/) |
| React Compiler 적용 범위와 update 성능 목표 | [Introduction – React Compiler](https://react.dev/learn/react-compiler/introduction), [React Compiler – Expo](https://docs.expo.dev/guides/react-compiler.md) |
| 현재 package version(expo 58.0.23, react-native 0.88.1, expo-image 58.0.18, @shopify/flash-list 2.3.3) | [npm registry: expo](https://registry.npmjs.org/expo) |
