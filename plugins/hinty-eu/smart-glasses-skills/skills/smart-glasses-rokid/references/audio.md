# Audio: glasses microphone and speakers

Last checked: 2026-11-08. Verification: docs-only. The stream format is from the CXR-L 1.1.2 changelog on Rokid's
SDK overview ("PCM 16k / mono / 16bit"); the docs mark it as confirmed on a real device. The code is ours, not
compiled here.

## Options

| Source | How | Notes |
|---|---|---|
| Glasses microphone through CXR-L | `CxrSession.startAudioStream()` + `IAudioCallback` | 16 kHz mono 16-bit PCM; mouth is a few cm away, so the wearer's own voice is loud and clear |
| Phone microphone | `AudioRecord` as usual | independent of the glasses; better for the other person in a conversation |
| Glasses as a Bluetooth headset (calls) | Android SCO / iOS `AVAudioSession` with Bluetooth input | the glasses handle phone calls; whether a third-party app gets a usable SCO input while Hi Rokid holds the link is unverified |

For live captions of the person opposite you, the phone microphone is often the better choice. For dictation by
the wearer, or to tell "me" from "them", the glasses microphone is the interesting one.

## Glasses microphone with CXR-L

Prerequisites:
- `GlassPermission.MICROPHONE` in the `requestAuthorization` scopes.
- A session in `Started` (a `CUSTOM_VIEW` is enough; the scene must be built, so call it after `onSessionStarted`).
- One stream at a time.

```kotlin
import com.rokid.cxr.session.CxrSession
import com.rokid.cxr.session.IAudioCallback
import java.io.ByteArrayOutputStream

class GlassesMic(private val onPcm: (ByteArray) -> Unit, private val onState: (String) -> Unit) {
    private val callback = object : IAudioCallback {
        override fun onAudioReceived(data: ByteArray) = onPcm(data)          // may arrive off the main thread
        override fun onAudioError(errorCode: Int, errorMessage: String?) = onState("mic_error:$errorCode")
        override fun onAudioStreamStateChanged(isStreaming: Boolean) = onState(if (isStreaming) "mic_on" else "mic_off")
    }

    fun start(session: CxrSession): Boolean {
        session.addAudioCallback(callback)
        val r = session.startAudioStream()
        if (!r.isSuccess) session.removeAudioCallback(callback)
        return r.isSuccess
    }

    fun stop(session: CxrSession) {
        session.stopAudioStream()
        session.removeAudioCallback(callback)
    }
}
```

Format facts:
- 16 000 samples per second, 1 channel, 16-bit signed samples. One second is 32 000 bytes.
- Chunk sizes vary. Do not assume a fixed frame length; buffer and re-slice if your speech-to-text service wants,
  for example, 20 ms (640 bytes) or 100 ms (3200 bytes) frames.
- Byte order is not stated in the docs; Android PCM is little-endian, and that is what to expect (unverified).
- The callback can run on a binder thread. Copy the array if you hand it to another thread later, and never block
  in the callback.
- During `onSessionPaused(AI_ASSIST)` the stream pauses with the session; after `onSessionResumed` it continues by
  itself according to the docs. Keep your speech-to-text connection open across short pauses, or close it after a
  timeout to save money.

## Feeding speech-to-text

Most streaming STT services accept raw `linear16` at 16 kHz mono, so the chunks can go out unchanged over a
WebSocket. If a service wants floats or WAV:

```kotlin
/** 16-bit little-endian PCM to floats in -1..1. */
fun pcm16ToFloat(pcm: ByteArray): FloatArray {
    val out = FloatArray(pcm.size / 2)
    for (i in out.indices) {
        val lo = pcm[2 * i].toInt() and 0xFF
        val hi = pcm[2 * i + 1].toInt()
        out[i] = ((hi shl 8) or lo) / 32768f
    }
    return out
}

/** 44-byte WAV header for saving a test recording (16 kHz, mono, 16-bit). */
fun wavHeader(dataBytes: Int): ByteArray = java.nio.ByteBuffer.allocate(44).order(java.nio.ByteOrder.LITTLE_ENDIAN).apply {
    put("RIFF".toByteArray()); putInt(36 + dataBytes); put("WAVE".toByteArray())
    put("fmt ".toByteArray()); putInt(16); putShort(1); putShort(1); putInt(16000); putInt(32000); putShort(2); putShort(16)
    put("data".toByteArray()); putInt(dataBytes)
}.array()
```

First test on a new device: record 10 s, save with the header above, play it back. If it sounds like noise, the byte
order or sample rate assumption is wrong.

## Keeping it alive in the background

- A phone app that records while the screen is off needs a foreground service with type `microphone` on Android 14+,
  even when the audio comes from the glasses, because your process must stay alive to receive callbacks. Whether
  Android treats the CXR-L stream as microphone access for the purpose of the foreground-service type is unverified;
  declaring `microphone` is the safe choice if you also use the phone mic.
- Hi Rokid must stay alive too. A community project reports some Hi Rokid builds stop delivering photo callbacks after
  the phone sleeps ([TroroOrosi/rokid-docscan-starter](https://github.com/TroroOrosi/rokid-docscan-starter)); test the
  audio stream with the phone locked in a pocket before you rely on it.
- Streaming audio and showing a view both use the glasses battery. Stop the stream when you do not need it.

## Speakers and spoken output

- The glasses have speakers and act as a Bluetooth audio device for the phone (music and calls work according to
  reviews). Text-to-speech from your phone app plays in the glasses like any media audio. This is rung 5 of the
  display-text ladder and needs no SDK.
- Keep spoken hints short and do not talk over the person the wearer is listening to.
- CXR-L has no audio output API of its own; `setGlassVolume(0..100)` changes the glasses volume. Leave it to the
  wearer unless your app is the only thing playing.

## Conflicts with the Rokid assistant

With `AiInterceptMode.ALLOW_WITH_PAUSE` (the default in the quick start) the wearer can still wake the Rokid
assistant; your session pauses meanwhile, including the microphone stream. `BLOCK_AI` changes this, see
[input.md](input.md). Do not block the system assistant without telling the user why.
