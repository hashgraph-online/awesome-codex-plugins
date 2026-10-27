---
name: cometchat-flutter-v5-sdk
description: "Add voice & video calling to any Flutter app FROM SCRATCH with the headless CometChat Calls SDK v5 (`cometchat_calls_sdk`, pub.dev) — no UI Kit. init→login→generateCallToken→joinSession, which hands back a Flutter `Widget?` you mount in your tree; CallSession listeners, in-call actions (mute/video/layout/record/PiP/raise-hand), meet-style session rooms AND 1:1 ringing (Chat SDK signaling + Calls SDK media). Triggers: 'add calling from scratch flutter', 'standalone video call dart', 'headless calls sdk flutter', 'build my own call screen flutter', 'meeting room join by session id flutter', 'one-on-one ringing call without uikit flutter'."
license: "MIT"
compatibility: "Flutter >=2.5.0, Dart >=2.17.0 <4.0.0 · Android minSdk 26 (Android 8.0) · iOS 15.1. cometchat_calls_sdk ^5.0.3 — resolves to 5.0.7, which this skill is verified against. 1:1 ringing also needs cometchat_sdk v5 (>=5.0.6; the pinned harness resolves 5.0.7 — the signaling symbols are identical across both) for signaling."
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat calls sdk v5 headless voice video webrtc dart flutter calling standalone"
---

> **Ground truth:** `cometchat_calls_sdk` **5.0.7 from pub.dev** + catalog `flutter-calls-v5.json` (the closed symbol list — 59 COMPILER-VERIFIED symbols; every type below is in it). Catalog built from the PUBLISHED package; at 5.0.7 it matches the `calls-core` monorepo exactly — but **never infer that from a version string** (`references/docs-map.md` § "Upstream"). Official docs: `/calls/flutter/**` = **v5** · Docs MCP. Fetch exact `SessionSettings` fields, event names and signatures from the docs (`references/docs-map.md`) — never memory. **⚠️ The live pages carry ~56 symbols that DO NOT COMPILE, including the entire documented token flow — see "Doc corrections" below; prefer THIS skill's names over the page's.** **APPEND to the user's app — additive wiring only.** This is the HEADLESS path (no UI Kit); for the prebuilt drop-in call UI use `cometchat-flutter-v6-calls` instead.

## Companion skills (read first)
- **Standalone/headless entry** — this skill owns its own package (the Calls SDK) and has no `-core` sibling; self-contained for meet-style calling.
- **For 1:1 RINGING only** it also drives the **Chat SDK** (`cometchat_sdk` v5) for signaling — signatures fetched via `references/docs-map.md` (§ "1:1 RINGING"). It does NOT depend on the Flutter UI Kit.
- **Prefer the UI Kit instead?** If the app also wants chat and a prebuilt call UI, use `cometchat-flutter-v6-core` + `cometchat-flutter-v6-calls` — not this skill.

## Use this skill when
"add calling from scratch / without the UI Kit", "standalone voice/video on Flutter", "build my own call screen", "headless calls SDK", "meeting-room join by session id", "one-on-one ringing". Precondition: the caller chose the **from-scratch / standalone** path (the "add calling" router asks this). If they want the prebuilt call UI, route to `cometchat-flutter-v6-calls`.

## Prerequisites & install
```yaml
# pubspec.yaml
dependencies:
  cometchat_calls_sdk: ^5.0.7   # verified against 5.0.7
```
then `flutter pub get`.

**1:1 ringing additionally needs the Chat SDK** (`cometchat_sdk` v5) for signaling.

**Permissions — REQUIRED or the call dies on the first permission prompt.**
- `android/app/src/main/AndroidManifest.xml`: `INTERNET`, `CAMERA`, `RECORD_AUDIO`, `MODIFY_AUDIO_SETTINGS`, `ACCESS_NETWORK_STATE`. On **API 23+ you must ALSO request camera + mic at runtime** — the manifest alone is not enough, and this is the single most common "the SDK is broken" report on Android.
- `ios/Runner/Info.plist`: `NSCameraUsageDescription` + `NSMicrophoneUsageDescription`.
- Android **`minSdkVersion 26`**, iOS **`platform :ios, '15.1'`** — the real 5.0.7 floors. **The docs say 24 and iOS 12; both fail at BUILD time.** iOS moved 13.0 → 15.1 *in 5.0.7*, so an app can break on a routine `pub upgrade`.

**Credentials:** App ID · Region · Auth Key (dev only), via the CLI — `npx @cometchat/skills-cli@3 auth login` → `provision use --app-id <id> --json` (`@3` pins the CLI major that matches the v5 skills). Mint **auth tokens server-side** for production; never ship the Auth Key.

## Init & login ordering (BAKED — invariant)
Init (once, must succeed) → `CometChatCalls.login(...)` → then `generateCallToken` / `joinSession` / listeners. Nothing joins before init+login resolve. `CometChatCalls.isInitialized` is the guard.

- **DEFAULT to `CometChatCalls.initFromSettings(onSuccess:, onError:)`** — the ai-agent / telemetry-attributed path (persists `integrationSource="ai-agent"`).

  <!-- STOPGAP: source-derived (calls-core/calls-sdk-flutter), NOT in the public docs.
       `initFromSettings` is `@nodoc` and ai-agent-only. DOCS-BACKLOG F4/D4 closed it WONTFIX —
       it is to STAY hidden, so this stopgap is permanent, not pending a docs fix. -->
  It takes **no settings argument**: it reads `cometchat-settings.json` through **`rootBundle`**, so the file must sit at the **project root** *and* be registered as a Flutter asset:
  ```yaml
  flutter:
    assets:
      - cometchat-settings.json
  ```
  Root keys `appId` + `region`; optional `callsSDK` → `adminHost`/`clientHost`/`callsHost`. **No Auth Key — the Calls SDK reads nothing else from this file** (the key is a `login()` argument). Registering it under `flutter: assets:` is the ONLY step; no Xcode or Gradle change, because it is read through `rootBundle`. Miss the `assets:` entry and init fails with settings-file-not-found — a quiet callback, not a crash.

- **Fallback (public-doc path):**
  ```dart
  CallAppSettings s = (CallAppSettingBuilder()..appId = appId..region = region).build();
  CometChatCalls.init(s, onSuccess: (String m) {}, onError: (CometChatCallsException e) {});
  ```
  Note the **Dart cascade** (`..appId =`) — these are **fields, not `setX()` methods**. `CallAppSettingBuilder` is singular (no `s`).
- ⚠️ **Never do both.** A builder init AFTER `initFromSettings` re-attributes the app to `"manual"` and the ai-agent telemetry is lost.
- **Login:** `CometChatCalls.login(uid:, authKey:, onSuccess:, onError:)` (dev) or `CometChatCalls.loginWithAuthToken(authToken:, onSuccess:, onError:)` (production). Check `await CometChatCalls.getLoggedInUser()` first — it returns `Future<User?>` and the SDK keeps the session, so logging in twice is wasted work. **Both `onSuccess` callbacks hand you a NULLABLE `User?`** — the docs dereference it unguarded; do not copy that.

## Two build modes (BAKED — the router picks one)
- **Meet-style (session room)** — Calls SDK ONLY, no Chat SDK. Everyone joining the same session id lands in the same call.
- **1:1 ringing** — Chat SDK signals, Calls SDK carries media. Needs `cometchat_sdk` v5 as well. Fetch signatures via `references/docs-map.md` § "1:1 RINGING".

## ⚠️ The Flutter fork: `joinSession` returns a WIDGET
Every other platform mounts the call into a container you hand it. **Flutter hands the call back to
you as a `Widget?`** and mounts nothing:
```dart
Widget? _callWidget;

CometChatCalls.joinSession(
  sessionId: sessionId,
  sessionSettings: settings,
  onSuccess: (Widget? w) => setState(() => _callWidget = w),   // ← THIS is the render step
  onError: (CometChatCallsException e) { /* surface it */ },
);

@override
Widget build(BuildContext c) => Scaffold(body: _callWidget ?? const CircularProgressIndicator());
```
An emit that ignores the `onSuccess` argument **joins the call successfully and shows nothing** — audio flows, no video, no controls. It reads as a broken SDK and it is the #1 Flutter-specific failure. There is no container parameter and no zero-bounds trap; there is only "did you put the widget in the tree".

## SDK method map (BAKED closed list — from the catalog; signatures → FETCH from docs)
- **Lifecycle:** `CometChatCalls.initFromSettings` · `CometChatCalls.init` · `CallAppSettingBuilder` → `CallAppSettings` · `CometChatCalls.isInitialized` · `login` · `loginWithAuthToken` · `logout` · `getLoggedInUser` → `User?`
- **Session:** `CometChatCalls.generateCallToken(sessionId, …)` → `CallToken` · `joinSession(…)` → `Widget?` · `SessionSettingsBuilder` → `SessionSettings` · `SessionType`
- **⚠️ TWO join paths, both real in 5.0.7** — pick one: `generateCallToken(sessionId)` → `joinSession(callToken:sessionSettings:)`, **or** `joinSession(sessionId:sessionSettings:)` directly.
- **In-call actions — on `CallSession.getInstance()`, for CUSTOM controls ONLY** (the returned widget already renders them; see pitfall #1): `leaveSession` · `muteAudio`/`unMuteAudio` · `pauseVideo`/`resumeVideo` · `setLayout` · `setAudioModeType` · `switchCamera` · `raiseHand`/`lowerHand` · `startRecording`/`stopRecording` · `startScreenShare`/`stopScreenShare`/`toggleScreenShare` · `pinParticipant`/`unPinParticipant` · `muteParticipant` · `pauseParticipantVideo` · `enablePictureInPictureLayout`/`disablePictureInPictureLayout` · `enterPipMode`/`isPipSupported` · `setChatButtonUnreadCount` · `isCallSessionActive`
  - **Toggles** (Flutter-only, no iOS analogue): `toggleMuteAudio` · `togglePauseVideo` · `toggleCameraSource` · `toggleRaiseHand`
  - **Aliases** for the same actions: `endCallSession` · `startCallRecording`/`stopCallRecording` · `setCallLayoutType`
  - **Settings panels:** `hideSettingsPanel` · `openCallSettingsPanel` · `openVirtualBackgroundSettingsPanel`
  - **State getters (read, don't track):** `isAudioMuted` · `isVideoPaused` · `isHandRaised` · `isRecording` · `isScreenSharing` · `isTranscribing`
- **Listeners (on `CallSession.getInstance()`; four are add/remove, `LayoutListeners` is a single-slot property):** `SessionStatusListeners` · `ParticipantEventListeners` · `MediaEventListeners` · `ButtonClickListeners` · `LayoutListeners`
- **Call logs:** `CallLogRequestBuilder` (top-level; **FIELDS, no `setX()`**) → `CallLogRequest` → `fetchNext`/`fetchPrevious` → `CallLog` (+ `CallUser`/`CallGroup`/`CallEntity`)
- **Background:** `CometChatOngoingCallService.launch()` / `.abort()` — Android foreground service, no-op on iOS
- **Enums:** `AudioMode` (`.speaker`/`.earpiece`/`.bluetooth`) · `SessionType` · `LayoutType` (`.tile`/`.spotlight`/`.sidebar`) · `CameraFacing`

> A curated highlight, **NOT the full surface**. The authoritative closed list is the **catalog** (59 symbols, each proven by a `flutter analyze` probe). A symbol is real **iff it is in the catalog** — confirm there, then fetch its signature from the page in `references/docs-map.md`.

## Listener lifecycle (BAKED)
**All five listener types are `abstract class`es you IMPLEMENT — they are NOT constructible.**
The live docs build every one of them with named callbacks
(`SessionStatusListeners(onSessionJoined: () {…})`); an abstract class cannot be instantiated, so
none of those examples compile. `flutter analyze` reports `instantiate_abstract_class`.
```dart
class _Status extends SessionStatusListeners {
  @override void onSessionJoined() { /* ... */ }
  @override void onSessionTimedOut() { /* distinct from onSessionLeft — handle BOTH */ }
  // `extends` instead of `implements` and the other four inherit their no-op bodies.
}

final _status = _Status();                                       // hoist into a FIELD
CallSession.getInstance()?.addSessionStatusListener(_status);     // BEFORE joining
// teardown:
CallSession.getInstance()?.removeSessionStatusListener(_status);  // the SAME instance
CallSession.getInstance()?.leaveSession();
```
- Every method already has a no-op body, so **`extends` lets you override only what you need**; `implements` obliges you to write them all.
- **`remove*Listener` takes the object you added.** Constructing a fresh listener to remove one is a no-op that silently leaks the original — and it is what the live docs show (D4). Hoist into a field; there is no other shape in which removal works.
- **⚠️ Registration names do NOT match the type names** — full table in `references/docs-map.md`. Two you cannot guess: `MediaEvent**Listeners**` registers via `addMediaEvent**s**Listener`, and **`LayoutListeners` has no add/remove at all** — it is a single-slot `layoutListener = l` setter, cleared with `= null`.
- **`CallSession.getInstance()` is never actually null** — the singleton is eagerly built, so registering BEFORE `joinSession` really does attach (certified: `onSessionJoined` fires). The type is still `CallSession?`, so keep `?.`; use `isCallSessionActive()` to test for a live session.
- **`ButtonClickListeners` callbacks fire alongside the SDK's own action and do NOT suppress it.** Reacting to `onLeaveSessionButtonClicked` must NOT also call `leaveSession()` — the SDK is already leaving; doing both double-leaves. Use it to run `CometChat.endCall(sessionId)` on the ringing path.
- **`Participant` has TWELVE fields, all nullable:** `uid` · `name` · `avatar` · `mid` · `state` · `isJoined` · `deviceId` · `joinedAt` · `leftAt` · `totalAudioMinutes` · `totalVideoMinutes` · `totalDurationInMinutes`. **No mute/pin/hand/share flags** — the seven the docs' "Participant Object Reference" lists (`pid`/`role`/`audioMuted`/`videoPaused`/`isPinned`/`isPresenting`/`raisedHandTimestamp`) do NOT exist and do not compile (see `doc-corrections.md`); accumulate that live state from `ParticipantEventListeners`, as iOS must. Prefer `onParticipantListChanged`, which delivers the WHOLE list. (`Participants`, plural, is a `@Deprecated` typedef alias of `Participant`.)

## Least-code recipe (meet-style — ORDER, not signatures)
```dart
// Fetch every signature/field from references/docs-map.md. This is the ORDER, which is the part that bites.
import 'package:cometchat_calls_sdk/cometchat_calls_sdk.dart';

1. CometChatCalls.initFromSettings(onSuccess:, onError:)   // ai-agent default; cometchat-settings.json as a Flutter ASSET
2. CometChatCalls.login(uid:, authKey:, onSuccess:, onError:)   // or loginWithAuthToken in production
3. final settings = (SessionSettingsBuilder()..setDisplayName(name)..setType(SessionType.video)).build();
4. CallSession.getInstance()?.addSessionStatusListener(_status);   // register BEFORE joining
5. CometChatCalls.joinSession(sessionId:, sessionSettings:, onSuccess: (Widget? w) => setState(() => _call = w), onError:)
   //   or: generateCallToken(sessionId) -> joinSession(callToken:sessionSettings:)
6. // return _call from build() — NOTHING renders until you do
7. // NO control buttons needed — the returned widget ALREADY renders mute/video/leave.
8. // teardown -> remove each listener (same instance); CallSession.getInstance()?.leaveSession()
```

## Backgrounding & call notifications → `references/platform-notes.md`
Two things that are NOT on the join path and are easy to get wrong:
- **Backgrounding** — Android kills a call the moment the app backgrounds unless
  `CometChatOngoingCallService.launch()` holds a foreground service (`.abort()` on teardown).
  **Flutter-only**; both calls are safe no-ops on iOS. The manifest permissions are not optional.
- **Ringing a closed app** — **there is no first-party CometChat Flutter push package** (iOS has
  one; Flutter does not), and **no symbol in this skill's catalog implements it**. It is FCM on
  Android and APNs/PushKit/CallKit on iOS, wired by the app. Needs a dashboard push provider and a
  **physical device**. An emit naming a `cometchat_push_notifications` Flutter package invented it.

## Doc corrections (⚠️ the live pages do not compile — full table: `references/doc-corrections.md`)
**23 classes of symbol** on `/calls/flutter/**` fail `flutter analyze` against 5.0.7. Read
`references/doc-corrections.md` before copying off a page. The two that bite hardest:

| The docs write | It does not compile — use |
|---|---|
| `generateToken(sessionId: …)` → `CallToken` (13 pages) | **`generateCallToken(sessionId, onSuccess:, onError:)`** → `CallToken`. `generateToken` is `@Deprecated`, takes two POSITIONAL args, and yields `GenerateToken`. **No page mentions `generateCallToken` at all** |
| `Participant.pid` / `.role` / `.audioMuted` / `.videoPaused` / `.isPinned` / `.isPresenting` / `.raisedHandTimestamp` | **None exist.** `Participant` has 7 fields; track the rest from events |

Docs PR cometchat/docs#492 fixes the first seven classes (56 → 3 analyzer errors). **Five more —
including the abstract-listener one — were found by running `flutter analyze` over this skill's
own harness AFTER #492 was open, and are not in it.** 12 fences on those pages parse in no shape
and were never machine-checked, so the table is a floor, not a total.

## Common pitfalls (BAKED)
- **Forgetting to mount the returned widget (the #1 Flutter mistake)** — `joinSession` renders nothing itself. Store the `Widget?` from `onSuccess` in State and return it from `build()`.
- **Don't duplicate the built-in call controls (the #1 mistake everywhere else).** The joined widget renders a COMPLETE call UI — mute, camera, layout, participants, leave. Do NOT add your own buttons around it. The `CallSession.getInstance()` action methods are for CUSTOM controls ONLY — reach for them **just when the user EXPLICITLY asks** to replace the defaults, and hide the built-ins first via the `..hide*Button` setters on `SessionSettingsBuilder`. To merely REACT to the built-in leave button, use `ButtonClickListeners(onLeaveSessionButtonClicked:)` — do not add a second button.
- **Removing a listener you did not keep** — construct once into a field; `remove*Listener` matches by instance.
- **`User` is exported by BOTH barrels** — ringing imports both SDKs; `ambiguous_import` until one hides it (`… hide User;`). No page says so.
- **Ringing teardown needs BOTH SDKs** — `leaveSession()` ends your media, `CometChat.endCall(sessionId)` tells the peer and completes the log. Only the first, and the peer still thinks the call is live.
- **There is no `cancelCall`** — cancel your own outgoing call with `rejectCall(sessionId, CometChatCallStatus.cancelled)`.
- **Manifest permissions without the runtime request** — on Android 6+ the manifest alone grants nothing; request camera/mic before joining or the call is black and silent.
- **`minSdkVersion` left at Flutter's default** — the floor is **26** (docs say 24), in `android/app/build.gradle.kts` on current Flutter, not `android/build.gradle`.
- **iOS Simulator on Apple Silicon:** `CometChatWebRTC` excludes arm64, so the app builds x86_64 — fine on an iOS 18 simulator (Rosetta), **impossible on iOS 26+**. Device or iOS 18 sim; details in `references/platform-notes.md`.
- **`cometchat-settings.json` not in `flutter: assets:`** — `initFromSettings` fails with settings-file-not-found. It is a *quiet* error callback, not a crash. Registering the asset is the whole job; no Xcode step.
- **Double init** — `init` after `initFromSettings` silently re-attributes telemetry to `"manual"`.
- **Handling `onSessionLeft` but not `onSessionTimedOut`** — idle timeout (default **300s**, `0` disables) fires a DIFFERENT callback; miss it and the user sits on a dead call screen.
- **Emitting an API Flutter lacks** — no presentation mode, no first-party push package. Say so rather than emitting code that cannot resolve. The two PiPs are also different calls: `enablePictureInPictureLayout()` is the in-app layout, `enterPipMode()` is Android system PiP.
- **Screen share — the control methods DO ship (docs lag them).** `CallSession.getInstance()` has real `startScreenShare()`/`stopScreenShare()`/`toggleScreenShare()` + an `isScreenSharing` getter (barrel-reachable in 5.0.7; the method channel invokes a native `startScreenShare` and web routes to `getDisplayMedia`), and `hideScreenSharingButton` defaults to **`false`** so the built-in button is visible. So an emit calling `startScreenShare()` COMPILES and dispatches — do NOT tell the user local screen share is impossible or "invented." The **`/calls/flutter/screen-sharing` DOC page still says "receive-only"** — it documents only the RECEIVE side (`onParticipantStartedScreenShare`, `participant.isPresenting`, viewing a web participant's share); the shipped local-share control API is undocumented there. Reflect the shipped methods, and note the page lags them.
- **Joining before init+login resolve** — chain from the success callbacks.
- **Assuming a signature** — event names, `SessionSettings` fields and action params are FETCHED from docs, never guessed.

## Verify it works
- **Tier-1 catalog:** every `cometchat_calls_sdk` symbol emitted appears in `flutter-calls-v5.json` (`node test-suite/scripts/verify-catalog.mjs --family flutter-calls-v5`).
- **Tier-2 compile:** the emit analyzes clean against the installed `cometchat_calls_sdk` (5.0.7) with `flutter analyze` in `test-suite/harness/flutter-calls`.
- **Tier-3 smoke:** the round-trip (init→login→generateCallToken→join→**widget-mounted**→leaveSession) via the pack's dev calls-smoke harness (internal QA, not shipped) — **certified on a physical Android device**. **Ringing runs as TWO concurrent devices**, one process per role, and only counts if both succeed on the SAME session id — see `references/docs-map.md` § "1:1 RINGING".
