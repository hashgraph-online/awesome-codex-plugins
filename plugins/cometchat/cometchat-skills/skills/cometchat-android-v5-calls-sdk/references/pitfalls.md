# Common pitfalls — full detail (calls-sdk-android 5.0.4, headless)

> The one-liners live in `SKILL.md` § Common pitfalls; this file keeps the FULL evidence and reasoning
> so a symptom is searchable. minSdk-26 floor and the missing `<service>` are covered in
> `SKILL.md` § Prerequisites (evidence in `references/build-truth.md`).

## Don't duplicate the built-in call controls (the #1 mistake)
`joinSession` renders a COMPLETE call UI — mute, camera, switch camera, audio mode, layout, participants,
raise hand, recording, share invite, timer and the red leave button — into your `RelativeLayout`. Do **NOT**
add your own control row; the custom-control-panel page is for an explicit "replace the controls" ask
(then `hideControlPanel(true)` FIRST).

## Docs ≠ AAR (verified vs 5.0.4 — the compiler and the device are right)
Per-page notes are in `references/docs-map.md`. Confirmed drifts:
- `setType(...)` → **`setSessionType`**
- `unMuteAudio` → **`unmuteAudio`**
- `unPinParticipant` → **`unpinParticipant`**
- `pinParticipant(uid)` → **`(uid, pid)`**
- `MediaEventsListener.onScreenShareStarted/Stopped` **do not exist** (screen-share events are on `ParticipantEventListener`)
- background-handling's named-arg `joinSession(view=FrameLayout, context=…)` **does not exist**
- `raiseHand`/`setLayout`/`startRecording` **no-ops** (see below).

The docs now state minSdk 26 + document SoLoader (AUDIT-229).

## Wrong container
`joinSession` needs a `RelativeLayout`; `wrap_content` or zero size renders the call invisibly
(`ERROR_CALLING_VIEW_REF_NULL` if null).

## `joinSession` crashes with `libhermes_executor.so not found`
The SoLoader merged-mapping init is missing; see `SKILL.md` § Prerequisites § SoLoader.

## Joining before init+login resolve
`ERROR_COMETCHAT_CALLS_SDK_INIT` / `ERROR_AUTH_TOKEN`; always chain off the callbacks.

## `ERROR_COMETCHAT_CALLS_SDK_INIT` after a user switch is MISLEADING (AUDIT-194)
`logout()` — and the implicit one inside `login(<other uid>)` — leaves `isInitialized()==false` though `login`
reports `onSuccess`; `generateToken` then fails naming the wrong cause. **Re-init between logout and login:**
`references/user-switch.md`.

## No runtime permissions
The call joins with a dead mic/camera; request `CAMERA` + `RECORD_AUDIO` first (the AAR only DECLARES them).

## Listeners registered before join
No live session yet; register in `joinSession`'s `onSuccess` with a `LifecycleOwner`.

## Hang-up on one SDK only (ringing)
`leaveSession` without `CometChat.endCall` leaves the peer in-call and the log incomplete; do both.

## Android can't START screen share (receive-only)
And has **no virtual-background page** — don't promise either.

## Rotation / Home kill the call
Add `configChanges` (+ `supportsPictureInPicture` for PiP); keep it alive with
`CometChatOngoingCallService.launch(activity)` in `onSessionJoined` — **needs the `<service>` from Prerequisites**
(else `launch` fails silently); PiP = `enterPictureInPictureMode` + `enablePictureInPictureLayout`.

## Ongoing-call service LEAKS if you only `.abort` in `onSessionLeft` (AUDIT-227, verified live)
BACK destroys the Activity → `onSessionLeft` is **not delivered** to the destroyed `LifecycleOwner`, so `.abort`
never fires and the FGS + ongoing notification survive with NO call. **Also `CometChatOngoingCallService.abort(this)`
in `onDestroy`** (idempotent) — abort on EVERY teardown path.

## No-op in-call actions (5.0.4, live two-participant test — SDK bug, AUDIT-187)
`raiseHand`/`lowerHand`, `setLayout(...)` mid-call and `startRecording`/`stopRecording` produce **no effect,
no callback and no error**, while `muteAudio`/`pauseVideo`/`switchCamera` on the same path work. Prefer the SDK's
OWN buttons for these; recording may also be **plan-gated with NO error signal** — confirm via
`CallLog.getRecordings()`. STOPGAP: drop when a fixed 5.0.x ships.

## Backgrounded apps do not ring and do not hear the accept
Auto socket mode drops the WebSocket — foreground only; VoIP push for the rest (§ 1:1 ringing).

## Mixing majors
The Calls SDK is **5.x** (`joinSession`); `startSession`/`CallSettingsBuilder` and `/calls/v4/android` are the OLD tree.
