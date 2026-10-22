# Doc corrections — Flutter Calls SDK v5

Every row below is **verified against the shipped `cometchat_calls_sdk 5.0.7`**, by compiling the
documented shape and reading the analyzer's verdict (and, for the
ringing rows, `cometchat_sdk 5.0.6`). Where a live page under `/calls/flutter/**` disagrees with
this file, **this file wins** — the page does not compile.

| The docs write | It does not compile — use |
|---|---|
| `CometChatCalls.generateToken(sessionId: …)` returning a `CallToken` (the token flow on 13 pages) | **`CometChatCalls.generateCallToken(sessionId, onSuccess:, onError:)`** → `CallToken`. `generateToken` is `@Deprecated` ("auth token is now managed internally after `login()`"), takes **two positional** args, and yields **`GenerateToken`** — the pages paired the deprecated name with the replacement's callback type, so it type-errors either way. **No page mentioned `generateCallToken` at all** |
| `CometChatCalls.SessionSettingsBuilder()` (23×, 13 pages) | **`SessionSettingsBuilder()`** — a top-level class, not a member of `CometChatCalls` |
| `SessionStatusListener` / `MediaEventsListener` / `ParticipantEventListener` / `ButtonClickListener` / `LayoutListener` (34×, 16 pages) | **All five are PLURAL types**: `SessionStatusListeners`, `MediaEventListeners`, `ParticipantEventListeners`, `ButtonClickListeners`, `LayoutListeners`. Note `MediaEvent**Listeners**` but `addMediaEvent**s**Listener` — the type and the method pluralise differently |
| `removeSessionStatusListener()` with no argument, next to an inline-constructed listener | **`remove*Listener(theSameInstance)`** — hoist the listener into a field first; an inline listener can never be removed |
| `callLog.sessionID` | **`callLog.sessionId`** — lowercase `d` |
| `CometChatConstants.RECEIVER_TYPE_USER` etc. (ringing) | **`CometChatReceiverType.user` / `CometChatCallType.video` / `CometChatCallStatus.cancelled`** — `CometChatConstants` does not exist; these live in the **Chat SDK** |
| `onSuccess: (User user)` on `login` / `loginWithAuthToken` | **`(User? user)`** — nullable; the pages dereference it unguarded |
| `CallSession.getInstance().x` | **`CallSession.getInstance()?.x`** — it returns `null` with no active session |
| `setAudioMode(...)` as a `CallSession` action | **`setAudioModeType(AudioMode.speaker)`** on the session; `..setAudioMode(...)` is the **builder** setter. Same concept, two different names on two different objects |
| `unpinParticipant(participant)` | **`unPinParticipant()`** — capital `P`, and it takes **no argument**. The other three (`muteParticipant`/`pauseParticipantVideo`/`pinParticipant`) take a `uid` **String**, not a `Participant` |
| `CallLogRequest.CallLogRequestBuilder().setLimit(30).setSessionType("video")` (call-logs, recording, migration-guide) | **Three errors in one line.** `CallLogRequestBuilder` is **top-level** (no `CallLogRequest.` prefix); it has **no `setX()` methods at all** — public FIELDS, so cascaded *assignments*: `(CallLogRequestBuilder()..limit = 30..callType = "video").build()`; and the field is **`callType`**, not `sessionType`. Note this is the OPPOSITE shape to `SessionSettingsBuilder`, which does take cascaded setter calls |
| `Android: Minimum API Level 24 (Android 7.0)` / `iOS: Minimum iOS 12` (overview) | **`minSdkVersion 26`** (Android 8.0) in `android/build.gradle` — wrong for every 5.0.x — and **iOS 15.1** in the 5.0.7 podspec (it was 13.0 in 5.0.6). Both documented floors are too low and both fail at BUILD time. Since the page pins `^5.0.3`, a reader resolves 5.0.7 and needs 15.1 |
| `recording.recordingURL` and the `recordingURL` property row (recording, call-logs) | **`recordingUrl`** — lowercase `rl`. `Recordings` has exactly four fields: `rid`, `recordingUrl`, `startTime`, `endTime`, plus `duration` |
| `Recording` / `CallStatus` / `CallCategory` / `CallDirection` as Dart types | **`Recordings`** (plural) is the type; the three enums **do not exist on Flutter** — those call-log filters take plain **Strings** (`"missed"`, `"call"`, `"incoming"`) |
| `SessionStatusListeners(onSessionJoined: …)` and the other four, built with named callbacks (16 pages) | **All five are `abstract class`es — they cannot be constructed.** `class X extends SessionStatusListeners { @override void onSessionJoined() {…} }`, then pass an instance. Every method already defaults to a no-op. Renaming them to the plural (docs#492) fixed the NAME; the constructor-call shape is still wrong |
| `CometChat.addCallListener(id, CallListener(onIncomingCallReceived: …))` (ringing) | **`CallListener` is a `mixin`** — also not constructible. `class X with CallListener { @override void onIncomingCallReceived(Call c) {…} }`, then pass an instance |
| `Call(receiverID, receiverType, callType)` (ringing) | **`Call` takes NAMED required params** — `Call(receiverUid: …, receiverType: …, type: …)`. It has no positional parameters at all, and the third one is `type`, not `callType` |
| `joinCallSession(call.sessionId!)` (ringing) | **`Call.sessionId` is `String?`** — the force-unwrap turns a signal that arrived without a session into a crash instead of a handled error |
| `AppSettingsBuilder()..region = …` by analogy with `CallAppSettingBuilder` (ringing) | **`AppSettingsBuilder` uses chained `setX()`** — `..setRegion(…)`, `..setAutoEstablishSocketConnection(true)`. The two builders sit in the same file and take different shapes |
| — (no doc page states it) | **`CometChatCalls.init` is a *plain* init, not the ai-agent one.** `initFromSettings` is `@nodoc` and undocumented; see the STOPGAP note above |
| `CallSession…addLayoutListener(l)` / `removeLayoutListener(l)` (events, migration-guide) | **Neither method exists.** `CallSession` has `set layoutListener(LayoutListeners?)` + a getter — one slot, cleared with `layoutListener = null` |
| `CometChat.initiateCall(call, timeout: 30, …)` and two parameter tables documenting it (ringing) | **There is no `timeout` parameter.** `initiateCall` takes the `Call` plus `onSuccess`/`onError`, and the repository beneath it takes only receiver/receiverType/type. The unanswered timeout is server-side; cancel early with `rejectCall(sessionId, CometChatCallStatus.cancelled)` on your own timer |
| — (no page mentions it) | **`User` is exported by BOTH barrels.** Ringing imports `cometchat_calls_sdk` *and* `cometchat_sdk`; the file fails with `ambiguous_import` until one hides it — `import '…/cometchat_calls_sdk.dart' hide User;` |
| `Participant.pid` / `.role` / `.audioMuted` / `.videoPaused` / `.isPinned` / `.isPresenting` / `.raisedHandTimestamp` — the "Participant Object Reference" on `actions` | **None of those seven exist.** `Participant` has TWELVE real fields, all nullable: `uid` · `name` · `avatar` · `mid` · `state` · `isJoined` · `deviceId` · `joinedAt` · `leftAt` · `totalAudioMinutes` · `totalVideoMinutes` · `totalDurationInMinutes` (source: `lib/src/model/participants.dart` 5.0.7; `Participants` plural is a `@Deprecated` typedef alias). Track live mute/pin/hand/share state from the `ParticipantEventListeners` callbacks — the same way iOS must. This skill previously repeated the docs' phantom list *and added emphasis*, then over-corrected to a WRONG "exactly seven" count — a closed list that isn't is worse than no list; the real closed list is the twelve above |
| `region` is "`us`" or "`eu`" (setup's `CallAppSettingBuilder` table) | **`in` is also live** — a real provisioned app uses it. A reader following the table concludes their credentials are wrong |



The first seven rows are fixed in docs PR cometchat/docs#492. **The five after them are NOT** —
they were found by running `flutter analyze` over this skill's own harness, after #492 was
already open, and the abstract-listener one is the largest single defect on the tree: #492
renamed those five types to their real plural spelling but left every one of them being
CONSTRUCTED, which still does not compile. Until a follow-up lands, until it merges the live `/calls/flutter/**`
pages still carry them. **12 fences on those pages parse in no shape and were never machine-checked**,
so treat this table as a floor, not a total — the abstract-listener class was itself found
outside the gate. Re-check when #492 and its follow-up land.

---

## Drift warning

The preview host is being fixed under this table. As of the last check, `session-settings` and
`join-session` already carry the top-level `SessionSettingsBuilder()`, and `setup` already pins
`^5.0.7` — so the occurrence counts above (`23×, 13 pages`) **overstate what is still broken**.
The rows remain correct about what does and does not compile; treat the counts as historical.
Re-probe a page before quoting a number from here.
