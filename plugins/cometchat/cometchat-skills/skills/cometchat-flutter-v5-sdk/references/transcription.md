# Transcription & closed captions — Flutter Calls SDK 5.0.7

> Transcription shipped in `cometchat_calls_sdk` **5.0.7** (published 2026-09-02). It had no
> documentation at all when this file was written; **`/calls/flutter/transcription` now exists**
> (docs#492, DOCS-BACKLOG D3) and is the source of truth once it merges. Until then this file is
> a labelled **STOPGAP** — every shape below is compile-verified against the published package,
> and both were written from the same verification pass, so they agree. Prefer the page when it
> lands, and delete the stopgap note here.

Server-side feature: **state the dashboard prerequisite** rather than assuming it is enabled.

## Control — on `CallSession.getInstance()`

```dart
await CallSession.getInstance()?.startTranscription();
await CallSession.getInstance()?.stopTranscription();
final bool? on = CallSession.getInstance()?.isTranscribing;
```

## Session settings — ⚠️ both buttons are HIDDEN BY DEFAULT

```dart
final settings = (SessionSettingsBuilder()
      ..setType(SessionType.video)
      ..enableAutoStartTranscription(true)   // start with the session
      ..hideTranscriptionButton(false)       // ← REQUIRED to show it
      ..hideClosedCaptionButton(false)       // ← REQUIRED to show it
      ..setCaptionLanguage('en-US'))         // a METHOD, not a field
    .build();
```

`hideTranscriptionButton` and `hideClosedCaptionButton` both default to **`true`**, joining
`hideRecordingButton`, `hideShareInviteButton` and `hideChatButton`. Wiring a click handler
without passing `false` gives you a control that can never appear — the same trap, now on five
buttons rather than three.

Note `setCaptionLanguage(String)` is a **setter method**, unlike `CallAppSettingBuilder`'s
`..appId =` fields. This builder is method-cascade throughout; only the *call-log* builder takes
field assignments.

## Retrieval

```dart
final req = (TranscriptRequestBuilder()
      ..setSessionId(sessionId)
      ..setLimit(30))          // defaultLimit 30 · maxLimit 1000
    .build();

await req.fetchNext(
  onSuccess: (List<Transcript> transcripts) { /* ... */ },
  onError: (CometChatCallsException e) { /* ... */ },
);
await req.fetchPrevious(onSuccess: (_) {}, onError: (_) {});
```

The callbacks are **required** — the same shape as `CallLogRequest.fetchNext`. Both methods also
return the `Future<List<Transcript>>`, so either channel works, but you cannot omit the callbacks.

### `Transcript`

| Field | Type | |
|---|---|---|
| `tid` | `String?` | transcript id |
| `mid` | `String?` | message id |
| `roomName` | `String?` | the session's room |
| `startTime` / `endTime` | `int?` | epoch bounds |
| `url` · `transcriptUrl` | `String?` | where to fetch the text |
| `transcriptDate` | `String?` | |
| `metaData` | `Map<String, dynamic>?` | the raw server record — new/unknown keys are never lost |

All nullable — unwrap before use. (Nine fields total; `metaData` is barrel-reachable and on the live `/calls/flutter/transcription` page too.)

## Finding calls that have one

```dart
final logs = (CallLogRequestBuilder()..hasTranscriptions = true).build();
```

`CallLogRequestBuilder` also gained a `setHasTranscriptions(bool)` **method** in 5.0.7 — the only
setter on an otherwise all-field builder. Prefer the field assignment for consistency with the
rest of that builder.

## What Flutter still does not have

No `TranscriptsBuilder`-style server filter beyond session id and limit, and no live caption
*stream* to subscribe to — captions are rendered by the SDK's own UI, and transcripts are fetched
after the fact. iOS's `TranscriptsRequest` surface is not identical; do not port its snippets.
