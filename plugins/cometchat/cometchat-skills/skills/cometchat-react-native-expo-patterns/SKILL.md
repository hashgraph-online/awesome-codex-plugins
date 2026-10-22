---
name: cometchat-react-native-expo-patterns
description: "Expo-specific wiring for the CometChat React Native UI Kit v5 — why Expo Go cannot work, development builds, app.json permissions, and the Expo-only extra dependency. Triggers: CometChat in Expo, Expo chat app, expo development build CometChat, Expo Go chat not working, expo run ios CometChat."
license: "MIT"
compatibility: "Expo SDK >=53 (development builds; ships React Native 0.79 — SDK 52 ships RN 0.76, below the pack's RN floor); React Native >=0.77; @cometchat/chat-uikit-react-native ^5.4.0"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "chat cometchat react-native expo development-build app-json permissions"
---

> **Ground truth:** `@cometchat/chat-uikit-react-native@5` + catalog `rn-v5.json`.
> Docs: `/ui-kit/react-native/expo-integration` · `expo-conversation` · `expo-tab-based-chat`.

## Companion skills (read first)
- `cometchat-react-native-core` — install, provider chain, init→login→render. Assumed, not repeated here.
- `cometchat-react-native-bare-patterns` — the bare React Native CLI equivalent. Use that one, not this, for a non-Expo app.

## Use this skill when
- the project has `app.json`/`app.config.js` with an `expo` key, or `expo` in `package.json`
- "add chat to my Expo app" · "chat isn't working in Expo Go"

## Prerequisites & install

### ⚠️ Expo Go does not work — and this is the #1 support issue
The UI Kit ships **custom native modules**. Expo Go is a fixed prebuilt binary that cannot load them.
There is no workaround, no config flag, and nothing to fix in code. You need a **development build**.

Symptom: the app runs in Expo Go but chat screens crash or render nothing, with a NativeModule error
that names `gesture-handler` / `svg` / `video` rather than CometChat — so it reads as unrelated.

```bash
npx expo run:ios      # or: npx expo run:android
```

Both produce a development build. From then on use that build, not Expo Go.

### Packages
Same list as bare RN, **plus `punycode`, which is Expo-only**:

```bash
npm install @cometchat/chat-uikit-react-native@5 @cometchat/chat-sdk-react-native@4
npm install @react-native-clipboard/clipboard \
  react-native-svg react-native-video react-native-localize react-native-gesture-handler \
  react-native-safe-area-context @react-native-async-storage/async-storage@^2.1.2 dayjs punycode
```

## Native config lives in `app.json` — never in ios/ or android/

This is the whole Expo/bare divergence: Expo **generates** the native projects, so hand-editing
`Info.plist` or `AndroidManifest.xml` is pointless — the next prebuild overwrites it. Declare
permissions in `app.json` and let Expo write them:

```json
{
  "expo": {
    "ios": {
      "infoPlist": {
        "NSCameraUsageDescription": "Camera access for video calls",
        "NSMicrophoneUsageDescription": "Microphone access for voice/video calls"
      }
    },
    "android": {
      "permissions": [
        "android.permission.INTERNET",
        "android.permission.CAMERA",
        "android.permission.MODIFY_AUDIO_SETTINGS",
        "android.permission.RECORD_AUDIO",
        "android.permission.ACCESS_NETWORK_STATE",
        "android.permission.BLUETOOTH_CONNECT",
        "android.permission.VIBRATE"
      ]
    }
  }
}
```
- **`BLUETOOTH_CONNECT`** (Android 12+) lets calls route audio to a Bluetooth headset — `/calls/react-native/setup` lists it; the calls SDK's own manifest only merges the legacy `BLUETOOTH`.
- **No `READ_`/`WRITE_EXTERNAL_STORAGE`**, though the `expo-integration` page lists them: they are no-ops on modern Android (WRITE from 11, READ from 13), and the UI Kit's own manifest already merges them for older devices.

After changing `app.json`, **rebuild** — a JS reload will not pick up a native permission change.

## Calling on Expo
Calling adds native WebRTC, so it needs a fresh development build too:

```bash
npm install @cometchat/calls-sdk-react-native@5
# 6 REQUIRED peer deps — the calls SDK's declared peerDependencies. Pinned; do NOT float them.
npm install @react-native-async-storage/async-storage@^2.1.2 react-native-background-timer@^2.4.1 \
  react-native-performance@^5.1.2 react-native-svg@^15.12.0 react-native-url-polyfill@2.0.0 \
  react-native-webrtc@124.0.7
npx expo run:ios
```
⚠️ `react-native-url-polyfill` + `react-native-performance` are **bundle-critical** (the UIKit
module-scope `require()`s the calls SDK, so Metro resolves its peers even in a chat-only build — a
missing one fails the bundle). Keep `react-native-performance` on **5.x** (a floated `^6` breaks every
later `npm install` with ERESOLVE). `@react-native-community/netinfo` / `react-native-callstats` are
NOT declared peers — do not add them.

Simulators cannot capture camera or microphone — verify calls on a real device.

## What is the same as bare RN
Everything above the native layer: the provider chain, `init → login → render`, every component,
theming, navigation. Only install and native config differ. Do not re-derive app code per toolchain.

## Common pitfalls
1. **Testing in Expo Go** — custom native modules cannot load. Development build, always.
2. **Editing `ios/` or `android/` directly** — prebuild overwrites it. Use `app.json`.
3. **Forgetting `punycode`** — Expo-only, and its absence surfaces as an unrelated module error.
4. **Reloading JS after an `app.json` change** — native config needs a rebuild.
5. **Expecting calls to work on a simulator** — no camera or mic capture.

## Verify it works
- The app runs from a development build, not Expo Go.
- `npm run verify:fences:rn-v5` is green.
- On device: chat renders, the composer survives the keyboard, gestures respond, and — if calling is
  installed — the permission prompts appear on first call.
