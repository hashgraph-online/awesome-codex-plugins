# Background ringing & background calls — the native half

Two DIFFERENT problems that get confused. Read the one you need.

| Problem | You need | Page |
|---|---|---|
| Callee's phone must ring while their app is **closed** | **VoIP push** + a native dialer (CallKit / ConnectionService) | `/calls/react-native/voip-calling` |
| A call already in progress must **survive backgrounding** | Background modes + a foreground service | `/calls/react-native/background-handling` |

Foreground ringing (`onIncomingCallReceived` over the Chat SDK websocket) is in the main SKILL. It works
only while the callee's app is open. Everything below is what makes ringing behave like a real phone call.

> **Where this comes from.** Almost everything here is transcribed from the two CometChat pages above —
> the Swift/Java modules, the manifest entries, the certificate and Firebase steps, the permission lists and
> the platform-behaviour tables. Three things are **not** from those pages and are labelled **`[not in the
> doc]`** inline so you can check them yourself:
> 1. the **typed token API** (`CometChatNotifications.registerPushToken` / `PushPlatforms` /
>    `unregisterPushToken`) — read from the shipped `@cometchat/chat-sdk-react-native` `.d.ts`; the doc page
>    still shows the legacy `CometChat.registerTokenForPushNotification` (DOCS-BACKLOG **C16**);
> 2. **register-after-login / unregister-on-logout** — from the pack's own `cometchat-react-native-push`
>    skill; this page has no logout step at all;
> 3. the **`reportNewIncomingCall` termination rule** — Apple platform behaviour, not a CometChat claim.
>
> Nothing here is written from memory: if it is not on a CometChat page it is either in the SDK's types or
> labelled as outside guidance.

---

# PART 1 — Ringing a CLOSED app (VoIP push)

The Chat SDK's call listener needs a live socket. A killed or backgrounded app has none, so the server must
wake it with a **push**, and the OS must show a **native call screen**. That is platform work — not JS.

## 1a. iOS — VoIP push + CallKit

**Capabilities** (Xcode → target → Signing & Capabilities): add **Push Notifications**, add
**Background Modes**, enable **Voice over IP**.

**Certificate:** Apple Developer → Certificates, Identifiers & Profiles → create a **VoIP Services
Certificate** → download, install, export the `.p12`. Upload it (with its password) in the CometChat
Dashboard under **Notifications → Push Notifications**.

**Native module** — PushKit receives the wake-up, CallKit draws the system call UI:

```swift
// ios/CallKitManager.swift
import CallKit
import PushKit

@objc(CallKitManager)
class CallKitManager: NSObject, CXProviderDelegate, PKPushRegistryDelegate {
  static let shared = CallKitManager()
  private let provider: CXProvider
  private let callController = CXCallController()
  private var voipRegistry: PKPushRegistry?

  override init() {
    let config = CXProviderConfiguration()
    config.supportsVideo = true
    config.maximumCallsPerCallGroup = 1
    config.supportedHandleTypes = [.generic]
    provider = CXProvider(configuration: config)
    super.init()
    provider.setDelegate(self, queue: nil)
  }

  @objc func registerForVoIPPushes() {
    voipRegistry = PKPushRegistry(queue: .main)
    voipRegistry?.delegate = self
    voipRegistry?.desiredPushTypes = [.voIP]
  }

    // Token → hand to JS → CometChatNotifications.registerPushToken(token, APNS_REACT_NATIVE_VOIP)
  func pushRegistry(_ registry: PKPushRegistry, didUpdate pushCredentials: PKPushCredentials, for type: PKPushType) {
    let token = pushCredentials.token.map { String(format: "%02x", $0) }.joined()
    NotificationCenter.default.post(name: NSNotification.Name("VoIPTokenReceived"), object: nil, userInfo: ["token": token])
  }

  // The wake-up. You MUST report an incoming call here or iOS kills the app.
  func pushRegistry(_ registry: PKPushRegistry, didReceiveIncomingPushWith payload: PKPushPayload, for type: PKPushType, completion: @escaping () -> Void) {
    guard type == .voIP else { return }
    let callerId   = payload.dictionaryPayload["callerId"]   as? String ?? "Unknown"
    let callerName = payload.dictionaryPayload["callerName"] as? String ?? "Unknown"
    let hasVideo   = payload.dictionaryPayload["hasVideo"]   as? Bool   ?? false
    let update = CXCallUpdate()
    update.remoteHandle = CXHandle(type: .generic, value: callerId)
    update.localizedCallerName = callerName
    update.hasVideo = hasVideo
    provider.reportNewIncomingCall(with: UUID(), update: update) { _ in completion() }
  }

  func providerDidReset(_ provider: CXProvider) {}

  func provider(_ provider: CXProvider, perform action: CXAnswerCallAction) {
    NotificationCenter.default.post(name: NSNotification.Name("CallKitAnswerCall"), object: nil,
                                    userInfo: ["callUUID": action.callUUID.uuidString])
    action.fulfill()
  }

  func provider(_ provider: CXProvider, perform action: CXEndCallAction) {
    NotificationCenter.default.post(name: NSNotification.Name("CallKitEndCall"), object: nil,
                                    userInfo: ["callUUID": action.callUUID.uuidString])
    action.fulfill()
  }
}
```

> ⚠️ **`reportNewIncomingCall` is not optional** — **`[not in the doc]`**, this is Apple's own PushKit rule:
> iOS terminates an app that accepts a VoIP push without reporting a call. The CometChat page shows the call
> being reported but does not say why it is mandatory. Report first, then do the CometChat work.

## 1b. Android — FCM + a self-managed ConnectionService

**Firebase:** add Firebase to the Android project, then in `android/app/build.gradle`:

```groovy
dependencies { implementation 'com.google.firebase:firebase-messaging:23.0.0' }
```

Upload the Firebase server key in the CometChat Dashboard under **Notifications → Push Notifications**.

**ConnectionService** — registers the app as a self-managed dialer so the system rings:

```java
// android/app/src/main/java/com/yourapp/CallConnectionService.java
package com.yourapp;

import android.telecom.Connection;
import android.telecom.ConnectionRequest;
import android.telecom.ConnectionService;
import android.telecom.PhoneAccountHandle;
import android.telecom.TelecomManager;

public class CallConnectionService extends ConnectionService {
  @Override
  public Connection onCreateIncomingConnection(PhoneAccountHandle h, ConnectionRequest request) {
    CallConnection connection = new CallConnection();
    connection.setConnectionProperties(Connection.PROPERTY_SELF_MANAGED);
    connection.setCallerDisplayName(request.getExtras().getString("callerName"), TelecomManager.PRESENTATION_ALLOWED);
    connection.setRinging();
    return connection;
  }

  @Override
  public Connection onCreateOutgoingConnection(PhoneAccountHandle h, ConnectionRequest request) {
    CallConnection connection = new CallConnection();
    connection.setConnectionProperties(Connection.PROPERTY_SELF_MANAGED);
    connection.setDialing();
    return connection;
  }
}
```

`AndroidManifest.xml`:

```xml
<uses-permission android:name="android.permission.MANAGE_OWN_CALLS" />
<uses-permission android:name="android.permission.READ_PHONE_STATE" />

<service
    android:name=".CallConnectionService"
    android:permission="android.permission.BIND_TELECOM_CONNECTION_SERVICE"
    android:exported="true">
  <intent-filter><action android:name="android.telecom.ConnectionService" /></intent-filter>
</service>
```

## 1c. Register the token (both platforms)

> ⚠️ **`[not in the doc]` — the doc page uses the LEGACY token API.** `/calls/react-native/voip-calling` shows
> `CometChat.registerTokenForPushNotification(token, { voip: true })` — an untyped `settings` bag with no
> platform enum and no unregister counterpart. The SDK ships a **typed** replacement with a dedicated VoIP
> platform, and it is what the pack's `cometchat-react-native-push` skill uses. Prefer it. (DOCS-BACKLOG C16)

```tsx
import { CometChatNotifications } from "@cometchat/chat-sdk-react-native";

const { PushPlatforms } = CometChatNotifications;

// iOS VoIP pushes are a DIFFERENT platform from ordinary iOS pushes — an app that rings AND sends
// message notifications registers two tokens on two platforms.
async function registerVoIPToken(token: string, platform: "ios" | "android"): Promise<void> {
  try {
    await CometChatNotifications.registerPushToken(
      token,
      platform === "ios" ? PushPlatforms.APNS_REACT_NATIVE_VOIP   // the PushKit token
                         : PushPlatforms.FCM_REACT_NATIVE_ANDROID,
    );
  } catch (error) {
    console.error("VoIP token registration failed", error);
  }
}

// On logout — otherwise the next user on this device inherits the previous user's calls.
await CometChatNotifications.unregisterPushToken();
```

Register **after login** — a token registered with no logged-in user is attached to nobody. Re-register on
token refresh, and unregister on logout. **`[not in the doc]`** — this ordering comes from the pack's
`cometchat-react-native-push` skill; the VoIP page states no login ordering and has no logout step.

## 1d. Answer from the native call screen → join the session

The OS answer action comes back to JS; from there it is the SAME flow as foreground ringing:

> ⚠️ **`CallKitManager` is iOS-ONLY and emits EXACTLY three events** — `VoIPTokenReceived`,
> `CallKitAnswerCall`, `CallKitEndCall`. Subscribing to any other name throws at runtime:
> ``` `FcmTokenReceived` is not a supported event type for CallKitManager ```. In particular **the Android
> FCM token does NOT arrive through this module** — see § Android token below.

```tsx
import { useEffect } from "react";
import { NativeEventEmitter, NativeModules, Platform } from "react-native";
import { CometChat } from "@cometchat/chat-sdk-react-native";
import { CometChatCalls } from "@cometchat/calls-sdk-react-native";

export default function useVoIPPush(onToken: (t: string) => void) {
  useEffect(() => {
    if (Platform.OS !== "ios") return;                 // Android: see § Android token
    const emitter = new NativeEventEmitter(NativeModules.CallKitManager);

    // The iOS token arrives HERE — PushKit hands it to Swift, Swift posts it, this consumes it.
    // Without this listener the Swift side emits into nothing and no token is ever registered.
    const tok = emitter.addListener("VoIPTokenReceived", (d: { token: string }) => {
      void registerVoIPToken(d.token, "ios");
    });

    const answer = emitter.addListener("CallKitAnswerCall", async (data: { sessionId: string }) => {
      await CometChat.acceptCall(data.sessionId);                       // signaling
      const { token } = await CometChatCalls.generateToken(data.sessionId); // media
      onToken(token);                                                    // render <CometChatCalls.Component>
    });

    const end = emitter.addListener("CallKitEndCall", () => CometChatCalls.leaveSession());

    return () => { tok.remove(); answer.remove(); end.remove(); };
  }, [onToken]);
}
```

### Android token — a DIFFERENT source

**`[not in the doc]`** — the VoIP page says to add Firebase but never says where the token comes from. It is
**not** an event on `CallKitManager` (that module is iOS-only). It comes from your messaging library, the
same one the pack's `cometchat-react-native-push` skill uses:

```tsx
import messaging from "@react-native-firebase/messaging";

// once, after login
const fcmToken = await messaging().getToken();
await registerVoIPToken(fcmToken, "android");

// and whenever Firebase rotates it
const unsub = messaging().onTokenRefresh((t) => registerVoIPToken(t, "android"));
```

So the two platforms differ in **where the token comes from**, not in what you do with it: iOS via the
PushKit → Swift → `VoIPTokenReceived` chain, Android via `messaging().getToken()`. Both end at the same
`registerPushToken` call with their own `PushPlatforms` value.

---

# PART 2 — Keeping an ACTIVE call alive in the background

Different problem: the call already started and the user switches apps or locks the screen.

## 2a. iOS

**Background Modes** → **Audio, AirPlay, and Picture in Picture** (add **Voice over IP** too if using Part 1).
The SDK configures the audio session itself; override only if you need to:

```swift
// ios/AppDelegate.swift
import AVFoundation

try? AVAudioSession.sharedInstance().setCategory(
  .playAndRecord, mode: .voiceChat,
  options: [.allowBluetooth, .allowBluetoothA2DP, .defaultToSpeaker])
try? AVAudioSession.sharedInstance().setActive(true)
```

| Scenario | iOS behaviour |
|---|---|
| App backgrounded | Audio continues, **video pauses** |
| Phone call arrives | Call audio interrupted, resumes after |
| Screen locked | Audio continues |

## 2b. Android — the permissions most integrations miss

```xml
<uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
<uses-permission android:name="android.permission.FOREGROUND_SERVICE_MICROPHONE" />
<uses-permission android:name="android.permission.FOREGROUND_SERVICE_CAMERA" />
<uses-permission android:name="android.permission.FOREGROUND_SERVICE_MEDIA_PLAYBACK" />
<uses-permission android:name="android.permission.FOREGROUND_SERVICE_MEDIA_PROJECTION" />
<uses-permission android:name="android.permission.WAKE_LOCK" />
<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
```

Android 10+ requires a **foreground service** for a call to continue in the background. The SDK ships
`com.cometchat.calls.services.CometChatOngoingCallService` and declares it in its own manifest, so it merges
into your app automatically — **you normally declare nothing**. Only if you must override it:

```xml
<service android:name="com.cometchat.calls.services.CometChatOngoingCallService"
         android:foregroundServiceType="camera|microphone|mediaProjection|mediaPlayback" />
```

Wake locks are managed by the SDK. Do not add your own.

| Scenario | Android behaviour |
|---|---|
| App backgrounded | Audio continues **via the foreground service** |
| Phone call arrives | Call audio may be interrupted |
| Screen off | Audio continues (wake lock) |

## 2c. App-state + connection wiring

```tsx
import { useEffect, useRef } from "react";
import { AppState, AppStateStatus } from "react-native";
import { CometChatCalls } from "@cometchat/calls-sdk-react-native";

export default function useBackgroundCall(onEnded: () => void) {
  const appState = useRef(AppState.currentState);

  useEffect(() => {
    const sub = AppState.addEventListener("change", (next: AppStateStatus) => {
      if (appState.current.match(/active/) && next === "background") CometChatCalls.enablePictureInPictureLayout();
      else if (appState.current === "background" && next === "active") CometChatCalls.disablePictureInPictureLayout();
      appState.current = next;
    });
    return () => sub.remove();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const { signal } = controller;
    CometChatCalls.addEventListener("onConnectionLost", () => {}, { signal });      // show "reconnecting"
    CometChatCalls.addEventListener("onConnectionRestored", () => {}, { signal });  // hide it
    CometChatCalls.addEventListener("onConnectionClosed", onEnded, { signal });
    return () => controller.abort();
  }, [onEnded]);
}
```

---

## Verifying this — and what "verified" honestly means

**None of Part 1 can be tested here.** VoIP push needs a real device, real certificates, and the app
genuinely backgrounded or killed. It does not work on an iOS Simulator (APNs is absent), it cannot run in CI,
and the pack's `sdk-smoke` cannot mount native code. Any "ringing works" claim without a two-device run on
real hardware is **unproven** — say so rather than implying coverage.

Test matrix that actually proves it:

| Check | How |
|---|---|
| Token registered | log the token, confirm registration resolves AFTER login |
| Push arrives, app backgrounded | background the callee app, call from device 2 → native call UI appears |
| Push arrives, app KILLED | swipe the callee app away, call → app wakes and rings |
| Answer → media | accept from the OS screen → `<CometChatCalls.Component>` mounts and audio flows |
| Reject / timeout | reject, and separately let it ring out (default 45s) |
| Call survives backgrounding | during an active call, background the app → audio continues |

**Two live clients are required** for every row. Two instances of the same build on one simulator share a
session and will not ring each other.
