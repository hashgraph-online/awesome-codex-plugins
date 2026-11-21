---
name: smart-glasses-live-captions
description: Live captions, translation and real-time hints on smart glasses - capture speech on the phone or the glasses, stream it to speech-to-text, turn partial and final results into lines that fit each glasses display, keep end-to-end latency low, and fall back to a short hint or voice in the ear. Covers Even Realities G2, Meta Ray-Ban Display (Web Apps and DAT), Rokid Glasses, Vuzix Z100, USB-C display glasses, phone notifications and audio-only glasses, with a runnable example (Node caption server, glasses web page, Even Hub plugin). Use when building subtitles for deaf or hard-of-hearing users, a live translator, a teleprompter, meeting captions or an AI assistant that shows or speaks text on glasses, or when captions on glasses lag, flicker, wrap badly or drop characters. Not for offline video subtitling or meeting transcription that never reaches glasses.
license: Apache-2.0
metadata:
  version: "1.0.1"
  last-updated: "2026-11-09"
---

# Live captions on smart glasses

Last checked: 2026-11-08. Verification: the example server and glasses web page ran locally, the Even G2 plugin ran in
the official Even Hub simulator; nothing in this skill ran on glasses yet. Vendor facts are `docs-only` unless marked.

This skill assumes the target glasses are known. If they are not, start with the `smart-glasses` skill (which
glasses, which rung of the display-text ladder, vendor SDK pointers). The rungs used below: 1 vendor SDK, 2 web app on
the glasses, 3 USB-C display glasses as an external display, 4 phone notification mirrored by the glasses' app,
5 voice in the ear.

## The pipeline

```
microphone ─► VAD ─► streaming STT ─► caption events ─► transport ─► line fitter ─► glasses display
 (phone or     (drop     (partial and      seq, text,      WebSocket,   per display     (SDK, web page,
  glasses)     silence)   final results)   final           HTTP poll    budget          USB-C, notification)
                                                └──────────► short hint ─► text-to-speech ─► ear
```

Make these decisions in order. Each has a reference file with the details and sources.

| # | Decision | Default | Reference |
|---|---|---|---|
| 1 | Where to capture audio | Phone microphone | `references/pipeline.md` |
| 2 | Which speech-to-text | Cloud streaming STT with partial results | `references/stt-options.md` |
| 3 | How partial and final results become lines | Replace the last line until final | `references/line-fitting.md` |
| 4 | How many lines and how often to update | Per display budget, coalesced | `references/line-fitting.md` |
| 5 | Latency budget | First words under 1 s, finals under 2 s | `references/latency.md` |
| 6 | Non-Latin scripts | Check the font first, render to image if missing | `references/scripts-and-fonts.md` |
| 7 | Tiny screen or no screen | A few-word hint, spoken finals only | `references/short-hints.md` |

## 1. Capture audio on the phone unless you need the wearer's own voice

Glasses microphones are tuned for the wearer's mouth. Captions are usually about the other person, so the phone
(on the table or in a hand, not in a pocket) hears them better. The phone path also keeps Bluetooth free for the
display and avoids the call-audio mode that some glasses switch into when their microphone opens.

| Glasses (as of 2026-11-08) | Microphone available to your app | Use it for |
|---|---|---|
| Even Realities G2 | Yes, from the plugin itself: `AudioInputSource.Phone` (phone mic) or `.Glasses`, 16 kHz s16le mono PCM | phone mic: the other person; glasses mic: the wearer |
| Meta Ray-Ban Display, Web App | No (Meta: only the Device Access Toolkit can capture audio) | nothing; capture on the phone |
| Meta glasses via DAT | Bluetooth headset (HFP) microphone; on-glasses speech recognition is beta | wearer's speech, with known issues |
| Rokid Glasses (CXR-L) | Yes: `startAudioStream`, 16 kHz 16-bit mono PCM (Rokid docs) | wearer's speech |
| Vuzix Z100 | No microphone | nothing; capture on the phone |
| USB-C display glasses | Usually a USB audio device on the phone | either |
| Audio-only glasses (Ray-Ban Meta and others) | Bluetooth headset microphone only | wearer's speech; costs audio quality |

**Even G2 needs no second app for the phone microphone.** The Even Hub plugin opens it itself with
`bridge.audioControl(true, AudioInputSource.Phone)` (permission `phone-microphone`) to caption the other person, or
`AudioInputSource.Glasses` (permission `g2-microphone`, only after `createStartUpPageContainer`) for the wearer. Frames
arrive in `onEvenHubEvent` as `event.audioEvent.audioPcm` (`Uint8Array`, PCM 16 kHz, signed 16-bit little-endian,
mono). The SDK has no speech-to-text: send the PCM as binary WebSocket frames to your STT relay, which holds the
provider key and sends caption text back over the same socket. Use `audioControl`, not `getUserMedia`, which fails in
the plugin WebView on iOS ([device APIs](https://hub.evenrealities.com/docs/build/device-apis), 2026-08-29;
[#11](https://github.com/even-realities/everything-evenhub/issues/11)). The example plugin has this as an optional
phone-microphone mode.

Details, VAD and streaming: `references/pipeline.md`.

### Even Hub plugin checklist (as of 2026-11-09)

- `app.json` `permissions`: `{"name": "phone-microphone", "desc": "..."}` for `AudioInputSource.Phone`,
  `g2-microphone` for `AudioInputSource.Glasses`, and `network` with a `whitelist` of full origins, both
  `https://captions.example.com` and `wss://captions.example.com` (no wildcards, no bare hosts). The whitelist does
  not bypass CORS: the relay must still send `Access-Control-Allow-Origin`. Declare only what the code uses
  ([packaging](https://hub.evenrealities.com/docs/ship/packaging), [networking](https://hub.evenrealities.com/docs/build/networking)).
- On the root page a double tap calls `bridge.shutDownPageContainer(1)` (system exit dialog); mode 0 is rejected.
- No provider keys in the package: "Never bundle secrets or API keys into the `.ehpk`"
  ([app submission](https://hub.evenrealities.com/docs/ship/app-submission), 2026-10-09). The official `asr`
  template reads `VITE_STT_API_KEY`, which ends up in the bundle; replace it with your relay.
- The privacy policy covers every permission, and the glasses show a message when setup is missing.
- The simulator "is not a hardware emulator" (BLE timing, real font rendering and WebView suspension are not
  reproduced): measure latency and microphone behaviour on glasses before you promise "about a second".

## 2. Pick a streaming STT that returns partial results

Captions need partial (interim) results; a batch API that answers after the sentence ends feels broken on glasses.

- **Cloud streaming** (Deepgram, AssemblyAI, Speechmatics, ElevenLabs Scribe Realtime, Google, Azure, OpenAI,
  Amazon, Gladia): best accuracy and language coverage, about USD 0.15 to 1.00 per audio hour at list price
  (2026-11-08), needs a network. Keep the key on a server; browsers and glasses get short-lived tokens or go through
  your relay.
- **On device** (Android `SpeechRecognizer` on-device, iOS `SpeechAnalyzer` or `SFSpeechRecognizer`, whisper.cpp,
  WhisperKit, Moonshine): offline and private, fewer languages, session limits to work around.
- **Browser Web Speech API**: free and quick for a prototype in Chrome or Safari; in Chrome the audio goes to a cloud
  service unless an on-device language pack is installed (Chrome 139+).

Comparison with prices, latency claims, endpoints and limits: `references/stt-options.md`.

## 3. Caption events: partial results replace, finals commit

Normalise every provider to one event shape before anything reaches a display:

```ts
type Caption = { seq: number; text: string; final: boolean } // text = the whole sentence so far, not a delta
type CaptionState = { finals: string[]; partial: string; seq: number }

function apply(st: CaptionState, m: Caption | { type: 'clear' }): boolean {
  if ('type' in m) { st.finals = []; st.partial = ''; return true }
  if (m.seq <= st.seq) return false            // replay after a reconnect, already shown
  st.seq = m.seq
  if (!m.final) { st.partial = m.text; return true }
  st.partial = ''
  if (m.text) st.finals = [...st.finals.slice(-29), m.text]
  return true
}
```

Rules that keep text stable on a small display:

- Committed lines never move or re-wrap. Only the lines of the current partial change.
- A partial starts on a fresh line, so replacing it never shifts older text.
- Providers revise earlier words in a partial ("for" becomes "four"). Show the revision; do not append.
- Some providers finalise a sentence in several segments (Deepgram `is_final` segments until `speech_final`). Join
  them in the adapter and emit one final per sentence.

## 4. Fit lines per display and coalesce updates

Wrap with the real font metrics of the target and keep the newest N lines, newest at the bottom. Caption-friendly
budgets (as of 2026-11-08, verify on the device):

| Display | Lines for captions | Width per line | Update path and rate |
|---|---|---|---|
| Even G2 (576x288, one firmware font, 27 px lines) | 3 to 8 of 10 | about 55 Latin characters | `textContainerUpgrade`, one call at a time, 120 ms debounce |
| Meta Ray-Ban Display Web App (600x600) | 3 to 4 at 32 to 40 px | about 26 to 32 characters | DOM, 30 Hz panel |
| Meta DAT display | 3 to 4 | preset text styles | every send replaces the whole screen |
| Rokid Glasses (CXR-L custom view) | 3 at 24 sp | about 22 Latin characters (estimate) | `customViewUpdate`, at most one every 250 ms (estimate) |
| Vuzix Z100 (640x480) | 3 (up to 7 fit) | about 36 in the text layout, which wraps near 42 (MentraOS measurement, community) | `sendText` or canvas `updateText` + `commit()` |
| USB-C display glasses (1920x1080 per eye) | 2 to 4, large, centre of view | your choice | normal phone UI, 60 Hz |
| Phone notification on glasses | 1 to 2 | about 30 to 40 characters | a new notification per final, at most one every 2-3 s |

Coalesce partials to what the link can carry: queue only the newest frame, send it when the previous write finished.
Never fire concurrent writes at a BLE display. Full rules, wrapping code, CJK and paging: `references/line-fitting.md`.

## 5. Keep a latency budget

Aim for the first words of a sentence on the glasses within about 1 s of being spoken and the final sentence within
2 s. The biggest items are usually the STT partial delay (vendor claims range from about 150 to 500 ms), endpointing
before finals (300 ms to 1 s of silence) and the display path (Even G2: 120 ms debounce plus about 80 ms per container
write, community measurement). Measure each stage with timestamps before tuning: `references/latency.md`.

## 6. Check the font before promising a language

The Even G2 firmware font has Latin, Cyrillic, Greek and CJK, and silently drops Arabic, Hebrew, Thai and Indic
scripts. Meta Web Apps render what the font stack covers, so ship a subset web font for your scripts. Vuzix uploads
missing glyphs from the phone. Rokid Arabic support is an open question. Strip characters the target cannot draw
and tell the wearer, or render the line to an image (slow, finals only). Per brand: `references/scripts-and-fonts.md`.

## 7. On tiny screens and in the ear, show a hint, not a transcript

A two-line display or a voice in the ear cannot carry a running transcript. Turn each final sentence (or the other
person's question) into a 3 to 8 word hint, speak only finals, never talk over the wearer, and drop stale hints.
Prompt patterns and per display budgets: `references/short-hints.md`.

## Architecture: where the code runs

- **One phone app does everything** (capture, STT, fit, send to the glasses SDK): lowest latency, needed for rungs 1,
  3, 4 and 5 on Android and iOS.
- **Phone or browser captures, a server relays, the glasses page or plugin displays**: needed for rung 2 and for
  plugin platforms such as Even Hub, where the display code runs in a WebView. On Even Hub the plugin can also be the
  capture side: it streams PCM from `audioControl` to the relay and shows the captions that come back. Pair screens
  with a short room code typed on the phone; keep STT keys on the server.
- **WebSocket first, HTTP polling as the fallback.** Some glasses WebViews fail the WebSocket handshake while `fetch`
  works (reported for the Even app on iOS, community). After two failed attempts, poll a `/latest` endpoint every
  0.5 to 1 s and keep retrying the socket slowly.
- **Reconnect on resume.** Glasses WebViews and phone apps get suspended in the background. Re-open the connection
  when the page or plugin comes back to the foreground, and replay the last lines from the server.

## Example app

`examples/live-captions/` in this repository: a Node server (`--demo` script, `--browser-mic` with the Web Speech
API, `--stt deepgram` adapter), a web page for glasses browsers and the Meta Ray-Ban Display, an Even Hub plugin, and
native Android and iOS targets written against the same protocol.

```sh
cd examples/live-captions/server && npm install && node server.mjs --demo   # prints a room code
# open http://localhost:8787/?room=CODE, or run the Even plugin in the simulator:
cd ../even-hub && npm install && npm run test:sim
```

The README there has the protocol (`caption`, `clear`, `hello`, `action`, `GET /latest`), the verification level of
each target with its date, and how to run each one on hardware.

## Pitfalls

- **Partial text treated as a delta.** Appending partials duplicates words. Every partial replaces the previous one.
- **Re-wrapping everything on each partial.** Older lines jump and the wearer loses their place. Wrap committed
  lines once; re-wrap only the partial.
- **Concurrent display writes over BLE.** On Even G2, parallel `textContainerUpgrade` calls are reported to break the
  link (community). Serialize all writes through one queue.
- **An overflowing event-capture container on Even G2.** The firmware scrolls it and swallows swipes until a
  boundary. Keep the capture container one line, or fit its text exactly.
- **Long silent sessions.** Deepgram closes a stream after about 10 s without audio unless you send `KeepAlive`;
  AssemblyAI bills the time the socket is open; Google STT streams end after 5 minutes; `SFSpeechRecognizer` plans
  for a one-minute limit; Meta DAT speech stops reporting after one minute (known issue, restart the capability).
  Rotate or restart sessions on a sentence boundary.
- **Chrome on Android ignores `continuous`.** Restart Web Speech recognition in `onend`.
- **Meta DAT microphone over HFP ends the display session** on Ray-Ban Display (meta-wearables-dat-android issue
  #210, open as of 2026-11-08; Meta staff: the Display fix comes "at a later date"). Use the phone microphone with a
  display.
- **Notifications as a caption channel.** Android sheds updates to an existing notification beyond 5 per second per
  app, and no brand documents how it forwards updates; companion apps show one or two lines and may delay. Post a new
  notification per final, at most one every 2-3 s.
- **Smart formatting changes what you show.** Deepgram `smart_format` turned "four o'clock" into "04:00" in our test.
  Decide on number and time formatting for the display, not just for the transcript.
- **Missing glyphs vanish silently** on Even G2: half a sentence disappears with no error. Strip and warn.

## Privacy and consent

Captions transcribe people who did not install your app. Tell them (a visible indicator, a spoken notice for long
sessions), check recording-consent law where the app is used, do not store audio, and keep transcripts on the device
or delete them after the session. Platform rules apply too: Meta's developer policies prohibit surreptitiously
collecting recognisable audio of the user or others and identifying people by their voice; Android XR guidance limits
continuous transcription when the wearer is not engaged. Prefer on-device STT when the content is sensitive.

## Related skills

- `smart-glasses`: choosing glasses, the display-text ladder, input, publishing, and the install commands of the
  official vendor skills (Even Hub, Meta DAT, Meta Web Apps, Android XR Glimmer).
- `smart-glasses-rokid` and `smart-glasses-vuzix`: the native display calls used by the Android and iOS targets.
