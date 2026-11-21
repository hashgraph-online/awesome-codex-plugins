# Audio routing for glasses apps

Read this before you capture speech or play audio in a glasses app: which microphone to use, how Bluetooth profiles
interact, what each brand gives you, and how to set up the audio session on Android and iOS.

Last checked: 2026-11-08. Verification: docs-only (no hardware test yet). The snippets use public Android and AVFAudio
APIs, were written for this file and have not been compiled here or run against any glasses.

## Decide first

| You need | Use | Why |
|---|---|---|
| Captions or translation of the **other person** | Phone microphone | Glasses mics are tuned for the wearer; Meta says HFP beamforming "isolates the wearer's voice" ([microphones and speakers](https://wearables.developer.meta.com/docs/develop/dat/microphones-and-speakers/)). A phone on the table hears the room. |
| The **wearer's** voice (commands, dictation, "me" vs "them") | Glasses mic: the vendor SDK stream if there is one, HFP otherwise | Mouth is centimetres away; a separate stream from the phone mic gives you a speaker hint for free |
| Speech or earcons **to** the wearer | Bluetooth A2DP output, phone mic for input | Keeps the glasses in stereo and out of HFP |
| Both mics at once | Vendor PCM stream + phone `AudioRecord` / `AVAudioEngine` | Only possible where the glasses mic arrives as data (Even, Rokid, Mentra, Halo), not as an OS audio route |

Default for captions, assistants and translators: phone mic, your own speech-to-text, text to the display, TTS over
A2DP only on demand. The live pipeline (STT, partial results, line fitting) is in
[`smart-glasses-live-captions`](../../smart-glasses-live-captions/SKILL.md).

## Bluetooth profiles in short

- **A2DP** is output only, 44.1 or 48 kHz stereo. It is what TTS and music use.
- **HFP** (audio over SCO) is two-way mono voice at 16 kHz or 8 kHz. The profiles are mutually exclusive: opening the
  glasses mic over HFP moves output to mono voice quality for everything on the phone.
- A **vendor SDK stream** (Even `audioControl`, Rokid `startAudioStream`, Mentra `session.mic`, Halo Lua) carries PCM
  as data over the vendor's link. It does not change the phone's audio route, so A2DP output keeps working.
- Any app on the phone can open HFP and change the route under you (a call, a voice assistant, a messenger). Watch
  route changes instead of assuming the state you set is still in force.

## What each brand gives your app (as of 2026-11-08)

| Glasses | Glasses mic for your app | Speaker | Main catch | Details |
|---|---|---|---|---|
| Even Realities G2 | PCM over the SDK, 16 kHz mono 16-bit LE; the same call can feed the phone mic | None, no audio API | `getUserMedia` fails in the iOS WebView; `audioControl` can stay `false` until reopen | [even-g2.md](brands/even-g2.md#audio) |
| Meta Ray-Ban Display (DAT) | HFP through the OS; in-stream PCM is beta and needs a camera stream | Open-ear, A2DP | Opening HFP ends the Display session on current glasses software | [meta-display.md](brands/meta-display.md#audio) |
| Meta Ray-Ban Display Web Apps | None | `speechSynthesis`, Web Audio on the glasses | Capture on the phone | [meta-display.md](brands/meta-display.md#audio) |
| Ray-Ban Meta, Oakley Meta | HFP through the OS; DAT in-stream PCM (beta, capture LED on) | A2DP | HFP drops output to mono; it ended DAT camera sessions on some firmware, Meta says software 192.1 fixes most cases (unconfirmed) | [meta-audio-glasses.md](brands/meta-audio-glasses.md#audio-which-microphone) |
| Ray-Ban Meta Audio | HFP only, no DAT support | A2DP | Treat it as a plain headset | [meta-audio-glasses.md](brands/meta-audio-glasses.md) |
| Rokid Glasses | PCM over CXR-L, 16 kHz mono 16-bit | Yes, phone media audio | Stream pauses while the Rokid assistant runs | [Rokid audio](../../smart-glasses-rokid/references/audio.md) |
| Vuzix Z100 | None | None | Phone mic in, phone or earbuds out | [vuzix-z100.md](brands/vuzix-z100.md#audio) |
| Android XR glasses | HFP at 16 kHz after `RECORD_AUDIO`, `BLUETOOTH_CONNECT` and the projected permission flow | Yes | Policy forbids persistent background recording | [android-xr.md](brands/android-xr.md) |
| MentraOS | `session.mic` chunks, PCM or LC3 | Depends on the glasses | Shares the mic with the Mentra assistant | [mentra.md](brands/mentra.md) |
| Brilliant Labs Halo | Two mics, PCM or LC3, started from Lua over BLE | Bone conduction (separate audio characteristic) | Small BLE bandwidth | [brilliant-labs.md](brands/brilliant-labs.md) |
| Snap Specs | ASR module on the glasses | Yes | Mic plus internet needs Transparent Permission (prompt and LED) | [snap-spectacles.md](brands/snap-spectacles.md) |
| USB-C display glasses | Varies; some appear as a USB audio device | Varies | Can take over the phone's capture route | [usb-c-displays.md](brands/usb-c-displays.md#audio) |
| Standalone Android (RayNeo X3 Pro, INMO Air3) | `AudioRecord` on the glasses (unverified) | Yes | Battery lasts hours, not a day | [standalone-android-glasses.md](brands/standalone-android-glasses.md#audio) |

## Conflicts you will hit

- **Meta: HFP versus camera and display.** HFP ends a DAT Display session ([android #210](https://github.com/meta/meta-wearables-dat-android/issues/210),
  [ios #342](https://github.com/meta/meta-wearables-dat-ios/issues/342)) and DAT camera sessions
  ([android #206](https://github.com/meta/meta-wearables-dat-android/issues/206), firmware `72387580077200100`); on
  2026-11-04 Meta staff said glasses software 192.1 covers most displayless cases and the Display fix comes later
  (unconfirmed, see [meta-audio-glasses.md](brands/meta-audio-glasses.md#audio-which-microphone)); recording over Bluetooth can show the
  phone-call UI on the display ([ios #186](https://github.com/meta/meta-wearables-dat-ios/issues/186)); photo capture
  fails with the session in HFP ([ios #260](https://github.com/meta/meta-wearables-dat-ios/issues/260)). Meta's order
  for camera plus HFP: start HFP, let the route settle (their sample waits 2 s), check that the route contains
  `.bluetoothHFP`, then start the stream. A phone call ends the session too. On iPhone 17 with iOS 26, HFP may carry no
  audio at all (Meta known issue, fixed in iOS 27).
- **Mentra: the assistant hears the same mic.** A voice miniapp cannot suppress the host assistant
  ([#3893](https://github.com/Mentra-Community/MentraOS/issues/3893), open); a maintainer's suggestion is to have the
  user turn Mentra AI off, which is optional. Say so in onboarding.
- **Rokid: the assistant pauses you.** With `AiInterceptMode.ALLOW_WITH_PAUSE` the wearer can wake the Rokid assistant
  and your session, including the mic stream, pauses until `onSessionResumed`.
- **Android: other apps take the mic.** Since Android 10 two ordinary apps never capture at once; the other one gets
  silence. The assistant, a call (`MODE_IN_COMMUNICATION`) and privacy-sensitive sources (`VOICE_COMMUNICATION`,
  `CAMCORDER`) win ([sharing audio input](https://developer.android.com/media/platform/sharing-audio-input)). Detect it
  with `AudioRecordingConfiguration.isClientSilenced()` instead of debugging an empty transcript.
- **USB-C glasses and headsets take the input.** When glasses enumerate as USB audio, Android may record from them.
  Pin the built-in mic (code below).
- **Android XR:** apps "must not change or disable system-enforced audio denoisers"
  ([quality guidelines](https://developer.android.com/docs/quality-guidelines/android-xr/augmented)).

## Android setup (Kotlin, minSdk 29 for the silence callback)

```kotlin
import android.annotation.SuppressLint
import android.media.*
import java.util.concurrent.Executors

/** Phone mic, 16 kHz mono PCM16, pinned to the built-in mic so the glasses stay on A2DP. */
class PhoneMic(private val am: AudioManager, private val onPcm: (ByteArray, Int) -> Unit, private val onSilenced: (Boolean) -> Unit) {
    private var record: AudioRecord? = null
    @Volatile private var running = false

    @SuppressLint("MissingPermission") // the caller checked RECORD_AUDIO
    fun start() {
        val min = AudioRecord.getMinBufferSize(16_000, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT)
        val r = AudioRecord(MediaRecorder.AudioSource.VOICE_RECOGNITION, 16_000,
            AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT, maxOf(min, 3200) * 2)
        am.getDevices(AudioManager.GET_DEVICES_INPUTS).firstOrNull { it.type == AudioDeviceInfo.TYPE_BUILTIN_MIC }
            ?.let { r.setPreferredDevice(it) }
        r.registerAudioRecordingCallback(Executors.newSingleThreadExecutor(), object : AudioManager.AudioRecordingCallback() {
            override fun onRecordingConfigChanged(configs: List<AudioRecordingConfiguration>) {
                r.activeRecordingConfiguration?.let { onSilenced(it.isClientSilenced) } // assistant or a call took the mic
            }
        }) // must be registered before startRecording()
        record = r; running = true
        r.startRecording()
        Thread { val buf = ByteArray(640); while (running) { val n = r.read(buf, 0, buf.size); if (n > 0) onPcm(buf, n) } }.start()
    }

    fun stop() { running = false; record?.run { stop(); release() }; record = null }
}

/** Only when you want the wearer's voice over HFP (API 31+). Output drops to mono; ends a Meta Display session (2026-11). */
fun useGlassesHfpMic(am: AudioManager): Boolean {
    val sco = am.availableCommunicationDevices.firstOrNull { it.type == AudioDeviceInfo.TYPE_BLUETOOTH_SCO } ?: return false
    am.mode = AudioManager.MODE_IN_COMMUNICATION
    return am.setCommunicationDevice(sco)
}
fun releaseGlassesHfpMic(am: AudioManager) { am.clearCommunicationDevice(); am.mode = AudioManager.MODE_NORMAL }
```

`startBluetoothSco()` is deprecated since API 34; use `setCommunicationDevice`. Never call either for the phone-mic path.

## iOS setup (Swift)

```swift
import AVFoundation

enum MicSource { case phone, glassesHFP }

func configureAudio(_ source: MicSource) throws {
    let s = AVAudioSession.sharedInstance()
    switch source {
    case .phone: // phone mic in, A2DP out: the glasses stay in stereo
        try s.setCategory(.playAndRecord, mode: .default, options: [.allowBluetoothA2DP, .defaultToSpeaker])
        try s.setActive(true)
        if let mic = s.availableInputs?.first(where: { $0.portType == .builtInMic }) { try s.setPreferredInput(mic) }
    case .glassesHFP: // the wearer's voice; output becomes mono voice quality
        try s.setCategory(.playAndRecord, mode: .default, options: [.allowBluetoothHFP]) // pre-Xcode 26 name: .allowBluetooth
        try s.setActive(true)
        if let hfp = s.availableInputs?.first(where: { $0.portType == .bluetoothHFP }) { try s.setPreferredInput(hfp) }
    }
}
```

Rules from Apple's docs that decide the route:
- Mode `.voiceChat` (and `.videoChat`) applies `.allowBluetoothHFP` by itself, and using the voice-processing I/O unit
  sets `.voiceChat` implicitly ([voiceChat](https://developer.apple.com/documentation/avfaudio/avaudiosession/mode-swift.struct/voicechat)).
  So `inputNode.setVoiceProcessingEnabled(true)` for echo cancellation can pull a pair of glasses into HFP (our
  inference from those docs, unverified on glasses). Keep mode `.default` on the phone-mic path.
- With both `.allowBluetoothHFP` and `.allowBluetoothA2DP` set, a device that supports both is routed to HFP
  ([allowBluetoothA2DP](https://developer.apple.com/documentation/avfaudio/avaudiosession/categoryoptions-swift.struct/allowbluetootha2dp)).
- `.allowBluetooth` and `.allowBluetoothHFP` have the same raw value; Xcode 26 flags the old name.
- `.bluetoothHighQualityRecording` (iOS 26+) works only on routes that support it, such as certain AirPods, not in the
  EU, and Apple does not recommend it for real-time use.
- Observe `AVAudioSession.routeChangeNotification` and `AVAudioEngineConfigurationChange`; after a route change the
  sample rate can change and the engine stops, so reinstall your tap and restart it.

## Playing TTS while you record

- **Audio focus (Android).** Recording needs no focus. For each utterance request
  `AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK` with speech `AudioAttributes` and abandon it in `onDone`. Android XR asks apps to
  "request and give up audio focus as appropriate". Use `QUEUE_FLUSH` so the newest hint replaces stale ones.
- **iOS.** `AVSpeechSynthesizer` plays through your app's session, so the category above applies. Do not switch to
  `.playback` mid-session or you lose the input; stay in `.playAndRecord` with `.allowBluetoothA2DP`.
- **Echo.** An open-ear speaker sits next to the glasses mic, so a glasses-mic transcript will contain your own TTS.
  The phone mic picks up less but not nothing. Cheapest fix: while you speak plus about 300 ms after, drop the
  frames or tag the STT results and discard them. Platform echo cancellation (`AcousticEchoCanceler.isAvailable()` on
  Android, voice processing on iOS) varies by device and on iOS has the HFP side effect above. Measure before you rely
  on it.
- **No speaker on the glasses** (Even G2, Vuzix Z100): TTS goes to the phone speaker or the user's earbuds. Ask which.
  Keep spoken items to one short sentence; see [ui-small-screens.md](ui-small-screens.md) for wording.

## Background audio

- **Android.** Since Android 9 an app without a visible UI or a foreground service records silence. On Android 14+
  declare `foregroundServiceType="microphone"` with `FOREGROUND_SERVICE_MICROPHONE`; `RECORD_AUDIO` is a while-in-use
  permission, so start that service while your app is visible, never from the background or `BOOT_COMPLETED`
  ([service types](https://developer.android.com/develop/background-work/services/fgs/service-types)). Add
  `connectedDevice` if the service also keeps a glasses link. The companion app (Hi Rokid, Vuzix Connect, Meta AI)
  must survive battery managers too.
- **iOS.** `UIBackgroundModes` `audio` keeps a recording alive that started in the foreground. Starting one from the
  background fails with `cannotStartRecording` in developer reports
  ([forum thread](https://developer.apple.com/forums/thread/120038)), so start sessions on a user action.
  `bluetooth-central` delivers BLE events but does not keep a suspended app running. Guideline 2.5.4 allows background
  modes only for their intended purpose. Handle interruptions (calls) and expect reactivation to fail while
  backgrounded.
- **Even Hub plugins** run in a WebView that iOS can suspend or kill; there is no background audio output at all
  ([#26](https://github.com/even-realities/everything-evenhub/issues/26)).

## Privacy rules

Recording other people is regulated by law and by every vendor. This is engineering guidance, not legal advice.

- **Law.** Some jurisdictions require consent from everyone in a recorded conversation; the US rules differ by state
  ([RCFP recording guide](https://www.rcfp.org/reporters-recording-guide/)), and in the EU voice is personal data under
  GDPR. Live captions that keep no audio are easier to defend than stored recordings.
- **Apple** 2.5.14: explicit consent and "a clear visual and/or audible indication when recording"
  ([guidelines](https://developer.apple.com/app-store/review/guidelines/)). 5.1.1: purpose strings that describe the use.
- **Google Play** [User Data policy](https://support.google.com/googleplay/android-developer/answer/10144311): prominent
  disclosure before collecting audio, matching Data safety answers.
- **Android XR** ([audio safety](https://developer.android.com/docs/quality-guidelines/android-xr/augmented)): no
  persistent background recording or transcription outside a user-initiated task, no identifying non-wearer voices,
  no changing system denoisers or LED behaviour, and Back must really stop the sensors.
- **Meta** [Acceptable Use Policy](https://wearables.developer.meta.com/acceptable-use-policy) (binds unpublished apps):
  no covert recording, no hiding the capture LED, no identifying people by voice without an approved exception;
  captioning with "narrow purpose, short retention, obvious to bystanders" is fine.
- **Snap**: mic plus internet in one Lens only through [Transparent Permission](https://developers.snap.com/spectacles/permission-privacy/transparent-permission)
  (prompt plus LED).
- **Even Hub review** wants a privacy policy that covers every declared permission
  ([app submission](https://hub.evenrealities.com/docs/ship/app-submission)).
- **In your UI:** start capture only on a user action, show "listening" on the glasses and the phone, stop when the
  glasses come off (DAT `donState`, Rokid wearing events), keep no audio by default.
