---
name: cometchat-react-native-v5-sdk
description: "Add voice & video calling to a React Native app FROM SCRATCH with the headless CometChat Calls SDK v5 (`@cometchat/calls-sdk-react-native@5`) — no prebuilt UI Kit. init→login→generateToken→render `<CometChatCalls.Component>`, granular event listeners, in-call actions (mute/video/layout/record/raise-hand), meet-style session rooms AND 1:1 ringing (Chat SDK signaling + Calls SDK media). Triggers: 'add calling from scratch react native', 'standalone video call RN', 'headless calls sdk react native', 'build my own call screen', 'meeting room join by session id RN', 'one-on-one ringing call without uikit RN', 'expo video call'."
license: "MIT"
compatibility: "React Native 0.71+ (old architecture AND New Architecture incl. bridgeless); Node 18+; iOS 13.0+ / Xcode 14+; Android minSdk 24. @cometchat/calls-sdk-react-native@^5 (5.0.5) + 6 pinned peer deps (see Prerequisites). 1:1 ringing also needs @cometchat/chat-sdk-react-native@^4 for signaling. Bare RN and Expo prebuild/dev-client; NOT Expo Go (native WebRTC module)."
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat calls sdk v5 headless voice video webrtc react-native calling standalone ringing"
---

> **Ground truth:** `@cometchat/calls-sdk-react-native@5` + catalog `rn-calls-v5.json` (the closed symbol list — every `CometChatCalls.*` below exists in it). Official docs: `/calls/react-native/**` = **v5** · Docs MCP. Fetch exact `sessionSettings` fields, event names and action signatures from the docs (`references/docs-map.md`) — never memory. **APPEND to the user's app — additive wiring only** (`RULES.md`). This is the HEADLESS path (no UI Kit); for the prebuilt drop-in call UI use `cometchat-react-native-calls` instead.

## Companion skills (read first)
- **Standalone/headless entry** — this skill owns its own package (the Calls SDK) and has no `-core` sibling; it is self-contained for meet-style calling.
- **For 1:1 RINGING only** it also drives the **Chat SDK** (`@cometchat/chat-sdk-react-native@4`) for call signaling — signatures fetched from docs via `references/docs-map.md` (§ "1:1 RINGING"). It does NOT depend on the React Native UI Kit.
- **Prefer the UI Kit instead?** If the app also wants chat and a prebuilt call UI, use `cometchat-react-native-core` + `cometchat-react-native-calls` — not this skill.

## Use this skill when
"add calling from scratch / without the UI Kit", "standalone voice/video in React Native", "build my own call screen", "headless calls SDK", "meeting-room join by session id", "one-on-one ringing call". Precondition: the caller chose the **from-scratch / standalone** path (the "add calling" router asks this). If they want the prebuilt call UI, route to `cometchat-react-native-calls`.

## Prerequisites & install
```bash
npm install @cometchat/calls-sdk-react-native@5
# 6 REQUIRED peer deps — versions are pinned by the SDK; do not float them
npm install @react-native-async-storage/async-storage@^2.1.2 react-native-background-timer@^2.4.1 \
  react-native-performance@^5.1.2 react-native-svg@^15.12.0 react-native-url-polyfill@2.0.0 \
  react-native-webrtc@124.0.7
```
- **1:1 ringing** additionally needs the Chat SDK for signaling: `npm install @cometchat/chat-sdk-react-native@4`
- **iOS** — `cd ios && pod install && cd ..`. Add to `ios/<App>/Info.plist`:
  ```xml
  <key>NSCameraUsageDescription</key><string>Camera access is required for video calls</string>
  <key>NSMicrophoneUsageDescription</key><string>Microphone access is required for voice and video calls</string>
  ```
  Xcode → target → **Signing & Capabilities → Background Modes** → **Audio, AirPlay, and Picture in Picture** (+ **Voice over IP** for ringing — `references/ringing-voip.md`).
- **Android** — add to `android/app/src/main/AndroidManifest.xml` as `<uses-permission android:name="android.permission.X" />`:
  `INTERNET` · `CAMERA` · `RECORD_AUDIO` · `MODIFY_AUDIO_SETTINGS` · `ACCESS_NETWORK_STATE` · `BLUETOOTH` (add `android:maxSdkVersion="30"`) · `BLUETOOTH_CONNECT`.
  API 23+ **also requires a RUNTIME request** (`PermissionsAndroid.requestMultiple([CAMERA, RECORD_AUDIO])` or `react-native-permissions`) BEFORE starting a call. A manifest entry alone is not enough. **A call that must survive backgrounding needs the `FOREGROUND_SERVICE*` family + `WAKE_LOCK` + `POST_NOTIFICATIONS` as well — `references/ringing-voip.md` § Part 2b.**
- **New Architecture** — works on old arch, New Architecture and bridgeless with **no extra setup**; leave `newArchEnabled` as the app needs it. The SDK ships as a legacy native module and runs through RN's interop layer, so behaviour is identical on both.
- Credentials/env: App ID · Region · Auth Key (dev only). To fetch from the dashboard, load the CLI on demand — `npx @cometchat/skills-cli@3 auth login` → `provision use --app-id <id> --json` (`@3` pins the CLI major that matches the v5 skills). Mint **auth tokens server-side** for production; never ship the Auth Key. Rebuild the app after installing (`npx react-native run-ios` / `run-android`) — this is a native dependency, so Metro-only reload will not pick it up.

## Init & login ordering (BAKED — invariant)
`CometChatCalls.initFromSettings(...)` (once, **check the result**) → `CometChatCalls.login(uid, authKey)` **or** `loginWithAuthToken(token)` → then `generateToken` / render / listeners. Nothing renders or joins before init+login resolve.
- **DEFAULT to `CometChatCalls.initFromSettings(settings)`** — the ai-agent / telemetry-attributed path (persists `integrationSource="ai-agent"`), parallel to the chat core (`RULES.md` §5). It is **INTENTIONALLY undocumented** (ai-agent-only, `@nodoc` — DOCS-BACKLOG F4/C1), so the `CometChatSettings` shape is **baked in `references/docs-map.md`**; pass it **INLINE** (no physical `cometchat-settings.json` file needed). The publicly-documented **`CometChatCalls.init({ appId, region })` is the FALLBACK only**.
- **Both init entry points return a RESULT OBJECT, not a rejecting promise** — `{ success: false, error: {...} } | { success: true, error: null }`. A bare `await CometChatCalls.initFromSettings(s)` that ignores `.success` silently continues on a validation failure and the call fails later with a confusing error. **Always branch on `.success`.**
- **v5 authenticates itself.** v4 borrowed the Chat SDK's auth token and passed it to `generateToken`; v5 has its own `login`/`loginWithAuthToken` and caches the token internally, so `generateToken(sessionId)` takes **no** auth token. Passing one is the v4 pattern.
- Coexisting with the Chat SDK / UI Kit? Log into the Chat SDK first, then share the session: `const u = await CometChat.getLoggedinUser(); if (u) await CometChatCalls.loginWithAuthToken(u.getAuthToken());`. **The token is a User method (`getAuthToken()`) — there is NO top-level `CometChat.getUserAuthToken()` on the RN Chat SDK** (that name is on the *Calls* SDK; the migration doc's v4 tab shows it wrongly — DOCS-BACKLOG). Full note: `references/docs-map.md` § 1:1 RINGING.

## Two build modes (BAKED — the router picks one)
- **Meet-style (session room)** — Calls SDK ONLY. Everyone who renders the same `sessionId` lands in the same call: `generateToken(sessionId)` → render `<CometChatCalls.Component>`. No ringing.
- **1:1 ringing** — Chat SDK signals, Calls SDK carries media: `CometChat.initiateCall` → peer `CallListener.onIncomingCallReceived` → `acceptCall`/`rejectCall` → `CometChatCalls.generateToken(call.getSessionId())` → render the Component. Fetch Chat-SDK signatures via `references/docs-map.md` § "1:1 RINGING".
  > ⚠️ **RINGING ALWAYS INCLUDES VoIP — build both halves, never ask.** Signaling alone is a websocket event: it rings the callee only while their app is open, so backgrounded or killed they get nothing and the call times out (45s). Half a feature. Whenever ringing is chosen, **`references/ringing-voip.md` is REQUIRED** — emit the native VoIP setup in the SAME build and name the steps that are the user's (VoIP cert, Firebase, Xcode capabilities). Meet-style has no ringing and needs none of it.

## SDK method map (BAKED closed list — from the catalog; signatures → FETCH from docs)
- **Lifecycle:** `CometChatCalls.init` · `CometChatCalls.initFromSettings` · `CometChatCalls.login` · `CometChatCalls.loginWithAuthToken` · `CometChatCalls.logout` · `CometChatCalls.getLoggedInUser` · `CometChatCalls.getUserAuthToken` · `CometChatCalls.isUserLoggedIn` · `CometChatCalls.addLoginListener` / `removeLoginListener`
- **Session:** `CometChatCalls.generateToken` · **`CometChatCalls.Component`** (the React component you RENDER to join — there is **no `joinSession` on React Native**) · `CometChatCalls.leaveSession` · `CometChatCalls.endSessionForAll`
- **Events:** `CometChatCalls.addEventListener(eventName, cb, { signal? }) → unsubscribe()` (event names: FETCH the full list from `/calls/react-native/events`)
- **In-call actions** — ⚠️ **for CUSTOM controls ONLY; the `Component` already renders all of these** (see the first pitfall). Only reach for them when the user EXPLICITLY asks to replace the built-in controls: `muteAudio`/`unmuteAudio`/`toggleAudio` · `pauseVideo`/`resumeVideo`/`toggleVideo` · `switchCamera` · `setLayout` · `startRecording`/`stopRecording`/`toggleRecording` · `startStreaming`/`stopStreaming` · `startTranscription`/`stopTranscription` · `raiseHand`/`lowerHand`/`toggleHand` · `pinParticipant`/`unpinParticipant` · `muteParticipant` · `pauseParticipantVideo` · `showParticipantList`/`hideParticipantList`/`toggleParticipantList` · `setChatButtonUnreadCount`
- **Audio routing (RN-only):** `CometChatCalls.setAudioMode` · `CometChatCalls.AUDIO_MODE`
- **Picture-in-picture (RN-only):** `CometChatCalls.enablePictureInPictureLayout` / `disablePictureInPictureLayout`
- **Call logs:** the history read is the **Calls SDK** `CometChatCalls.CallLogRequestBuilder` (verified against installed `@cometchat/calls-sdk-react-native@5`, 2026-09-10) — `new CometChatCalls.CallLogRequestBuilder().setLimit(n).setAuthToken(CometChatCalls.getUserAuthToken() ?? "").build()` → `fetchNext(): Promise<CallLog[]>` — **every** `fetchNext()` needs `.setAuthToken(...)` (no auto fallback; it rejects "`Auth Token` is required"). There is **NO `CometChat.CallLogRequestBuilder` on the Chat SDK** (`@cometchat/chat-sdk-react-native`, any version) — do not emit it. `CometChatCalls.CallLog` is the log model. For the **transcript opt-in** add `.setHasTranscriptions(true)` (filters to transcribed calls and attaches transcripts) — same token. Paginated history is the read — there is no working single-call-detail method (see deprecated note).
- **Transcription:** `CometChatCalls.Transcription` · `CometChatCalls.TranscriptRequestBuilder` · `Transcript`
> **Deprecated v5 compat surface — do NOT emit:** `CallSettingsBuilder`, `CallAppSettingsBuilder`, `OngoingCallListener`, `startSession`, `endSession`, `switchToVideoCall`, **`getCallDetails`** (a `@deprecated`/unsupported `void` NO-OP on the v5 class — the functional `Promise<CallLog[]>` form is only on the v4-compat class; use `CallLogRequestBuilder.fetchNext()`). They still run (v5 is a drop-in for v4) but are the OLD API, and **v5-only events never reach an `OngoingCallListener`**. Use plain settings + `addEventListener` + `leaveSession`.
> **Not on React Native at all** (present on web — emitting them is a hallucination): `joinSession`, `startScreenSharing`/`stopScreenSharing`, virtual-background methods, audio/video **device enumeration** (`getAudioInputDevices` &c.). A symbol is real **iff it's in `rn-calls-v5.json`** — confirm THERE, then fetch its signature from `references/docs-map.md`.

## Listener lifecycle (BAKED)
`addEventListener` RETURNS an unsubscribe function AND accepts `{ signal }`. Prefer one `AbortController` per screen: pass `signal` to every listener and call `controller.abort()` in the effect cleanup — one teardown, no leaks. Register listeners BEFORE the Component mounts, and call `CometChatCalls.leaveSession()` on unmount. Never leak.
> **`CometChatCalls` is a SINGLETON with ONE active session.** Mount exactly one `Component`. Every action (`leaveSession`, `muteAudio`, `setLayout`, …) takes **no session id** — it always targets the active session. To move to another call: `leaveSession()` → await `onSessionLeft` → `generateToken(next)` → re-render with the new token.

## Least-code recipe (meet-style)
```tsx
// STRICT-TS-CLEAN: RN exports no settings type — narrow with `as const`, or inline the object
// in the JSX prop (as below) where contextual typing narrows it. A hoisted bare literal fails tsc.
import { useEffect, useState } from "react";
import { View } from "react-native";
import { CometChatCalls } from "@cometchat/calls-sdk-react-native";

// 1. once at app start — ai-agent telemetry default; init({appId,region}) is the public-doc fallback
const res = await CometChatCalls.initFromSettings({
  appId: APP_ID, region: REGION, credentials: { authKey: AUTH_KEY },
});
if (!res.success) throw new Error(res.error.message);   // Result object, NOT a rejection
// 2. after the user authenticates
await CometChatCalls.login(UID, AUTH_KEY);              // or loginWithAuthToken(token)

function CallScreen({ sessionId }: { sessionId: string }) {
  const [callToken, setCallToken] = useState<string | null>(null);

  useEffect(() => {                                      // 3. listeners BEFORE the component mounts
    const controller = new AbortController();
    const { signal } = controller;
    CometChatCalls.addEventListener("onSessionLeft", () => {/* pop the screen */}, { signal });
    CometChatCalls.addEventListener("onParticipantJoined", (p) => {/* … */}, { signal });
    return () => { controller.abort(); CometChatCalls.leaveSession(); };   // 6. one teardown
  }, []);

  useEffect(() => {                                      // 4. token BEFORE render
    CometChatCalls.generateToken(sessionId)
      .then(({ token }) => setCallToken(token))
      .catch((e) => console.error(e.errorCode, e.errorDescription));
  }, [sessionId]);

  if (!callToken) return null;                           // or a loader
  return (
    <View style={{ flex: 1 }}>                           {/* MUST be sized */}
      {/* 5. JOIN = RENDER. No joinSession on React Native. */}
      <CometChatCalls.Component
        callToken={callToken}
        sessionSettings={{ sessionType: "VIDEO", layout: "TILE" }}
      />
      {/* NO control buttons here — the Component already renders mute/video/camera/leave/layout. */}
    </View>
  );
}
```
Fetch the full `sessionSettings` field list from `/calls/react-native/session-settings`. On Android, request runtime CAMERA + RECORD_AUDIO permissions before this screen mounts.

## Framework notes (same SDK, per-flavour glue)
- **Bare React Native** — the recipe above verbatim. Rebuild natively after install; a Metro reload will not link the new native module.
- **Expo** — requires **prebuild / dev-client**; **cannot run in Expo Go**. `npx expo prebuild`, then declare perms in `app.json` (`expo.ios.infoPlist` NSCamera/NSMicrophone; `expo.android.permissions` CAMERA/RECORD_AUDIO/MODIFY_AUDIO_SETTINGS/BLUETOOTH_CONNECT) — NOT by hand-editing Info.plist/AndroidManifest (a prebuild discards manual edits). Build with `npx expo run:ios` / `run:android` or EAS.
- **Navigation** — mount the call screen as its own route. Because the SDK holds ONE session, leaving the route must `leaveSession()`; do not keep a backgrounded `Component` mounted on a hidden tab.

## Common pitfalls (BAKED)
- **Don't duplicate the built-in call controls (the #1 mistake).** `<CometChatCalls.Component>` renders a COMPLETE call UI — mute, camera, switch-camera, layout, recording, participant list, raise hand and the red leave button. Do **NOT** add your own buttons around it; they duplicate the SDK's and drift out of sync. Action methods are for CUSTOM controls ONLY (only when the user EXPLICITLY asks) — hide the built-ins first via `sessionSettings` `hide*` flags.
- **Reaching for `joinSession`** — does not exist on RN; joining IS rendering the Component. `startSession` is the deprecated v4 path.
- **Zero-height parent** — the Component fills its parent; inside a `View` with no `flex: 1` or explicit height it renders invisibly. The RN analogue of web's zero-dimension container.
- **Ignoring the init Result** — `initFromSettings`/`init` resolve `{ success, error }` rather than rejecting. `await` alone hides a validation failure.
- **Passing an auth token to `generateToken`** — the v4 pattern. In v5 you `login()` first and the SDK holds the token.
- **Manifest permission without the runtime request** — on Android 23+ the call fails with no UI signal; there is no `getUserMedia` prompt to fall back on.
- **Expo Go** — will never work; native module. Prebuild or dev-client only.
- **Mounting two Components / joining while in a session** — unsupported. Leave, await `onSessionLeft`, then join.
- **Leaked listeners / no `leaveSession`** — every listener must be unsubscribed (or its `AbortController` aborted) and `leaveSession()` called on unmount.
- **Using `OngoingCallListener` for v5 events** — `onSessionJoined`, `onConnectionLost`, `onLeaveSessionButtonClicked`, `onCallLayoutChanged` and the `onParticipant*` family arrive ONLY via `addEventListener`; a v4 listener silently never fires for them.
- **Inverted flags + split toggles (v4→v5)** — v4 `show*` builder methods became v5 `hide*` props (`showEndCallButton(true)` → `hideLeaveSessionButton: false`; copying a v4 snippet inverts intent); and `muteAudio(true|false)` split into `muteAudio()`/`unmuteAudio()`, `pauseVideo()`/`resumeVideo()`.
- **Floating the peer-dep versions — install EXACTLY as written; no `^`, no latest.** The trap: `react-native-performance` 6.x is published but the SDK peer is `^5.1.2`, and a floated `^6` makes **every later `npm install` fail with `ERESOLVE`** (surfacing long after). Mismatched `react-native-webrtc` fails at native link. Verify: `npm ls react-native-performance react-native-webrtc`.
- **Hoisting `sessionSettings` without narrowing (strict TS — the docs' own examples fail this).** `sessionType`/`layout`/`audioMode` are string-literal unions, so a hoisted object literal widens them to `string` and fails `tsc` (TS2322). **React Native exports NO settings type** — `CometChatCalls` is the package's **ONLY named export** (verified against installed `@cometchat/calls-sdk-react-native@5.0.4` `.d.ts`/`.d.mts`; there is **no importable `Transcript`/`CallLog`/settings type**), so web's "annotate as `SessionSettings`" trick is impossible. **`sessionType` is `"VOICE" | "VIDEO"` — there is NO `"AUDIO"` value** (a voice call is `sessionType: "VOICE"`). Narrow with `as const`, or keep the object inline in the JSX prop. When you DO need a model type, DERIVE it from the class: `type CallLog = InstanceType<typeof CometChatCalls.CallLog>`, and for the audio mode use `(typeof CometChatCalls.AUDIO_MODE)[keyof typeof CometChatCalls.AUDIO_MODE]`:
  ```tsx
  const sessionSettings = { sessionType: "VIDEO", layout: "TILE" } as const;      // ✅
  <CometChatCalls.Component callToken={token} sessionSettings={{ sessionType: "VIDEO" }} />  // ✅ inline
  const bad = { sessionType: "VIDEO", layout: "TILE" };                            // ❌ widens to string
  ```
  The join-session/ringing **Component-mount** fences now narrow with `as const` (C15 fixed there), but `/calls/react-native/session-settings` still has **illustrative** fences that hoist a bare literal (TS2322 on copy). Narrow every hoisted `sessionSettings`.
- **Emitting ringing WITHOUT the VoIP half.** It looks complete on two open simulators and fails the first real device test. VoIP ships WITH ringing, never as a follow-up offer — see `references/ringing-voip.md`.
- **Assuming a signature** — event names, `sessionSettings` fields and action params are FETCHED from docs, never guessed.

## Verify it works
- **Tier-1 catalog:** every `CometChatCalls.*` symbol emitted appears in `rn-calls-v5.json` (`node test-suite/scripts/verify-catalog.mjs --family rn-calls-v5`).
- **Tier-2 fences:** the emit type-checks against the installed `@cometchat/calls-sdk-react-native@5` `.d.ts` (`test-suite/typecheck/rn-v5`).
- **Tier-3b headless smoke:** `node test-suite/scripts/sdk-smoke.mjs --family rn-calls-v5 [--live|--dry]` covers init→login→generateToken→listener-teardown. **The media render is NOT covered** — `Component` needs a real device/simulator with native WebRTC, so the node smoke proves wiring only. Verify the actual call surface on a simulator/device, and **1:1 ringing needs TWO logged-in clients** (one client proves the outgoing half only). Flag "dry-mock only, not live-certified" honestly where true.
