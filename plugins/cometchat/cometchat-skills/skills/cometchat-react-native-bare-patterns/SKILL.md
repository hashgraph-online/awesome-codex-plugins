---
name: cometchat-react-native-bare-patterns
description: "Bare React Native CLI wiring for the CometChat UI Kit v5 — pod install, Android manifest permissions, and the gesture-handler import that must be the first line of your entry file. Triggers: CometChat React Native CLI, pod install CometChat, RN chat crashes on Android build, gesture handler crash release build, AndroidManifest CometChat permissions."
license: "MIT"
compatibility: "React Native >=0.77 (CLI / bare); @cometchat/chat-uikit-react-native ^5.4.0"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "chat cometchat react-native cli bare pods gradle manifest gesture-handler"
---

> **Ground truth:** `@cometchat/chat-uikit-react-native@5` + catalog `rn-v5.json`.
> Docs: `/ui-kit/react-native/react-native-cli-integration` · `react-native-conversation` ·
> `react-native-tab-based-chat`.

## Companion skills (read first)
- `cometchat-react-native-core` — install, provider chain, init→login→render. Assumed, not repeated here.
- `cometchat-react-native-expo-patterns` — the Expo equivalent. Use that one for an Expo project.

## Use this skill when
- the project has real `ios/` and `android/` directories and **no** `expo` key in `app.json`
- "add chat to my React Native CLI app" · "Android build fails after installing CometChat"

## Prerequisites & install

```bash
npm install @cometchat/chat-uikit-react-native@5 @cometchat/chat-sdk-react-native@4
npm install @react-native-clipboard/clipboard \
  react-native-svg react-native-video react-native-localize react-native-gesture-handler \
  react-native-safe-area-context @react-native-async-storage/async-storage@^2.1.2 dayjs
cd ios && pod install && cd ..
```

You own `ios/` and `android/`, so native config is edited **directly** — the opposite of Expo, where
those directories are generated and hand-edits get overwritten.

## The four native steps that are not optional

### 1. `react-native-gesture-handler` must be the FIRST import of your entry file
```js title="index.js"
import 'react-native-gesture-handler';
// …every other import after this
```
Not at the top of a screen — the **very top of `index.js`**, before anything else. Getting this wrong
often works in debug and **crashes in release**, which is the worst possible failure shape: it passes
local testing and breaks for users.

### 2. iOS Podfile needs modular headers for two transitive pods
`@cometchat/chat-uikit-react-native` is a **Swift** pod that depends on `SPTPersistentCache`
and `DVAssetLoaderDelegate`, neither of which defines a module. On a static-library build —
the React Native default — `pod install` **fails outright**:

> The Swift pod `react-native-cometchat-ui-kit` depends upon `SPTPersistentCache` and
> `DVAssetLoaderDelegate`, which do not define modules.

Add these inside your target in `ios/Podfile`, then re-run `pod install`:

```ruby title="ios/Podfile"
target 'YourApp' do
  pod 'SPTPersistentCache', :modular_headers => true
  pod 'DVAssetLoaderDelegate', :modular_headers => true
  # …
end
```

Both official CometChat sample apps carry exactly these two lines. The integration docs do
not mention them (**RN-G14**), so a first `pod install` fails with an error that names two
pods the developer has never heard of.

### 3. Android permissions in the manifest
`android/app/src/main/AndroidManifest.xml` — `INTERNET` at minimum; the camera/audio set only if you
add calling. Fetch the exact list from the integration page rather than copying a partial set.

## Calling on bare RN
```bash
npm install @cometchat/calls-sdk-react-native@5
# 6 REQUIRED peer deps — the calls SDK's declared peerDependencies. Pinned; do NOT float them.
npm install @react-native-async-storage/async-storage@^2.1.2 react-native-background-timer@^2.4.1 \
  react-native-performance@^5.1.2 react-native-svg@^15.12.0 react-native-url-polyfill@2.0.0 \
  react-native-webrtc@124.0.7
cd ios && pod install && cd ..
```
⚠️ `react-native-url-polyfill` + `react-native-performance` are **bundle-critical** (the UIKit
module-scope `require()`s the calls SDK, so Metro resolves its peers even in a chat-only build). Keep
`react-native-performance` on **5.x** (a floated `^6` breaks later `npm install` with ERESOLVE).
`@react-native-community/netinfo` / `react-native-callstats` are NOT declared peers — do not add them.

iOS permissions go in `ios/<YourApp>/Info.plist`:

```xml
<key>NSCameraUsageDescription</key>
<string>Camera access for video calls</string>
<key>NSMicrophoneUsageDescription</key>
<string>Microphone access for voice/video calls</string>
```

Simulators cannot capture camera or microphone — verify calls on a real device.

## After any native change — rebuild, don't reload
Metro reload only refreshes JavaScript. A new native module, a Gradle edit or a plist change needs a
full rebuild (`npx react-native run-ios` / `run-android`). "I installed it and nothing changed" is
almost always a missed rebuild.

## What is the same as Expo
Everything above the native layer: providers, `init → login → render`, components, theming,
navigation. Only install and native config differ.

## Common pitfalls
1. **`gesture-handler` imported late** — works in debug, crashes in release.
2. **Missing the Podfile modular-headers lines** — `pod install` fails, naming two unfamiliar transitive pods.
3. **Skipping `pod install`** after adding a package — iOS fails to link.
4. **Reloading instead of rebuilding** after a native change.
5. **Copying Expo's `app.json` permission block** into a bare app — it does nothing there.

## Verify it works
- `index.js` starts with the gesture-handler import.
- iOS and Android both build clean from scratch.
- `npm run verify:fences:rn-v5` is green.
- On device: chat renders, gestures respond, the composer survives the keyboard. Test a **release**
  build too — the gesture-handler ordering bug only shows there.
