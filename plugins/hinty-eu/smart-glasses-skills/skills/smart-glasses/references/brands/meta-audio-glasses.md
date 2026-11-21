# Ray-Ban Meta, Oakley Meta, Ray-Ban Meta Audio (no display; Bluetooth audio and Device Access Toolkit)

Last checked: 2026-11-08. Verification: docs-only (no hardware test yet). Snippets use standard Android and iOS audio
APIs and have not been run against these glasses.

## At a glance
- Models with camera, DAT supported: Ray-Ban Meta Gen 1 and Gen 2, Ray-Ban Meta Optics, Meta glasses, Oakley Meta HSTN,
  Oakley Meta Vanguard ([setup](https://wearables.developer.meta.com/docs/develop/dat/getting-started-toolkit/)). Gen 3
  (Sept 2026) is not in the docs yet but Meta staff confirmed support
  ([android discussion #221](https://github.com/meta/meta-wearables-dat-android/discussions/221), 2026-10-26).
- Ray-Ban Meta Audio (no camera, Sept 2026): "isn't supported by the Device Access Toolkit, on iOS or Android, in any
  released version" ([Meta staff in ios #345](https://github.com/meta/meta-wearables-dat-ios/issues/345), 2026-11-02).
  Treat it as a Bluetooth headset.
- Display: none. How your app reaches the wearer: rung 5 only, voice in the ear (TTS over Bluetooth).
- Input: touchpad and capture button. Without DAT they act as headset controls (mapping to your app unverified). With
  DAT, raw input is the beta `Inputs` capability.
- Microphone for your app: the HFP headset mic (wearer only, beamformed, 16 or 8 kHz) through the OS; DAT in-stream PCM
  (beta, needs a camera stream, LED on). The phone mic is usually better.
- Speaker: open-ear, A2DP 44.1/48 kHz stereo, or mono voice while HFP is open
  ([microphones and speakers](https://wearables.developer.meta.com/docs/develop/dat/microphones-and-speakers/)).
- Phones: any phone for plain Bluetooth. DAT 1.0.1: Android 10+, iOS 17.2+, Meta AI app V292+, glasses V128+.
- Publishing to everyone today: plain Bluetooth audio apps follow normal store rules. DAT integrations: invited Beta
  testers only, no App Store (as of 2026-11-08, see [meta-display.md](meta-display.md#publishing-and-distribution)).
- Test without hardware: any Bluetooth headset for audio routing; DAT MockDeviceKit for device states, camera and the
  touchpad tap (Meta's docs page); Meta's official skills also describe beta `Inputs` and `Speech` injection.
- Official agent skill: `npx skills add meta/meta-wearables-dat-android` / `npx skills add meta/meta-wearables-dat-ios`
  (for DAT only; plain Bluetooth audio needs no vendor SDK). For SDK details install the official skill.

## Getting words to the wearer (voice in the ear)
There is no text path. Speak short items on the phone and let the OS route them to the glasses over A2DP. This works
on every model above, needs no Meta SDK and no registration.

- One idea per utterance, a few words. Live captions read aloud are unusable; speak hints, answers, translations.
- The newest item replaces the old one (flush the queue), so the wearer never hears stale text.
- Optional short earcon first; keep the same text on the phone screen.
- Open-ear speakers leak: people nearby can hear (Meta says the same for Web App TTS). No secrets.

```kotlin
import android.content.Context
import android.media.AudioAttributes
import android.speech.tts.TextToSpeech
import java.util.Locale

class EarVoice(context: Context) {
    private var ready = false
    private val tts = TextToSpeech(context.applicationContext) { status -> ready = status == TextToSpeech.SUCCESS }
    init {
        tts.setAudioAttributes(
            AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_ASSISTANCE_NAVIGATION_GUIDANCE)
                .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                .build()
        )
    }
    fun say(text: String, locale: Locale = Locale.US) {
        if (!ready) return
        tts.setLanguage(locale)
        tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "hint") // QUEUE_FLUSH: newest replaces the rest
    }
    fun close() = tts.shutdown()
}
```

```swift
import AVFoundation

final class EarVoice {
  private let synth = AVSpeechSynthesizer()
  init() throws {
    // Output only: A2DP to the glasses. If you also record from the phone mic, use .playAndRecord with
    // .allowBluetoothA2DP (not .allowBluetoothHFP) so input stays on the phone and output stays on A2DP.
    // Trade-off: .duckOthers implies .mixWithOthers, and a mixable session never becomes Now Playing, so touchpad
    // taps keep controlling the user's music and never reach MPRemoteCommandCenter. To use taps as app input, drop
    // the option (a non-mixable session pauses other audio) and see input.md, "Media keys on iOS".
    try AVAudioSession.sharedInstance().setCategory(.playback, mode: .spokenAudio, options: [.duckOthers])
    try AVAudioSession.sharedInstance().setActive(true)
  }
  func say(_ text: String, language: String = "en-US") {
    synth.stopSpeaking(at: .immediate) // newest replaces the rest
    let u = AVSpeechUtterance(string: text)
    u.voice = AVSpeechSynthesisVoice(language: language)
    synth.speak(u)
  }
}
```

On Android keep the phone mic on `AudioRecord` and never call `setCommunicationDevice(...)` / start SCO unless you
want the glasses mic: that switches the glasses to HFP and output drops to mono.

## Audio: which microphone

| Source | Hears | Status | Cost |
|---|---|---|---|
| Phone mic | Everyone near the phone | Any app | None; best for captioning other people |
| Glasses mic via HFP (OS API) | Mostly the wearer (beamformed) | Any app | Output drops to 16/8 kHz mono; can end a running DAT session (status below) |
| DAT in-stream PCM 16/44.1/48 kHz | Ambient, not beamformed | Beta, not in production channels | Needs a camera stream; capture LED stays on ([ios #318](https://github.com/meta/meta-wearables-dat-ios/issues/318)) |
| DAT `Speech` (on-glasses ASR) | Text, not audio | Beta | Stops reporting after about a minute ([known issues](https://wearables.developer.meta.com/docs/develop/dat/knownissues/), [ios #360](https://github.com/meta/meta-wearables-dat-ios/issues/360)) |

For the wearer's own voice (commands, dictation) HFP is the right mic. For captions of the other person use the phone.

HFP and DAT sessions, as of 2026-11-08 (confidence: vendor staff statements, unverified by us):
- On glasses firmware `72387580077200100` HFP ended DAT camera sessions within milliseconds, even in Meta's documented
  order ([android #206](https://github.com/meta/meta-wearables-dat-android/issues/206), still open). Meta staff
  (2026-10-13): the fix is a glasses software update, not an SDK release.
- Meta staff (2026-11-04, [android #210](https://github.com/meta/meta-wearables-dat-android/issues/210)): glasses
  software 192.1 "should cover most of the displayless cases". Nobody in either thread has confirmed it yet, and that
  label does not match the glasses version format in Meta's docs (V128+) or in the Meta AI app (129.0.0.218.272 in
  [ios #342](https://github.com/meta/meta-wearables-dat-ios/issues/342)), so we cannot tell you which installed
  version has the fix. The Ray-Ban Display fix comes "at a later date".
- So: log the glasses software version, test HFP plus your DAT session on the wearer's pair, and keep the phone mic as
  the default.

## What DAT adds on these glasses
- Stable: camera stream, device state (`batteryLevel`, `donState` worn or not, `hingeState`, `thermalLevel`).
  Useful for a captions or assistant app: pause when the glasses come off.
- Beta, dev and Beta channels only: photo capture, in-stream audio, `Inputs`, `Motion` (rotated 90 degrees on displayless
  glasses, known issue), `Speech`, voice invocations ("Hey Meta, start <app>").
- No audio output API: speech and earcons still go through A2DP as above.
- While a session runs without interactive content, a single touchpad tap pauses the session and tap-and-hold stops it
  ([inputs](https://wearables.developer.meta.com/docs/develop/dat/inputs/)), so a DAT session takes over the tap.
- Verdict for captions and assistants (our reading): plain Bluetooth plus the phone mic covers the core; add DAT only for
  wear detection or camera features, and only for testers until publishing opens.
- Camera, only if you need it: streams that stall in `waitingForDevice`
  ([ios #276](https://github.com/meta/meta-wearables-dat-ios/issues/276)), undocumented HEVC framing
  ([android #155](https://github.com/meta/meta-wearables-dat-android/issues/155)), FPS drops with an active encoder
  ([android #45](https://github.com/meta/meta-wearables-dat-android/issues/45)).

## Input
- Without DAT the glasses behave as a headset: touchpad gestures control playback and volume on the phone. Whether your
  app gets them through `MediaSession` (Android) or `MPRemoteCommandCenter` (iOS) is unverified on these glasses; on
  iOS it can only work with a non-mixable audio session (no `.duckOthers`), see [input.md](../input.md).
- With DAT `Inputs` (beta): a touchpad double tap arrives as `Select`, a swipe as `Nav` (the wearer can invert
  directions), the capture button as `Capture` with `SHORT_PRESS`, `HOLD`, `DOUBLE_PRESS`. A double press also sends a
  `SHORT_PRESS` first: buffer it. Inputs stop after doff and don with wear detection on: re-add the capability.
- "Hey Meta" belongs to Meta AI. Your app can only answer DAT voice invocations (beta).

## Testing without hardware
- Any Bluetooth headset reproduces A2DP output and the HFP switch; do this before blaming the glasses.
- DAT `MockDeviceKit` ([docs](https://wearables.developer.meta.com/docs/develop/dat/mock-device-kit/), read
  2026-11-08): pair a mock Ray-Ban Meta, power it, don or doff, unfold, feed the camera from a file or the phone camera,
  simulate a touchpad tap (pause and resume) and tap-and-hold (stop), set permission results. The docs page lists
  nothing for audio or speech; Meta's official agent skills for the beta capabilities describe injecting `Inputs`
  events and `Speech` transcriptions through the mock glasses (unverified, not on the docs page). It does not reproduce
  HFP conflicts, reserved gestures or real input mapping.

## Publishing and distribution
- Plain Bluetooth audio app: Google Play and App Store as usual; no Meta component is involved (our reading).
- Countries: Ray-Ban Meta is sold in 35 countries, Oakley Meta in 31 ([help center](https://www.meta.com/help/ai-glasses/4961066940605960/),
  2026-11-08). The [FAQ](https://developers.meta.com/wearables/faq/) limits the full toolkit, including Developer
  Center, to those countries.
- DAT: as for Display. One invite-only Beta channel, Google Play allowed but registration gated, App Store blocked by
  MFi (see [meta-display.md](meta-display.md#publishing-and-distribution)). The
  [Acceptable Use Policy](https://wearables.developer.meta.com/acceptable-use-policy) binds DAT apps even unpublished:
  no covert recording, no hiding the capture LED, no voice or face identification of people without Meta approval.

## Pitfalls
- Ray-Ban Meta Audio never appears in `Wearables.devices` or never connects
  ([android #222](https://github.com/meta/meta-wearables-dat-android/issues/222), [ios #345](https://github.com/meta/meta-wearables-dat-ios/issues/345)):
  not supported, nothing on your side fixes it.
- HFP ended DAT camera sessions on firmware `72387580077200100`, even in the documented order (settle HFP first, then
  start the stream) ([android #206](https://github.com/meta/meta-wearables-dat-android/issues/206), open). The fix is
  glasses-side; Meta says software 192.1 covers most displayless cases (2026-11-04, unconfirmed, see Audio above).
- `DAT_APP_ON_THE_GLASSES_UPDATE_REQUIRED` on Gen 2 ([android #192](https://github.com/meta/meta-wearables-dat-android/issues/192)):
  see the recovery order in [meta-display.md](meta-display.md#pitfalls).
- After the glasses v128 update, camera capture fails until the glasses reboot (dev and Beta, known issue).
- iPhone 17 on iOS 26: HFP may carry no audio in either direction; Meta's fix is iOS 27 (known issue).

## Official resources
- https://wearables.developer.meta.com/docs/develop/dat/microphones-and-speakers/, https://wearables.developer.meta.com/docs/develop/dat/inputs/
- https://github.com/meta/meta-wearables-dat-android, https://github.com/meta/meta-wearables-dat-ios
