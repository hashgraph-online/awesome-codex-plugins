# Latency: budget, where the time goes, how to measure

Last checked: 2026-11-08. Verification: `docs-only` for vendor numbers (vendor claims, not our measurements). The
measurement method below is generic; we have not measured on glasses yet.

## Targets

People read captions comfortably when the words show up while the speaker is still in the same sentence.

| Moment | Good | Usable | Feels broken |
|---|---|---|---|
| First word of a sentence on the glasses after it is spoken | under 0.7 s | under 1.2 s | over 2 s |
| Final (corrected) sentence after the speaker stops | under 1.5 s | under 2.5 s | over 4 s |
| A short hint after a question ends (assistant mode) | under 1.5 s | under 3 s | over 5 s |

These are working targets for design reviews, not a published standard.

## Where the time goes

Costs without a named source are our estimates for a phone on a good network.

| Stage | Typical cost | Notes |
|---|---|---|
| Audio frame buffering | 20 to 100 ms | the frame size you send; 100 ms frames add up to 100 ms |
| VAD pre-roll and start detection | 0 to 100 ms | pre-roll sends buffered audio at once, so the cost is detection only |
| Uplink to the STT provider | 20 to 150 ms | mobile networks vary; the first connection adds TLS and WebSocket setup, so open it early |
| STT partial result | vendor claims: about 150 ms (ElevenLabs Scribe v2 Realtime), P50 303 ms (AssemblyAI multilingual), under 500 ms (Speechmatics partials) | 2026-11-08 vendor docs; see `stt-options.md` |
| STT final result | endpointing silence (Deepgram `endpointing`, default 10 ms, the example uses 300 ms) plus model time; Speechmatics finals 0.7 to 2 s depending on `max_delay`; Deepgram Flux end of turn about 260 ms (quickstart) | finals wait for silence by design |
| Server relay | under 5 ms on the server, plus one network hop | worth it for pairing and key safety |
| Downlink to the glasses or the phone app | 20 to 150 ms; Meta Ray-Ban Display link about 150 ms round trip (Meta guidance) | |
| HTTP polling fallback | half the poll interval on average (350 ms at 700 ms polling) | the price of WebViews without a WebSocket |
| Display queue | Even G2: 120 ms debounce plus about 83 ms per container write over BLE (community measurement) | coalescing trades a little latency for stability |
| Panel refresh | Meta Ray-Ban Display 30 Hz (33 ms) | |
| Text-to-speech | 100 to 400 ms to first audio on device engines | speak finals or hints only |

Typical sum for a partial: 100 ms frame + 80 ms uplink + 300 ms STT + 80 ms downlink + 200 ms Even display queue,
about 0.75 s. Most of the room for improvement is in the STT choice and the display path, not the server.

## Cutting latency

- **Open connections before speech.** STT socket and glasses link up when the session starts, not on the first word.
- **Smaller frames** (40 to 50 ms) when the provider accepts them; Deepgram suggests 80 ms chunks for Flux.
- **Show partials.** Waiting for finals adds the endpointing silence to every sentence.
- **Shorter endpointing for hints, longer for captions.** Captions can show partials while the final waits; a hint
  generator needs the final, so tune its silence threshold separately.
- **Regional endpoints** close to the user (for example Speechmatics `eu` and `global` hosts).
- **Do not re-render what did not change.** On Even G2, only send containers whose text changed; on the web, only
  replace the caption element's children.
- **Drop stale frames.** A latest-only queue (see `line-fitting.md`) never builds a backlog; a FIFO of partials does.
- **WebSocket over polling** whenever it works; keep polling as the fallback, not the default.

## How to measure

1. **Timestamps per stage.** Log `Date.now()` (or a monotonic clock) when an audio frame is captured, when it is sent,
   when each STT result arrives, when the caption message is sent, and when the display write resolves. Correlate by
   caption `seq`. Clocks on different devices drift; compare durations within one device, or sync with an NTP-style
   ping (send `t0`, server replies `t1`, offset is about `t1 - (t0 + rtt / 2)`).
2. **Glass-to-glass check.** Film the speaker's mouth (or a clap with a spoken word) and the glasses display together
   with a phone camera in slow motion (240 fps gives about 4 ms per frame). Count frames from the sound to the first
   pixel of the word. Repeat ten times and report the median and the worst case.
3. **Simulators for the display path only.** The Even Hub simulator does not model BLE timing; its console timestamps
   show your code's latency, not the link's. Meta's simulator does not reproduce the device network.
4. **Test with real audio**: a recording of two people in a cafe, played through a speaker next to the phone, gives
   repeatable runs. A WAV piped into the example server (`node server.mjs --stt deepgram < talk.wav`) is paced to
   real time, so the STT stage behaves as with a live microphone.
5. **Report percentiles**, not averages: a 1 s median with a 4 s 95th percentile feels broken.

## What the wearer notices

- Jumping text is worse than slightly late text: keep committed lines still (`line-fitting.md`).
- A frozen screen reads as a crash: show a small "listening" or "offline" state in a status line.
- After a network drop, commit the last partial, show the reconnect state, and do not replay a backlog of old partials.
