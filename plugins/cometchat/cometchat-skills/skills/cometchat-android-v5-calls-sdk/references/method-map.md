# SDK method map — full curated highlight (calls-sdk-android 5.0.4, headless)

> `SKILL.md` § SDK method map keeps the spine (Lifecycle · Session · Active call + the catalog note);
> this file carries the full per-category enumeration. The **AUTHORITATIVE** closed list is still the
> **`android-calls-v5.json` catalog** (also transcription/streaming, `CometChatCallsEventsListener`, the
> v4-era `CallSettingsBuilder`). A symbol is real **iff it's in the catalog**; then fetch its page via
> `references/docs-map.md`. Signatures → FETCH from docs, never memory.

## Lifecycle (`CometChatCalls` statics)
`initFromSettings` · `init` · `isInitialized` · `login(uid, authKey, l)` / `login(authToken, l)` · `logout` ·
`getLoggedInUser` · `getUserAuthToken`

## Session
- `generateToken(sessionId, l)` → `GenerateToken.token`
- `joinSession(token | sessionId, SessionSettings, RelativeLayout, l)` → `CallSession`
  (`startSession`/`CallSettingsBuilder` = **v4 path, do not use**)
- `CometChatCalls.SessionSettingsBuilder()`: `setSessionType(SessionType.VIDEO|VOICE)` ·
  `setLayout(LayoutType.TILE|SIDEBAR|SPOTLIGHT)` · `setDisplayName` · `setTitle` · `setAudioMode(AudioMode.*)` ·
  `setIdleTimeoutPeriod(sec)` · `startAudioMuted`/`startVideoPaused` · `setInitialCameraFacing` ·
  `enableAutoStartRecording` · `hideControlPanel`/`hideHeaderPanel`/`hide<Button>`
  (full list: `/calls/android/session-settings`)

## Active call (`CallSession.getInstance()`)
`isSessionActive` · `leaveSession` · lifecycle-bound listeners `addSessionStatusListener(owner, …)` /
`addParticipantEventListener` / `addMediaEventsListener` / `addButtonClickListener` / `addLayoutListener` ·
`clearAllListeners`

## In-call actions
⚠️ **CUSTOM controls ONLY; the joined surface already renders them** (pitfall #1; `hideControlPanel(true)` first):
`muteAudio`/`unmuteAudio` · `pauseVideo`/`resumeVideo` · `switchCamera` · `setAudioMode` · `muteParticipant(uid)` ·
`pauseParticipantVideo(uid)` · `pinParticipant(uid, pid)`/`unpinParticipant()` ·
`enablePictureInPictureLayout`/`disablePictureInPictureLayout` · ⚠️ `setLayout` · `startRecording`/`stopRecording` ·
`raiseHand`/`lowerHand` — real symbols, **no-ops in 5.0.4** (see `references/pitfalls.md`).

## Call logs
`CallLogRequest.CallLogRequestBuilder().setLimit(n)…build()` → `fetchNext(l)` / `fetchPrevious(l)` →
`List<CallLog>` (`getRecordings()` → `Recording.recordingURL`).

## Transcription & closed captions (v5.0.4+; PLAN-GATED)
- builder: `enableAutoStartTranscription`/`hideTranscriptionButton`/`hideClosedCaptionButton`/`setCaptionLanguage`
- mid-call: `CallSession…startTranscription()`/`stopTranscription()`
- retrieve: `TranscriptRequest.TranscriptRequestBuilder().setSessionId(sid)…build()` → `fetchNext` →
  `List<Transcript>` (`.transcriptUrl` = downloadable JSON; empty≠error). Full row: `references/docs-map.md`.

## Background
`CometChatOngoingCallService.launch(activity)` / `.abort(activity)` (foreground service + ongoing notification;
`OngoingNotification.buildOngoingConferenceNotification(n)` to brand it) — **`.abort` on EVERY teardown path incl.
`onDestroy`, not only `onSessionLeft`** (BACK destroys the owner before the callback → FGS + notification leak,
AUDIT-227; see the Rotation pitfall in `references/pitfalls.md`).

## Constants/enums
`SessionType` · `LayoutType` · `AudioMode` · `CameraFacing` · `CometChatCallsConstants.CALL_STATUS_*` /
`CALL_TYPE_*` / `RECEIVER_TYPE_*`
