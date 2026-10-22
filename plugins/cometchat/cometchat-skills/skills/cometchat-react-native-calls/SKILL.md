---
name: cometchat-react-native-calls
description: "Voice and video calling in the CometChat React Native UI Kit v5 — the RN calls SDK, the native permissions and version floors it needs, and why installing the package is itself the enable switch. Triggers: add video calling React Native, CometChat voice call RN, incoming call screen RN, calls not ringing React Native, webrtc CometChat."
license: "MIT"
compatibility: "React Native >=0.77; @cometchat/chat-uikit-react-native ^5.4.0; @cometchat/calls-sdk-react-native ^5.0.4; Android minSdk 24; iOS 13.0"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "chat cometchat react-native calls voice video webrtc permissions"
---

> **Ground truth:** `@cometchat/calls-sdk-react-native@5` + catalog `rn-calls-v5.json` (58 symbols) +
> `features.rn-v5.json` → `voice-video-calls`. Docs: `/ui-kit/react-native/calling-integration` ·
> `call-features` · `call-buttons` · `call-logs` · `incoming-call` · `outgoing-call`.

## Companion skills (read first)
- `cometchat-react-native-core` — install, provider chain, init→login→render. Assumed, not repeated here.

## Use this skill when
- "add voice/video calling" · "incoming call screen" · "calls aren't ringing" · "call logs"

## Prerequisites & install

⚠️ **React Native has its OWN calls SDK.** `@cometchat/calls-sdk-javascript` is the web package and
will not work here.

```bash
npm install @cometchat/calls-sdk-react-native@5
# 6 REQUIRED peer deps — the SDK's declared peerDependencies. Versions are pinned; do NOT float them.
npm install @react-native-async-storage/async-storage@^2.1.2 react-native-background-timer@^2.4.1 \
  react-native-performance@^5.1.2 react-native-svg@^15.12.0 react-native-url-polyfill@2.0.0 \
  react-native-webrtc@124.0.7
# ⚠️ react-native-performance MUST stay 5.x — 6.x is published, and a floated `^6` makes every later
#    `npm install` in the app fail with ERESOLVE. react-native-url-polyfill + react-native-performance
#    are BUNDLE-critical: the UIKit does a module-scope require() of the calls SDK, so Metro resolves
#    them even for a chat-only build — omit either and the bundle fails with "Unable to resolve module".
#    (NOT react-native-community/netinfo or react-native-callstats — those are not declared peers.)
cd ios && pod install && cd ..     # bare RN;  Expo: npx expo run:ios
```

## Enabling calls — there is no flag

**Installing the package IS the switch.** The kit does a `try { require("@cometchat/calls-sdk-react-native") }`
at startup; if it resolves, calling is enabled automatically.

React's `setCallingEnabled(true)` **does not exist in this kit** — do not emit it. There is likewise **no
opt-out on the `initFromSettings` golden path** — the `CometChatSettings` file/object has no calling field,
and `CometChatUIKit.initFromSettings()` never reads one. `disableCalling: true` exists **only** as a field
on the `UIKitSettings` object you pass to the legacy `CometChatUIKit.init(uiKitSettings)` — so to disable
calling while the package stays installed you must switch to that `init()` entry point (or simply not
install the calls SDK).

Consequence worth knowing: a half-finished install (package added, pods not run) can leave calling
"enabled" in JS while the native side is missing — which surfaces as a crash on first call rather than
a clear error at startup.

## Native floors — below these it will not build

| Platform | Requirement | Where |
|---|---|---|
| Android | `minSdkVersion 24` | `android/app/build.gradle` |
| iOS | `IPHONEOS_DEPLOYMENT_TARGET` 13.0 | Xcode target or a Podfile `post_install` |

## Permissions — camera and microphone

**Bare RN** — `ios/<App>/Info.plist`:
```xml
<key>NSCameraUsageDescription</key><string>Camera access for video calls</string>
<key>NSMicrophoneUsageDescription</key><string>Microphone access for voice/video calls</string>
```
Android: `CAMERA` · `RECORD_AUDIO` · `MODIFY_AUDIO_SETTINGS` · `BLUETOOTH_CONNECT` (Android 12+, Bluetooth audio routing) in `AndroidManifest.xml`.

**Expo** — the same values go in `app.json` (`ios.infoPlist`, `android.permissions`), then rebuild.
Never hand-edit the generated native projects.

## Components (from `catalogs/rn-v5.json`)

| Component | Purpose |
|---|---|
| `CometChatCallButtons` | audio/video triggers — the message header shows these by default |
| `CometChatIncomingCall` | the ring screen — **mount once above the navigator** |
| `CometChatOutgoingCall` | the dialling screen |
| `CometChatOngoingCall` | the in-call surface (**no React equivalent**) |
| `CometChatCallLogs` | call history **list** |

`CometChatIncomingCall` mounted inside one screen means calls only arrive while that screen is open —
the commonest "calls don't ring" cause after a missing permission.

The table above is not enough to copy — wire it:

```tsx
// App.tsx — IncomingCall sits ABOVE the navigator so a call rings on any screen.
function App() {
  const incomingCall = useRef<CometChat.Call | null>(null);
  const [callReceived, setCallReceived] = useState(false);

  useEffect(() => {
    const listenerId = "APP_CALL_LISTENER";
    CometChat.addCallListener(
      listenerId,
      new CometChat.CallListener({
        onIncomingCallReceived: (call) => {
          incomingCall.current = call;
          setCallReceived(true);
        },
        onOutgoingCallRejected: () => setCallReceived(false),
        onIncomingCallCancelled: () => setCallReceived(false),
      }),
    );
    return () => CometChat.removeCallListener(listenerId);   // or it fires after unmount
  }, []);

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <NavigationContainer>{/* … */}</NavigationContainer>
      {callReceived && incomingCall.current ? (
        <CometChatIncomingCall
          call={incomingCall.current}
          onDecline={() => { incomingCall.current = null; setCallReceived(false); }}
        />
      ) : null}
    </GestureHandlerRootView>
  );
}
```

```tsx
// Call triggers — the message header renders these by default; mount them yourself only
// when you build a custom header. onError is the ONLY callback: success is an event
// (ccOutgoingCall), not a promise.
<CometChatCallButtons user={user} group={group} onError={(e) => console.error(e)} />

// Dialling screen — driven by the Call object you created.
{call && <CometChatOutgoingCall call={call} />}

// Call history list. Detail screens do NOT ship (see below).
<CometChatCallLogs onItemPress={(log) => openCallDetail(log)} />
```

```tsx
// The in-call surface. sessionID comes from the accepted Call; callSettingsBuilder is a
// CometChatCalls builder, NOT a chat-SDK one.
<CometChatOngoingCall
  sessionID={sessionId}
  callSettingsBuilder={callSettings}
  onError={(e) => console.error(e)}
/>
```

> **DOCS GAP (RN-G15 — narrowed upstream, verified 2026-09-09):** `CometChatOngoingCall` is exported by
> the RN kit and is now **listed** on `/ui-kit/react-native/call-features` (the Components row), but it
> still has **no dedicated props page** — only Incoming / Outgoing / Buttons / Logs get their own pages.
> The fence above is a **STOPGAP built from the kit's own types** — replace it once a props page ships.
> Flagged for the docs team; do not conclude the component is unavailable on RN.

## Call logs: the list ships, the detail screens do not
Kit v5 removed `CometChatCallLogDetails` / `History` / `Participants` / `Recordings`. For a custom detail
view, fetch the history yourself with the **Calls-SDK** `CallLogRequestBuilder` — a static on
`CometChatCalls`, reachable only from `@cometchat/calls-sdk-react-native`:

```ts
// Call history — CometChatCalls.CallLogRequestBuilder from the CALLS SDK.
// There is NO CallLogRequestBuilder on the Chat SDK (@cometchat/chat-sdk-react-native).
import { CometChat } from "@cometchat/chat-sdk-react-native";
import { CometChatCalls } from "@cometchat/calls-sdk-react-native";
// fetchNext() REJECTS without an auth token ("`Auth Token` is required") — no fallback. Pass the
// logged-in user's token, exactly as the kit's own CometChatCallLogs does.
const authToken = (await CometChat.getLoggedinUser())?.getAuthToken() ?? "";
const req = new CometChatCalls.CallLogRequestBuilder().setLimit(30).setAuthToken(authToken).build();
const logs = await req.fetchNext();

// Transcript opt-in — same builder + token. setHasTranscriptions(true) filters to transcribed calls
// AND makes the server attach each call's transcripts to the log.
const treq = new CometChatCalls.CallLogRequestBuilder().setLimit(30).setAuthToken(authToken).setHasTranscriptions(true).build();
```

> **RN-G9 (verified 2026-09-10 vs `@cometchat/calls-sdk-react-native@5`):** `CallLogRequestBuilder` is a
> static on `CometChatCalls` (calls SDK) — `new CometChatCalls.CallLogRequestBuilder()`. It does **not**
> exist on the Chat SDK: there is no `CometChat.CallLogRequestBuilder` in `@cometchat/chat-sdk-react-native`
> (any version). Use the Calls-SDK builder for history, always with `.setAuthToken(...)` (without it `fetchNext()`
> rejects — verified in `@cometchat/calls-sdk-react-native@5.0.5`); add `setHasTranscriptions(true)` only when you need
> transcripts. It is reachable as a static on the module, not as a bare named import.

## Verification requires a real device
**Simulators and emulators cannot capture camera or microphone.** A green simulator run proves the
screens render, not that a call connects. Media, permissions and ringing must be checked on hardware.

## Common pitfalls
1. **Installing the web calls SDK** — wrong package.
2. **Emitting `setCallingEnabled(true)`** — does not exist; installation is the switch.
3. **`CometChatIncomingCall` inside a screen** — calls only ring there.
4. **Skipping `pod install` / rebuild** — crash on first call, not at startup.
5. **Below the version floors** — build failure, not a runtime message.
6. **Signing off from a simulator** — no media capture.

## Verify it works
- Every emitted symbol is in `catalogs/rn-v5.json` or `catalogs/rn-calls-v5.json`.
- `npm run verify:fences:rn-v5` is green.
- **On two real devices:** call connects both ways, permission prompts appear on first use, the
  incoming screen shows while the app is on any tab, and the call log records the call.
