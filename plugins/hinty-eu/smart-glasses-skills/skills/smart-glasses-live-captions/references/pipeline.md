# Capture, VAD and streaming

Last checked: 2026-11-08. Verification: the PCM path (browser microphone -> 16 kHz PCM -> server -> Deepgram) ran
locally in `examples/live-captions`; the per-brand microphone facts are `docs-only`.

## Where to capture audio

### Default: the phone microphone

- **It hears the other person.** Glasses microphone arrays are beamformed toward the wearer's mouth. That is what you
  want for dictation and voice commands, and the opposite of what captions for a conversation need.
- **Bluetooth stays free for the display.** A BLE display link carries small text writes; streaming audio over the
  same radio (or switching the glasses into a headset profile) competes with them.
- **No call-audio mode.** Opening a Bluetooth headset microphone (HFP/SCO) puts the glasses into call audio: playback
  drops to call quality, and on Meta Ray-Ban Display it ends the display session (meta-wearables-dat-android issue
  #210, Meta reply 2026-11-04: fixed for glasses without a display in firmware 192.1, display fix "at a later date").
- **Simpler permissions and review.** One microphone permission on the phone instead of a glasses permission flow.

Placement matters more than the microphone: a phone in a pocket or bag records muffled audio and rustle. Tell the
wearer to put it on the table or hold it. A clip-on or USB-C microphone on the phone beats both for lectures.

### When the glasses microphone is the right one

- Captioning or translating **what the wearer says** (language practice, speaking to someone in another language).
- **Separating "me" from "them"** with two channels: glasses microphone = wearer, phone microphone = everyone else.
  This is cheaper and more reliable than speaker diarization for a two-person conversation. Even's SDK adds a
  `speakerRole` (`self` / `other` / `unknown`) to glasses audio frames from an app-side algorithm (SDK 0.0.14+);
  treat it as a hint, not identity.
- The phone has to stay in a pocket (walking, working with both hands).

### Per brand (as of 2026-11-08)

| Glasses | How to get audio | Format | Source |
|---|---|---|---|
| Even Realities G2 | `bridge.audioControl(true, AudioInputSource.Glasses)` (or `.Phone`); frames arrive in `onEvenHubEvent` as `audioEvent.audioPcm`; needs the `g2-microphone` or `phone-microphone` permission in `app.json`; the glasses source also needs the page created first, the phone source does not; the plugin captures either itself, no second app | PCM 16 kHz, s16le, mono; the simulator sends 100 ms per event | https://hub.evenrealities.com/docs (SDK 0.0.16 types) |
| Meta Ray-Ban Display Web App | none | - | https://wearables.developer.meta.com/docs/develop/webapps |
| Meta glasses with DAT | the glasses as a Bluetooth headset (HFP); the Speech capability (beta, dev and beta channels) returns text on the glasses side | HFP audio, or text | https://wearables.developer.meta.com/docs/develop/dat/knownissues/ |
| Rokid Glasses (CXR-L from the phone) | `startAudioStream()`, callback `onAudioReceived(ByteArray)`, needs the microphone scope approved in the Hi Rokid app | PCM 16 kHz, 16-bit, mono (CXR-L 1.1.2 changelog, 2026-09-08, on Rokid's SDK overview, read 2026-11-08) | https://developerdoc.rokid.com/sdk?lang=zh |
| Vuzix Z100 | no microphone | - | https://vuzix.github.io/ultralite-sdk-android/javadoc/allclasses-index.html (no audio API) |
| USB-C display glasses (XREAL, VITURE, RayNeo Air) | the phone's audio input routing, when the glasses expose a USB microphone | device dependent | unverified |
| Audio-only glasses (Ray-Ban Meta, others) | Bluetooth headset microphone (HFP) | call quality | general Bluetooth behaviour |

Use the brand skills for the exact calls: `smart-glasses` lists the official Even, Meta and Android XR skills.

## Audio format

- **16 kHz, 16-bit little-endian, mono PCM** is accepted by every major streaming STT and by on-device engines.
  Exception: OpenAI's realtime transcription expects 24 kHz PCM (2026-11-08); resample on the server.
- **Frame size:** 100 ms (3200 bytes) is a good default. 20 to 50 ms frames cut a little latency at the cost of more
  messages; Deepgram recommends 80 ms chunks for Flux.
- **Bandwidth:** 32 KB/s raw. On mobile data, Opus at 16 to 24 kbps saves most of it if the provider accepts Opus
  (Deepgram does: `encoding=opus` / `ogg-opus`).
- **Browser capture:** `getUserMedia` with `echoCancellation` and `noiseSuppression`, an `AudioContext` (Chrome accepts
  `{ sampleRate: 16000 }` and resamples for you), and an `AudioWorklet` that converts float samples to Int16 and posts
  100 ms frames. `examples/live-captions/server/mic.html` has a 15-line worklet.

## VAD: do not stream silence

Why: most providers bill per second of audio sent (AssemblyAI bills the time the socket is open), silence invites
hallucinated words from some models, and less audio leaves the device.

How:

- **Energy gate with pre-roll and hangover** is enough for a quiet room: keep the last 300 to 500 ms in a ring buffer,
  start sending (ring buffer first) when the level crosses a threshold, keep sending 700 ms to 1 s after it drops.
  The hangover matters: endpointing needs trailing silence to finalise a sentence.
- **Model VAD** (Silero VAD, WebRTC VAD) for noisy places. Run it on the phone, not on the glasses.
- **Keep the connection alive while gated.** Deepgram closes a stream after about 10 s without audio unless you send
  `{"type":"KeepAlive"}`; other providers have similar idle timeouts. Some providers (AssemblyAI, Gladia) have their
  own turn detection; with those, gate less aggressively.

```ts
// Energy gate for 16 kHz Int16 frames: returns the frames to send now (pre-roll included on speech start)
function createGate(thresholdDb = -45, preRollMs = 400, hangoverMs = 900, frameMs = 100) {
  const ring: Int16Array[] = []
  let quietFor = Infinity
  return (frame: Int16Array): Int16Array[] => {
    let sum = 0
    for (const s of frame) sum += s * s
    const db = 20 * Math.log10(Math.sqrt(sum / frame.length) / 32768 + 1e-9)
    const loud = db > thresholdDb
    quietFor = loud ? 0 : quietFor + frameMs
    if (quietFor === 0 && ring.length) return [...ring.splice(0), frame] // speech started: flush pre-roll
    if (quietFor <= hangoverMs) return [frame]                           // speaking or in hangover
    ring.push(frame)
    if (ring.length > preRollMs / frameMs) ring.shift()
    return []
  }
}
```

## Streaming sessions

- **One long-lived connection per session**, opened before the wearer starts talking (a TLS plus WebSocket handshake
  costs 100 to 300 ms on mobile).
- **Reconnect with backoff and a short buffer.** Queue up to about 10 s of audio while reconnecting, then drop the
  oldest. After a reconnect the provider starts a new transcript: commit the old partial as final first.
- **Session limits** (2026-11-08): Google STT streams end after 5 minutes; `SFSpeechRecognizer` (server-based) plans
  for one minute of audio; Meta DAT Speech stops reporting text after one minute (known issue); Chrome's Web Speech
  stops after silence and ignores `continuous` on Android; Android's `SpeechRecognizer` is not meant for continuous
  use (use `EXTRA_SEGMENTED_SESSION` on API 33+ or restart per sentence). Rotate sessions on a sentence boundary,
  overlapping the new one by a second.
- **Diarization in streaming** exists at Deepgram, AssemblyAI, Speechmatics and Azure (`ConversationTranscriber`), and
  not in Google Chirp 3 streaming, OpenAI's live transcription or Gladia live (2026-11-08). For two people, two
  microphones beat diarization.

## Background and locked phone

- **Android:** a foreground service with `foregroundServiceType="microphone"` and the `FOREGROUND_SERVICE_MICROPHONE`
  permission keeps capture running with the screen off. Start it while the app is visible.
- **iOS:** the `audio` background mode keeps an active `AVAudioSession` recording when the app goes to the background.
- **Even Hub plugin:** the plugin's WebView keeps running on iOS and may be suspended on Android; glasses audio capture
  stops with it. Persist state with the bridge storage and reconnect on `FOREGROUND_ENTER_EVENT`.
- **Meta Web Apps:** a hidden page suspends timers and promises. Re-sync when `visibilityState` is `visible`.

## Where each piece runs

| Piece | Phone app | Server relay | Glasses page or plugin |
|---|---|---|---|
| Capture | yes | - | Even and Rokid only |
| VAD | yes | optional | no |
| STT | on-device or cloud client | cloud client, holds the keys | no |
| Caption state, `seq` | yes | yes | mirror only |
| Line fitting | for native SDK targets | no | yes, it knows its display |

The relay costs one extra hop (tens of milliseconds on the same continent) and buys pairing by room code, one STT
connection shared by several screens, and keys that never leave the server.
