# Streaming speech-to-text options

Checked: 2026-11-08 on the vendors' public pricing and docs pages (most pages carry no date). Prices are
pay-as-you-go list prices for **streaming** in USD; volume and committed-use prices are lower. Latency figures are
vendor claims, not our measurements. Verification of the integrations: only the Deepgram adapter in
`examples/live-captions/server/stt/deepgram.mjs` ran (Nova-3, 2026-11-08); everything else is `docs-only`.
No provider is recommended over the others; pick by language, latency, price and where the audio may go.

## Cloud streaming

| Provider and streaming model | List price | Partial results | Latency claim | Streaming diarization | Browser credential |
|---|---|---|---|---|---|
| Deepgram Nova-3 (`wss://api.deepgram.com/v1/listen`) | $0.0077/min ($0.46/h); multilingual $0.0092/min; diarization +$0.0020/min; $200 credit | yes (`interim_results=true`) | "comparable to Nova-2" | yes | temporary JWT from `POST /v1/auth/grant` (TTL 30 s default) |
| Deepgram Flux (`wss://api.deepgram.com/v2/listen`, launched 2025-10-01) | $0.0077/min English, $0.0078/min multilingual | turn events | about 260 ms end of turn (quickstart) | no data | same as above |
| AssemblyAI Universal-Streaming (`wss://streaming.assemblyai.com/v3/ws`) | $0.15/h; Universal-3.6 Pro realtime $0.45/h; diarization +$0.12/h; billed for open socket time; $50 credit | yes (`Turn` messages) | P50 303 ms (multilingual, 2025-11-12 post) | yes (`speaker_labels=true`) | temporary token from `token.assemblyai.com`, 1 to 600 s |
| Speechmatics real-time (`wss://eu.rt.speechmatics.com/v2`) | Standard $0.45/h, Enhanced $0.80/h; diarization included; $100 credit | yes (`enable_partials`) | partials under 500 ms, finals 0.7 to 2 s (`max_delay`) | yes | temporary JWT as `?jwt=` |
| ElevenLabs Scribe v2 Realtime (`wss://api.elevenlabs.io/v1/speech-to-text/realtime`) | $0.39/h | yes (`partial_transcript`) | about 150 ms | not documented | single-use token, 15 min |
| Google Cloud STT V2, Chirp 3 (gRPC `StreamingRecognize`) | V2 standard $0.016/min ($0.96/h) for the first 500k min/month; Chirp 3 price line unverified | interim results on Chirp 3 unverified | not published | no (batch only) | none documented (unverified) |
| Microsoft Azure AI Speech (Speech SDK) | real-time $1.00/h (eastus, Azure price API); free tier 5 h/month | yes (`recognizing` events) | not published | yes (`ConversationTranscriber`) | 10-minute token from `issueToken` |
| OpenAI `gpt-live-transcribe` (`wss://api.openai.com/v1/realtime?intent=transcription`) | $0.017/min ($1.02/h); `gpt-4o-mini-transcribe` $0.003/min, `gpt-4o-transcribe` $0.006/min | yes (`...transcription.delta`, deltas) | `delay` setting from minimal to xhigh; no figure | no | ephemeral client secret, 10 s to 2 h |
| Amazon Transcribe streaming | $0.01/min ($0.60/h); 60 free min/month for 12 months | yes (`IsPartial`, unverified) | not published | unverified | SigV4 presigned URL |
| Gladia Solaria-1 live (`POST /v2/live` then WebSocket) | from EUR 0.68/h (USD price unverified); EUR 50 credit | yes (`receive_partial_transcripts`) | not published | no (async only) | the returned WebSocket URL carries its own token |

Sources: https://deepgram.com/pricing, https://developers.deepgram.com/reference/speech-to-text/listen-streaming,
https://developers.deepgram.com/docs/flux/quickstart, https://www.assemblyai.com/pricing,
https://www.assemblyai.com/docs/speech-to-text/universal-streaming, https://www.speechmatics.com/pricing,
https://docs.speechmatics.com/api-ref/realtime-transcription-websocket, https://elevenlabs.io/pricing/api,
https://elevenlabs.io/docs/api-reference/speech-to-text/v-1-speech-to-text-realtime,
https://cloud.google.com/speech-to-text/pricing, https://docs.cloud.google.com/speech-to-text/v2/docs/chirp_3-model,
https://azure.microsoft.com/en-us/pricing/details/cognitive-services/speech-services/,
https://developers.openai.com/api/docs/pricing, https://developers.openai.com/api/docs/guides/realtime-transcription,
https://aws.amazon.com/transcribe/pricing/, https://www.gladia.io/pricing, https://docs.gladia.io/chapters/live-stt/getting-started

### Languages (streaming, 2026-11-08)

- Deepgram Nova-3: about 63 languages monolingual, about 55 in the multilingual (code-switching) mode, including
  Japanese, Chinese, Korean, Arabic, Hebrew and Hindi. Flux multilingual: 10 languages.
- AssemblyAI: Universal-3.6 Pro 32 languages; Universal-Streaming Multilingual 6 (en, es, pt, de, fr, it). CJK and
  Arabic on 3.6 Pro unverified.
- Speechmatics: Japanese, Mandarin, Korean, Arabic, Hebrew and Hindi listed without a real-time restriction.
- ElevenLabs Scribe: "90+ languages"; which of them stream well is unverified.
- Google Chirp 3: 29 languages generally available for streaming plus 82 in preview.
- Amazon Transcribe: Japanese, Chinese, Korean, Arabic, Hebrew and Hindi support streaming.
- Gladia: "100+ languages".

### Message names for writing an adapter

Normalise each provider to `onText(wholeSentenceSoFar, final)` (the interface of the example server's adapters):

| Provider | Partial | Final | Notes |
|---|---|---|---|
| Deepgram v1 | `Results` with `is_final:false` | `is_final:true` closes a segment, `speech_final:true` or `UtteranceEnd` ends the sentence | join `is_final` segments until `speech_final`; send `KeepAlive` during silence, `CloseStream` at the end |
| Deepgram Flux | `TurnInfo` | `EndOfTurn` (`EagerEndOfTurn` / `TurnResumed` for early guesses) | v2 endpoint only, `encoding` and `sample_rate` required |
| AssemblyAI v3 | `Turn` with `end_of_turn:false` | `Turn` with `end_of_turn:true` (`turn_is_formatted` for the formatted copy) | auth header without "Bearer"; send `Terminate` |
| Speechmatics | `AddPartialTranscript` | `AddTranscript`, `EndOfUtterance` | first message `StartRecognition` with `audio_format` and `transcription_config` |
| ElevenLabs | `partial_transcript` | `committed_transcript` | audio as base64 in `input_audio_chunk`; `commit_strategy` `vad` or `turn_prediction` |
| OpenAI | `conversation.item.input_audio_transcription.delta` (append deltas) | `...transcription.completed` | 24 kHz PCM; `gpt-live-transcribe` has no server VAD, commit with your own VAD |
| Azure Speech SDK | `recognizing` | `recognized` | use the SDK; the raw WebSocket protocol is not documented |
| Gladia | `transcript` with `is_final:false` | `is_final:true` | end with `stop_recording` |

## On device

| Engine | Platforms | Streaming and partials | Limits to plan for |
|---|---|---|---|
| Android `SpeechRecognizer` | Android; on-device via `createOnDeviceSpeechRecognizer` (API 31+) | `EXTRA_PARTIAL_RESULTS` (the service may ignore it) | "not intended to be used for continuous recognition"; main thread only; `EXTRA_SEGMENTED_SESSION` for long form (API 33+); language packs via `checkRecognitionSupport` / `triggerModelDownload` (API 33+) |
| iOS `SpeechAnalyzer` + `SpeechTranscriber` | iOS and macOS 26+ | volatile results (`volatileResults` reporting option) | models downloaded through `AssetInventory`; `DictationTranscriber` on older devices |
| iOS `SFSpeechRecognizer` | iOS 10+ | `shouldReportPartialResults` (default true) | plan for one minute of audio per request with server recognition; `requiresOnDeviceRecognition` (iOS 13+) only where `supportsOnDeviceRecognition`, less accurate |
| whisper.cpp (MIT) | everywhere, CPU and GPU | `whisper-stream` re-transcribes a rolling window (for example `--step 500 --length 5000`) or runs in VAD mode | words in the window change until they leave it; tune step and length |
| WhisperKit (MIT, Argmax) | Apple platforms | CLI `--stream` | real-time with speakers and a server mode are in the paid Pro SDK |
| faster-whisper (MIT) | desktop and server | not streaming itself; wrappers such as WhisperLive add it | Silero VAD built in |
| Moonshine (MIT, most models) | Android, iOS, WASM and others | built for live streaming | speech-to-text languages: en, es, de, zh, ja, ko, vi, tl, uk, ar; some legacy non-English models are non-commercial |
| NVIDIA Parakeet TDT 0.6B v3 (CC-BY-4.0) | GPU servers, desktops | chunked streaming through NeMo | 25 European languages |

Sources: https://developer.android.com/reference/android/speech/SpeechRecognizer,
https://developer.android.com/reference/android/speech/RecognizerIntent,
https://developer.apple.com/documentation/speech/speechanalyzer,
https://developer.apple.com/documentation/speech/sfspeechrecognizer,
https://github.com/ggml-org/whisper.cpp/tree/master/examples/stream, https://github.com/argmaxinc/WhisperKit,
https://github.com/SYSTRAN/faster-whisper, https://github.com/moonshine-ai/moonshine,
https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3

## Browser: Web Speech API

- `SpeechRecognition` (prefixed `webkitSpeechRecognition` in older versions) with `interimResults = true` gives partial
  results; results from `resultIndex` on are the current sentence.
- Chrome desktop: prefixed since 33, unprefixed with on-device options (`processLocally`, `SpeechRecognition.available()`,
  `install()` for language packs) since 139. Default recognition is server-based: the audio goes to a web service.
- Chrome on Android: `continuous` "can be set, but has no effect", so restart in `onend`; `processLocally` not supported.
- Safari: prefixed since 14.1, `continuous` since 17.
- Firefox: Mozilla announced on-device-only `SpeechRecognition` for desktop (intent posted 2026-09-16); not confirmed in a
  release yet.
- Android WebView (which many glasses apps and plugin hosts use): reports of it failing; do not rely on it.

Source: https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API/Using_the_Web_Speech_API and MDN
browser-compat-data (https://github.com/mdn/browser-compat-data/blob/main/api/SpeechRecognition.json, 2026-11-02).

## How to choose

1. **Languages first.** Check the streaming model's list for every language you promise, and test short utterances:
   a developer reports cloud STT doing badly on short Japanese phrases
   (https://github.com/even-realities/everything-evenhub/issues/9, comment of 2026-08-17).
2. **Latency second.** Run your own partial-latency test with your audio path (`latency.md`); vendor claims are
   measured on their best path.
3. **Where the audio may go.** Medical, legal or classroom use may rule out cloud processing; then on-device engines,
   or a provider with a regional endpoint (Speechmatics EU and global endpoints, for example).
4. **Billing model.** Per audio second sent rewards a VAD gate; per open-socket time (AssemblyAI) rewards closing the
   socket during long silences.
5. **Offline fallback.** A cloud primary with an on-device fallback when the network drops keeps captions alive on
   the move; mark the fallback text so the wearer knows quality changed.
6. **Keys.** Never ship a long-lived provider key in a glasses page, plugin or app. Use a server relay or the
   provider's short-lived browser token.
