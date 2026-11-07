# Performance

> Profile release builds only, then fix the JS thread, the list, and the image cache before touching anything else.

Read this when the request names jank, slow startup, list scroll performance, memory, app size, bundle size, or "최적화" on an Expo app. This file owns the runtime engine, the list and image levers, animation cost, and the bundle-analysis loop; `rules/expo/native-platform-and-security.md` owns the native configuration around them.

## Measure first

"JavaScript thread performance suffers greatly when running in dev mode… Always make sure to test performance in release builds" [L-42], and the profiling guide opens with "make sure that Development Mode is OFF!" [L-43]. Every number below is meaningless on a dev build.

- Hermes is the default engine and needs no configuration; React Native **0.84** made Hermes V1 the default with "improved execution speed and reduced memory usage", and no migration is required for apps already on Hermes [L-44][L-45]. On SDK 58 the engine is settled, so a `useHermesV1` flag in guidance is stale.
- The frame budget is 16.67 ms at 60 fps, and there are two independent frame rates — the JS thread and the UI/main thread — so a smooth UI can still hide a blocked JS thread and vice versa [L-42].
- Record, on a release build on a real device: time to interactive for a cold start, the worst dropped-frame stretch while scrolling the heaviest list, the memory high-water mark after ten minutes of use, and the install and download size.
- Use the React Native profiler and the platform's own tooling (Xcode Instruments, Android Studio profiler) to attribute the cost to the JS thread, the UI thread, or native work before choosing a lever [L-43].

Bundle and asset weight, measured separately:

```bash
EXPO_ATLAS=true npx expo export      # writes .expo/atlas.jsonl
npx expo-atlas                       # opens the graph locally
```

The Atlas JSONL "contains the original and transformed source code of every bundled module, including the values of inlined `EXPO_PUBLIC_` environment variables", so treat the file as source and never commit or upload it [L-48]. Lighthouse covers the web target only [L-48].

## Rules

Ordered by typical impact.

1. **`official` — Get work off the JS thread before micro-optimizing it.** Reanimated worklets and `useAnimatedStyle` bodies run on the UI thread, and shared values synchronize between the JS and UI threads [L-50]. For the built-in `Animated`, set `useNativeDriver: true`; use `LayoutAnimation` for fire-and-forget transitions [L-42]. A gesture that updates React state on every frame is the single most common jank source.
2. **`official` — Replace large `FlatList`s with FlashList v2.** FlashList "recycles components under the hood" as a drop-in replacement and targets the New Architecture, which SDK 55+ requires [L-40]. Expo SDK 58 lists `@shopify/flash-list` as supported in Expo Go with a recommended version of 2.3.2 (registry `latest` is 2.3.3) [L-39][L-70]. If a `FlatList` must stay, supply `getItemLayout` [L-42][L-47].
3. **`official` — Use `expo-image`, and set `recyclingKey` inside a recycling list.** `expo-image` is the supported image component on this SDK; `recyclingKey` exists specifically so FlashList recycling does not show the previous row's image [L-41]. `cachePolicy` defaults to `'disk'`, and on Android and iOS the disk cache "does not follow the `Cache-Control` or `Expires` headers" of the response, so a changed image needs a version query param or a new `cacheKey` [L-41].
4. **`official` — Strip `console.*` from production bundles.** Logging costs JS-thread time in release builds too, including calls inside third-party code; the documented fix is `transform-remove-console` [L-42].
5. **`official` — Animate `transform`, not layout.** Animate an image with `transform: [{ scale }]` rather than animated `width`/`height`, and use `renderToHardwareTextureAndroid`/`shouldRasterizeIOS` sparingly because the memory cost is real [L-42][L-43].
6. **`official` — Do not sell bundle splitting as a native win.** `asyncRoutes` is stable and on by default on web in SDK 58; on native it is experimental, opt-in, and development-only, and "when bundling for production on native platforms, all suspense boundaries will be disabled and there will be no loading states" [L-37]. Hermes bytecode is already memory-mapped ahead of time, so "apps using the Hermes Engine will not benefit as much from bundle splitting" [L-37]. The config key is `asyncRoutes` in the `expo-router` plugin, and changing it requires `--clear` on the Metro cache [L-37][L-38].
7. **`official` — Read `EXPO_PUBLIC_*` with static dot access only.** Values are inlined at build time and visible in the shipped bundle; `process.env['EXPO_PUBLIC_KEY']` and `const { EXPO_PUBLIC_X } = process.env` "is invalid and will not be inlined" [L-49]. A computed access silently ships `undefined` and looks like a runtime bug.
8. **`hypercore-default` — Make Expo Atlas on export plus Lighthouse on the web build the bundle-size gate.** Atlas gives the per-module graph for the native bundle; Lighthouse covers only the web target [L-48]. Record the delta for the modules a change touches, not the whole graph.
9. **`official` — Enable `experiments.reactCompiler` deliberately, and only then drop manual memoization.** The compiler improves update performance, not initial load, and Expo's implementation "will only run on application code (no node modules), and only when bundling for the client (disabled in server rendering)" [L-02][L-36]. A `useMemo` removed from a file outside that scope loses its memoization with no replacement.

## Do not

- Measure on a dev build, or on a simulator when the problem is GPU or memory bound. Dev-mode JS timing is not representative [L-42][L-43].
- Add a `useHermesV1` opt-in flag. Hermes V1 has been the default since React Native 0.84 [L-45].
- Keep a `FlatList` for a long feed because migration "might change the look", then tune `windowSize`/`removeClippedSubviews` instead of fixing the recycling [L-40][L-47].
- Use `expo-image` without `recyclingKey` inside FlashList, or expect the disk cache to re-fetch when the server changes the image behind the same URL [L-41].
- Treat `priority` on `expo-image` as a guarantee. It only orders queued loads best-effort [L-41].
- Turn on `asyncRoutes` for a native production build and promise faster startup or loading states [L-37].
- Inline `EXPO_PUBLIC_*` through bracket access or destructuring, or treat an inlined public value as a secret [L-49].
- Commit or upload `.expo/atlas.jsonl`, which contains source and inlined environment values [L-48].
- Remove `useMemo`/`useCallback`/`React.memo` from `node_modules`-adjacent code or server-rendered code and expect the compiler to cover it [L-36].

## Checklist

- [ ] Every number comes from a release build on a real device, with the engine and SDK named.
- [ ] The cost was attributed to the JS thread, the UI thread, or native work before a lever was chosen.
- [ ] No new `useHermesV1` opt-in appears; Hermes V1 is treated as the default.
- [ ] Large lists use FlashList v2, or a retained `FlatList` has `getItemLayout`.
- [ ] Every recycled list image uses `expo-image` with `recyclingKey`, and changed images carry a version param or `cacheKey`.
- [ ] Gesture-driven animation runs in a worklet or with `useNativeDriver: true`; no per-frame React state updates remain.
- [ ] Image and layout animation uses `transform`, not animated `width`/`height`.
- [ ] `console.*` is stripped from the production bundle.
- [ ] `asyncRoutes` claims are limited to the web target, and the Metro cache was cleared after the change.
- [ ] `EXPO_PUBLIC_*` uses static dot access, and `.expo/atlas.jsonl` is untracked.
- [ ] Before and after numbers exist for every claimed gain, from the same build type and device.
- [ ] The change keeps the gates in `stacks/expo/architecture-rules.md` and the checks from `rules/setup/typescript.md` passing.

## Sources

> Checked 2026-11-07. React Native, Expo, FlashList, and Reanimated statements come from each project's own documentation; versions come from the npm registry.

| Claim | Source |
|---|---|
| Release-build-only measurement, 16.67 ms frame budget, two frame rates, documented RN fixes | [Performance Overview – React Native](https://reactnative.dev/docs/performance) |
| Dev mode off for profiling, `renderToHardwareTextureAndroid`/`shouldRasterizeIOS` cost | [Profiling – React Native](https://reactnative.dev/docs/profiling) |
| Hermes as the default engine | [Using Hermes – React Native](https://reactnative.dev/docs/hermes) |
| Hermes V1 default from React Native 0.84 | [React Native 0.84](https://reactnative.dev/blog/2026/02/11/react-native-0.84) |
| FlashList v2 recycling and New Architecture target | [FlashList – Introduction](https://shopify.github.io/flash-list/docs/) |
| `@shopify/flash-list` support in Expo Go and recommended version | [@shopify/flash-list – Expo](https://docs.expo.dev/versions/latest/sdk/flash-list.md) |
| `expo-image` `cachePolicy`, `recyclingKey`, `priority`, `placeholderContentFit` | [expo-image (SDK 58)](https://docs.expo.dev/versions/latest/sdk/image.md) |
| `asyncRoutes` web default, native production behavior, Hermes bytecode note | [Async routes – Expo Router](https://docs.expo.dev/router/web/async-routes.md) |
| `asyncRoutes` config key and accepted values | [expo-router API (SDK 58)](https://docs.expo.dev/versions/latest/sdk/router.md) |
| `EXPO_PUBLIC_` inlining rules | [Environment variables – Expo](https://docs.expo.dev/guides/environment-variables.md) |
| Expo Atlas export, JSONL contents, Lighthouse web-only scope | [Analyzing JS bundles with Expo Atlas and Lighthouse](https://docs.expo.dev/guides/analyzing-bundles.md) |
| Reanimated worklets and `useAnimatedStyle` on the UI thread | [Reanimated glossary](https://docs.swmansion.com/react-native-reanimated/docs/fundamentals/glossary/) |
| React Compiler scope and update-performance target | [Introduction – React Compiler](https://react.dev/learn/react-compiler/introduction), [React Compiler – Expo](https://docs.expo.dev/guides/react-compiler.md) |
| Current package versions (expo 58.0.23, react-native 0.88.1, expo-image 58.0.18, @shopify/flash-list 2.3.3) | [npm registry: expo](https://registry.npmjs.org/expo) |
