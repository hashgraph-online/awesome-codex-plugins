# dependencies — the exact React Native peer set

Verified against `@cometchat/chat-uikit-react-native@5.4.0` `package.json` + the integration pages.
**Take this list verbatim — do not infer it.** A missing native module fails at **mount**, not at
build, and the error names the peer (`gesture-handler`, `svg`, `video`), never CometChat.

```bash
npm install @cometchat/chat-uikit-react-native@5 @cometchat/chat-sdk-react-native@4
npm install @react-native-clipboard/clipboard \
  react-native-svg react-native-video react-native-localize react-native-gesture-handler \
  react-native-safe-area-context @react-native-async-storage/async-storage@^2.1.2 dayjs
```

**Expo also needs `punycode`.** Bare RN then needs `cd ios && pod install`; Expo needs a fresh
development build (`npx expo run:ios`) — **Expo Go cannot load custom native modules.**

## Native config that is NOT optional

| Platform | Requirement | Failure if missed |
|---|---|---|
| bare RN, iOS | two `modular_headers` lines in `ios/Podfile` (below) | **`pod install` fails outright** |
| bare RN, both | `import 'react-native-gesture-handler'` as the **first line of `index.js`** | works in debug, **crashes in release** |
| Expo | permissions in `app.json` (never in `ios/`/`android/` — prebuild overwrites them) | permission prompts never appear |

```ruby title="ios/Podfile"
target 'YourApp' do
  pod 'SPTPersistentCache', :modular_headers => true
  pod 'DVAssetLoaderDelegate', :modular_headers => true
  # …
end
```

The kit is a **Swift** pod depending on two pods that define no module, so a static-library build —
the RN default — cannot link it. Both official CometChat sample apps carry exactly these two lines;
the integration docs do not mention them (**RN-G14**).

## Optional — calling
```bash
npm install @cometchat/calls-sdk-react-native@5
# 6 REQUIRED peer deps — the calls SDK's declared peerDependencies. Pinned; do NOT float them.
npm install @react-native-async-storage/async-storage@^2.1.2 react-native-background-timer@^2.4.1 \
  react-native-performance@^5.1.2 react-native-svg@^15.12.0 react-native-url-polyfill@2.0.0 \
  react-native-webrtc@124.0.7
```
⚠️ **Not** `@cometchat/calls-sdk-javascript` — that is the web package.
⚠️ **`react-native-url-polyfill` + `react-native-performance` are BUNDLE-critical**, not runtime-optional:
the UIKit does a module-scope `require("@cometchat/calls-sdk-react-native")` (`CallingPackage.ts`), so
Metro resolves the calls SDK's peers even for a **chat-only** build — if the calls SDK is present in
`package.json`, a missing `url-polyfill`/`performance` fails the Metro bundle with "Unable to resolve module".
⚠️ Keep `react-native-performance` on **5.x** — 6.x is published and a floated `^6` makes every later
`npm install` fail with ERESOLVE. (`@react-native-community/netinfo` and `react-native-callstats` are
NOT declared peers of the calls SDK — do not add them for calling.)
Floors: Android `minSdkVersion 24`, iOS deployment target `13.0` (the calls SDK podspec requires 13.0). Below them the build fails.

## Version floors
React Native **0.77+**. `@cometchat/chat-sdk-react-native@4` requires
`@react-native-async-storage/async-storage` (it ships as a direct dependency, but autolinking needs
it present and pod-installed).

## After any native change — rebuild
Metro reload only refreshes JavaScript. A new native module, a Gradle edit or a plist change needs a
full rebuild. "I installed it and nothing changed" is almost always a missed rebuild.
