# Default numbers, and when to change them

The sources below disagree, usually because they edit different formats. Each row gives a default and the condition that changes it. **None of these numbers was tested against viewer outcomes by anyone we read**, and no blind test of an agent's cut against an editor's exists. They describe what careful people ship. A measured reference in the same format beats this table.

## Cutting speech

| Topic | Default | Change it when | Who |
|---|---|---|---|
| Where to cut | The quietest 10 ms slice between words, never inside a word | Never | @nateherk, @condzxyz |
| Silence threshold | Measure this file's room and voice, then sit between them | -38 dBFS is only a first probe. Noisy phone footage: near -30. Clean TTS: down to -44 | @condzxyz, @Emarky, @finnardley |
| Padding before a first word | 50 ms | 35 ms for clean TTS with true digital silence | video-use, @condzxyz, @finnardley |
| Padding after a last word | 80 ms mid-thought, 150 ms at a sentence end. Stay inside 30-200 ms | 150-200 ms everywhere if timings are Whisper and word ends clip | video-use, @condzxyz, @ladprofit, @darrrragh |
| Audio fade at a join | 30 ms, inside the padding | 8 ms when padding is under 50 ms or the cut sits in measured silence | video-use, @condzxyz |
| Pause inside a thought | Over 0.32 s becomes 0.22 s | First pass on unknown material: cut only over 0.5 s, then review. Story or documentary: loosen by ear | @condzxyz, @Emarky |
| Pause after a sentence | 0.36 s | Ads: no gap over 0.45 s anywhere | @condzxyz, @ladprofit |
| Speaker handoff | 400-600 ms | | video-use |
| Beat before a price or punchline | Keep it, about 0.3 s. List these for review | No detector can tell a deliberate pause from a stumble | @ladprofit, @cathrynlavery |
| Boundaries | Whole frames. Merge touching segments. Do not remove under 0.2 s on a locked shot: that is a jump cut for nothing | | @condzxyz, ours |
| Joins that keep sounding wrong | Export a timeline with handles and let a person trim | | @ladprofit |

## Pacing and framing

| Topic | Default | Change it when | Who |
|---|---|---|---|
| Cut rate | Never universal. Measure 1 reference in the same format. **Agents err slow:** they change shots 0.72x as often as the reference and hold their longest static shot 1.5x as long. Editors penalize that, 6.6 win-or-tie points per halving, and do not penalize faster | No reference: 12-25 cuts/min for talks, about 24 for a talking-head ad | [Timeline-Bench](https://arxiv.org/abs/2609.35143), @Emarky (agent-measured), @ladprofit, @MarioJoos |
| Shortest shot on a real face | 1.2 s | Animated Shorts run 0.6-2.5 s, median 1.2 s | @ladprofit, @finnardley |
| Same framing | No longer than 7 s on a one-camera talk | Ads: the camera can stay still, with variation from cuts | @Emarky, @ladprofit |
| Hiding a jump cut | Instant crop on the cut, alternating 1.0 and 1.075, eyes at the same height | Key claim: about 1.3x. Creator style: 1.3x and 1.5x often. 1.5x on 1080p source softens | @condzxyz, @Emarky, @ForwardEditor |
| Long-form intro | 8-25 s | "No golden numbers", same author | @MarioJoos |
| Cold open on an edited talk | Strongest line from later, 2-4 s | | @condzxyz |
| Spoken speed | Never speed up a voice to hit a length. Cut words | | @ladprofit |

## Picture on top of speech

| Topic | Default | Change it when | Who |
|---|---|---|---|
| Time base | Every cut, caption, overlay and sound keys to a word, never to a typed second | | @bozhou_ai, @finnardley, @trq212 |
| Picture cut | On the word, up to 2 frames early | | @ladprofit, @finnardley |
| Overlay reveal | Starts early, so its landing frame sits on the word | A visual must not arrive a whole word before its name | video-use, @bozhou_ai |
| Caption | The frame the word begins, or 1 frame before | UI walkthrough: settled 0.4 s before the click it explains | @finnardley, @elie2222 |
| Caption size, vertical short | 1-3 words, chunked by meaning. No cue under 0.35 s | One word only for very fast Shorts | @darrrragh, video-use, @ladprofit |
| Caption size, long horizontal | Phrase-level, or an SRT at 42 characters and 2 lines | | @condzxyz |
| Caption position | Lower third, inside the safe area, never over the face | Move it if the subject sits there | @ladprofit, HeyGen |
| Accent | 1-2 keywords per block | | @eliana_jordan |
| Text on one screen | At most 5 elements, keywords only. Sentences belong in captions | | @bozhou_ai |
| Text size | 28 px at 1080 is a hard floor; vertical body 30-40 px | 20 px only for brief desktop walkthroughs | @heygalatea, video-use, @elie2222 |
| Easing | Ease-out such as bezier(0.16, 1, 0.3, 1). Never linear | Playful or character work may use springs | @trq212, @shintaro032, video-use |
| Overlay timing, reference set at 24 fps | Reveal 13 frames, stagger 4, overlay in 10, overlay out 8 | | @trq212 |
| Launch-film camera | Moves of 1.5-3 s, half your default speed | "0.7x" is speed, so durations grow about 1.43x. Not for talking-head punch-ins | @jake11moran |
| B-roll share | A style choice, from a reference: 5-10% to 30-50% | | @Emarky |
| B-roll entry | On the word that names it. Return to the speaker after | Skip it if it adds no new information, and never invent it | @ladprofit, @MarioJoos, @DZhao63405 |
| Product UI | Real only. Never invented | Someone else's product: a recording. Your own: rebuild from real captures | @jake11moran, @elie2222, @bozhou_ai |

## Sound

| Topic | Default | Change it when | Who |
|---|---|---|---|
| Master | -14 LUFS, two-pass loudnorm on the final mix. It silently falls back to dynamic mode if true peak would pass the limit, so check `normalization_type` is `linear`, and limit first if not | Voice-only podcast feed: -16. A stated platform spec wins | 6 sources; @Emarky uses -16 |
| True peak | -1.5 dBTP | Never above -1 | @condzxyz, @Emarky, video-use |
| Voice chain | High-pass 80 Hz, de-ess, compressor 3:1, then loudnorm | Low-mid moves only for a boxy room or thin mic, with a person's approval | @Emarky, @condzxyz |
| Music under speech | Duck about 12 dB | Ads: bed 8 dB under the voice. Talks can have none | @condzxyz, @ladprofit, video-use |
| Masking check | Re-transcribe the final mix: at least 95% of words match | | @condzxyz |
| Sound effects | Off by default. Each one is tied to a visible event, with its transient on the frame | Launch films: about 8 per 18 s at most | @ladprofit, @bozhou_ai, video-use |
| Who judges music | A person. Agents cannot hear | | @nateherk, @elie2222 |

## Picture quality and delivery

| Topic | Default | Change it when | Who |
|---|---|---|---|
| Frame rate | One constant rate matching the source: `fps=N,format=yuv420p -fps_mode cfr`, never `-r N` | Mixed cameras: the main camera's rate | @eliana_jordan, video-use |
| HDR phone footage | Convert to SDR before editing. Do not grade your way out | | @darrrragh |
| Log footage | A proper log-to-Rec.709 transform first, then look. A person reviews skin | A hand-written LUT looked fine to a crew and failed with a colorist | @itsohqay, @trq212 |
| Grade | None unless asked. If asked, offer options and let a person choose | | video-use, @trq212 |
| Encode | H.264 CRF 16-18, yuv420p, AAC 256-320k, BT.709, +faststart | Self-hosted web: CRF about 20. Intermediates: CRF 12-14. To tag BT.709, use `setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709` in the graph: a tester found `-colorspace bt709` as an output option really converts untagged footage (34 dB against 51 dB luma PSNR) | @condzxyz, @finnardley, @eliana_jordan |
| Assembly | One filter graph, trimming video by frame number; overlays and subtitles last | Per-segment extract with `-c copy` concat lets you re-render one piece, but encode audio to PCM first or it drifts. See below | ours, @hassancs91 |
| Previews | Rough cut 1-2 min to build, then one full render | One user spent nearly 3 h on 10 renders of a 90 s ad | @ladprofit, @bozhou_ai |

## Rounds to expect

| Situation | Rounds | Who |
|---|---|---|
| New format | 3-5 | @darrrragh 3-4; @williamkast_ v3-v4 |
| Style file already trained | 1-3 | @bozhou_ai, @alexgoughcooper (self-reported) |
| First motion-heavy day | About 20, about 6 h | Ali Abdaal (as summarized by @Jaden_riku) |

If rounds do not fall from video to video, the rules are not being saved or applied.

## Measured on our own test clip

An 85 s talking-head take with planted defects, transcribed locally with Whisper `small.en` (2026-11-03). One clip, so read these as a warning about what can happen and not as rates.

| What we tried | Result |
|---|---|
| Pauses of 0.4 s or more found from the audio | 13 |
| Found from gaps between words, one Whisper pass | 1 |
| Found from gaps between words, one pass per stretch of speech | 12 |
| Words placed badly, one pass / island pass | 23 / 2 |
| Pushing single-pass word times through the edit list | Lost 23 of 222 words |
| Planted false start and a real stutter | Hidden by one pass, exposed by the island pass |
| Per-segment AAC plus `-c copy` concat, 14 cuts | +300 ms against the edit list, about 21 ms per cut |
| One filter graph, trimmed by time | +67 ms, 2 extra frames |
| One filter graph, trimmed by frame number | Exact, video 64.833 s against 64.833 s |
| One-frame slate flash at a join | Every audio check passed it. Frame difference 97, against under 20 at normal joins |
| 140 ms of speech cut at every join, no fades | Fresh transcript still matched the clean cut at 99.1%. `hot_joins` flagged 12 of 13, against 0 of 13 on the clean cut |

`qa_cut.py` also failed correctly when given the raw take: 6 failures, including the opening silence, the repeated sentence and the loudness.
