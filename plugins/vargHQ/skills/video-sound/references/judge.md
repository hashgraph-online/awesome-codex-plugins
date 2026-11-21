# Ranking takes with an LLM judge, without bias

Use an audio LLM judge to shortlist takes and to check the words. Never use it to measure levels or to pick by taste.
Write one yes/no question per known failure, and let a script answer every question a script can. Compute the winner
in code. Compare takes two at a time in both orders, and let a person make the final pick.

For a finished video (frames, loudness, sound after the cut, voice against the script as word error rate), run the
`media-judge` skill first. Its `references/llm-judge.md` has the general protocol and a 476-judgment test on pictures.
This file is the sound part: which sound questions a model can answer, our test on soundtracks, and `scripts/judge_takes.py`.

## The criteria: one question per failure, one checker per question

Modern TTS "stopped failing on artifacts. It fails on subtle things now: prosody, breath placement, expressive
overshoot" ([harrrshall](https://x.com/HarshalsinghCN/status/2060234447681892546)). A criterion is clear when "two
domain experts would independently reach the same pass/fail verdict" ([Anthropic](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)).

| What | Passes when | Checked by | Why that checker |
|---|---|---|---|
| Voice: words | the words match the script line, nothing added, dropped or said wrong | script (transcript diff; `media-judge --script`), then the judge on names | Gemini judged pronunciation with "negligible hallucinations, leveraging Gemini's robust ASR" ([EmergentTTS-Eval](https://arxiv.org/abs/2505.23009)). A transcript lifts audio-judge pronunciation accuracy from 46% to 63% ([AudioJudge](https://arxiv.org/abs/2507.12705)) |
| Voice: tags | no stage direction ("sigh", "exhales") spoken as a word | script (transcript), the judge as backup | speech models sometimes "directly read the words 'sigh' out loud" ([Chiang et al.](https://arxiv.org/abs/2506.05984)); 0 of 16 in our Eleven v4 test |
| Voice: ending | the last syllable is not cut off | the judge, on that take alone | Elie Steinbock's judge scores "pacing, mispronunciations, odd stresses and clipped endings" ([post](https://x.com/elie2222/status/2107186094777434454)) |
| Voice: pace | 140-170 words a minute for narration (dialogue may sit outside on purpose) | `audition.py score` | audio judges told which of two clips was faster 47-55% of the time (AudioJudge) |
| Voice: pauses | each planned pause is there and at least as long as the cue says | script (silence detection) | Gemini judges were weaker on pause length (EmergentTTS-Eval); ours got 3 of 4 |
| Voice: pitch | pitch spread of at least 2 semitones | `audition.py score` | "a spread under 2 semitones reads flat" (digitalsamba pick_takes) |
| Voice: delivery | sounds like the brief ("apologising, not reading") | the judge in pairs, both orders, as a shortlist; a person picks | the best audio judge "still only achieves less than 70% agreement with human preferences" on naturalness ([SpeechJudge](https://arxiv.org/abs/2511.07931)) |
| Dialogue in video | each line said by the right character, in order, nothing extra | the judge on that clip alone, with MM:SS times | Gemini's documented audio uses include transcription and speaker diarization ([docs](https://ai.google.dev/gemini-api/docs/audio)) |
| Lip sync | mouths match the words | a person, or a judge at a raised frame rate | Gemini samples video at 1 frame a second by default; "fast action sequences might lose detail" ([docs](https://ai.google.dev/gemini-api/docs/video-understanding)) |
| Music: tempo, length | BPM and length match the plan | `sound.py beats` | right 3 of 3 in our test |
| Music: quiet part | the planned quiet section is there | script (loudness over time) | the model delivered it 0 of 3 times in our test |
| Music: vocals | no vocals in an instrumental bed | the judge: "describe what you hear", then a text check | "most are speech-trained and return a transcript, not the music" ([wolfram](https://x.com/wolframs91/status/2092881736967315889)) |
| Music: fit | fits the video's mood | a person | a music-quality predictor reached 0.926 rank correlation over whole systems but 0.633 per clip ([MusicEval](https://arxiv.org/abs/2501.10811)); Audiobox Aesthetics predicted people's pick 62.3% of the time, chance 50% ([Zhang et al.](https://arxiv.org/abs/2504.21815)) |
| Effect: there and on time | not silent, its peak within 1 frame of the cue | `sound.py check` | 1 of 5 generated effects came back silent in our test |
| Effect: identity | it is the sound asked for | the judge: describe first, compare in code | audio LLMs "tend to give affirmative answers" to "is there a sound of X?" ([Kuan et al.](https://arxiv.org/abs/2406.08402)) |
| Mix: levels | platform loudness ±1 LUFS, true peak, voice 10 dB or more above music in 300 Hz-4 kHz during every line | `sound.py check` | judges kept 73-93% of verdicts unchanged at 1 dB signal-to-noise (AudioJudge): they hear words through noise you want flagged; ours misread the plain mix's levels |
| Mix: feel | the soundtrack carries the video | a person | no judge in our sources was validated for this |

## Our test: an audio judge on our own soundtracks (2026-11-03)

varg `analyze_video` (Gemini 3.8 Flash on a video; it hears the soundtrack), 30 calls, $1.50. Each pair played as one
video with neutral CLIP A / CLIP B cards, in both orders, scored against measured truth: the designed vs the plain
launch mix (`examples/launch-20s`), a bare vs a breath-tagged take for two voices, and two takes of one line as a control.

| Setup | Mix: designed vs plain | Voices: bare vs tagged (2 pairs) | Control: two near-identical takes |
|---|---|---|---|
| Vague question, 2 runs x 2 orders | the plain mix every time it answered (3 of 3; once no answer) | the tagged take 7 of 8; once "B" in both orders (the slot, not the take) | a confident pick every time; take 2 in run 1, take 1 in run 2 |
| 5 yes/no questions, winner by a fixed rule | right in one order, tie in the other | right in one order each, ties in the other | tie in both orders |
| The same questions, each clip alone | designed 4 of 5 answers right, plain 1 of 5 | pause question 3 of 4 right | not needed |

- Its reasons are not evidence. On the control it explained "the slightly mechanical delivery of Clip A". It reported
  a 54-second timeline for a 41.5-second video, and "chuckling" that is not there.
- The first clip leaks into the second: 6 of 30 answers about the same clip changed with its position. Both pause
  errors came when the bare take played right after a tagged one.
- The rubric removed every wrong winner and decided nothing on its own: each real pair was right in one order and a
  tie in the other, so under the both-orders rule all three are ties. The ranking then comes from scripts and a person.
- Content checks were reliable: "exact words?" and "stage direction read aloud?" matched the transcripts 16 of 16.
- Gemini processes audio inside a video at 1 Kbps on one channel; an audio file gets 16 Kbps, mixed to mono
  ([audio](https://ai.google.dev/gemini-api/docs/audio), [video](https://ai.google.dev/gemini-api/docs/video-understanding)).
  Send audio files when the judge takes them. No judge here can hear stereo width.

Raw replies and pair files: vargHQ/aeo `research/2026-11-03-sound-voice/tests/judge`.

## Twelve rules

1. **Criteria from real failures, one judge per failure.** "In practice, we recommend building a separate judge for
   each failure mode" ([Hamel Husain](https://x.com/HamelHusain/status/2112588257104216294)). Grade real takes before
   writing the prompt: criteria change as people grade ([Shankar et al.](https://arxiv.org/abs/2404.12272)).
2. **Yes/no questions, never 1-5.** "The difference between adjacent points (like 3 vs 4) is subjective"
   ([Husain and Shankar](https://hamel.dev/blog/posts/evals-faq/)). Yes/no checklists raised agreement across judge
   models by 0.45 ([CheckEval](https://arxiv.org/abs/2403.18771)). Each question names one thing and what to ignore.
3. **Describe, don't confirm.** Ask for a transcript and a list of non-word sounds with MM:SS, and check them in code
   (Kuan et al.). Allow "unknown". End with "Don't call the sound good. Report what the checks show"
   ([Woody](https://x.com/woody_research/status/2109296837651738980)).
4. **Reason first; it won't remove bias.** Explanation before the verdict ([Cameron Wolfe](https://x.com/cwolferesearch/status/1815405425866518846)),
   but for audio a chain-of-thought rubric "just inverted the bias from always-B to always-A"
   ([harrrshall](https://x.com/HarshalsinghCN/status/2058882516136968549)).
5. **The winner is computed in code** from the answers. "Which is better" never decides.
6. **Two at a time, both orders, only agreeing verdicts count.** Audio models "pick whichever clip is in slot B, then
   write a confident rationale" (harrrshall). The median model flips 45% of decisive pairs
   ([Lech Mazur](https://x.com/LechMazur/status/2046661738339430489)). Position bias grows with three or four options
   in one prompt ([CALM](https://arxiv.org/abs/2410.02736)): never rank five takes in one call.
7. **One clip alone for yes/no; one stitched file per pair.** Stitching both takes into one file raised pronunciation
   accuracy from 46% to 66% (AudioJudge). Separate clips stop the first leaking into the second.
8. **Comparable and blind.** Same text, same voice, same loudness, same lead-in. Every audio judge AudioJudge tested
   preferred the longer clip; voice timbre shifts emotion verdicts (EmergentTTS-Eval); judges score "refined" answers
   higher without saying so (CALM). Name files p01_ab, never "v2" or "tagged".
9. **Split dimensions.** Three narrow judges (words, delivery, quality) with a majority vote reached 0.912 rank
   correlation with people (AudioJudge). Scoring content and voice apart beat one judge, 0.78 vs 0.62
   ([Neethu Joy](https://x.com/DrNeethuJoy/status/2110968706298007920)).
10. **Repeat, vote, send the unstable to a person.** A majority of 5 runs helped; averaging or best-of-5 did not
    ([Gu et al.](https://arxiv.org/abs/2411.15594)). Sending the 20% most order-unstable pairs to people matched human
    accuracy at 39% lower cost ([Wang et al.](https://arxiv.org/abs/2305.17926)).
11. **A different model family, or proof.** One judge "marked 38% of its own failed unit tests as passed, vs 1.9% for
    other models' code" ([Sword](https://x.com/SwordHQ/status/2102792080808354251)). Husain and Shankar say the same
    model "is usually fine" if it matches human labels; rule 12 decides.
12. **Measure the judge against people.** About 100 labelled examples per failure, passes and fails
    ([Husain](https://hamel.dev/blog/posts/llm-judge/)). Report defects caught apart from good takes passed: one judge
    passed over 95% of good outputs and caught 30-60% of bad ones ([Eugene Yan](https://eugeneyan.com/writing/llm-evaluators/)).
    Use Cohen's kappa, not correlation (kappa 0.3-0.5 vs correlation 0.8-0.9 on the same judge, Yan). Aim at people's
    own agreement, not 100%: about 70% of TTS pairs had full or weak human agreement (SpeechJudge); dialogue style
    r = 0.253 (Chiang et al.). Pin the model, log raw replies, and verify every claim: "Video and audio judges
    hallucinate problems, so verify every claim against frames" (Steinbock).

## Ranking five takes

```bash
S=scripts/judge_takes.py
# 1. filter by script: transcript vs line, pace window, pitch spread, clipping
uv run --with librosa python3 scripts/audition.py score sound/audition/audition.json
# 2. each surviving take alone: send the take + this prompt, save the reply, let code decide
python3 $S prompt take --line "I didn't mean to break it. I'm sorry." > take_prompt.txt
python3 $S check replies/take3.json --line "I didn't mean to break it. I'm sorry." --need-breath   # exit 1 = fail
# 3. survivors two at a time, both orders, blind file names, one narrow question per call
python3 $S make takes/t1.mp3 takes/t3.mp3 takes/t4.mp3 -o sound/judge/          # --video for video-only judges
python3 $S prompt pair --question "Which take sounds more like someone apologising than reading?"
# 4. verdicts.json = {"p01_ab": "A", "p01_ba": "tie", ...}: wins count only when both orders agree
python3 $S tally sound/judge/pairs.json sound/judge/verdicts.json
```

A take passes step 2 when every answer is "no", the transcript matches and, with `--need-breath`, a breath is listed.
"Unknown" goes to a person. Five takes make 10 pairs, so 20 calls per question: about $1 at 5 credits a call on
`analyze_video`. Pairs that split across orders go to a person. **STOP:** a person listens to the top 2-3 on headphones
and on a phone, and picks. Their pick and reason become labels for rule 12.

## Sources

Audio and speech judges: [AudioJudge](https://arxiv.org/abs/2507.12705), [SpeechJudge](https://arxiv.org/abs/2511.07931),
[EmergentTTS-Eval](https://arxiv.org/abs/2505.23009), [Chiang et al.](https://arxiv.org/abs/2506.05984),
[Kuan et al.](https://arxiv.org/abs/2406.08402), [MusicEval](https://arxiv.org/abs/2501.10811),
[Zhang et al.](https://arxiv.org/abs/2504.21815), Gemini [audio](https://ai.google.dev/gemini-api/docs/audio) and
[video](https://ai.google.dev/gemini-api/docs/video-understanding) docs. Bias and rubrics: [CALM](https://arxiv.org/abs/2410.02736),
[CheckEval](https://arxiv.org/abs/2403.18771), [Wang et al.](https://arxiv.org/abs/2305.17926),
[Gu et al.](https://arxiv.org/abs/2411.15594), [Shankar et al.](https://arxiv.org/abs/2404.12272). Calibration:
[Husain](https://hamel.dev/blog/posts/llm-judge/), [Husain and Shankar](https://hamel.dev/blog/posts/evals-faq/),
[Eugene Yan](https://eugeneyan.com/writing/llm-evaluators/), [Anthropic](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents).
The 143 judge findings (73 from X, 70 from papers and docs) with quotes are in vargHQ/aeo
`research/2026-11-03-sound-voice/judge`.
